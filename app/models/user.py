from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base

class RoleEnum:
    ADMIN = "Admin"
    KHO = "Quản lý kho"
    QUAN_DOC = "Quản đốc"
    KE_TOAN = "Kế toán"

    ALL_ROLES = [ADMIN, KHO, QUAN_DOC, KE_TOAN]

class User(Base):
    """Bảng người dùng và phân quyền hệ thống xưởng gỗ."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False, default=RoleEnum.KHO)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def is_admin(self) -> bool:
        return self.role == RoleEnum.ADMIN
