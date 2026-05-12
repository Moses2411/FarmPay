from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from routers import auth, product, admin, order, payment, rider, review, dispute
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
    try:
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        command.upgrade(alembic_cfg, "head")
        print("Migrations completed successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
        traceback.print_exc()
else:
    model.Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
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
