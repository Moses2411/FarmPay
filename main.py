from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from routers import auth, product, admin, order, payment, rider, review, dispute, notifications
from db.database import engine
from db import model
import traceback
from dotenv import load_dotenv
load_dotenv()  

app = FastAPI(title="FarmPay API", version="1.0.0")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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