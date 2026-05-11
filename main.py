from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from routers import auth, product, admin, order, payment, rider, review, dispute, notifications
from db.database import engine, DATABASE_URL, Base
from db import model
import traceback
from dotenv import load_dotenv
load_dotenv()

import os
from alembic.config import Config as AlembicConfig
from alembic import command

app = FastAPI(title="FarmPay API", version="1.0.0")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

is_production = DATABASE_URL and DATABASE_URL.startswith("postgresql")

if is_production:
    print("Production DB detected - Running Alembic migrations...")
    try:
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
        traceback.print_exc()
else:
    print("Local dev mode - Using create_all for SQLite")
    model.Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://j01krjbq-5173.uks1.devtunnels.ms"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(payment.router)
app.include_router(dispute.router)
app.include_router(admin.router)
app.include_router(rider.router)
app.include_router(review.router)
app.include_router(notifications.router)

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print("ERROR:", str(e))
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

@app.get("/")
def read_root():
    return {"message": "FarmPay"}


@app.get("/migrations/status")
def migration_status():
    if not is_production:
        return {"mode": "local", "message": "Using create_all, no migrations tracked"}
    
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import text
    
    with engine.connect() as conn:
        context = MigrationContext.get_context(conn)
        current_rev = context.get_current_revision()
        
        from alembic.script import ScriptDirectory
        script = ScriptDirectory.from_config(AlembicConfig("alembic.ini"))
        heads = script.get_heads()
        
        return {
            "current_revision": current_rev,
            "latest_head": heads[0] if heads else None,
            "is_up_to_date": current_rev in heads if current_rev else False
        }


@app.post("/migrations/upgrade")
def run_migrations():
    if not is_production:
        return {"error": "Not available in local mode"}
    
    try:
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
        return {"status": "success", "message": "Migrations applied"}
    except Exception as e:
        return {"status": "error", "message": str(e)}