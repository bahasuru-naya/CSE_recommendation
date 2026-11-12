"""Database Explorer — exposes schema/table metadata and paginated table data."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import get_db

router = APIRouter()

# Schemas we expose (whitelist for safety)
ALLOWED_SCHEMAS = {"raw", "staging", "core", "features", "ml", "app"}


@router.get("/schemas")
def list_schemas(db: Session = Depends(get_db)):
    """List all lake schemas with their tables and row counts."""
    result = {}
    for schema in sorted(ALLOWED_SCHEMAS):
        # Get tables in schema
        tables_q = text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [r[0] for r in db.execute(tables_q, {"schema": schema}).fetchall()]
        schema_info = {}
        for tbl in tables:
            try:
                cnt = db.execute(text(f"SELECT COUNT(*) FROM {schema}.{tbl}")).scalar()
                schema_info[tbl] = {"row_count": cnt}
            except Exception:
                schema_info[tbl] = {"row_count": -1}
        result[schema] = schema_info
    return result


@router.get("/table/{schema}/{table}")
def get_table_data(
    schema: str,
    table: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    search: str | None = Query(default=None),
    sort_col: str | None = Query(default=None),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Return paginated rows from a table with optional full-text search."""
    if schema not in ALLOWED_SCHEMAS:
        raise HTTPException(status_code=403, detail=f"Schema '{schema}' not allowed")

    # Validate table exists
    check = db.execute(text("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = :s AND table_name = :t AND table_type = 'BASE TABLE'
    """), {"s": schema, "t": table}).scalar()
    if not check:
        raise HTTPException(status_code=404, detail=f"Table {schema}.{table} not found")

    # Get column names and types
    cols_q = text("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = :s AND table_name = :t
        ORDER BY ordinal_position
    """)
    cols = db.execute(cols_q, {"s": schema, "t": table}).fetchall()
    columns = [{"name": c[0], "type": c[1]} for c in cols]
    col_names = [c["name"] for c in columns]

    offset = (page - 1) * page_size

    # Search: cast every column to text and ILIKE
    where_clause = ""
    params: dict[str, Any] = {"limit": page_size, "offset": offset}
    if search and search.strip():
        search_parts = [f"CAST({cn} AS TEXT) ILIKE :search" for cn in col_names]
        where_clause = f"WHERE ({' OR '.join(search_parts)})"
        params["search"] = f"%{search.strip()}%"

    # Sort
    sort_expr = ""
    if sort_col and sort_col in col_names:
        sort_expr = f"ORDER BY {sort_col} {sort_dir.upper()}"
    else:
        # Default sort: first column desc if it looks like a date/id
        default_sort = next(
            (c for c in col_names if c in ("id", "created_at", "trading_date", "as_of_date", "run_id", "started_at")),
            col_names[0],
        )
        sort_expr = f"ORDER BY {default_sort} {sort_dir.upper()}"

    # Count
    count_q = text(f"SELECT COUNT(*) FROM {schema}.{table} {where_clause}")
    total = db.execute(count_q, params).scalar()

    # Data
    data_q = text(f"SELECT * FROM {schema}.{table} {where_clause} {sort_expr} LIMIT :limit OFFSET :offset")
    rows = db.execute(data_q, params).fetchall()

    def serialize(v):
        if v is None:
            return None
        if isinstance(v, (int, float, bool)):
            return v
        try:
            return str(v)
        except Exception:
            return repr(v)

    data = [
        {col_names[i]: serialize(val) for i, val in enumerate(row)}
        for row in rows
    ]

    return {
        "schema": schema,
        "table": table,
        "columns": columns,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, -(-total // page_size)),  # ceiling division
        "data": data,
    }
