import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Cấu hình cơ sở dữ liệu SQLite
DATABASE_PATH = BASE_DIR / "wood_factory.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Khóa bảo mật session
SECRET_KEY = os.getenv("SECRET_KEY", "xuong-go-secret-key-super-secure-2026")

# Thư mục upload ảnh sản phẩm / hóa đơn
UPLOAD_DIR = BASE_DIR / "app" / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Thư mục backup database
BACKUP_DIR = BASE_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# Thông tin xưởng gỗ
FACTORY_NAME = "XƯỞNG GỖ NỘI THẤT CAO CẤP PHÚC THỊNH"
FACTORY_ADDRESS = "Khu Công Nghiệp Thạch Thất, Hà Nội"
FACTORY_PHONE = "0988.123.456 - 0912.789.012"
FACTORY_EMAIL = "lienhe@xuonggophucthinh.vn"
FACTORY_TAX_ID = "0108998877"
APP_TITLE = "Hệ Thống Quản Lý Xưởng Gỗ Phúc Thịnh"
