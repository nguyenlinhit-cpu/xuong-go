from datetime import date
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.production import Worker
from app.models.finance import CashTransaction, TransactionType, TransactionCategory, PaymentMethod
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes
from app.services.production_service import calculate_monthly_payroll

router = APIRouter(prefix="/payroll")

@router.get("", response_class=HTMLResponse)
def payroll_page(
    request: Request,
    year: int = Query(date.today().year),
    month: int = Query(date.today().month),
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    payroll_data = calculate_monthly_payroll(db, year, month)
    total_net = sum(p["net_salary"] for p in payroll_data)

    return templates.TemplateResponse(
        "payroll/index.html",
        {
            "request": request,
            "title": f"Bảng Lương Thợ Tháng {month}/{year}",
            "current_user": current_user,
            "payroll_data": payroll_data,
            "year": year,
            "month": month,
            "total_net": total_net,
            "flashes": get_flashes(request)
        }
    )

@router.post("/pay")
def pay_salary_action(
    request: Request,
    worker_id: int = Form(...),
    year: int = Form(...),
    month: int = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KE_TOAN, RoleEnum.ADMIN]))
):
    """Chi trả lương tháng cho thợ và sinh phiếu chi vào sổ quỹ."""
    w = db.query(Worker).filter(Worker.id == worker_id).first()
    if not w:
        set_flash(request, "Không tìm thấy thợ!", "danger")
        return RedirectResponse(url=f"/payroll?year={year}&month={month}", status_code=status.HTTP_303_SEE_OTHER)

    if amount <= 0:
        set_flash(request, "Số tiền thực lĩnh bằng 0 hoặc không hợp lệ!", "warning")
        return RedirectResponse(url=f"/payroll?year={year}&month={month}", status_code=status.HTTP_303_SEE_OTHER)

    pc = CashTransaction(
        code=f"PC-LUONG-{year}{month:02d}-{w.code}",
        transaction_type=TransactionType.CHI,
        category=TransactionCategory.CHI_LUONG_THO,
        amount=amount,
        transaction_date=date.today(),
        payment_method=PaymentMethod.CHUYEN_KHOAN,
        payer_or_receiver=w.full_name,
        reference_code=w.code,
        worker_id=w.id,
        note=f"Chi trả lương tháng {month}/{year} cho thợ {w.full_name}",
        created_by_id=current_user.id
    )
    db.add(pc)
    db.commit()

    set_flash(request, f"Đã thanh toán lương tháng {month}/{year} cho {w.full_name} và lập phiếu chi {pc.code}!", "success")
    return RedirectResponse(url=f"/payroll?year={year}&month={month}", status_code=status.HTTP_303_SEE_OTHER)
