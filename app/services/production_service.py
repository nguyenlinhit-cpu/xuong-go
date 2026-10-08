from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.production import (
    ProductionOrder, ProductionStage, Worker, Timesheet, SalaryAdvance,
    ProductionOrderStatus, ProductionStageName, StageStatus, WorkerSalaryType
)
from app.models.sales import Product, Order, OrderStatus
from app.models.inventory import Material
from app.services.inventory_service import create_inventory_issue

def calculate_materials_needed_for_order(db: Session, product_id: int, quantity: int) -> List[Dict[str, Any]]:
    """Tính toán danh sách nguyên vật liệu cần dựa trên định mức BOM x số lượng sản phẩm."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return []

    needed_list = []
    for bom in product.bom_items:
        required_qty = round(bom.quantity * quantity, 3)
        mat = bom.material
        needed_list.append({
            "material_id": mat.id,
            "material_code": mat.code,
            "material_name": mat.name,
            "unit": mat.unit,
            "unit_price": mat.unit_price,
            "required_qty": required_qty,
            "current_stock": mat.stock_quantity,
            "is_sufficient": mat.stock_quantity >= required_qty,
            "missing_qty": max(0.0, required_qty - mat.stock_quantity)
        })
    return needed_list

def create_production_order(
    db: Session,
    code: str,
    product_id: int,
    quantity: int,
    start_date: date,
    due_date: Optional[date],
    order_id: Optional[int] = None,
    note: Optional[str] = None
) -> ProductionOrder:
    """Tạo lệnh sản xuất mới cùng với 6 công đoạn tiêu chuẩn."""
    p_order = ProductionOrder(
        code=code,
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        start_date=start_date,
        due_date=due_date,
        status=ProductionOrderStatus.CHUA_KHOI_DONG,
        materials_deducted=False,
        note=note
    )
    db.add(p_order)
    db.flush()

    # Tạo 6 công đoạn sản xuất tiêu chuẩn của xưởng gỗ
    stages = [
        (1, ProductionStageName.PHA_PHOI),
        (2, ProductionStageName.GIA_CONG),
        (3, ProductionStageName.LAP_RAP),
        (4, ProductionStageName.CHA_NHAM),
        (5, ProductionStageName.SON),
        (6, ProductionStageName.DONG_GOI)
    ]
    for seq, stage_name in stages:
        stage = ProductionStage(
            production_order_id=p_order.id,
            order_seq=seq,
            name=stage_name,
            status=StageStatus.CHUA_LAM
        )
        db.add(stage)

    # Nếu được tạo từ Đơn hàng, cập nhật trạng thái đơn hàng thành 'Đang sản xuất'
    if order_id:
        parent_order = db.query(Order).filter(Order.id == order_id).first()
        if parent_order and parent_order.status == OrderStatus.MOI:
            parent_order.status = OrderStatus.DANG_SAN_XUAT

    db.commit()
    db.refresh(p_order)
    return p_order

def deduct_materials_for_production(db: Session, production_order_id: int, user_id: Optional[int]) -> bool:
    """Kiểm tra và trừ kho nguyên vật liệu cho lệnh sản xuất theo BOM."""
    p_order = db.query(ProductionOrder).filter(ProductionOrder.id == production_order_id).first()
    if not p_order:
        raise ValueError("Không tìm thấy lệnh sản xuất")
    if p_order.materials_deducted:
        raise ValueError("Lệnh sản xuất này đã được trừ kho vật tư từ trước!")

    materials_needed = calculate_materials_needed_for_order(db, p_order.product_id, p_order.quantity)
    # Kiểm tra xem có thiếu vật tư nào không
    missing = [m for m in materials_needed if not m["is_sufficient"]]
    if missing:
        details = ", ".join([f"{m['material_name']} (thiếu {m['missing_qty']} {m['unit']})" for m in missing])
        raise ValueError(f"Không thể xuất kho! Các vật tư sau bị thiếu: {details}")

    # Xuất kho
    issue_items = [
        {
            "material_id": m["material_id"],
            "quantity": m["required_qty"],
            "unit_price": m["unit_price"]
        }
        for m in materials_needed
    ]

    issue_code = f"PXK-LSX-{p_order.code}"
    create_inventory_issue(
        db=db,
        code=issue_code,
        issue_date=date.today(),
        reason=f"Xuất NVL theo lệnh sản xuất {p_order.code}",
        items=issue_items,
        production_order_id=p_order.id,
        note=f"Xuất cho sản phẩm {p_order.product.name} (SL: {p_order.quantity})",
        user_id=user_id
    )

    p_order.materials_deducted = True
    p_order.status = ProductionOrderStatus.DANG_THUC_HIEN
    db.commit()
    return True

def update_stage_progress(
    db: Session,
    stage_id: int,
    status: str,
    worker_id: Optional[int] = None,
    notes: Optional[str] = None
) -> ProductionStage:
    """Cập nhật tiến độ của một công đoạn sản xuất và tự động đồng bộ trạng thái đơn hàng khi hoàn tất."""
    stage = db.query(ProductionStage).filter(ProductionStage.id == stage_id).first()
    if not stage:
        raise ValueError("Không tìm thấy công đoạn")

    stage.status = status
    if worker_id is not None:
        stage.worker_id = worker_id
    if notes is not None:
        stage.notes = notes

    if status == StageStatus.DANG_LAM and not stage.started_at:
        stage.started_at = datetime.utcnow()
    elif status == StageStatus.HOAN_THANH:
        stage.completed_at = datetime.utcnow()

    p_order = stage.production_order

    # Cập nhật trạng thái lệnh sản xuất
    all_stages = p_order.stages
    all_done = all(s.status == StageStatus.HOAN_THANH for s in all_stages)
    any_doing = any(s.status in (StageStatus.DANG_LAM, StageStatus.HOAN_THANH) for s in all_stages)

    if all_done:
        p_order.status = ProductionOrderStatus.HOAN_THANH
        p_order.completion_date = date.today()
        # Nếu có đơn hàng liên kết, cập nhật đơn hàng thành "Hoàn thiện"
        if p_order.order_id:
            order = db.query(Order).filter(Order.id == p_order.order_id).first()
            if order:
                order.status = OrderStatus.HOAN_THIEN
    elif any_doing:
        p_order.status = ProductionOrderStatus.DANG_THUC_HIEN

    db.commit()
    db.refresh(stage)
    return stage

def calculate_monthly_payroll(db: Session, year: int, month: int) -> List[Dict[str, Any]]:
    """Tính bảng lương nhân công xưởng theo tháng/năm."""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_dt = date(year, month, 1)
    end_dt = date(year, month, last_day)

    workers = db.query(Worker).filter(Worker.is_active == True).all()
    payroll_data = []

    for w in workers:
        # Lấy chấm công trong tháng
        timesheets = db.query(Timesheet).filter(
            Timesheet.worker_id == w.id,
            Timesheet.work_date >= start_dt,
            Timesheet.work_date <= end_dt
        ).all()

        total_work_days = sum(t.work_units for t in timesheets)
        total_ot_hours = sum(t.overtime_hours for t in timesheets)

        # Tiền công ngày cơ bản
        base_pay = total_work_days * w.base_salary_rate
        # Tiền tăng ca (tính theo 1.5 lần giờ lương ngày / 8h)
        hourly_rate = (w.base_salary_rate / 8.0) * 1.5
        ot_pay = round(total_ot_hours * hourly_rate)

        # Tạm ứng trong tháng
        advances = db.query(SalaryAdvance).filter(
            SalaryAdvance.worker_id == w.id,
            SalaryAdvance.advance_date >= start_dt,
            SalaryAdvance.advance_date <= end_dt
        ).all()
        total_advance = sum(a.amount for a in advances)

        gross_salary = base_pay + ot_pay
        net_salary = max(0.0, gross_salary - total_advance)

        payroll_data.append({
            "worker_id": w.id,
            "worker_code": w.code,
            "worker_name": w.full_name,
            "skill_level": w.skill_level,
            "salary_rate": w.base_salary_rate,
            "total_days": total_work_days,
            "total_ot_hours": total_ot_hours,
            "base_pay": base_pay,
            "ot_pay": ot_pay,
            "gross_salary": gross_salary,
            "total_advance": total_advance,
            "net_salary": net_salary
        })

    return payroll_data
