import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
import traceback
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent as chat_agent
from models import ChatHistoryMessage, ChatReply, ChatRequest, CustomerInfo, ProductCard

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "campus_customs.db"
PRODUCTS_DIR = BASE_DIR / "data" / "products"
TRANSPARENT_DIR = BASE_DIR / "data" / "products_transparent"

PBKDF2_ITERATIONS = 120_000

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("campus_customs.main")


def _redact_secrets(text: str) -> str:
    """Strip the Portkey API key out of a log line, in case it ever ends up in an
    error message somewhere down the stack.
    """
    key = os.environ.get("PORTKEY_API_KEY")
    return text.replace(key, "[REDACTED]") if key else text

# token -> user_id. Lives only as long as this backend process does; a restart
# signs everyone out and they simply log in again (passwords are unaffected).
SESSIONS: dict[str, int] = {}

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=PRODUCTS_DIR), name="images")
app.mount("/images-cutout", StaticFiles(directory=TRANSPARENT_DIR), name="images-cutout")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_write_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt, hex_digest = stored_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), hex_digest)


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductSummary(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float
    image_url: str
    in_stock_sizes: list[str] = []


class ProductDetail(ProductSummary):
    search_tags: list[str]
    sizes: list[SizeStock]


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut


def row_to_user(row: sqlite3.Row) -> UserOut:
    return UserOut(
        id=row["id"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
        email=row["email"],
    )


def current_user_row_optional(authorization: str | None) -> sqlite3.Row | None:
    """Resolve the logged-in user strictly from the session token — never from anything
    the browser could claim about who it is — so nobody can read someone else's chat
    history by sending a different user id. Returns None for a guest (no/invalid token);
    that's a normal case here, not an error.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    user_id = SESSIONS.get(authorization.removeprefix("Bearer "))
    if user_id is None:
        return None
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT id, first_name, last_name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def current_user_row(authorization: str | None) -> sqlite3.Row:
    row = current_user_row_optional(authorization)
    if row is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return row


def image_url_for(image_file_path: str) -> str:
    stem = Path(image_file_path).stem
    if (TRANSPARENT_DIR / f"{stem}.png").exists():
        return f"/images-cutout/{stem}.png"
    return f"/images/{Path(image_file_path).name}"


def row_to_summary(row: sqlite3.Row, in_stock_sizes: list[str]) -> ProductSummary:
    return ProductSummary(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        price=row["price"],
        image_url=image_url_for(row["image_file_path"]),
        in_stock_sizes=in_stock_sizes,
    )


def in_stock_sizes_by_product(conn: sqlite3.Connection) -> dict[str, list[str]]:
    rows = conn.execute(
        "SELECT product_id, size FROM inventory WHERE quantity > 0 ORDER BY "
        "CASE size WHEN 'XS' THEN 0 WHEN 'S' THEN 1 WHEN 'M' THEN 2 "
        "WHEN 'L' THEN 3 WHEN 'XL' THEN 4 WHEN 'XXL' THEN 5 ELSE 6 END"
    ).fetchall()
    result: dict[str, list[str]] = {}
    for row in rows:
        result.setdefault(row["product_id"], []).append(row["size"])
    return result


@app.get("/api/products", response_model=list[ProductSummary])
def list_products():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        sizes_map = in_stock_sizes_by_product(conn)
        return [row_to_summary(row, sizes_map.get(row["product_id"], [])) for row in rows]
    finally:
        conn.close()


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")

        size_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY "
            "CASE size WHEN 'XS' THEN 0 WHEN 'S' THEN 1 WHEN 'M' THEN 2 "
            "WHEN 'L' THEN 3 WHEN 'XL' THEN 4 WHEN 'XXL' THEN 5 ELSE 6 END",
            (product_id,),
        ).fetchall()

        in_stock_sizes = [r["size"] for r in size_rows if r["quantity"] > 0]
        summary = row_to_summary(row, in_stock_sizes)
        return ProductDetail(
            **summary.model_dump(),
            search_tags=json.loads(row["search_tags"]),
            sizes=[SizeStock(size=r["size"], quantity=r["quantity"]) for r in size_rows],
        )
    finally:
        conn.close()


@app.post("/api/auth/signup", response_model=AuthResponse)
def signup(payload: SignupRequest):
    first_name = payload.first_name.strip()
    last_name = payload.last_name.strip()
    email = payload.email.strip().lower()

    if not first_name or not last_name:
        raise HTTPException(status_code=400, detail="First and last name are required")
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    conn = get_write_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE LOWER(email) = ?", (email,)
        ).fetchone()
        if existing is not None:
            raise HTTPException(status_code=409, detail="An account with that email already exists")

        password_hash = hash_password(payload.password)
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash, first_name, last_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (f"{first_name} {last_name}", email, password_hash, first_name, last_name),
        )
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()

    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user_id
    return AuthResponse(
        token=token,
        user=UserOut(id=user_id, first_name=first_name, last_name=last_name, email=email),
    )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, first_name, last_name, email, password_hash FROM users WHERE LOWER(email) = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = secrets.token_urlsafe(32)
    SESSIONS[token] = row["id"]
    return AuthResponse(token=token, user=row_to_user(row))


@app.get("/api/auth/me", response_model=UserOut)
def me(authorization: str | None = Header(default=None)):
    return row_to_user(current_user_row(authorization))


@app.post("/api/auth/logout")
def logout(authorization: str | None = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        SESSIONS.pop(authorization.removeprefix("Bearer "), None)
    return {"status": "ok"}


CHAT_HISTORY_TURNS_FOR_AGENT = 10
CHAT_HISTORY_MESSAGES_FOR_PANEL = 50


def save_chat_message(user_id: int, role: str, content: str, products: list[ProductCard] | None = None) -> None:
    conn = get_write_connection()
    try:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (
                user_id,
                role,
                content,
                json.dumps([p.model_dump() for p in products]) if products else None,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def load_recent_history(user_id: int, limit: int) -> list[tuple[str, str]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE user_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()
    return [(row["role"], row["content"]) for row in reversed(rows)]


@app.post("/api/chat", response_model=ChatReply)
async def chat(payload: ChatRequest, authorization: str | None = Header(default=None)):
    user_row = current_user_row_optional(authorization)
    customer = (
        CustomerInfo(
            first_name=user_row["first_name"] or "",
            last_name=user_row["last_name"] or "",
            email=user_row["email"],
        )
        if user_row is not None
        else None
    )
    history = load_recent_history(user_row["id"], CHAT_HISTORY_TURNS_FOR_AGENT) if user_row is not None else []

    try:
        reply = await chat_agent.run_chat(
            payload.message,
            customer=customer,
            page=payload.page,
            history=history,
            user_id=user_row["id"] if user_row is not None else None,
        )
    except KeyError:
        logger.error("Chat request failed: PORTKEY_API_KEY is not set (check backend/.env)")
        raise HTTPException(status_code=503, detail="Chat is not configured (missing PORTKEY_API_KEY).")
    except Exception:
        logger.error("Chat request failed:\n%s", _redact_secrets(traceback.format_exc()))
        raise HTTPException(status_code=502, detail="The chat assistant is unavailable right now.")

    if user_row is not None:
        save_chat_message(user_row["id"], "user", payload.message)
        save_chat_message(user_row["id"], "assistant", reply.reply, reply.products)

    return reply


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(authorization: str | None = Header(default=None)):
    user_row = current_user_row(authorization)
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (user_row["id"], CHAT_HISTORY_MESSAGES_FOR_PANEL),
        ).fetchall()
    finally:
        conn.close()

    messages = []
    for row in reversed(rows):
        products_data = json.loads(row["products_json"]) if row["products_json"] else []
        messages.append(
            ChatHistoryMessage(
                role=row["role"],
                content=row["content"],
                products=[ProductCard(**p) for p in products_data],
            )
        )
    return messages


@app.get("/api/health")
def health():
    return {"status": "ok"}
