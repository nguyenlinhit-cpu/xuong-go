from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, BASE_DIR, APP_TITLE
from app.utils import format_currency, format_number, format_date, format_datetime
from app.routes import (
    auth,
    dashboard,
    users,
    materials,
    suppliers,
    inventory_receipts,
    products,
    customers,
    orders,
    production,
    workers,
    payroll,
    finance,
    system
)

app = FastAPI(
    title=APP_TITLE,
    description="Hệ Thống Web App Quản Lý Xưởng Sản Xuất Nội Thất Gỗ Chuyên Nghiệp",
    version="1.0.0"
)

# 1. Cấu hình SessionMiddleware (để quản lý session đăng nhập và flash message)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# 2. Cấu hình Static Files
static_dir = BASE_DIR / "app" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Tương thích Starlette TemplateResponse giữa các phiên bản
_orig_template_response = Jinja2Templates.TemplateResponse
def _compat_template_response(self, *args, **kwargs):
    if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], dict):
        name = args[0]
        context = args[1]
        req = context.get("request")
        rest = args[2:]
        return _orig_template_response(self, request=req, name=name, context=context, *rest, **kwargs)
    elif len(args) == 1 and isinstance(args[0], str) and "context" in kwargs:
        name = args[0]
        context = kwargs.pop("context")
        req = context.get("request")
        return _orig_template_response(self, request=req, name=name, context=context, **kwargs)
    return _orig_template_response(self, *args, **kwargs)

Jinja2Templates.TemplateResponse = _compat_template_response

# 3. Cấu hình Jinja2 Templates & Bộ lọc (Filters)
templates_dir = BASE_DIR / "app" / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Đăng ký bộ lọc Jinja2 theo yêu cầu đồ án: Tiền VNĐ 1.250.000 đ, ngày dd/mm/yyyy
templates.env.filters["currency"] = format_currency
templates.env.filters["number"] = format_number
templates.env.filters["date"] = format_date
templates.env.filters["datetime"] = format_datetime

# Gắn templates vào state ứng dụng để các router dùng
app.state.templates = templates

# 4. Gắn các Router module
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(materials.router)
app.include_router(suppliers.router)
app.include_router(inventory_receipts.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(orders.router)
app.include_router(production.router)
app.include_router(workers.router)
app.include_router(payroll.router)
app.include_router(finance.router)
app.include_router(system.router)

@app.get("/")
def root_redirect():
    """Chuyển hướng trang chủ về Dashboard."""
    return RedirectResponse(url="/dashboard")

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "title": "Không tìm thấy trang"},
        status_code=404
    )
