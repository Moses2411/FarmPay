import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
import uuid
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def upload_image_to_cloudinary(image: UploadFile) -> str:
    if not image.filename:
        raise HTTPException(400, "Invalid filename")

    file_ext = image.filename.split(".")[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File type not allowed. Use: {ALLOWED_EXTENSIONS}")

    image.file.seek(0, 2)
    size = image.file.tell()
    image.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large. Max 5MB")

    try:
        result = cloudinary.uploader.upload(
            image.file,
            public_id=f"farmpay/{uuid.uuid4()}",
            folder="farmpay/products",
            resource_type="image",
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"},
                {"quality": "auto", "fetch_format": "auto"}
            ]
        )
        return result["secure_url"]
    except Exception as e:
        raise HTTPException(500, f"Failed to upload image: {str(e)}")


def delete_image_from_cloudinary(image_url: str) -> bool:
    try:
        public_id = image_url.split("/")[-1].split(".")[0]
        public_id = f"farmpay/products/{public_id}"
        cloudinary.uploader.destroy(public_id)
        return True
    except Exception:
        return False