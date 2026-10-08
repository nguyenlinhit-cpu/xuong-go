from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sales import Customer
from app.services.auth_service import login_required, set_flash, get_flashes

router = APIRouter(prefix="/customers")

@router.get("", response_class=HTMLResponse)
def list_customers(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    customers = db.query(Customer).order_by(Customer.name.asc()).all()
    return templates.TemplateResponse(
        "customers/index.html",
        {
            "request": request,
            "title": "Quản lý Khách hàng & Công nợ",
            "current_user": current_user,
            "customers": customers,
            "flashes": get_flashes(request)
        }
    )

@router.get("/new", response_class=HTMLResponse)
def new_customer_page(request: Request, current_user = Depends(login_required)):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "customers/form.html",
        {
            "request": request,
            "title": "Thêm Khách Hàng Mới",
            "current_user": current_user,
            "customer": None,
            "flashes": get_flashes(request)
        }
    )

@router.post("/new")
def create_customer(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    code = code.strip().upper()
    if db.query(Customer).filter(Customer.code == code).first():
        set_flash(request, f"Mã khách hàng '{code}' đã tồn tại!", "danger")
        return RedirectResponse(url="/customers/new", status_code=status.HTTP_303_SEE_OTHER)

    c = Customer(
        code=code,
        name=name.strip(),
        phone=phone.strip(),
        email=email.strip() if email else None,
        address=address.strip() if address else None,
        debt_amount=0.0,
        note=note.strip() if note else None
    )
    db.add(c)
    db.commit()
    set_flash(request, f"Đã thêm khách hàng '{c.name}' thành công!", "success")
    return RedirectResponse(url="/customers", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{customer_id}", response_class=HTMLResponse)
def view_customer(
    customer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Không tìm thấy khách hàng")
    return templates.TemplateResponse(
        "customers/detail.html",
        {
            "request": request,
            "title": f"Hồ sơ: {c.name}",
            "current_user": current_user,
            "customer": c,
            "orders": c.orders,
            "flashes": get_flashes(request)
        }
    )
