"""Fetch company info and logos from CSE API and populate dim_security."""

import sys
sys.path.insert(0, ".")

import time
import requests
import logging
from src.db import SessionLocal
from src.core.security_master import SecurityMasterBuilder
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_logos")

def sync_active_logos(limit: int = 50):
    session = SessionLocal()
    try:
        # Get active common voting symbols
        rows = session.execute(text("""
            SELECT symbol FROM core.dim_security 
            WHERE is_active = TRUE 
            ORDER BY (symbol LIKE '%.N0000') DESC, symbol ASC
            LIMIT :limit
        """), {"limit": limit}).fetchall()
        
        symbols = [r[0] for r in rows]
        logger.info(f"Syncing logos for {len(symbols)} active securities...")
        
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        updated = 0
        for sym in symbols:
            try:
                resp = requests.post(
                    "https://www.cse.lk/api/companyInfoSummery",
                    data={"symbol": sym},
                    headers=headers,
                    timeout=8
                )
                if resp.status_code == 200:
                    data = resp.json()
                    logo_info = data.get("reqLogo") or {}
                    path = logo_info.get("path") if isinstance(logo_info, dict) else None
                    if path:
                        logo_url = f"https://cdn.cse.lk/cmt/{path.lstrip('/')}"
                        session.execute(text("""
                            UPDATE core.dim_security 
                            SET logo_url = :logo_url, updated_at = NOW()
                            WHERE symbol = :symbol
                        """), {"logo_url": logo_url, "symbol": sym})
                        
                        # Also update app.recommendations if any exist for this symbol
                        session.execute(text("""
                            UPDATE app.recommendations
                            SET logo_url = :logo_url
                            WHERE symbol = :symbol
                        """), {"logo_url": logo_url, "symbol": sym})
                        
                        updated += 1
                        logger.info(f"  [+] {sym} -> {logo_url}")
                time.sleep(0.15)
            except Exception as e:
                logger.warning(f"  [-] Failed {sym}: {e}")
                
        session.commit()
        logger.info(f"Successfully updated logos for {updated}/{len(symbols)} securities.")
    finally:
        session.close()

if __name__ == "__main__":
    sync_active_logos(limit=50)
