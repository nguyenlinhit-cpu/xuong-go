from datetime import datetime, date
from typing import Optional, Union
import bcrypt

def hash_password(password: str) -> str:
    """Mã hóa mật khẩu bằng thuật toán bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu nhập vào khớp với hash bcrypt."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def format_currency(amount: Optional[Union[int, float]]) -> str:
    """Định dạng tiền tệ VNĐ dạng: 1.250.000 đ."""
    if amount is None:
        return "0 đ"
    try:
        # Làm tròn và chuyển thành số nguyên nếu là tiền chẵn
        rounded = int(round(float(amount)))
        # Format dấu chấm phân cách hàng nghìn theo chuẩn Việt Nam
        formatted = f"{rounded:,}".replace(",", ".")
        return f"{formatted} đ"
    except (ValueError, TypeError):
        return "0 đ"

def format_number(val: Optional[Union[int, float]], decimals: int = 2) -> str:
    """Định dạng số lượng (ví dụ m³ hoặc chiếc) không có ký hiệu đ."""
    if val is None:
        return "0"
    try:
        fval = float(val)
        if fval.is_integer():
            return f"{int(fval):,}".replace(",", ".")
        formatted = f"{fval:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted.rstrip("0").rstrip(",")
    except Exception:
        return "0"

def format_date(d: Optional[Union[datetime, date, str]]) -> str:
    """Định dạng ngày dd/mm/yyyy."""
    if not d:
        return ""
    if isinstance(d, str):
        try:
            d = datetime.strptime(d[:10], "%Y-%m-%d").date()
        except Exception:
            return d
    return d.strftime("%d/%m/%Y")

def format_datetime(dt: Optional[Union[datetime, str]]) -> str:
    """Định dạng ngày giờ dd/mm/yyyy HH:MM."""
    if not dt:
        return ""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except Exception:
            return dt
    return dt.strftime("%d/%m/%Y %H:%M")
