from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
import os, shutil

from utils.security import (
    get_current_user,
    admin_only
)
from models.users import User

router = APIRouter(prefix="/files", tags=["File Upload"])

UPLOAD_DIR = "uploads"
ALLOWED_TYPES = ["image/jpeg", "image/png", "application/pdf"]


#  UPLOAD FILE
@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: User = Depends(admin_only)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    #  Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only images and PDFs allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    #  Prevent overwrite
    if os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="File already exists")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "filename": file.filename,
            "url": f"/files/file/{file.filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#  LIST FILES
@router.get("/")
async def get_files(current_user: User = Depends(admin_only)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    return {"files": os.listdir(UPLOAD_DIR)}


#  GET SINGLE FILE
@router.get("/file/{name}")
async def get_file(name: str, current_user: User = Depends(admin_only)):
    file_path = os.path.join(UPLOAD_DIR, name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


#  DELETE FILE (ADMIN ONLY)
@router.delete("/file/{name}")
async def delete_file(
    name: str,
    admin: User = Depends(admin_only)
):
    file_path = os.path.join(UPLOAD_DIR, name)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(file_path)
        return {"message": "File deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))