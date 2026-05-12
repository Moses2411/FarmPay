from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import shutil
import os
import uuid
from core.config import settings
from services.disease_detector import analyze_image, get_supported

from db.database import get_db
from db.model import Product, ProductImage, ScanResult, User
from authentication.OAuth2 import get_current_user

router = APIRouter(prefix="/detect", tags=["Disease Detection"])

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/supported-crops")
def list_supported_crops():
    """Get all supported crop types"""
    return get_supported()


@router.post("/analyze")
async def analyze_crop(
    image: UploadFile = File(...),
    crop_type: str = Form("auto", description="Crop type: auto, cassava, yam, rice, etc.")
):
    """
    Comprehensive crop health analysis
    
    - Auto-detects crop type using existing model
    - Or specify crop type for Nigerian crops (cassava, yam, rice, maize, etc.)
    - Returns disease, pest info, and recommendations
    """
    file_ext = image.filename.split(".")[-1] if image.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    try:
        result = analyze_image(file_path, crop_type)
        return result
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)