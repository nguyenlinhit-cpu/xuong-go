from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.production import Worker, Timesheet, SalaryAdvance, WorkerSalaryType
from app.models.finance import CashTransaction, TransactionType, TransactionCategory, PaymentMethod
from app.models.user import RoleEnum
from app.services.auth_service import login_required, require_roles, set_flash, get_flashes

router = APIRouter(prefix="/workers")

@router.get("", response_class=HTMLResponse)
def list_workers(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    workers = db.query(Worker).order_by(Worker.id.asc()).all()
    return templates.TemplateResponse(
        "workers/index.html",
        {
            "request": request,
            "title": "Hồ Sơ Nhân Công & Thợ Xưởng",
            "current_user": current_user,
            "workers": workers,
            "flashes": get_flashes(request)
        }
    )

@router.get("/new", response_class=HTMLResponse)
def new_worker_page(
    request: Request,
    current_user = Depends(require_roles([RoleEnum.QUAN_DOC, RoleEnum.ADMIN]))
):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "workers/form.html",
        {
            "request": request,
            "title": "Thêm Hồ Sơ Thợ Mộc Mới",
            "current_user": current_user,
            "worker": None,
            "salary_types": [WorkerSalaryType.NGAY, WorkerSalaryType.SAN_PHAM],
            "flashes": get_flashes(request)
        }
    )

@router.post("/new")
def create_worker(
    request: Request,
    code: str = Form(...),
    full_name: str = Form(...),
    phone: Optional[str] = Form(None),
    skill_level: Optional[str] = Form(None),
    salary_type: str = Form(...),
    base_salary_rate: float = Form(0.0),
    note: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.QUAN_DOC, RoleEnum.ADMIN]))
):
    code = code.strip().upper()
    if db.query(Worker).filter(Worker.code == code).first():
        set_flash(request, f"Mã thợ '{code}' đã tồn tại!", "danger")
        return RedirectResponse(url="/workers/new", status_code=status.HTTP_303_SEE_OTHER)

    w = Worker(
        code=code,
        full_name=full_name.strip(),
        phone=phone.strip() if phone else None,
        skill_level=skill_level.strip() if skill_level else None,
        salary_type=salary_type,
        base_salary_rate=base_salary_rate,
        note=note.strip() if note else None,
        is_active=True
    )
    db.add(w)
    db.commit()
    set_flash(request, f"Đã thêm hồ sơ thợ '{w.full_name}' thành công!", "success")
    return RedirectResponse(url="/workers", status_code=status.HTTP_303_SEE_OTHER)

# CHẤM CÔNG HÀNG NGÀY
@router.get("/timesheets", response_class=HTMLResponse)
def timesheet_page(
    request: Request,
    target_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    t_date = datetime.strptime(target_date, "%Y-%m-%d").date() if target_date else date.today()

    workers = db.query(Worker).filter(Worker.is_active == True).all()
    # Tìm bảng chấm công đã có cho ngày này
    records = {ts.worker_id: ts for ts in db.query(Timesheet).filter(Timesheet.work_date == t_date).all()}

    return templates.TemplateResponse(
        "workers/timesheet.html",
        {
            "request": request,
            "title": f"Chấm Công Thợ - Ngày {t_date.strftime('%d/%m/%Y')}",
            "current_user": current_user,
            "workers": workers,
            "records": records,
            "target_date_str": t_date.strftime("%Y-%m-%d"),
            "flashes": get_flashes(request)
        }
    )

@router.post("/timesheets")
async def save_timesheets(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.QUAN_DOC, RoleEnum.ADMIN]))
):
    form_data = await request.form()
    work_date_str = form_data.get("work_date")
    work_date = datetime.strptime(work_date_str, "%Y-%m-%d").date() if work_date_str else date.today()

    worker_ids = form_data.getlist("worker_id[]")
    units = form_data.getlist("work_units[]")
    ots = form_data.getlist("overtime_hours[]")
    notes = form_data.getlist("notes[]")

    for w_id, u, ot, nt in zip(worker_ids, units, ots, notes):
        wid = int(w_id)
        unit_val = float(u or 1.0)
        ot_val = float(ot or 0.0)

        existing = db.query(Timesheet).filter(
            Timesheet.worker_id == wid,
            Timesheet.work_date == work_date
        ).first()

        if existing:
            existing.work_units = unit_val
            existing.overtime_hours = ot_val
            existing.note = nt.strip() if nt else None
        else:
            ts = Timesheet(
                worker_id=wid,
                work_date=work_date,
                work_units=unit_val,
                overtime_hours=ot_val,
                note=nt.strip() if nt else None
            )
            db.add(ts)

    db.commit()
    set_flash(request, f"Đã lưu bảng chấm công ngày {work_date.strftime('%d/%m/%Y')} thành công!", "success")
    return RedirectResponse(url=f"/workers/timesheets?target_date={work_date_str}", status_code=status.HTTP_303_SEE_OTHER)

# TẠM ỨNG LƯƠNG THỢ
@router.get("/advances", response_class=HTMLResponse)
def advances_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    advances = db.query(SalaryAdvance).order_by(SalaryAdvance.advance_date.desc(), SalaryAdvance.id.desc()).all()
    workers = db.query(Worker).filter(Worker.is_active == True).order_by(Worker.full_name.asc()).all()
    today_str = date.today().strftime("%Y-%m-%d")

    return templates.TemplateResponse(
        "workers/advance.html",
        {
            "request": request,
            "title": "Tạm Ứng Lương Thợ",
            "current_user": current_user,
            "advances": advances,
            "workers": workers,
            "today_str": today_str,
            "flashes": get_flashes(request)
        }
    )

@router.post("/advances")
def create_advance_action(
    request: Request,
    worker_id: int = Form(...),
    advance_date: str = Form(...),
    amount: float = Form(...),
    reason: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_roles([RoleEnum.KE_TOAN, RoleEnum.ADMIN]))
):
    w = db.query(Worker).filter(Worker.id == worker_id).first()
    if not w:
        raise HTTPException(status_code=404, detail="Không tìm thấy thợ")

    adv_dt = datetime.strptime(advance_date, "%Y-%m-%d").date()
    adv = SalaryAdvance(
        worker_id=worker_id,
        advance_date=adv_dt,
        amount=amount,
        reason=reason.strip() if reason else None
    )
    db.add(adv)

    # Tự động lập phiếu chi sổ quỹ
    pc = CashTransaction(
        code=f"PC-UNG-{adv_dt.strftime('%Y%m%d')}-{worker_id}",
        transaction_type=TransactionType.CHI,
        category=TransactionCategory.CHI_LUONG_THO,
        amount=amount,
        transaction_date=adv_dt,
        payment_method=PaymentMethod.TIEN_MAT,
        payer_or_receiver=w.full_name,
        reference_code=w.code,
        worker_id=w.id,
        note=f"Tạm ứng lương thợ: {reason or 'Ứng lương theo yêu cầu'}",
        created_by_id=current_user.id
    )
    db.add(pc)

    db.commit()
    set_flash(request, f"Đã ghi nhận tạm ứng {w.full_name} số tiền {amount:,.0f} đ và lập phiếu chi thành công!", "success")
    return RedirectResponse(url="/workers/advances", status_code=status.HTTP_303_SEE_OTHER)
