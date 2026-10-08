from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import authenticate_user, set_flash, get_flashes, get_current_user
from app.config import APP_TITLE

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, current_user = Depends(get_current_user)):
    """Trang đăng nhập hệ thống."""
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "title": f"Đăng nhập - {APP_TITLE}",
            "flashes": get_flashes(request)
        }
    )

@router.post("/login")
def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Xử lý xác thực đăng nhập."""
    user = authenticate_user(db, username.strip(), password)
    if not user:
        set_flash(request, "Tên đăng nhập hoặc mật khẩu không chính xác!", "danger")
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    # Lưu session
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role
    request.session["full_name"] = user.full_name
    set_flash(request, f"Chào mừng {user.full_name} quay trở lại!", "success")
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
def logout_action(request: Request):
    """Đăng xuất người dùng."""
    request.session.clear()
    set_flash(request, "Bạn đã đăng xuất thành công.", "info")
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
