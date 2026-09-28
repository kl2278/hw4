"""Sets up the Campus Customs chat agent: PydanticAI wired to an OpenAI-compatible
model through the Portkey gateway. Mirrors the pattern from Homework 3's agent.py.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, CallToolsNode, ModelRequestNode, ModelRetry, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits
try:
    from pydantic_ai.models.openai import OpenAIModel
except ImportError:  # Compatibility with older pydantic-ai releases.
    from pydantic_ai.models.openai import OpenAIChatModel as OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

import audit
import tools
from models import AuditEntry, ChatReply, CustomerInfo, PageContext, ProductCard, ProductDetails, StockBySize

# Hard cap on how much work one chat message can trigger, so a confused or
# adversarial loop can't run indefinitely (or run up API cost indefinitely).
MAX_MODEL_CALLS_PER_MESSAGE = 8
MAX_TOOL_CALLS_PER_MESSAGE = 8
USAGE_LIMITS = UsageLimits(
    request_limit=MAX_MODEL_CALLS_PER_MESSAGE,
    tool_calls_limit=MAX_TOOL_CALLS_PER_MESSAGE,
)

LOOP_LIMIT_REPLY = ChatReply(
    reply=(
        "That question took a lot of back-and-forth checking! Let's try it as a "
        "smaller question — ask about one product or one thing at a time and "
        "I'll be able to help better."
    ),
    products=[],
)


@dataclass
class ChatDeps:
    """Per-run context: who's chatting (None for a guest), what page they're on, and
    their recent conversation history (oldest first) if they're logged in.
    """

    customer: CustomerInfo | None
    page: PageContext | None
    history: list[tuple[str, str]] = field(default_factory=list)

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / ".env")  # .env lives at the project root, not in backend/
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

logger = logging.getLogger("campus_customs.agent")

CONTENT_FILTER_REPLY = ChatReply(
    reply=(
        "I can't help with that one. Let's get back to Yale gear — I'm happy to help "
        "you find a hoodie, crewneck, or tee, or answer questions about sizing and stock."
    ),
    products=[],
)


def _is_content_filter_block(exc: ModelHTTPError) -> bool:
    """True if the model provider (e.g. Azure OpenAI) blocked the request as unsafe,
    rather than the request actually failing.
    """
    body = exc.body
    return isinstance(body, dict) and body.get("code") == "content_filter"


def build_client() -> AsyncOpenAI:
    portkey_key = os.environ["PORTKEY_API_KEY"]
    return AsyncOpenAI(
        api_key=portkey_key,
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-api-key": portkey_key},
    )


def search_products_tool(query: str, all_matches: bool = False) -> list[ProductCard]:
    """Search the Campus Customs catalogue for products matching a name, category, or keyword.
    Set all_matches=True when the customer is browsing a whole type/category of item (e.g.
    "what hoodies do you have") so every match comes back, instead of just the top few — the
    front end uses a full category result set to replace the Products page grid. Leave
    all_matches=False for a narrower or specific-product question.
    Returns an empty list if nothing matches — that means Campus Customs doesn't carry it, not
    that the search failed. If more than one result comes back for a specific-product question,
    ask the customer which one they mean (or show the options) rather than picking one for them.
    """
    return tools.search_products(query, limit=None if all_matches else 6)


def get_product_details_tool(product_id: str) -> ProductDetails:
    """Get the full catalogue record (description, price, colors) for one product_id.
    Get the product_id from search_products_tool first — never guess one.
    """
    try:
        return tools.get_product_details(product_id)
    except tools.ProductNotFoundError as exc:
        raise ModelRetry(str(exc)) from exc


def check_stock_tool(product_id: str) -> list[StockBySize]:
    """Look up stock by size for a specific product_id. Get the product_id from
    search_products_tool first — never guess one. Every size is always included, even
    ones with quantity 0 (out of stock) — report those explicitly as out of stock rather
    than omitting them or saying the size isn't carried at all.
    """
    try:
        return tools.check_stock(product_id)
    except tools.ProductNotFoundError as exc:
        raise ModelRetry(str(exc)) from exc


def filter_products_tool(
    category: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> list[ProductCard]:
    """Find products matching any combination of a category/type, a max price, and a size
    that must be in stock — all in one call. Use this instead of search_products_tool plus
    a separate check_stock_tool per candidate whenever the customer gives more than one
    filter at once (e.g. "hoodies under $60 in medium", "crewnecks in large"). Leave a
    filter as None if the customer didn't specify it. Results are sorted cheapest first.
    Also useful for finding in-stock alternatives: if check_stock_tool shows a product is
    out of stock in a size, call this with that product's category and the requested size
    to suggest similar products that do have it.
    """
    return tools.find_products(category=category, max_price=max_price, size=size)


def build_context_prompt(ctx: RunContext[ChatDeps]) -> str:
    """Dynamic system prompt addition: who's chatting and what page they're on, evaluated
    fresh for every run since it depends on the request's deps, not the static prompt file.
    """
    deps = ctx.deps
    lines: list[str] = []

    if deps.customer is not None:
        lines.append(
            f"The shopper is logged in as {deps.customer.first_name} {deps.customer.last_name} "
            f"(email: {deps.customer.email}). You may greet them by first name and, if asked, "
            f"confirm their own name or email using exactly these values — never state a "
            f"different name or email, and never mention, guess at, or discuss a password or "
            f"password hash; you don't have access to that and never will."
        )
    else:
        lines.append(
            "This shopper is a guest — not logged in. Don't address them by name. If they ask "
            "about 'my account' or similar, tell them they'll need to log in first."
        )

    if deps.page is not None:
        if deps.page.product_id:
            lines.append(
                f"The shopper is currently viewing the product page for product_id "
                f"'{deps.page.product_id}'. If they refer to 'this', 'it', or 'this product' "
                f"without naming it, assume they mean this product_id and look it up with the "
                f"tools — don't ask them which product they mean."
            )
        else:
            lines.append(f"The shopper is currently on the page at path '{deps.page.path}'.")

    if deps.history:
        transcript = "\n".join(f"{role}: {content}" for role, content in deps.history)
        lines.append("Recent conversation with this shopper so far, oldest first:\n" + transcript)

    return "\n\n".join(lines)


def build_agent(client: AsyncOpenAI) -> Agent[ChatDeps, ChatReply]:
    system_prompt = (ROOT / "prompts" / "prompt.md").read_text(encoding="utf-8")
    model = OpenAIModel("gpt-5.6-luna", provider=OpenAIProvider(openai_client=client))
    agent = Agent(model, deps_type=ChatDeps, output_type=ChatReply, system_prompt=system_prompt)
    agent.system_prompt(build_context_prompt)
    agent.tool_plain(search_products_tool)
    agent.tool_plain(get_product_details_tool)
    agent.tool_plain(check_stock_tool)
    agent.tool_plain(filter_products_tool)
    return agent


_client: AsyncOpenAI | None = None
_agent: Agent[ChatDeps, ChatReply] | None = None


def get_agent() -> Agent[ChatDeps, ChatReply]:
    """Lazily build the client + agent once per process and reuse them across requests."""
    global _client, _agent
    if _agent is None:
        _client = build_client()
        _agent = build_agent(_client)
    return _agent


def _who(user_id: int | None) -> str:
    """Never a name or email — only what's safe to write to a public audit log."""
    return f"user:{user_id}" if user_id is not None else "guest"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tool_call_from(model_response) -> tuple[str | None, str | None]:
    for part in model_response.parts:
        if part.part_kind == "tool-call" and not part.tool_name.startswith("final_result"):
            args = part.args
            if isinstance(args, str):
                args = json.loads(args) if args else {}
            return part.tool_name, audit.trim(args or {})
    return None, None


