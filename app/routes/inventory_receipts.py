from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.inventory import (
    Material, Supplier,
    InventoryReceipt, InventoryReceiptDetail,
    InventoryIssue, InventoryIssueDetail,
    InventoryTransaction
)
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes
from app.services.inventory_service import create_inventory_receipt, create_inventory_issue

router = APIRouter(prefix="/inventory")

# 1. PHIẾU NHẬP KHO
@router.get("/receipts", response_class=HTMLResponse)
def list_receipts(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    receipts = db.query(InventoryReceipt).order_by(InventoryReceipt.date.desc(), InventoryReceipt.id.desc()).all()
    return templates.TemplateResponse(
        "inventory/receipts.html",
        {
            "request": request,
            "title": "Danh sách Phiếu Nhập Kho",
            "current_user": current_user,
            "receipts": receipts,
            "flashes": get_flashes(request)
        }
    )

@router.get("/receipts/new", response_class=HTMLResponse)
def new_receipt_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    suppliers = db.query(Supplier).order_by(Supplier.name.asc()).all()
    materials = db.query(Material).order_by(Material.name.asc()).all()
    today_str = date.today().strftime("%Y-%m-%d")
    code_default = f"PNK-{date.today().strftime('%Y%m%d')}-{db.query(InventoryReceipt).count() + 1:03d}"

    return templates.TemplateResponse(
        "inventory/receipt_new.html",
        {
            "request": request,
            "title": "Lập Phiếu Nhập Kho Nguyên Vật Liệu",
            "current_user": current_user,
            "suppliers": suppliers,
            "materials": materials,
            "today_str": today_str,
            "code_default": code_default,
            "flashes": get_flashes(request)
        }
    )

@router.post("/receipts/new")
async def create_receipt_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    form_data = await request.form()
    code = form_data.get("code", "").strip()
    supplier_id_raw = form_data.get("supplier_id")
    supplier_id = int(supplier_id_raw) if supplier_id_raw and supplier_id_raw != "" else None
    receipt_date_str = form_data.get("date")
    receipt_date = datetime.strptime(receipt_date_str, "%Y-%m-%d").date() if receipt_date_str else date.today()
    paid_amount = float(form_data.get("paid_amount", 0.0) or 0.0)
    note = form_data.get("note", "").strip() or None

    # Parse multi-row items: material_id[], quantity[], unit_price[]
    material_ids = form_data.getlist("material_id[]")
    quantities = form_data.getlist("quantity[]")
    unit_prices = form_data.getlist("unit_price[]")

    if not material_ids:
        set_flash(request, "Vui lòng chọn ít nhất 1 dòng nguyên vật liệu để nhập kho!", "danger")
        return RedirectResponse(url="/inventory/receipts/new", status_code=status.HTTP_303_SEE_OTHER)

    items = []
    for m_id, q, p in zip(material_ids, quantities, unit_prices):
        if m_id and float(q or 0) > 0:
            items.append({
                "material_id": int(m_id),
                "quantity": float(q),
                "unit_price": float(p or 0.0)
            })

    if not items:
        set_flash(request, "Dữ liệu dòng vật tư không hợp lệ!", "danger")
        return RedirectResponse(url="/inventory/receipts/new", status_code=status.HTTP_303_SEE_OTHER)

    try:
        receipt = create_inventory_receipt(
            db=db,
            code=code,
            supplier_id=supplier_id,
            receipt_date=receipt_date,
            items=items,
            paid_amount=paid_amount,
            note=note,
            user_id=current_user.id
        )
        set_flash(request, f"Đã lập phiếu nhập kho '{receipt.code}' thành công và cập nhật tồn kho!", "success")
        return RedirectResponse(url=f"/inventory/receipts/{receipt.id}", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        set_flash(request, f"Lỗi nhập kho: {str(e)}", "danger")
        return RedirectResponse(url="/inventory/receipts/new", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/receipts/{receipt_id}", response_class=HTMLResponse)
def view_receipt_detail(
    receipt_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    receipt = db.query(InventoryReceipt).filter(InventoryReceipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu nhập")
    return templates.TemplateResponse(
        "inventory/receipt_detail.html",
        {
            "request": request,
            "title": f"Chi tiết: {receipt.code}",
            "current_user": current_user,
            "receipt": receipt,
            "flashes": get_flashes(request)
        }
    )

# 2. PHIẾU XUẤT KHO
@router.get("/issues", response_class=HTMLResponse)
def list_issues(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    issues = db.query(InventoryIssue).order_by(InventoryIssue.date.desc(), InventoryIssue.id.desc()).all()
    return templates.TemplateResponse(
        "inventory/issues.html",
        {
            "request": request,
            "title": "Danh sách Phiếu Xuất Kho",
            "current_user": current_user,
            "issues": issues,
            "flashes": get_flashes(request)
        }
    )

@router.get("/issues/new", response_class=HTMLResponse)
def new_issue_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    materials = db.query(Material).filter(Material.stock_quantity > 0).order_by(Material.name.asc()).all()
    today_str = date.today().strftime("%Y-%m-%d")
    code_default = f"PXK-{date.today().strftime('%Y%m%d')}-{db.query(InventoryIssue).count() + 1:03d}"

    return templates.TemplateResponse(
        "inventory/issue_new.html",
        {
            "request": request,
            "title": "Lập Phiếu Xuất Kho Nguyên Vật Liệu",
            "current_user": current_user,
            "materials": materials,
            "today_str": today_str,
            "code_default": code_default,
            "flashes": get_flashes(request)
        }
    )

@router.post("/issues/new")
async def create_issue_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KHO, RoleEnum.ADMIN]))
):
    form_data = await request.form()
    code = form_data.get("code", "").strip()
    issue_date_str = form_data.get("date")
    issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d").date() if issue_date_str else date.today()
    reason = form_data.get("reason", "Sản xuất").strip()
    note = form_data.get("note", "").strip() or None

    material_ids = form_data.getlist("material_id[]")
    quantities = form_data.getlist("quantity[]")

    items = []
    for m_id, q in zip(material_ids, quantities):
        if m_id and float(q or 0) > 0:
            mat = db.query(Material).filter(Material.id == int(m_id)).first()
            items.append({
                "material_id": int(m_id),
                "quantity": float(q),
                "unit_price": mat.unit_price if mat else 0.0
            })

    if not items:
        set_flash(request, "Vui lòng chọn vật tư và số lượng xuất!", "danger")
        return RedirectResponse(url="/inventory/issues/new", status_code=status.HTTP_303_SEE_OTHER)

    try:
        issue = create_inventory_issue(
            db=db,
            code=code,
            issue_date=issue_date,
            reason=reason,
            items=items,
            production_order_id=None,
            note=note,
            user_id=current_user.id
        )
        set_flash(request, f"Đã lập phiếu xuất kho '{issue.code}' thành công!", "success")
        return RedirectResponse(url=f"/inventory/issues/{issue.id}", status_code=status.HTTP_303_SEE_OTHER)
    except ValueError as ve:
        set_flash(request, str(ve), "danger")
        return RedirectResponse(url="/inventory/issues/new", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        set_flash(request, f"Lỗi xuất kho: {str(e)}", "danger")
        return RedirectResponse(url="/inventory/issues/new", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/issues/{issue_id}", response_class=HTMLResponse)
def view_issue_detail(
    issue_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    issue = db.query(InventoryIssue).filter(InventoryIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu xuất")
    return templates.TemplateResponse(
        "inventory/issue_detail.html",
        {
            "request": request,
            "title": f"Chi tiết: {issue.code}",
            "current_user": current_user,
            "issue": issue,
            "flashes": get_flashes(request)
        }
    )

# 3. LỊCH SỬ GIAO DỊCH KHO
@router.get("/transactions", response_class=HTMLResponse)
def list_transactions(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    transactions = db.query(InventoryTransaction).order_by(InventoryTransaction.created_at.desc(), InventoryTransaction.id.desc()).limit(100).all()
    return templates.TemplateResponse(
        "inventory/transactions.html",
        {
            "request": request,
            "title": "Lịch Sử Biến Động Kho",
            "current_user": current_user,
            "transactions": transactions,
            "flashes": get_flashes(request)
        }
    )
