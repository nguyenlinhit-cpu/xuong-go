from datetime import date, datetime, timedelta
import calendar
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.services.auth_service import login_required, get_flashes
from app.models.sales import Order, OrderStatus
from app.models.inventory import Material
from app.models.production import ProductionOrder, ProductionOrderStatus
from app.models.finance import CashTransaction, TransactionType

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    today = date.today()

    # 1. Doanh thu tháng này
    first_day_of_month = date(today.year, today.month, 1)
    orders_month = db.query(Order).filter(
        Order.order_date >= first_day_of_month,
        Order.status != OrderStatus.HUY
    ).all()
    monthly_revenue = sum(o.final_amount for o in orders_month)

    # 2. Đơn hàng đang sản xuất
    active_orders = db.query(Order).filter(Order.status == OrderStatus.DANG_SAN_XUAT).count()

    # 3. Đơn sắp đến hạn giao (trong 7 ngày tới)
    next_7_days = today + timedelta(days=7)
    due_orders = db.query(Order).filter(
        Order.delivery_date >= today,
        Order.delivery_date <= next_7_days,
        Order.status.in_([OrderStatus.MOI, OrderStatus.DANG_SAN_XUAT, OrderStatus.HOAN_THIEN])
    ).order_by(Order.delivery_date.asc()).all()

    # 4. Nguyên liệu sắp hết hàng (tồn <= mức tối thiểu)
    low_stock_materials = db.query(Material).filter(
        Material.stock_quantity <= Material.min_stock_alert
    ).all()

    # 5. Lệnh sản xuất đang chạy
    running_productions = db.query(ProductionOrder).filter(
        ProductionOrder.status == ProductionOrderStatus.DANG_THUC_HIEN
    ).all()

    # 6. Dữ liệu biểu đồ doanh thu 12 tháng gần nhất (Chart.js)
    monthly_labels = []
    monthly_revenues = []
    for i in range(11, -1, -1):
        target_month_year = today - timedelta(days=i * 30)
        y, m = target_month_year.year, target_month_year.month
        month_label = f"T{m}/{y}"
        if month_label not in monthly_labels:
            monthly_labels.append(month_label)
            m_start = date(y, m, 1)
            _, last_d = calendar.monthrange(y, m)
            m_end = date(y, m, last_d)
            rev = db.query(func.sum(Order.final_amount)).filter(
                Order.order_date >= m_start,
                Order.order_date <= m_end,
                Order.status != OrderStatus.HUY
            ).scalar() or 0.0
            monthly_revenues.append(rev)

    # Đơn hàng mới nhất
    recent_orders = db.query(Order).order_by(Order.order_date.desc(), Order.id.desc()).limit(5).all()

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "title": "Bàn làm việc - Dashboard",
            "current_user": current_user,
            "flashes": get_flashes(request),
            "monthly_revenue": monthly_revenue,
            "active_orders": active_orders,
            "due_orders": due_orders,
            "low_stock_materials": low_stock_materials,
            "running_productions": running_productions,
            "recent_orders": recent_orders,
            "chart_labels": monthly_labels,
            "chart_data": monthly_revenues
        }
    )
