"""
One-time migration to add otp_code column to orders table
Run this on your production database (Neon PostgreSQL)
"""
from db.database import engine, Base
from db.model import Order
from sqlalchemy import text

def migrate():
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE orders ADD COLUMN otp_code VARCHAR DEFAULT NULL"))
            conn.commit()
            print("Added otp_code column to orders table")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            print("otp_code column already exists")
        else:
            print(f"Migration note: {e}")
            print("If using PostgreSQL, run this SQL manually:")
            print("ALTER TABLE orders ADD COLUMN otp_code VARCHAR;")

if __name__ == "__main__":
    migrate()