def _tool_return_from(request) -> tuple[str | None, str | None]:
    for part in request.parts:
        if part.part_kind == "tool-return":
            return part.tool_name, audit.trim(part.content)
    return None, None


async def _run_with_audit(message: str, deps: ChatDeps, who: str) -> ChatReply:
    """Runs the agent step by step (instead of a plain agent.run(...)) so every
    step can be appended to the audit trail, with a dedicated "run_end" entry
    recording the outcome even if the run errors out or hits the loop limit.
    """
    run_id = uuid.uuid4().hex[:8]
    entries: list[AuditEntry] = []
    step = 0
    stop_reason = "completed"

    def log(event: str, **fields) -> None:
        nonlocal step
        step += 1
        entries.append(AuditEntry(timestamp=_now(), run_id=run_id, step=step, event=event, who=who, **fields))

    try:
        async with get_agent().iter(message, deps=deps, usage_limits=USAGE_LIMITS) as run:
            async for node in run:
                if isinstance(node, CallToolsNode):
                    tool_name, tool_args = _tool_call_from(node.model_response)
                    if tool_name is not None:
                        log("tool_call", tool_name=tool_name, tool_args=tool_args)
                elif isinstance(node, ModelRequestNode):
                    tool_name, result = _tool_return_from(node.request)
                    if tool_name is not None:
                        log("tool_result", tool_name=tool_name, result=result)
                    log("model_call")
            return run.result.output
    except UsageLimitExceeded:
        stop_reason = "hit the loop limit"
        raise
    except ModelHTTPError as exc:
        stop_reason = "content filter" if _is_content_filter_block(exc) else f"error: {type(exc).__name__}"
        raise
    except Exception as exc:
        stop_reason = f"error: {type(exc).__name__}"
        raise
    finally:
        log("run_end", stop_reason=stop_reason)
        try:
            audit.append_entries(entries)
        except Exception:
            # Audit logging is a side effect, never allowed to break the
            # actual chat reply — if it somehow fails, log it and move on.
            logger.exception("Failed to append to the audit trail")


async def run_chat(
    message: str,
    customer: CustomerInfo | None = None,
    page: PageContext | None = None,
    history: list[tuple[str, str]] | None = None,
    user_id: int | None = None,
) -> ChatReply:
    deps = ChatDeps(customer=customer, page=page, history=history or [])
    who = _who(user_id)
    try:
        return await _run_with_audit(message, deps, who)
    except UsageLimitExceeded:
        logger.warning("Chat message hit the per-message model/tool call limit (who=%s)", who)
        return LOOP_LIMIT_REPLY
    except ModelHTTPError as exc:
        if _is_content_filter_block(exc):
            logger.warning(
                "Chat message blocked by the model provider's content filter (status %s)",
                exc.status_code,
            )
            return CONTENT_FILTER_REPLY
        raise
