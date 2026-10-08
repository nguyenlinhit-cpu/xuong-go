import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request, Depends, UploadFile, File, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from app.config import DATABASE_PATH, BACKUP_DIR
from app.models.user import RoleEnum
from app.services.auth_service import require_roles, set_flash, get_flashes

router = APIRouter(prefix="/system")

@router.get("/backup", response_class=HTMLResponse)
def backup_page(
    request: Request,
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    # Liệt kê các file backup có sẵn
    backups = []
    if BACKUP_DIR.exists():
        for f in sorted(BACKUP_DIR.glob("*.db"), key=os.path.getmtime, reverse=True):
            backups.append({
                "filename": f.name,
                "size_kb": round(f.stat().st_size / 1024, 2),
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M:%S")
            })

    db_size = round(DATABASE_PATH.stat().st_size / 1024, 2) if DATABASE_PATH.exists() else 0.0

    return templates.TemplateResponse(
        "system/backup.html",
        {
            "request": request,
            "title": "Sao Lưu & Khôi Phục Dữ Liệu",
            "current_user": current_user,
            "backups": backups,
            "db_size": db_size,
            "flashes": get_flashes(request)
        }
    )

@router.post("/backup/create")
def create_backup_action(
    request: Request,
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    """Tạo bản sao lưu database."""
    if not DATABASE_PATH.exists():
        set_flash(request, "Không tìm thấy file database hiện tại!", "danger")
        return RedirectResponse(url="/system/backup", status_code=status.HTTP_303_SEE_OTHER)

    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"wood_factory_backup_{now_str}.db"
    shutil.copy2(DATABASE_PATH, backup_file)

    set_flash(request, f"Đã sao lưu thành công file '{backup_file.name}'!", "success")
    return RedirectResponse(url="/system/backup", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/backup/download/{filename}")
def download_backup_file(
    filename: str,
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    target = BACKUP_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File không tồn tại")
    return FileResponse(path=target, filename=filename, media_type="application/octet-stream")

@router.post("/backup/restore")
async def restore_backup_action(
    request: Request,
    backup_file: UploadFile = File(...),
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    """Khôi phục dữ liệu từ file backup .db upload lên."""
    if not backup_file.filename.endswith(".db"):
        set_flash(request, "Chỉ chấp nhận file định dạng SQLite database (*.db)!", "danger")
        return RedirectResponse(url="/system/backup", status_code=status.HTTP_303_SEE_OTHER)

    # Lưu lại bản trước khi ghi đè để an toàn
    if DATABASE_PATH.exists():
        safety_copy = BACKUP_DIR / f"safety_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DATABASE_PATH, safety_copy)

    with open(DATABASE_PATH, "wb") as buffer:
        shutil.copyfileobj(backup_file.file, buffer)

    set_flash(request, "Đã khôi phục cơ sở dữ liệu thành công từ file tải lên!", "success")
    return RedirectResponse(url="/system/backup", status_code=status.HTTP_303_SEE_OTHER)
