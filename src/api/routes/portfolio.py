"""Portfolio and Watchlist API endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import get_db

router = APIRouter()


class PositionCreate(BaseModel):
    symbol: str
    entry_price: float
    quantity: int
    entry_date: date | None = None
    stop_loss: float | None = None
    target_price: float | None = None
    notes: str | None = None


class WatchlistCreate(BaseModel):
    symbol: str
    reason: str | None = None
    alert_price_above: float | None = None
    alert_price_below: float | None = None


@router.get("/positions")
def list_positions(status: str = "open", db: Session = Depends(get_db)):
    """List portfolio positions (supports status: 'open', 'closed', or 'all')."""
    clauses = []
    params: dict[str, Any] = {}
    if status and status.lower() != "all":
        clauses.append("p.status = :status")
        params["status"] = status.lower()

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    query = text(f"""
        SELECT p.id, p.security_id, p.symbol, p.side, p.entry_date, p.entry_price,
               p.quantity,
               COALESCE(p.exit_price, curr.close, p.current_price, p.entry_price) AS current_price,
               p.stop_loss, p.target_price, p.exit_date, p.exit_price,
               COALESCE(p.pnl, (COALESCE(p.exit_price, curr.close, p.current_price, p.entry_price) - p.entry_price) * p.quantity) AS pnl,
               COALESCE(p.pnl_pct, ((COALESCE(p.exit_price, curr.close, p.current_price, p.entry_price) - p.entry_price) / NULLIF(p.entry_price, 0)) * 100) AS pnl_pct,
               p.status, p.notes, s.logo_url
        FROM app.portfolio_positions p
        LEFT JOIN core.dim_security s ON UPPER(s.symbol) = UPPER(p.symbol)
        LEFT JOIN LATERAL (
            SELECT close FROM core.fact_price_daily
            WHERE security_id = p.security_id
            ORDER BY trading_date DESC LIMIT 1
        ) curr ON TRUE
        {where_sql}
        ORDER BY
            CASE WHEN p.status = 'open' THEN 0 ELSE 1 END,
            p.entry_date DESC,
            p.id DESC
    """)
    rows = db.execute(query, params).fetchall()
    return [
        {
            "id": r[0],
            "security_id": r[1],
            "symbol": r[2],
            "side": r[3],
            "entry_date": str(r[4]),
            "entry_price": float(r[5]),
            "quantity": r[6],
            "current_price": float(r[7]),
            "stop_loss": float(r[8]) if r[8] else None,
            "target_price": float(r[9]) if r[9] else None,
            "exit_date": str(r[10]) if r[10] else None,
            "exit_price": float(r[11]) if r[11] else None,
            "pnl": round(float(r[12]), 2) if r[12] is not None else 0.0,
            "pnl_pct": round(float(r[13]), 2) if r[13] is not None else 0.0,
            "status": r[14],
            "notes": r[15],
            "logo_url": r[16],
        }
        for r in rows
    ]


@router.post("/positions")
def add_position(pos: PositionCreate, db: Session = Depends(get_db)):
    """Add a new open position."""
    clean_sym = (pos.symbol or "").strip().upper()
    if not clean_sym:
        raise HTTPException(status_code=400, detail="Stock symbol is required")
    if pos.entry_price <= 0:
        raise HTTPException(status_code=400, detail="Entry price must be greater than zero")
    if pos.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

    # Find security_id
    sec_id = db.execute(
        text("SELECT security_id FROM core.dim_security WHERE UPPER(symbol) = :sym"),
        {"sym": clean_sym},
    ).scalar()

    if not sec_id:
        res = db.execute(
            text("""
                INSERT INTO core.dim_security (symbol, name, is_active)
                VALUES (:sym, :sym, TRUE)
                ON CONFLICT (symbol) DO UPDATE SET is_active = TRUE
                RETURNING security_id
            """),
            {"sym": clean_sym},
        )
        sec_id = res.scalar()
        db.commit()

    # Look up current market price if available
    curr_price = pos.entry_price
    if sec_id:
        latest_p = db.execute(
            text("SELECT close FROM core.fact_price_daily WHERE security_id = :sid ORDER BY trading_date DESC LIMIT 1"),
            {"sid": sec_id},
        ).scalar()
        if latest_p and float(latest_p) > 0:
            curr_price = float(latest_p)

    entry_d = pos.entry_date or date.today()
    insert_q = text("""
        INSERT INTO app.portfolio_positions (
            security_id, symbol, side, entry_date, entry_price, quantity,
            current_price, stop_loss, target_price, status, notes
        ) VALUES (
            :sec_id, :symbol, 'LONG', :entry_date, :entry_price, :quantity,
            :current_price, :stop_loss, :target_price, 'open', :notes
        )
        RETURNING id
    """)
    res = db.execute(
        insert_q,
        {
            "sec_id": sec_id,
            "symbol": clean_sym,
            "entry_date": entry_d,
            "entry_price": pos.entry_price,
            "quantity": pos.quantity,
            "current_price": curr_price,
            "stop_loss": pos.stop_loss,
            "target_price": pos.target_price,
            "notes": pos.notes or "Manual trade entry",
        },
    )
    new_id = res.scalar()
    db.commit()
    return {"status": "success", "id": new_id, "symbol": clean_sym}


def _close_position_record(id: int, exit_price: float | None, db: Session) -> dict[str, Any]:
    """Internal helper to close an open position at exit_price or latest market price."""
    row = db.execute(
        text("SELECT entry_price, quantity, security_id, symbol FROM app.portfolio_positions WHERE id = :id"),
        {"id": id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Position not found")

    entry_p, qty, sec_id, sym = float(row[0]), int(row[1]), row[2], row[3]
    actual_exit = exit_price
    if actual_exit is None or actual_exit <= 0:
        if sec_id:
            curr_close = db.execute(
                text("SELECT close FROM core.fact_price_daily WHERE security_id = :sid ORDER BY trading_date DESC LIMIT 1"),
                {"sid": sec_id},
            ).scalar()
            actual_exit = float(curr_close) if curr_close else entry_p
        else:
            actual_exit = entry_p

    pnl = (actual_exit - entry_p) * qty
    pnl_pct = ((actual_exit - entry_p) / entry_p) * 100 if entry_p > 0 else 0.0

    query = text("""
        UPDATE app.portfolio_positions
        SET status = 'closed',
            exit_date = CURRENT_DATE,
            exit_price = :exit_price,
            pnl = :pnl,
            pnl_pct = :pnl_pct,
            updated_at = NOW()
        WHERE id = :id
    """)
    db.execute(query, {"id": id, "exit_price": actual_exit, "pnl": pnl, "pnl_pct": pnl_pct})
    db.commit()
    return {"status": "closed", "id": id, "symbol": sym, "pnl": round(pnl, 2), "pnl_pct": round(pnl_pct, 2)}


@router.post("/positions/{id}/close")
def close_position_explicit(id: int, exit_price: float | None = None, db: Session = Depends(get_db)):
    """Close an open position at current or specified market price."""
    return _close_position_record(id=id, exit_price=exit_price, db=db)


@router.delete("/positions/{id}/permanent")
def delete_position_permanent(id: int, db: Session = Depends(get_db)):
    """Permanently delete a portfolio position record from the database (open or closed)."""
    row = db.execute(
        text("SELECT id, symbol FROM app.portfolio_positions WHERE id = :id"),
        {"id": id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Position not found")

    db.execute(text("DELETE FROM app.portfolio_positions WHERE id = :id"), {"id": id})
    db.commit()
    return {
        "status": "deleted",
        "id": id,
        "symbol": row[1],
        "message": f"Successfully deleted {row[1]} (Record #{id}) from Portfolio",
    }


@router.delete("/positions/{id}")
def remove_or_close_position(
    id: int,
    permanent: bool = False,
    exit_price: float | None = None,
    db: Session = Depends(get_db),
):
    """Delete permanently (if permanent=true) or close position."""
    if permanent:
        return delete_position_permanent(id=id, db=db)
    return _close_position_record(id=id, exit_price=exit_price, db=db)


@router.get("/summary")
def get_portfolio_summary(db: Session = Depends(get_db)):
    """Aggregated portfolio summary using latest live market prices, tracking both open and realized closed trades."""
    # 1. Open positions summary
    open_query = text("""
        SELECT
            COUNT(*) AS open_positions,
            COALESCE(SUM(p.quantity * COALESCE(curr.close, p.current_price, p.entry_price)), 0) AS total_value,
            COALESCE(SUM(p.quantity * p.entry_price), 0) AS total_invested
        FROM app.portfolio_positions p
        LEFT JOIN LATERAL (
            SELECT close FROM core.fact_price_daily
            WHERE security_id = p.security_id
            ORDER BY trading_date DESC LIMIT 1
        ) curr ON TRUE
        WHERE p.status = 'open'
    """)
    open_row = db.execute(open_query).fetchone()
    open_count = int(open_row[0]) if open_row else 0
    holdings_val = float(open_row[1]) if open_row else 0.0
    cost = float(open_row[2]) if open_row else 0.0
    unrealized_pnl = holdings_val - cost
    unrealized_pnl_pct = (unrealized_pnl / cost * 100) if cost > 0 else 0.0

    # 2. Closed positions summary (realized profit/loss)
    closed_query = text("""
        SELECT
            COUNT(*) AS closed_positions,
            COALESCE(SUM(pnl), 0) AS realized_pnl,
            COALESCE(SUM(quantity * entry_price), 0) AS closed_invested
        FROM app.portfolio_positions
        WHERE status = 'closed'
    """)
    closed_row = db.execute(closed_query).fetchone()
    closed_count = int(closed_row[0]) if closed_row else 0
    realized_pnl = float(closed_row[1]) if closed_row else 0.0
    closed_cost = float(closed_row[2]) if closed_row else 0.0
    realized_pnl_pct = (realized_pnl / closed_cost * 100) if closed_cost > 0 else 0.0

    # 3. Overall Portfolio Account metrics (Initial Paper Cash: 1,000,000 LKR)
    initial_capital = 1_000_000.0
    total_pnl = realized_pnl + unrealized_pnl
    cash_balance = initial_capital - cost + realized_pnl
    total_equity = cash_balance + holdings_val  # equals initial_capital + total_pnl
    total_return_pct = (total_pnl / initial_capital) * 100

    return {
        "open_positions": open_count,
        "closed_positions": closed_count,
        "total_positions": open_count + closed_count,
        # Holdings specific
        "holdings_value": round(holdings_val, 2),
        "total_cost": round(cost, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
        # Realized specific
        "realized_pnl": round(realized_pnl, 2),
        "realized_pnl_pct": round(realized_pnl_pct, 2),
        # Overall account equity & cash
        "portfolio_value": round(total_equity, 2),
        "total_equity": round(total_equity, 2),
        "total_pnl": round(total_pnl, 2),
        "total_return_pct": round(total_return_pct, 2),
        "cash_balance": round(cash_balance, 2),
        "initial_capital": initial_capital,
    }


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    """List watchlist items with latest price."""
    query = text("""
        SELECT w.id, w.symbol, w.reason, w.alert_price_above, w.alert_price_below,
               curr.close AS current_price, curr.change_pct, s.logo_url
        FROM app.watchlist w
        LEFT JOIN core.dim_security s ON s.symbol = w.symbol
        LEFT JOIN LATERAL (
            SELECT close, change_pct FROM core.fact_price_daily
            WHERE security_id = s.security_id
            ORDER BY trading_date DESC LIMIT 1
        ) curr ON TRUE
        WHERE w.is_active = TRUE
        ORDER BY w.added_at DESC
    """)
    rows = db.execute(query).fetchall()
    return [
        {
            "id": r[0],
            "symbol": r[1],
            "reason": r[2],
            "alert_price_above": float(r[3]) if r[3] else None,
            "alert_price_below": float(r[4]) if r[4] else None,
            "current_price": float(r[5]) if r[5] else None,
            "change_pct": float(r[6]) if r[6] else None,
            "logo_url": r[7],
        }
        for r in rows
    ]


@router.post("/watchlist")
def add_watchlist(item: WatchlistCreate, db: Session = Depends(get_db)):
    """Add item to watchlist."""
    clean_sym = (item.symbol or "").strip().upper()
    if not clean_sym:
        raise HTTPException(status_code=400, detail="Stock symbol is required")

    sec_id = db.execute(
        text("SELECT security_id FROM core.dim_security WHERE UPPER(symbol) = :sym"),
        {"sym": clean_sym},
    ).scalar()

    if not sec_id:
        ins = db.execute(
            text("""
                INSERT INTO core.dim_security (symbol, name, is_active)
                VALUES (:sym, :sym, TRUE)
                ON CONFLICT (symbol) DO UPDATE SET is_active = TRUE
                RETURNING security_id
            """),
            {"sym": clean_sym},
        )
        sec_id = ins.scalar()
        db.commit()

    # Check if already in active watchlist
    existing = db.execute(
        text("SELECT id FROM app.watchlist WHERE UPPER(symbol) = :sym AND is_active = TRUE"),
        {"sym": clean_sym},
    ).scalar()

    if existing:
        return {"status": "success", "id": existing, "message": f"{clean_sym} is already in your watchlist"}

    query = text("""
        INSERT INTO app.watchlist (security_id, symbol, reason, alert_price_above, alert_price_below, is_active)
        VALUES (:sec_id, :sym, :reason, :above, :below, TRUE)
        RETURNING id
    """)
    res = db.execute(
        query,
        {
            "sec_id": sec_id or 0,
            "sym": clean_sym,
            "reason": item.reason or "Technical observation",
            "above": item.alert_price_above,
            "below": item.alert_price_below,
        },
    )
    new_id = res.scalar()
    db.commit()
    return {"status": "success", "id": new_id, "symbol": clean_sym}


@router.delete("/watchlist/{id}")
def remove_watchlist(id: int, db: Session = Depends(get_db)):
    """Remove item from watchlist."""
    db.execute(text("DELETE FROM app.watchlist WHERE id = :id"), {"id": id})
    db.commit()
    return {"status": "removed", "id": id}
