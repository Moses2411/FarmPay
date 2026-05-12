from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import shutil
import os
import uuid

from services.disease_detector import analyze_image, get_supported

router = APIRouter(prefix="/detect", tags=["Disease Detection"])

UPLOAD_DIR = "/var/data/uploads" if os.path.exists("/var/data") else "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/supported-crops")
def list_supported_crops():
    return get_supported()


@router.post("/analyze")
async def analyze_crop(
    image: UploadFile = File(...),
    crop_type: str = Form("auto"),
):
    file_ext = image.filename.split(".")[-1] if image.filename else "jpg"
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    try:
        return analyze_image(file_path, crop_type)
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)