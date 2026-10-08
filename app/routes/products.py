import os
import shutil
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sales import Product, BillOfMaterials
from app.models.inventory import Material
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/products")

@router.get("", response_class=HTMLResponse)
def list_products(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    products = db.query(Product).order_by(Product.id.asc()).all()
    return templates.TemplateResponse(
        "products/index.html",
        {
            "request": request,
            "title": "Danh Mục Sản Phẩm & Định Mức BOM",
            "current_user": current_user,
            "products": products,
            "flashes": get_flashes(request)
        }
    )

@router.get("/new", response_class=HTMLResponse)
def new_product_page(
    request: Request,
    current_user = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.QUAN_DOC]))
):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "products/form.html",
        {
            "request": request,
            "title": "Thêm Sản Phẩm Mới",
            "current_user": current_user,
            "product": None,
            "flashes": get_flashes(request)
        }
    )

@router.post("/new")
async def create_product(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    wood_type: Optional[str] = Form(None),
    dimensions: Optional[str] = Form(None),
    price: float = Form(0.0),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.QUAN_DOC]))
):
    code = code.strip().upper()
    if db.query(Product).filter(Product.code == code).first():
        set_flash(request, f"Mã sản phẩm '{code}' đã tồn tại!", "danger")
        return RedirectResponse(url="/products/new", status_code=status.HTTP_303_SEE_OTHER)

    image_url = None
    if image and image.filename:
        file_ext = os.path.splitext(image.filename)[1]
        save_filename = f"{code}_{os.urandom(4).hex()}{file_ext}"
        file_path = UPLOAD_DIR / save_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"/static/uploads/{save_filename}"

    p = Product(
        code=code,
        name=name.strip(),
        wood_type=wood_type.strip() if wood_type else None,
        dimensions=dimensions.strip() if dimensions else None,
        price=price,
        image_url=image_url,
        description=description.strip() if description else None
    )
    db.add(p)
    db.commit()
    set_flash(request, f"Đã thêm sản phẩm '{p.name}'. Hãy thiết lập định mức nguyên liệu (BOM)!", "success")
    return RedirectResponse(url=f"/products/{p.id}/bom", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{product_id}/edit", response_class=HTMLResponse)
def edit_product_page(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.QUAN_DOC]))
):
    templates = request.app.state.templates
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return templates.TemplateResponse(
        "products/form.html",
        {
            "request": request,
            "title": f"Chỉnh sửa: {p.name}",
            "current_user": current_user,
            "product": p,
            "flashes": get_flashes(request)
        }
    )

@router.post("/{product_id}/edit")
async def update_product(
    product_id: int,
    request: Request,
    name: str = Form(...),
    wood_type: Optional[str] = Form(None),
    dimensions: Optional[str] = Form(None),
    price: float = Form(0.0),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.QUAN_DOC]))
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    p.name = name.strip()
    p.wood_type = wood_type.strip() if wood_type else None
    p.dimensions = dimensions.strip() if dimensions else None
    p.price = price
    p.description = description.strip() if description else None

    if image and image.filename:
        file_ext = os.path.splitext(image.filename)[1]
        save_filename = f"{p.code}_{os.urandom(4).hex()}{file_ext}"
        file_path = UPLOAD_DIR / save_filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        p.image_url = f"/static/uploads/{save_filename}"

    db.commit()
    set_flash(request, f"Đã cập nhật sản phẩm '{p.name}' thành công!", "success")
    return RedirectResponse(url="/products", status_code=status.HTTP_303_SEE_OTHER)

# CẤU HÌNH ĐỊNH MỨC NGUYÊN LIỆU (BOM)
@router.get("/{product_id}/bom", response_class=HTMLResponse)
def view_bom_page(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    materials = db.query(Material).order_by(Material.category.asc(), Material.name.asc()).all()
    # Tính tổng giá vốn dự kiến theo BOM
    estimated_cost = sum(item.quantity * item.material.unit_price for item in p.bom_items)

    return templates.TemplateResponse(
        "products/bom.html",
        {
            "request": request,
            "title": f"Định mức BOM: {p.name}",
            "current_user": current_user,
            "product": p,
            "materials": materials,
            "estimated_cost": estimated_cost,
            "flashes": get_flashes(request)
        }
    )

@router.post("/{product_id}/bom/add")
def add_bom_item(
    product_id: int,
    request: Request,
    material_id: int = Form(...),
    quantity: float = Form(...),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.QUAN_DOC]))
):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")

    # Kiểm tra xem vật tư này đã có trong BOM chưa, nếu có thì cộng thêm hoặc báo lỗi
    existing = db.query(BillOfMaterials).filter(
        BillOfMaterials.product_id == product_id,
        BillOfMaterials.material_id == material_id
    ).first()

    if existing:
        existing.quantity = quantity
        existing.note = note
    else:
        bom = BillOfMaterials(
            product_id=product_id,
            material_id=material_id,
            quantity=quantity,
            note=note
        )
        db.add(bom)

    db.commit()
    set_flash(request, "Đã cập nhật định mức nguyên liệu thành công!", "success")
    return RedirectResponse(url=f"/products/{product_id}/bom", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/{product_id}/bom/{bom_id}/delete")
def delete_bom_item(
    product_id: int,
    bom_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.ADMIN, RoleEnum.QUAN_DOC]))
):
    bom = db.query(BillOfMaterials).filter(
        BillOfMaterials.id == bom_id,
        BillOfMaterials.product_id == product_id
    ).first()
    if bom:
        db.delete(bom)
        db.commit()
        set_flash(request, "Đã xóa dòng nguyên liệu khỏi định mức BOM.", "info")

    return RedirectResponse(url=f"/products/{product_id}/bom", status_code=status.HTTP_303_SEE_OTHER)
