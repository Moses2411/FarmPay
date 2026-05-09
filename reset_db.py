# reset_render_db.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Your database URL (REPLACE THIS with the new URL after rotating password)
DATABASE_URL = "postgresql://farmpay_mgw8_user:q1RciQnKYmhH7zqom4zhWlfHBM3MPeJR@dpg-d71ppq8ule4c73d123og-a.frankfurt-postgres.render.com/farmpay_mgw8"

# Import your database setup
# Adjust these imports based on your project structure
try:
    # Try different common import patterns
    from db.database import Base, engine
    from db.model import *  # This ensures all models are registered
except ImportError:
    try:
        from db.database import Base, engine
        from db.model import *
    except ImportError:
        print("Could not find your database module.")
        print("Please update the imports in this script to match your project structure.")
        exit(1)

def reset_database():
    confirm = input("Type 'DROP IT' to confirm: ")
    
    if confirm != "DROP IT":
        print("Operation cancelled.")
        return False
    
    try:
        # Create engine for the remote database
        remote_engine = create_engine(DATABASE_URL)
        
        print("Dropping all tables...")
        # Drop all tables
        Base.metadata.drop_all(bind=remote_engine)
        print("Tables dropped successfully!")
        
        print("Creating all tables...")
        # Create all tables
        Base.metadata.create_all(bind=remote_engine)
        print("Tables created successfully!")
        
        print(" Database reset complete!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    reset_database()