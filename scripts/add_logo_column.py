from sqlalchemy import text
from src.db import engine

with engine.connect() as conn:
    # Add logo_url column to core.dim_security
    conn.execute(text("ALTER TABLE core.dim_security ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500);"))
    # Add logo_url column to app.recommendations
    conn.execute(text("ALTER TABLE app.recommendations ADD COLUMN IF NOT EXISTS logo_url VARCHAR(500);"))
    conn.commit()
    print("Columns logo_url successfully added or already exist.")
