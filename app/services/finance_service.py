from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.finance import CashTransaction, TransactionType, TransactionCategory, PaymentMethod
from app.models.sales import Order, Customer, OrderStatus, OrderDetail
from app.models.inventory import Material, Supplier, InventoryReceipt
from app.models.production import ProductionOrder

def get_cashbook_summary(db: Session, from_date: Optional[date] = None, to_date: Optional[date] = None) -> Dict[str, Any]:
    """Lấy số dư sổ quỹ tiền mặt và ngân hàng cùng tổng thu, chi."""
    query = db.query(CashTransaction)
    if from_date:
        query = query.filter(CashTransaction.transaction_date >= from_date)
    if to_date:
        query = query.filter(CashTransaction.transaction_date <= to_date)

    transactions = query.order_by(CashTransaction.transaction_date.desc(), CashTransaction.id.desc()).all()

    total_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.THU)
    total_expense = sum(t.amount for t in transactions if t.transaction_type == TransactionType.CHI)
    balance = total_income - total_expense

    return {
        "transactions": transactions,
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance
    }

def create_receipt_voucher(
    db: Session,
    code: str,
    category: str,
    amount: float,
    transaction_date: date,
    payment_method: str,
    payer: str,
    order_id: Optional[int] = None,
    note: Optional[str] = None,
    user_id: Optional[int] = None
) -> CashTransaction:
    """Tạo phiếu thu tiền và cập nhật số tiền đã thu trên đơn hàng nếu có liên kết."""
    tx = CashTransaction(
        code=code,
        transaction_type=TransactionType.THU,
        category=category,
        amount=amount,
        transaction_date=transaction_date,
        payment_method=payment_method,
        payer_or_receiver=payer,
        order_id=order_id,
        reference_code=None,
        note=note,
        created_by_id=user_id
    )

    if order_id:
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            tx.reference_code = order.code
            order.deposit_amount += amount
            order.remaining_amount = max(0.0, order.final_amount - order.deposit_amount)
            if order.remaining_amount == 0 and order.status == OrderStatus.DA_GIAO:
                order.status = OrderStatus.DA_THANH_TOAN

            # Cập nhật công nợ khách hàng
            if order.customer:
                order.customer.debt_amount = max(0.0, order.customer.debt_amount - amount)

    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

def create_payment_voucher(
    db: Session,
    code: str,
    category: str,
    amount: float,
    transaction_date: date,
    payment_method: str,
    receiver: str,
    receipt_id: Optional[int] = None,
    worker_id: Optional[int] = None,
    note: Optional[str] = None,
    user_id: Optional[int] = None
) -> CashTransaction:
    """Tạo phiếu chi tiền và giảm công nợ nhà cung cấp nếu thanh toán phiếu nhập kho."""
    tx = CashTransaction(
        code=code,
        transaction_type=TransactionType.CHI,
        category=category,
        amount=amount,
        transaction_date=transaction_date,
        payment_method=payment_method,
        payer_or_receiver=receiver,
        receipt_id=receipt_id,
        worker_id=worker_id,
        note=note,
        created_by_id=user_id
    )

    if receipt_id:
        rec = db.query(InventoryReceipt).filter(InventoryReceipt.id == receipt_id).first()
        if rec:
            tx.reference_code = rec.code
            rec.paid_amount += amount
            if rec.supplier and rec.supplier.debt_amount:
                rec.supplier.debt_amount = max(0.0, rec.supplier.debt_amount - amount)

    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

def get_financial_reports(db: Session, from_date: Optional[date] = None, to_date: Optional[date] = None) -> Dict[str, Any]:
    """Tổng hợp báo cáo tài chính, doanh thu, lợi nhuận ước tính, công nợ và giá trị tồn kho."""
    # 1. Doanh thu đơn hàng hoàn thành hoặc đang giao
    order_query = db.query(Order).filter(Order.status != OrderStatus.HUY)
    if from_date:
        order_query = order_query.filter(Order.order_date >= from_date)
    if to_date:
        order_query = order_query.filter(Order.order_date <= to_date)
    orders = order_query.all()

    total_revenue = sum(o.final_amount for o in orders)
    total_received = sum(o.deposit_amount for o in orders)
    total_customer_debt = sum(o.remaining_amount for o in orders)

    # 2. Chi phí từ sổ quỹ
    tx_query = db.query(CashTransaction).filter(CashTransaction.transaction_type == TransactionType.CHI)
    if from_date:
        tx_query = tx_query.filter(CashTransaction.transaction_date >= from_date)
    if to_date:
        tx_query = tx_query.filter(CashTransaction.transaction_date <= to_date)
    expenses = tx_query.all()

    total_expense = sum(e.amount for e in expenses)
    expense_by_category = {}
    for e in expenses:
        expense_by_category[e.category] = expense_by_category.get(e.category, 0.0) + e.amount

    # 3. Giá trị kho hiện tại
    materials = db.query(Material).all()
    inventory_value = sum(m.stock_quantity * m.unit_price for m in materials)

    # 4. Công nợ nhà cung cấp
    suppliers = db.query(Supplier).all()
    total_supplier_debt = sum(s.debt_amount or 0.0 for s in suppliers)

    # 5. Lợi nhuận ước tính (Doanh thu - Chi phí)
    estimated_profit = total_revenue - total_expense

    return {
        "total_revenue": total_revenue,
        "total_received": total_received,
        "total_customer_debt": total_customer_debt,
        "total_expense": total_expense,
        "expense_by_category": expense_by_category,
        "inventory_value": inventory_value,
        "total_supplier_debt": total_supplier_debt,
        "estimated_profit": estimated_profit,
        "order_count": len(orders)
    }
