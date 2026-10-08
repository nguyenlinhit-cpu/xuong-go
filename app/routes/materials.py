from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Query, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import get_db
from app.models.inventory import Material, MaterialCategory
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes
from app.services.excel_service import export_inventory_to_excel

router = APIRouter(prefix="/materials")

@router.get("", response_class=HTMLResponse)
def list_materials(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    low_stock_only: Optional[bool] = Query(False),
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    """Danh sách nguyên vật liệu kho xưởng gỗ."""
    templates = request.app.state.templates
    query = db.query(Material)

    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Material.code.ilike(search),
                Material.name.ilike(search),
                Material.wood_type.ilike(search)
            )
        )
    if category:
        query = query.filter(Material.category == category)
    if low_stock_only:
        query = query.filter(Material.stock_quantity <= Material.min_stock_alert)

    # Phân trang
    per_page = 15
    total_count = query.count()
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    materials = query.order_by(Material.category.asc(), Material.name.asc()).offset((page - 1) * per_page).limit(per_page).all()

    return templates.TemplateResponse(
        "materials/index.html",
        {
            "request": request,
            "title": "Quản lý Nguyên vật liệu & Kho",
            "current_user": current_user,
            "materials": materials,
            "categories": MaterialCategory.ALL,
            "selected_category": category,
            "q": q or "",
            "low_stock_only": low_stock_only,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "flashes": get_flashes(request)
        }
    )

@router.get("/new", response_class=HTMLResponse)
def new_material_page(
    request: Request,
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "materials/form.html",
        {
            "request": request,
            "title": "Thêm mới Nguyên vật liệu",
            "current_user": current_user,
            "categories": MaterialCategory.ALL,
            "material": None,
            "flashes": get_flashes(request)
        }
    )

@router.post("/new")
def create_material(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    wood_type: Optional[str] = Form(None),
    unit: str = Form(...),
    dimensions: Optional[str] = Form(None),
    stock_quantity: float = Form(0.0),
    unit_price: float = Form(0.0),
    min_stock_alert: float = Form(0.0),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    code = code.strip().upper()
    if db.query(Material).filter(Material.code == code).first():
        set_flash(request, f"Mã nguyên liệu '{code}' đã tồn tại!", "danger")
        return RedirectResponse(url="/materials/new", status_code=status.HTTP_303_SEE_OTHER)

    m = Material(
        code=code,
        name=name.strip(),
        category=category,
        wood_type=wood_type.strip() if wood_type else None,
        unit=unit.strip(),
        dimensions=dimensions.strip() if dimensions else None,
        stock_quantity=stock_quantity,
        unit_price=unit_price,
        min_stock_alert=min_stock_alert,
        description=description.strip() if description else None
    )
    db.add(m)
    db.commit()
    set_flash(request, f"Thêm nguyên vật liệu '{m.name}' thành công!", "success")
    return RedirectResponse(url="/materials", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{material_id}/edit", response_class=HTMLResponse)
def edit_material_page(
    material_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguyên vật liệu")
    return templates.TemplateResponse(
        "materials/form.html",
        {
            "request": request,
            "title": f"Chỉnh sửa: {m.name}",
            "current_user": current_user,
            "categories": MaterialCategory.ALL,
            "material": m,
            "flashes": get_flashes(request)
        }
    )

@router.post("/{material_id}/edit")
def update_material(
    material_id: int,
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    wood_type: Optional[str] = Form(None),
    unit: str = Form(...),
    dimensions: Optional[str] = Form(None),
    unit_price: float = Form(0.0),
    min_stock_alert: float = Form(0.0),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    m = db.query(Material).filter(Material.id == material_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Không tìm thấy nguyên vật liệu")

    m.name = name.strip()
    m.category = category
    m.wood_type = wood_type.strip() if wood_type else None
    m.unit = unit.strip()
    m.dimensions = dimensions.strip() if dimensions else None
    m.unit_price = unit_price
    m.min_stock_alert = min_stock_alert
    m.description = description.strip() if description else None

    db.commit()
    set_flash(request, f"Cập nhật nguyên vật liệu '{m.name}' thành công!", "success")
    return RedirectResponse(url="/materials", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/export-excel")
def export_excel(db: Session = Depends(get_db), current_user = Depends(login_required)):
    materials = db.query(Material).order_by(Material.category.asc(), Material.code.asc()).all()
    excel_stream = export_inventory_to_excel(materials)
    headers = {
        'Content-Disposition': 'attachment; filename="ton_kho_nguyen_lieu.xlsx"'
    }
    return Response(
        content=excel_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
