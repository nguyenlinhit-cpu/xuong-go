from typing import Optional, List
from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, RoleEnum
from app.utils import verify_password

def set_flash(request: Request, message: str, category: str = "success"):
    """Lưu thông báo flash vào session để hiển thị trên template."""
    if "flash" not in request.session:
        request.session["flash"] = []
    request.session["flash"].append({"message": message, "category": category})

def get_flashes(request: Request) -> List[dict]:
    """Lấy danh sách thông báo flash và xóa khỏi session."""
    flashes = request.session.pop("flash", [])
    return flashes

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Xác thực người dùng bằng username và password."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Dependency lấy thông tin user đang đăng nhập từ session."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    return user

def login_required(request: Request, current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Bắt buộc người dùng phải đăng nhập mới được truy cập."""
    if not current_user:
        set_flash(request, "Vui lòng đăng nhập để tiếp tục.", "warning")
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    return current_user

def require_roles(allowed_roles: List[str]):
    """Kiểm tra quyền truy cập theo danh sách Role."""
    def role_checker(request: Request, current_user: User = Depends(login_required)) -> User:
        if current_user.role == RoleEnum.ADMIN:
            return current_user # Admin có toàn quyền
        if current_user.role not in allowed_roles:
            set_flash(request, "Bạn không có quyền truy cập vào chức năng này!", "danger")
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                headers={"Location": "/dashboard"}
            )
        return current_user
    return role_checker
