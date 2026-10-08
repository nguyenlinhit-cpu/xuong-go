from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.production import (
    ProductionOrder, ProductionStage, Worker,
    ProductionOrderStatus, ProductionStageName, StageStatus
)
from app.models.sales import Product, Order
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes
from app.services.production_service import (
    create_production_order,
    calculate_materials_needed_for_order,
    deduct_materials_for_production,
    update_stage_progress
)

router = APIRouter(prefix="/production")

@router.get("", response_class=HTMLResponse)
def list_production_orders(
    request: Request,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    query = db.query(ProductionOrder)
    if status_filter:
        query = query.filter(ProductionOrder.status == status_filter)

    p_orders = query.order_by(ProductionOrder.start_date.desc(), ProductionOrder.id.desc()).all()
    return templates.TemplateResponse(
        "production/index.html",
        {
            "request": request,
            "title": "Quản lý Sản Xuất Xưởng Mộc",
            "current_user": current_user,
            "production_orders": p_orders,
            "statuses": ProductionOrderStatus.ALL,
            "selected_status": status_filter,
            "flashes": get_flashes(request)
        }
    )

@router.get("/new", response_class=HTMLResponse)
def new_production_order_page(
    request: Request,
    order_id: Optional[int] = None,
    product_id: Optional[int] = None,
    quantity: int = 1,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.QUAN_DOC, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    products = db.query(Product).order_by(Product.name.asc()).all()
    orders = db.query(Order).order_by(Order.id.desc()).limit(30).all()
    today_str = date.today().strftime("%Y-%m-%d")
    code_default = f"LSX-{date.today().strftime('%Y%m%d')}-{db.query(ProductionOrder).count() + 1:03d}"

    return templates.TemplateResponse(
        "production/form.html",
        {
            "request": request,
            "title": "Tạo Lệnh Sản Xuất",
            "current_user": current_user,
            "products": products,
            "orders": orders,
            "selected_order_id": order_id,
            "selected_product_id": product_id,
            "default_quantity": quantity,
            "today_str": today_str,
            "code_default": code_default,
            "flashes": get_flashes(request)
        }
    )

@router.post("/new")
def create_production_order_action(
    request: Request,
    code: str = Form(...),
    product_id: int = Form(...),
    quantity: int = Form(...),
    start_date: str = Form(...),
    due_date: Optional[str] = Form(None),
    order_id: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.QUAN_DOC, RoleEnum.ADMIN]))
):
    code = code.strip().upper()
    if db.query(ProductionOrder).filter(ProductionOrder.code == code).first():
        set_flash(request, f"Mã lệnh sản xuất '{code}' đã tồn tại!", "danger")
        return RedirectResponse(url="/production/new", status_code=status.HTTP_303_SEE_OTHER)

    s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    d_date = datetime.strptime(due_date, "%Y-%m-%d").date() if due_date else None
    oid = int(order_id) if order_id and order_id != "" else None

    p_order = create_production_order(
        db=db,
        code=code,
        product_id=product_id,
        quantity=quantity,
        start_date=s_date,
        due_date=d_date,
        order_id=oid,
        note=note.strip() if note else None
    )

    set_flash(request, f"Đã lập lệnh sản xuất '{p_order.code}' với 6 công đoạn hoàn chỉnh!", "success")
    return RedirectResponse(url=f"/production/{p_order.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{production_id}", response_class=HTMLResponse)
def view_production_detail(
    production_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    p_order = db.query(ProductionOrder).filter(ProductionOrder.id == production_id).first()
    if not p_order:
        raise HTTPException(status_code=404, detail="Không tìm thấy lệnh sản xuất")

    workers = db.query(Worker).filter(Worker.is_active == True).order_by(Worker.full_name.asc()).all()
    # Tính toán nguyên liệu theo BOM
    materials_needed = calculate_materials_needed_for_order(db, p_order.product_id, p_order.quantity)

    return templates.TemplateResponse(
        "production/detail.html",
        {
            "request": request,
            "title": f"Lệnh sản xuất: {p_order.code}",
            "current_user": current_user,
            "p_order": p_order,
            "workers": workers,
            "materials_needed": materials_needed,
            "stage_statuses": [StageStatus.CHUA_LAM, StageStatus.DANG_LAM, StageStatus.HOAN_THANH],
            "flashes": get_flashes(request)
        }
    )

@router.post("/{production_id}/deduct-materials")
def deduct_materials_action(
    production_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.QUAN_DOC, RoleEnum.KHO, RoleEnum.ADMIN]))
):
    try:
        deduct_materials_for_production(db, production_id, current_user.id)
        set_flash(request, "Đã kiểm tra kho và tự động xuất nguyên vật liệu thành công!", "success")
    except ValueError as ve:
        set_flash(request, str(ve), "danger")
    except Exception as e:
        set_flash(request, f"Lỗi trừ kho: {str(e)}", "danger")

    return RedirectResponse(url=f"/production/{production_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/stages/{stage_id}/update")
def update_stage_action(
    stage_id: int,
    request: Request,
    status: str = Form(...),
    worker_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.QUAN_DOC, RoleEnum.ADMIN]))
):
    w_id = int(worker_id) if worker_id and worker_id != "" else None
    try:
        stage = update_stage_progress(
            db=db,
            stage_id=stage_id,
            status=status,
            worker_id=w_id,
            notes=notes.strip() if notes else None
        )
        set_flash(request, f"Đã cập nhật tiến độ công đoạn '{stage.name}' sang '{status}'.", "success")
        return RedirectResponse(url=f"/production/{stage.production_order_id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        set_flash(request, f"Lỗi cập nhật công đoạn: {str(e)}", "danger")
        return RedirectResponse(url="/production", status_code=status.HTTP_303_SEE_OTHER)
