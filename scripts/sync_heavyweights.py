import sys
sys.path.insert(0, ".")

import requests
from src.db import SessionLocal
from sqlalchemy import text

def sync_specific_symbols():
    heavyweights = [
        "LOLC.N0000", "COMB.N0000", "JKH.N0000", "SAMP.N0000", "HNB.N0000",
        "DIAL.N0000", "SLTL.N0000", "DIST.N0000", "CTC.N0000", "MELI.N0000",
        "RICH.N0000", "HAYL.N0000", "EXPO.N0000", "LION.N0000", "NEST.N0000"
    ]
    session = SessionLocal()
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/x-www-form-urlencoded"}
    for sym in heavyweights:
        try:
            r = requests.post("https://www.cse.lk/api/companyInfoSummery", data={"symbol": sym}, headers=headers, timeout=5)
            if r.status_code == 200:
                p = (r.json().get("reqLogo") or {}).get("path")
                if p:
                    u = f"https://cdn.cse.lk/cmt/{p.lstrip('/')}"
                    session.execute(text("UPDATE core.dim_security SET logo_url = :u WHERE symbol = :s"), {"u": u, "s": sym})
                    session.execute(text("UPDATE app.recommendations SET logo_url = :u WHERE symbol = :s"), {"u": u, "s": sym})
        except Exception:
            pass
    session.commit()
    session.close()
    print("Heavyweights synced.")

if __name__ == "__main__":
    sync_specific_symbols()
