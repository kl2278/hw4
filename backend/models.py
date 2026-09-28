"""Pydantic types used by the chat agent (backend/agent.py, backend/tools.py)
and the /api/chat route in backend/main.py.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProductCard(BaseModel):
    """Product info the chat UI needs to render a product card, and enough for the
    Products page's client-side category/size filters to work on chat results too.
    """

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    description: str
    in_stock_sizes: list[str] = Field(
        default_factory=list,
        description=(
            "Sizes with quantity > 0 for this product, as of the search. This is a quick "
            "preview for filtering/browsing only — for a specific stock question, still call "
            "check_stock_tool for exact quantities and full out-of-stock reporting."
        ),
    )


class ProductDetails(BaseModel):
    """Full catalogue record for one product, for price/description/color questions."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float
    image_url: str


class StockBySize(BaseModel):
    size: str
    quantity: int = Field(description="0 means that size is out of stock, not unavailable/not carried.")


class PageContext(BaseModel):
    """Where the shopper is on the site right now, sent with every chat message so the
    agent doesn't have to guess what "this" or "it" refers to.
    """

    path: str
    product_id: str | None = Field(
        default=None,
        description="Set when the shopper is on a product detail page, to that product's product_id.",
    )


class CustomerInfo(BaseModel):
    """The only user fields the chat agent ever sees. Never include password_hash here."""

    first_name: str
    last_name: str
    email: str


class ChatRequest(BaseModel):
    message: str
    page: PageContext | None = None


class ChatHistoryMessage(BaseModel):
    """One saved turn, returned to the front end to repopulate the chat panel."""

    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatReply(BaseModel):
    reply: str = Field(description="The assistant's natural-language reply to show in the chat panel.")
    products: list[ProductCard] = Field(
        default_factory=list,
        description="Products mentioned in the reply, so the front end can render them as cards.",
    )
    search_query: str | None = Field(
        default=None,
        description=(
            "Set only when this reply is browsing a whole category/type of item (e.g. the "
            "customer asked 'what hoodies do you have'), to the term searched for (e.g. "
            "'hoodies'). The front end uses this to replace the Products page grid with "
            "'products' and label it 'Showing results for: <search_query>'. Leave null for "
            "any other kind of reply."
        ),
    )


class AuditEntry(BaseModel):
    """One step of one agent run, appended to output/audit_trail.json.

    That file is public on GitHub, so this model is deliberately narrow: `who`
    is only ever "guest" or "user:<id>" (never a name or email), and
    `tool_args`/`result` are short, redacted strings built by `backend/audit.py`
    — never a password, password hash, or the Portkey API key.
    """

    timestamp: str = Field(description="UTC ISO-8601 timestamp.")
    run_id: str = Field(description="Short id shared by every entry from one chat message's run, so they group together.")
    step: int = Field(description="1-indexed step within this run.")
    event: str = Field(
        description=(
            'What happened at this step: "model_call" (the model was invoked), "tool_call" '
            '(the model decided to call a tool), "tool_result" (a tool\'s result was fed back '
            'to the model), or "run_end" (the run finished — see stop_reason). Always set, so '
            "no entry is ever all-null."
        )
    )
    who: str = Field(description='"guest" or "user:<id>" — never a name or email.')
    tool_name: str | None = Field(default=None, description="Tool called at this step, if any.")
    tool_args: str | None = Field(default=None, description="Trimmed, redacted JSON of the tool's arguments.")
    result: str | None = Field(default=None, description="Trimmed, redacted summary of a tool's return value.")
    stop_reason: str | None = Field(
        default=None,
        description=(
            'Why the run ended (e.g. "completed", "content filter", "hit the loop limit", '
            '"error"). Only set on the final entry of a run.'
        ),
    )
