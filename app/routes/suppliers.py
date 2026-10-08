from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.inventory import Supplier
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes

router = APIRouter(prefix="/suppliers")

@router.get("", response_class=HTMLResponse)
def list_suppliers(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    suppliers = db.query(Supplier).order_by(Supplier.name.asc()).all()
    return templates.TemplateResponse(
        "suppliers/index.html",
        {
            "request": request,
            "title": "Nhà cung cấp vật tư",
            "current_user": current_user,
            "suppliers": suppliers,
            "flashes": get_flashes(request)
        }
    )

@router.get("/new", response_class=HTMLResponse)
def new_supplier_page(
    request: Request,
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "suppliers/form.html",
        {
            "request": request,
            "title": "Thêm nhà cung cấp mới",
            "current_user": current_user,
            "supplier": None,
            "flashes": get_flashes(request)
        }
    )

@router.post("/new")
def create_supplier(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    tax_id: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    code = code.strip().upper()
    if db.query(Supplier).filter(Supplier.code == code).first():
        set_flash(request, f"Mã NCC '{code}' đã tồn tại!", "danger")
        return RedirectResponse(url="/suppliers/new", status_code=status.HTTP_303_SEE_OTHER)

    s = Supplier(
        code=code,
        name=name.strip(),
        phone=phone.strip() if phone else None,
        email=email.strip() if email else None,
        address=address.strip() if address else None,
        tax_id=tax_id.strip() if tax_id else None,
        note=note.strip() if note else None,
        debt_amount=0.0
    )
    db.add(s)
    db.commit()
    set_flash(request, f"Đã thêm nhà cung cấp '{s.name}' thành công!", "success")
    return RedirectResponse(url="/suppliers", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{supplier_id}", response_class=HTMLResponse)
def view_supplier(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    s = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhà cung cấp")
    return templates.TemplateResponse(
        "suppliers/detail.html",
        {
            "request": request,
            "title": f"Chi tiết: {s.name}",
            "current_user": current_user,
            "supplier": s,
            "receipts": s.receipts,
            "flashes": get_flashes(request)
        }
    )
