"""Recommendations API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.db import get_db

router = APIRouter()


@router.get("/")
def get_recommendations(
    signal: str | None = Query(None, description="Filter by signal (BUY, SELL, HOLD, WATCH)"),
    status: str | None = Query(None, description="Filter by status (active, executed, cancelled, all)"),
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve recommendations with filtering, sorting, and pagination."""
    clauses = []
    params: dict[str, Any] = {"limit": limit, "offset": offset}

    status_str = status if isinstance(status, str) else None
    signal_str = signal if isinstance(signal, str) else None

    # Only show recommendations from the latest predictions date by default
    latest_date = db.execute(text("SELECT MAX(recommendation_date) FROM app.recommendations")).scalar()
    if latest_date:
        clauses.append("r.recommendation_date = :latest_date")
        params["latest_date"] = latest_date

    if status_str and status_str.lower() != "all":
        clauses.append("r.status = :status")
        params["status"] = status_str.lower()
    elif not status_str:
        # Default: show active and executed
        clauses.append("r.status IN ('active', 'executed')")

    if signal_str and signal_str.upper() != "ALL":
        clauses.append("r.signal = :signal")
        params["signal"] = signal_str.upper()

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    # Accurate count of matching unique recommendations (latest per symbol)
    total_query = text(f"""
        WITH ranked AS (
            SELECT r.id,
                   ROW_NUMBER() OVER (
                       PARTITION BY UPPER(r.symbol)
                       ORDER BY r.recommendation_date DESC, r.created_at DESC, r.id DESC
                   ) AS rn
            FROM app.recommendations r
            {where_sql}
        )
        SELECT COUNT(*) FROM ranked WHERE rn = 1
    """)
    total = db.execute(total_query, params).scalar() or 0

    query = text(f"""
        WITH ranked_recs AS (
            SELECT r.id, r.security_id, r.symbol, r.security_name, r.recommendation_date,
                   r.signal, r.confidence, r.entry_price_low, r.entry_price_high,
                   r.stop_loss, r.target_price, r.position_size_pct, r.max_quantity,
                   r.horizon_days, r.reasons, r.model_version, r.data_freshness,
                   r.expires_at, r.status, r.created_at,
                   COALESCE(r.logo_url, s.logo_url) AS logo_url,
                   EXISTS(
                       SELECT 1 FROM app.portfolio_positions p
                       WHERE UPPER(p.symbol) = UPPER(r.symbol) AND p.status = 'open'
                   ) AS has_open_position,
                   ROW_NUMBER() OVER (
                       PARTITION BY UPPER(r.symbol)
                       ORDER BY r.recommendation_date DESC, r.created_at DESC, r.id DESC
                   ) AS rn
            FROM app.recommendations r
            LEFT JOIN core.dim_security s ON s.symbol = r.symbol
            {where_sql}
        )
        SELECT id, security_id, symbol, security_name, recommendation_date,
               signal, confidence, entry_price_low, entry_price_high,
               stop_loss, target_price, position_size_pct, max_quantity,
               horizon_days, reasons, model_version, data_freshness,
               expires_at, status, created_at, logo_url, has_open_position
        FROM ranked_recs
        WHERE rn = 1
        ORDER BY
            CASE WHEN status = 'active' THEN 0 ELSE 1 END,
            CASE WHEN signal = 'BUY' THEN 0 WHEN signal = 'SELL' THEN 1 ELSE 2 END,
            confidence DESC,
            created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    rows = db.execute(query, params).fetchall()

    items = [
        {
            "id": r[0],
            "security_id": r[1],
            "symbol": r[2],
            "name": r[3],
            "recommendation_date": str(r[4]),
            "signal": r[5],
            "confidence": float(r[6]) if r[6] else None,
            "entry_price_low": float(r[7]) if r[7] else None,
            "entry_price_high": float(r[8]) if r[8] else None,
            "stop_loss": float(r[9]) if r[9] else None,
            "target_price": float(r[10]) if r[10] else None,
            "position_size_pct": float(r[11]) if r[11] else None,
            "max_quantity": r[12],
            "horizon_days": r[13],
            "reasons": r[14],
            "model_version": r[15],
            "data_freshness": r[16],
            "expires_at": r[17].isoformat() if r[17] else None,
            "status": r[18],
            "created_at": r[19].isoformat() if r[19] else None,
            "logo_url": r[20],
            "has_open_position": bool(r[21]),
        }
        for r in rows
    ]

    return {"total": total, "data": items}


@router.get("/history")
def get_recommendation_history(limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve historical recommendations."""
    query = text("""
        SELECT r.id, r.symbol, r.security_name, r.recommendation_date, r.signal,
               r.confidence, r.entry_price_high, r.stop_loss, r.target_price, r.status, r.created_at,
               COALESCE(r.logo_url, s.logo_url) AS logo_url
        FROM app.recommendations r
        LEFT JOIN core.dim_security s ON s.symbol = r.symbol
        ORDER BY r.recommendation_date DESC, r.created_at DESC
        LIMIT :limit
    """)
    rows = db.execute(query, {"limit": limit}).fetchall()
    return [
        {
            "id": r[0],
            "symbol": r[1],
            "name": r[2],
            "recommendation_date": str(r[3]),
            "signal": r[4],
            "confidence": float(r[5]) if r[5] else None,
            "entry_price": float(r[6]) if r[6] else None,
            "stop_loss": float(r[7]) if r[7] else None,
            "target_price": float(r[8]) if r[8] else None,
            "status": r[9],
            "created_at": r[10].isoformat() if r[10] else None,
            "logo_url": r[11],
        }
        for r in rows
    ]


@router.get("/performance")
def get_recommendation_performance(db: Session = Depends(get_db)):
    """Aggregated stats on recommendations."""
    query = text("""
        SELECT
            COUNT(*) AS total_signals,
            COUNT(*) FILTER (WHERE signal = 'BUY') AS buy_signals,
            COUNT(*) FILTER (WHERE signal = 'SELL') AS sell_signals,
            COUNT(*) FILTER (WHERE status = 'executed') AS executed_signals,
            AVG(confidence) AS avg_confidence
        FROM app.recommendations
    """)
    row = db.execute(query).fetchone()
    return {
        "total_signals": row[0] or 0,
        "buy_signals": row[1] or 0,
        "sell_signals": row[2] or 0,
        "executed_signals": row[3] or 0,
        "avg_confidence": round(float(row[4] or 0.0), 3),
    }


@router.get("/latest")
def get_latest_recommendations(
    signal: str | None = Query(None, description="Filter by signal (BUY, SELL, HOLD, WATCH)"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve the latest recommendations (alias for /)."""
    return get_recommendations(signal=signal, status=status, limit=limit, offset=offset, db=db)


@router.get("/{id}")
def get_recommendation_detail(id: int, db: Session = Depends(get_db)):
    """Get single recommendation detail with resolved logo_url and active holding status."""
    query = text("""
        SELECT r.id, r.security_id, r.symbol, r.security_name, r.recommendation_date,
               r.signal, r.confidence, r.entry_price_low, r.entry_price_high,
               r.stop_loss, r.target_price, r.position_size_pct, r.max_quantity,
               r.horizon_days, r.reasons, r.model_version, r.data_freshness,
               r.expires_at, r.status, r.created_at,
               COALESCE(r.logo_url, s.logo_url) AS logo_url,
               EXISTS(
                   SELECT 1 FROM app.portfolio_positions p
                   WHERE UPPER(p.symbol) = UPPER(r.symbol) AND p.status = 'open'
               ) AS has_open_position
        FROM app.recommendations r
        LEFT JOIN core.dim_security s ON s.symbol = r.symbol
        WHERE r.id = :id
    """)
    row = db.execute(query, {"id": id}).mappings().fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    res = dict(row)
    res["has_open_position"] = bool(res.get("has_open_position", False))
    return res


@router.post("/{id}/execute")
def mark_executed(id: int, db: Session = Depends(get_db)):
    """Mark recommendation as executed by user and create an open position in portfolio for BUY signals, or watchlist for WATCH/HOLD signals."""
    rec_q = text("""
        SELECT id, security_id, symbol, signal, entry_price_high, entry_price_low,
               stop_loss, target_price, max_quantity, confidence, status
        FROM app.recommendations
        WHERE id = :id
    """)
    rec_row = db.execute(rec_q, {"id": id}).fetchone()
    if not rec_row:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec_id, sec_id, sym, sig, p_high, p_low, sl, tp, qty, conf, prev_status = rec_row
    sym = (sym or "").strip().upper()

    # 1. Ensure security_id is resolved and exists in core.dim_security
    if not sec_id:
        sec_id = db.execute(
            text("SELECT security_id FROM core.dim_security WHERE UPPER(symbol) = :sym"),
            {"sym": sym},
        ).scalar()

        if not sec_id:
            ins = db.execute(
                text("""
                    INSERT INTO core.dim_security (symbol, name, is_active)
                    VALUES (:sym, :sym, TRUE)
                    ON CONFLICT (symbol) DO UPDATE SET is_active = TRUE
                    RETURNING security_id
                """),
                {"sym": sym},
            )
            sec_id = ins.scalar()
            db.commit()

        if sec_id:
            db.execute(
                text("UPDATE app.recommendations SET security_id = :sec_id WHERE id = :id"),
                {"sec_id": sec_id, "id": id},
            )

    # 2. Update recommendation status to executed
    db.execute(
        text("UPDATE app.recommendations SET status = 'executed' WHERE id = :id"),
        {"id": id},
    )

    action_taken = ""

    # 3. Handle signal execution
    if sig in ("BUY", "LONG"):
        entry_price = float(p_high or p_low or 0.0)
        if entry_price <= 0 and sec_id:
            latest_p = db.execute(
                text("SELECT close FROM core.fact_price_daily WHERE security_id = :sid ORDER BY trading_date DESC LIMIT 1"),
                {"sid": sec_id},
            ).scalar()
            entry_price = float(latest_p or 10.0)
        if entry_price <= 0:
            entry_price = 10.0

        trade_qty = int(qty or 100)

        # Check if already added to portfolio
        existing_pos = db.execute(
            text("SELECT id FROM app.portfolio_positions WHERE UPPER(symbol) = :sym AND status = 'open' AND notes LIKE :note_pat"),
            {"sym": sym, "note_pat": f"%Recommendation #{rec_id}%"},
        ).scalar()

        if not existing_pos:
            insert_pos_q = text("""
                INSERT INTO app.portfolio_positions (
                    security_id, symbol, side, entry_date, entry_price,
                    quantity, current_price, stop_loss, target_price,
                    status, notes, created_at, updated_at
                ) VALUES (
                    :sec_id, :symbol, 'LONG', CURRENT_DATE, :entry_price,
                    :quantity, :entry_price, :stop_loss, :target_price,
                    'open', :notes, NOW(), NOW()
                )
            """)
            db.execute(
                insert_pos_q,
                {
                    "sec_id": sec_id,
                    "symbol": sym,
                    "entry_price": entry_price,
                    "quantity": trade_qty,
                    "stop_loss": float(sl) if sl else None,
                    "target_price": float(tp) if tp else None,
                    "notes": f"Executed via Recommendation #{rec_id} (confidence: {round(float(conf or 0)*100)}%)",
                },
            )
            action_taken = f"Opened BUY position ({trade_qty} shares @ LKR {entry_price:.2f}) in Portfolio"
        else:
            # User clicked Record Buy again on this recommendation: log an additional holding batch
            insert_pos_q = text("""
                INSERT INTO app.portfolio_positions (
                    security_id, symbol, side, entry_date, entry_price,
                    quantity, current_price, stop_loss, target_price,
                    status, notes, created_at, updated_at
                ) VALUES (
                    :sec_id, :symbol, 'LONG', CURRENT_DATE, :entry_price,
                    :quantity, :entry_price, :stop_loss, :target_price,
                    'open', :notes, NOW(), NOW()
                )
            """)
            db.execute(
                insert_pos_q,
                {
                    "sec_id": sec_id,
                    "symbol": sym,
                    "entry_price": entry_price,
                    "quantity": trade_qty,
                    "stop_loss": float(sl) if sl else None,
                    "target_price": float(tp) if tp else None,
                    "notes": f"Additional BUY execution via Recommendation #{rec_id} (confidence: {round(float(conf or 0)*100)}%)",
                },
            )
            action_taken = f"Added {trade_qty} shares @ LKR {entry_price:.2f} of {sym} to Active Holdings in Portfolio"

    elif sig in ("SELL", "SHORT"):
        # If user holds open positions in this stock, close them
        open_positions = db.execute(
            text("SELECT id, entry_price, quantity FROM app.portfolio_positions WHERE UPPER(symbol) = :sym AND status = 'open'"),
            {"sym": sym},
        ).fetchall()

        if open_positions:
            for pos_id, e_price, p_qty in open_positions:
                curr_close = None
                if sec_id:
                    curr_close = db.execute(
                        text("SELECT close FROM core.fact_price_daily WHERE security_id = :sid ORDER BY trading_date DESC LIMIT 1"),
                        {"sid": sec_id},
                    ).scalar()
                exit_price = float(curr_close or p_high or e_price)
                e_p = float(e_price or 1.0)
                pnl = (exit_price - e_p) * int(p_qty)
                pnl_pct = ((exit_price - e_p) / e_p) * 100 if e_p > 0 else 0.0
                db.execute(
                    text("""
                        UPDATE app.portfolio_positions
                        SET status = 'closed', exit_date = CURRENT_DATE, exit_price = :exit_p,
                            pnl = :pnl, pnl_pct = :pnl_pct, updated_at = NOW()
                        WHERE id = :pid
                    """),
                    {"exit_p": exit_price, "pnl": pnl, "pnl_pct": pnl_pct, "pid": pos_id},
                )
            action_taken = f"Closed {len(open_positions)} open holding(s) for {sym} at market price (LKR {exit_price:.2f})"
        else:
            # Record an exited trade in portfolio so it appears in Portfolio -> Closed / Exited Trades
            exit_price = float(p_high or p_low or 0.0)
            if exit_price <= 0 and sec_id:
                latest_p = db.execute(
                    text("SELECT close FROM core.fact_price_daily WHERE security_id = :sid ORDER BY trading_date DESC LIMIT 1"),
                    {"sid": sec_id},
                ).scalar()
                exit_price = float(latest_p or 10.0)
            if exit_price <= 0:
                exit_price = 10.0

            entry_price = float(p_low or (exit_price * 0.95))
            trade_qty = int(qty or 100)
            pnl = (exit_price - entry_price) * trade_qty
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0

            db.execute(
                text("""
                    INSERT INTO app.portfolio_positions (
                        security_id, symbol, side, entry_date, entry_price,
                        quantity, current_price, exit_date, exit_price,
                        pnl, pnl_pct, status, notes, created_at, updated_at
                    ) VALUES (
                        :sec_id, :symbol, 'LONG', CURRENT_DATE, :entry_price,
                        :quantity, :exit_price, CURRENT_DATE, :exit_price,
                        :pnl, :pnl_pct, 'closed', :notes, NOW(), NOW()
                    )
                """),
                {
                    "sec_id": sec_id,
                    "symbol": sym,
                    "entry_price": entry_price,
                    "quantity": trade_qty,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "pnl_pct": pnl_pct,
                    "notes": f"Exited SELL trade logged from Recommendation #{rec_id}",
                },
            )
            action_taken = f"Logged closed SELL trade for {sym} in Portfolio"

    elif sig in ("WATCH", "HOLD"):
        # Add or reactivate in watchlist
        existing_w = db.execute(
            text("SELECT id, is_active FROM app.watchlist WHERE UPPER(symbol) = :sym LIMIT 1"),
            {"sym": sym},
        ).fetchone()

        if existing_w:
            w_id, is_act = existing_w[0], existing_w[1]
            if not is_act:
                db.execute(text("UPDATE app.watchlist SET is_active = TRUE WHERE id = :id"), {"id": w_id})
            action_taken = f"Added {sym} to Monitored Watchlist in Portfolio"
        else:
            db.execute(
                text("""
                    INSERT INTO app.watchlist (security_id, symbol, reason, alert_price_above, alert_price_below, is_active)
                    VALUES (:sec_id, :sym, :reason, :above, :below, TRUE)
                """),
                {
                    "sec_id": sec_id or 0,
                    "sym": sym,
                    "reason": f"From Recommendation #{rec_id} ({sig})",
                    "above": float(tp) if tp else None,
                    "below": float(sl) if sl else None,
                },
            )
            action_taken = f"Added {sym} to Monitored Watchlist in Portfolio"

    db.commit()
    return {
        "status": "success",
        "id": id,
        "new_status": "executed",
        "signal": sig,
        "symbol": sym,
        "action": action_taken,
        "message": f"Successfully recorded trade: {action_taken}",
    }


@router.post("/{id}/cancel")
def mark_cancelled(id: int, db: Session = Depends(get_db)):
    """Cancel recommendation."""
    query = text("UPDATE app.recommendations SET status = 'cancelled' WHERE id = :id RETURNING id")
    res = db.execute(query, {"id": id}).scalar()
    db.commit()
    if not res:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {"status": "success", "id": id, "new_status": "cancelled"}
