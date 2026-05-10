from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import shutil
import os
import uuid
from core.config import settings
from services.disease_detector import (
    detect_disease,
    detect_crop_health,
    detect_pests,
    analyze_comprehensive,
    get_supported_crops
)

from db.database import get_db
from db.model import Product, ProductImage, ScanResult, User
from authentication.OAuth2 import get_current_user

router = APIRouter(prefix="/detect", tags=["Disease Detection"])

UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/supported-crops")
def list_supported_crops():
    """Get all supported crop types"""
    return get_supported_crops()


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
        result = analyze_comprehensive(file_path, crop_type)
        return result
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/crop-specific")
async def detect_nigerian_crop(
    image: UploadFile = File(...),
    crop_type: str = Form(..., description="Crop: cassava, yam, rice, maize, sorghum, cowpea, tomato, pepper, okra, melon, spinach")
):
    """
    Detect disease for specific Nigerian/local crops
    
    Crops: cassava, yam, rice, maize, sorghum, cowpea, tomato, pepper, okra, melon, spinach
    """
    file_ext = image.filename.split(".")[-1] if image.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    try:
        result = detect_crop_health(file_path, crop_type)
        return result
    except Exception as e:
        raise HTTPException(500, f"Detection failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/pests")
async def detect_crop_pests(
    image: UploadFile = File(...)
):
    """
    Detect common pests and insects in crops
    
    Checks for: aphids, mealybugs, spider mites, stem borers, fruit borers, 
    leaf miners, thrips, caterpillars, grasshoppers, beetles
    """
    file_ext = image.filename.split(".")[-1] if image.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    try:
        result = detect_pests(file_path)
        return result
    except Exception as e:
        raise HTTPException(500, f"Pest detection failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@router.post("/quick")
async def quick_detect(
    image: UploadFile = File(...)
):
    """
    Quick disease detection (uses original PlantVillage model)
    
    Returns: disease detected, disease name, confidence %, treatment
    """
    file_ext = image.filename.split(".")[-1] if image.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    try:
        result = detect_disease(file_path)
        return result
    except Exception as e:
        raise HTTPException(500, f"Detection failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)