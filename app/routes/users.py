from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, RoleEnum
from app.services.auth_service import require_roles, set_flash, get_flashes
from app.utils import hash_password

router = APIRouter(prefix="/users")

@router.get("", response_class=HTMLResponse)
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    """Trang danh sách tài khoản (chỉ Admin)."""
    templates = request.app.state.templates
    users = db.query(User).order_by(User.id.asc()).all()
    return templates.TemplateResponse(
        "users/index.html",
        {
            "request": request,
            "title": "Quản lý tài khoản & phân quyền",
            "current_user": current_user,
            "users": users,
            "roles": RoleEnum.ALL_ROLES,
            "flashes": get_flashes(request)
        }
    )

@router.post("/create")
def create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    """Thêm người dùng mới."""
    username = username.strip()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        set_flash(request, f"Tên đăng nhập '{username}' đã tồn tại!", "danger")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    new_user = User(
        username=username,
        hashed_password=hash_password(password),
        full_name=full_name.strip(),
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    set_flash(request, f"Đã tạo thành công tài khoản '{username}'!", "success")
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{user_id}/toggle")
def toggle_user_active(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    """Khóa hoặc mở khóa tài khoản."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")
    if user.id == current_user.id:
        set_flash(request, "Không thể tự khóa tài khoản của chính mình!", "warning")
        return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

    user.is_active = not user.is_active
    db.commit()
    status_str = "kích hoạt" if user.is_active else "khóa"
    set_flash(request, f"Đã {status_str} tài khoản '{user.username}'.", "info")
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{user_id}/reset-password")
def reset_user_password(
    user_id: int,
    request: Request,
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN]))
):
    """Đặt lại mật khẩu cho tài khoản."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy tài khoản")

    user.hashed_password = hash_password(new_password)
    db.commit()
    set_flash(request, f"Đã đổi mật khẩu cho tài khoản '{user.username}' thành công!", "success")
    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)
