"""Tool implementations for the Campus Customs chat agent.

Reads directly from data/campus_customs.db (read-only) — never writes to it.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from models import ProductCard, ProductDetails, StockBySize

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT.parent / "data" / "campus_customs.db"
PRODUCTS_DIR = ROOT.parent / "data" / "products"
TRANSPARENT_DIR = ROOT.parent / "data" / "products_transparent"


class ProductNotFoundError(LookupError):
    """Raised when a product_id doesn't exist in the catalogue."""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def image_url_for(image_file_path: str) -> str:
    stem = Path(image_file_path).stem
    if (TRANSPARENT_DIR / f"{stem}.png").exists():
        return f"/images-cutout/{stem}.png"
    return f"/images/{Path(image_file_path).name}"


_SIZE_ALIASES = {
    "xs": "XS", "extra small": "XS", "x-small": "XS", "xsmall": "XS",
    "s": "S", "small": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L",
    "xl": "XL", "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "extra extra large": "XXL", "xx-large": "XXL", "xxlarge": "XXL",
}


def _normalize_size(size: str) -> str:
    """Map a size given as a word ("medium") or loose casing to the DB's exact code
    ("M"), since the model won't always phrase it exactly the way inventory stores it.
    """
    return _SIZE_ALIASES.get(size.strip().lower(), size.strip().upper())


def _term_variants(term: str) -> set[str]:
    """The catalogue only stores singular forms ("hoodie", never "hoodies"), but
    customers naturally ask in the plural, so also try a naive singular form.
    """
    t = term.strip()
    variants = {t}
    if len(t) > 3 and t.lower().endswith("s"):
        variants.add(t[:-1])
    return variants


def _in_stock_sizes_map(conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, list[str]]:
    """One bulk query for which sizes are in stock (quantity > 0) for a set of products,
    instead of a query per product.
    """
    if not product_ids:
        return {}
    placeholders = ",".join("?" for _ in product_ids)
    rows = conn.execute(
        f"SELECT product_id, size FROM inventory WHERE quantity > 0 AND product_id IN ({placeholders}) "
        "ORDER BY CASE size WHEN 'XS' THEN 0 WHEN 'S' THEN 1 WHEN 'M' THEN 2 "
        "WHEN 'L' THEN 3 WHEN 'XL' THEN 4 WHEN 'XXL' THEN 5 ELSE 6 END",
        product_ids,
    ).fetchall()
    result: dict[str, list[str]] = {}
    for row in rows:
        result.setdefault(row["product_id"], []).append(row["size"])
    return result


def _rows_to_cards(conn: sqlite3.Connection, rows: list[sqlite3.Row]) -> list[ProductCard]:
    sizes_map = _in_stock_sizes_map(conn, [row["product_id"] for row in rows])
    return [
        ProductCard(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            price=row["price"],
            image_url=image_url_for(row["image_file_path"]),
            description=row["description"],
            in_stock_sizes=sizes_map.get(row["product_id"], []),
        )
        for row in rows
    ]


def search_products(query: str, limit: int | None = 6) -> list[ProductCard]:
    """Search the catalogue by name, garment type, description, or search tags.
    limit=None returns every match, for category/type browsing.
    """
    clauses = []
    params: list[str | int] = []
    for term in _term_variants(query):
        like = f"%{term}%"
        clauses.append("(name LIKE ? OR garment_type LIKE ? OR description LIKE ? OR search_tags LIKE ?)")
        params.extend([like, like, like, like])

    sql = f"SELECT * FROM catalogue WHERE {' OR '.join(clauses)} ORDER BY name"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)

    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return _rows_to_cards(conn, rows)
    finally:
        conn.close()


def find_products(
    category: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> list[ProductCard]:
    """Find products matching any combination of category, max price, and a size that must
    be in stock, in a single query — for questions that combine several filters at once
    (e.g. "hoodies under $60 in medium"). Any filter left as None is simply not applied.
    """
    from_clause = "catalogue c"
    clauses: list[str] = []
    params: list[str | int | float] = []

    if size is not None:
        from_clause = "catalogue c JOIN inventory i ON i.product_id = c.product_id"
        clauses.append("i.size = ? AND i.quantity > 0")
        params.append(_normalize_size(size))

    if category is not None:
        cat_clauses = []
        for term in _term_variants(category):
            like = f"%{term}%"
            cat_clauses.append("(c.garment_type LIKE ? OR c.name LIKE ? OR c.search_tags LIKE ?)")
            params.extend([like, like, like])
        clauses.append("(" + " OR ".join(cat_clauses) + ")")

    if max_price is not None:
        clauses.append("c.price <= ?")
        params.append(max_price)

    where_sql = " AND ".join(clauses) if clauses else "1=1"
    sql = f"SELECT DISTINCT c.* FROM {from_clause} WHERE {where_sql} ORDER BY c.price ASC"

    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return _rows_to_cards(conn, rows)
    finally:
        conn.close()


def get_product_details(product_id: str) -> ProductDetails:
    """Full catalogue record for one product_id (get product_id from search_products first)."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        raise ProductNotFoundError(f"No product found with product_id '{product_id}'. Campus Customs doesn't carry it.")

    return ProductDetails(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        price=row["price"],
        image_url=image_url_for(row["image_file_path"]),
    )


def check_stock(product_id: str) -> list[StockBySize]:
    """Look up stock by size for one product_id (get product_id from search_products first)."""
    conn = get_connection()
    try:
        exists = conn.execute("SELECT 1 FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if exists is None:
            raise ProductNotFoundError(
                f"No product found with product_id '{product_id}'. Campus Customs doesn't carry it."
            )

        rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY "
            "CASE size WHEN 'XS' THEN 0 WHEN 'S' THEN 1 WHEN 'M' THEN 2 "
            "WHEN 'L' THEN 3 WHEN 'XL' THEN 4 WHEN 'XXL' THEN 5 ELSE 6 END",
            (product_id,),
        ).fetchall()
    finally:
        conn.close()

    return [StockBySize(size=row["size"], quantity=row["quantity"]) for row in rows]
