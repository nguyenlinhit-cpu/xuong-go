from datetime import date, datetime
from typing import Optional, List
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sales import Order, OrderDetail, Product, Customer, OrderStatus
from app.models.finance import CashTransaction, TransactionType, TransactionCategory, PaymentMethod
from app.services.auth_service import login_required, set_flash, get_flashes
from app.config import FACTORY_NAME, FACTORY_ADDRESS, FACTORY_PHONE, FACTORY_EMAIL, FACTORY_TAX_ID

router = APIRouter(prefix="/orders")

@router.get("", response_class=HTMLResponse)
def list_orders(
    request: Request,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)

    orders = query.order_by(Order.order_date.desc(), Order.id.desc()).all()
    return templates.TemplateResponse(
        "orders/index.html",
        {
            "request": request,
            "title": "Quản lý Đơn hàng Bán",
            "current_user": current_user,
            "orders": orders,
            "order_statuses": OrderStatus.ALL,
            "selected_status": status_filter,
            "flashes": get_flashes(request)
        }
    )

@router.get("/new", response_class=HTMLResponse)
def new_order_page(request: Request, db: Session = Depends(get_db), current_user = Depends(login_required)):
    templates = request.app.state.templates
    customers = db.query(Customer).order_by(Customer.name.asc()).all()
    products = db.query(Product).order_by(Product.name.asc()).all()
    today_str = date.today().strftime("%Y-%m-%d")
    code_default = f"DH-{date.today().strftime('%Y%m%d')}-{db.query(Order).count() + 1:03d}"

    return templates.TemplateResponse(
        "orders/form.html",
        {
            "request": request,
            "title": "Tạo Đơn Hàng Mới",
            "current_user": current_user,
            "customers": customers,
            "products": products,
            "today_str": today_str,
            "code_default": code_default,
            "flashes": get_flashes(request)
        }
    )

@router.post("/new")
async def create_order_action(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    form_data = await request.form()
    code = form_data.get("code", "").strip()
    customer_id = int(form_data.get("customer_id"))
    order_date_str = form_data.get("order_date")
    order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date() if order_date_str else date.today()
    delivery_date_str = form_data.get("delivery_date")
    delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date() if delivery_date_str else None
    discount = float(form_data.get("discount", 0.0) or 0.0)
    deposit = float(form_data.get("deposit_amount", 0.0) or 0.0)
    note = form_data.get("note", "").strip() or None

    product_ids = form_data.getlist("product_id[]")
    quantities = form_data.getlist("quantity[]")
    unit_prices = form_data.getlist("unit_price[]")
    custom_reqs = form_data.getlist("custom_requirements[]")

    if not product_ids:
        set_flash(request, "Vui lòng chọn ít nhất 1 sản phẩm cho đơn hàng!", "danger")
        return RedirectResponse(url="/orders/new", status_code=status.HTTP_303_SEE_OTHER)

    total_amount = 0.0
    order_items = []
    for idx, (p_id, q, p) in enumerate(zip(product_ids, quantities, unit_prices)):
        if p_id and int(q or 0) > 0:
            qty = int(q)
            price = float(p or 0.0)
            line_total = qty * price
            total_amount += line_total
            req = custom_reqs[idx] if idx < len(custom_reqs) else ""
            order_items.append({
                "product_id": int(p_id),
                "quantity": qty,
                "unit_price": price,
                "total_price": line_total,
                "custom_requirements": req.strip() if req else None
            })

    final_amount = max(0.0, total_amount - discount)
    remaining = max(0.0, final_amount - deposit)

    order = Order(
        code=code,
        customer_id=customer_id,
        order_date=order_date,
        delivery_date=delivery_date,
        status=OrderStatus.MOI,
        total_amount=total_amount,
        discount=discount,
        final_amount=final_amount,
        deposit_amount=deposit,
        remaining_amount=remaining,
        note=note,
        created_by_id=current_user.id
    )
    db.add(order)
    db.flush()

    for item in order_items:
        detail = OrderDetail(
            order_id=order.id,
            product_id=item["product_id"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
            total_price=item["total_price"],
            custom_requirements=item["custom_requirements"]
        )
        db.add(detail)

    # Cập nhật công nợ khách hàng
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.debt_amount = (customer.debt_amount or 0.0) + remaining

    # Tự động tạo phiếu thu tiền cọc nếu có
    if deposit > 0:
        receipt_tx = CashTransaction(
            code=f"PT-COC-{order.code}",
            transaction_type=TransactionType.THU,
            category=TransactionCategory.THU_COC_DON_HANG,
            amount=deposit,
            transaction_date=order_date,
            payment_method=PaymentMethod.CHUYEN_KHOAN,
            payer_or_receiver=customer.name if customer else "Khách hàng",
            reference_code=order.code,
            order_id=order.id,
            note=f"Thu tiền cọc đơn hàng {order.code}",
            created_by_id=current_user.id
        )
        db.add(receipt_tx)

    db.commit()
    set_flash(request, f"Đã tạo đơn hàng '{order.code}' thành công!", "success")
    return RedirectResponse(url=f"/orders/{order.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{order_id}", response_class=HTMLResponse)
def view_order_detail(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    templates = request.app.state.templates
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    return templates.TemplateResponse(
        "orders/detail.html",
        {
            "request": request,
            "title": f"Chi tiết Đơn hàng: {order.code}",
            "current_user": current_user,
            "order": order,
            "order_statuses": OrderStatus.ALL,
            "flashes": get_flashes(request)
        }
    )

@router.post("/{order_id}/status")
def update_order_status(
    order_id: int,
    request: Request,
    status: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    order.status = status
    db.commit()
    set_flash(request, f"Đã chuyển trạng thái đơn hàng sang '{status}'.", "info")
    return RedirectResponse(url=f"/orders/{order.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/{order_id}/print", response_class=HTMLResponse)
def print_invoice_view(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(login_required)
):
    """Trang in báo giá / hóa đơn thiết kế chuẩn in A4 (@media print)."""
    templates = request.app.state.templates
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    return templates.TemplateResponse(
        "orders/print_invoice.html",
        {
            "request": request,
            "title": f"Hóa đơn & Báo giá - {order.code}",
            "order": order,
            "factory": {
                "name": FACTORY_NAME,
                "address": FACTORY_ADDRESS,
                "phone": FACTORY_PHONE,
                "email": FACTORY_EMAIL,
                "tax_id": FACTORY_TAX_ID
            }
        }
    )
