from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.finance import CashTransaction, TransactionType, TransactionCategory, PaymentMethod
from app.models.sales import Order
from app.models.inventory import Supplier
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes
from app.services.finance_service import (
    get_cashbook_summary,
    create_receipt_voucher,
    create_payment_voucher,
    get_financial_reports
)
from app.services.excel_service import export_cashbook_to_excel

router = APIRouter(prefix="/finance")

# SỔ QUỸ THU CHI
@router.get("/cashbook", response_class=HTMLResponse)
def cashbook_page(
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    f_date = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else None
    t_date = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else None

    summary = get_cashbook_summary(db, f_date, t_date)

    return templates.TemplateResponse(
        "finance/cashbook.html",
        {
            "request": request,
            "title": "Sổ Quỹ Tiền Mặt & Ngân Hàng",
            "current_user": current_user,
            "transactions": summary["transactions"],
            "total_income": summary["total_income"],
            "total_expense": summary["total_expense"],
            "balance": summary["balance"],
            "from_date": from_date or "",
            "to_date": to_date or "",
            "flashes": get_flashes(request)
        }
    )

@router.get("/receipt-voucher/new", response_class=HTMLResponse)
def new_receipt_voucher_page(
    request: Request,
    order_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KE_TOAN, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    orders = db.query(Order).order_by(Order.id.desc()).limit(30).all()
    today_str = date.today().strftime("%Y-%m-%d")
    code_default = f"PT-{date.today().strftime('%Y%m%d')}-{db.query(CashTransaction).filter(CashTransaction.transaction_type == TransactionType.THU).count() + 1:03d}"

    selected_order = db.query(Order).filter(Order.id == order_id).first() if order_id else None

    return templates.TemplateResponse(
        "finance/receipt_voucher_form.html",
        {
            "request": request,
            "title": "Lập Phiếu Thu Tiền",
            "current_user": current_user,
            "categories": TransactionCategory.ALL_INCOME,
            "methods": [PaymentMethod.TIEN_MAT, PaymentMethod.CHUYEN_KHOAN],
            "orders": orders,
            "selected_order": selected_order,
            "today_str": today_str,
            "code_default": code_default,
            "flashes": get_flashes(request)
        }
    )

@router.post("/receipt-voucher/new")
def create_receipt_voucher_action(
    request: Request,
    code: str = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    transaction_date: str = Form(...),
    payment_method: str = Form(...),
    payer: str = Form(...),
    order_id: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KE_TOAN, RoleEnum.ADMIN]))
):
    t_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
    oid = int(order_id) if order_id and order_id != "" else None

    try:
        tx = create_receipt_voucher(
            db=db,
            code=code.strip().upper(),
            category=category,
            amount=amount,
            transaction_date=t_date,
            payment_method=payment_method,
            payer=payer.strip(),
            order_id=oid,
            note=note.strip() if note else None,
            user_id=current_user.id
        )
        set_flash(request, f"Đã lập phiếu thu '{tx.code}' thành công!", "success")
        return RedirectResponse(url="/finance/cashbook", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        set_flash(request, f"Lỗi tạo phiếu thu: {str(e)}", "danger")
        return RedirectResponse(url="/finance/receipt-voucher/new", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/payment-voucher/new", response_class=HTMLResponse)
def new_payment_voucher_page(
    request: Request,
    supplier_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KE_TOAN, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    suppliers = db.query(Supplier).order_by(Supplier.name.asc()).all()
    today_str = date.today().strftime("%Y-%m-%d")
    code_default = f"PC-{date.today().strftime('%Y%m%d')}-{db.query(CashTransaction).filter(CashTransaction.transaction_type == TransactionType.CHI).count() + 1:03d}"

    selected_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first() if supplier_id else None

    return templates.TemplateResponse(
        "finance/payment_voucher_form.html",
        {
            "request": request,
            "title": "Lập Phiếu Chi Tiền",
            "current_user": current_user,
            "categories": TransactionCategory.ALL_EXPENSE,
            "methods": [PaymentMethod.TIEN_MAT, PaymentMethod.CHUYEN_KHOAN],
            "suppliers": suppliers,
            "selected_supplier": selected_supplier,
            "today_str": today_str,
            "code_default": code_default,
            "flashes": get_flashes(request)
        }
    )

@router.post("/payment-voucher/new")
def create_payment_voucher_action(
    request: Request,
    code: str = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    transaction_date: str = Form(...),
    payment_method: str = Form(...),
    receiver: str = Form(...),
    receipt_id: Optional[str] = Form(None),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KE_TOAN, RoleEnum.ADMIN]))
):
    t_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
    rec_id = int(receipt_id) if receipt_id and receipt_id != "" else None

    try:
        tx = create_payment_voucher(
            db=db,
            code=code.strip().upper(),
            category=category,
            amount=amount,
            transaction_date=t_date,
            payment_method=payment_method,
            receiver=receiver.strip(),
            receipt_id=rec_id,
            note=note.strip() if note else None,
            user_id=current_user.id
        )
        set_flash(request, f"Đã lập phiếu chi '{tx.code}' thành công!", "success")
        return RedirectResponse(url="/finance/cashbook", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        set_flash(request, f"Lỗi tạo phiếu chi: {str(e)}", "danger")
        return RedirectResponse(url="/finance/payment-voucher/new", status_code=status.HTTP_303_SEE_OTHER)

# BÁO CÁO TÀI CHÍNH TỔNG HỢP
@router.get("/reports", response_class=HTMLResponse)
def reports_page(
    request: Request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    f_date = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else None
    t_date = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else None

    rep = get_financial_reports(db, f_date, t_date)
    suppliers = db.query(Supplier).all()

    return templates.TemplateResponse(
        "finance/reports.html",
        {
            "request": request,
            "title": "Báo Cáo Tài Chính & Hiệu Quả Xưởng Gỗ",
            "current_user": current_user,
            "rep": rep,
            "suppliers": suppliers,
            "from_date": from_date or "",
            "to_date": to_date or "",
            "flashes": get_flashes(request)
        }
    )

@router.get("/export-cashbook-excel")
def export_cashbook(db: Session = Depends(get_db), current_user = Depends(login_required)):
    transactions = db.query(CashTransaction).order_by(CashTransaction.transaction_date.desc(), CashTransaction.id.desc()).all()
    excel_stream = export_cashbook_to_excel(transactions)
    headers = {
        'Content-Disposition': 'attachment; filename="so_quy_thu_chi.xlsx"'
    }
    return Response(
        content=excel_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
