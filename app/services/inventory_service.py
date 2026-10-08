from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.inventory import (
    Material, Supplier,
    InventoryReceipt, InventoryReceiptDetail,
    InventoryIssue, InventoryIssueDetail,
    InventoryTransaction
)
from app.models.finance import CashTransaction, TransactionType, TransactionCategory, PaymentMethod

def get_low_stock_materials(db: Session) -> List[Material]:
    """Lấy danh sách nguyên vật liệu có lượng tồn kho <= mức tối thiểu cảnh báo."""
    return db.query(Material).filter(Material.stock_quantity <= Material.min_stock_alert).all()

def create_inventory_receipt(
    db: Session,
    code: str,
    supplier_id: Optional[int],
    receipt_date: date,
    items: List[Dict[str, Any]],
    paid_amount: float,
    note: Optional[str],
    user_id: Optional[int],
    create_payment_voucher: bool = True
) -> InventoryReceipt:
    """
    Tạo phiếu nhập kho nguyên vật liệu:
    - Cộng dồn tồn kho cho từng NVL
    - Lưu chi tiết phiếu nhập
    - Ghi nhận lịch sử biến động tồn kho
    - Tính công nợ NCC
    - Tùy chọn tự động tạo phiếu chi tiền mặt/CK nếu có thanh toán
    """
    total_amount = sum(float(item["quantity"]) * float(item["unit_price"]) for item in items)
    receipt = InventoryReceipt(
        code=code,
        supplier_id=supplier_id,
        date=receipt_date,
        total_amount=total_amount,
        paid_amount=paid_amount,
        note=note,
        created_by_id=user_id
    )
    db.add(receipt)
    db.flush() # Lấy receipt.id

    for item in items:
        mat_id = int(item["material_id"])
        qty = float(item["quantity"])
        price = float(item["unit_price"])
        line_total = qty * price

        detail = InventoryReceiptDetail(
            receipt_id=receipt.id,
            material_id=mat_id,
            quantity=qty,
            unit_price=price,
            total_price=line_total
        )
        db.add(detail)

        # Cập nhật tồn kho và đơn giá vốn bình quân
        mat = db.query(Material).filter(Material.id == mat_id).first()
        if mat:
            old_qty = mat.stock_quantity
            new_qty = old_qty + qty
            # Tính lại giá vốn bình quân gia quyền
            if new_qty > 0:
                mat.unit_price = round(((old_qty * mat.unit_price) + (qty * price)) / new_qty, 2)
            mat.stock_quantity = new_qty

            # Ghi log biến động kho
            tx = InventoryTransaction(
                material_id=mat.id,
                transaction_type="Nhập kho",
                reference_code=receipt.code,
                quantity_change=qty,
                balance_after=new_qty,
                note=f"Nhập kho từ phiếu {receipt.code}"
            )
            db.add(tx)

    # Cập nhật công nợ nhà cung cấp nếu còn thiếu tiền
    if supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            unpaid = total_amount - paid_amount
            if unpaid > 0:
                supplier.debt_amount = (supplier.debt_amount or 0.0) + unpaid

    # Tự động tạo phiếu chi quỹ nếu có thanh toán ngay
    if create_payment_voucher and paid_amount > 0:
        pay_tx = CashTransaction(
            code=f"PC-NK-{receipt.code}",
            transaction_type=TransactionType.CHI,
            category=TransactionCategory.CHI_NHAP_NVL,
            amount=paid_amount,
            transaction_date=receipt_date,
            payment_method=PaymentMethod.CHUYEN_KHOAN,
            payer_or_receiver=receipt.supplier.name if receipt.supplier else "Nhà cung cấp",
            reference_code=receipt.code,
            receipt_id=receipt.id,
            note=f"Chi tiền thanh toán phiếu nhập kho {receipt.code}",
            created_by_id=user_id
        )
        db.add(pay_tx)

    db.commit()
    db.refresh(receipt)
    return receipt

def create_inventory_issue(
    db: Session,
    code: str,
    issue_date: date,
    reason: str,
    items: List[Dict[str, Any]],
    production_order_id: Optional[int],
    note: Optional[str],
    user_id: Optional[int]
) -> InventoryIssue:
    """
    Tạo phiếu xuất kho nguyên vật liệu:
    - Kiểm tra đủ tồn kho
    - Trừ tồn kho
    - Ghi nhận lịch sử biến động
    """
    # 1. Kiểm tra tồn kho trước
    for item in items:
        mat_id = int(item["material_id"])
        qty = float(item["quantity"])
        mat = db.query(Material).filter(Material.id == mat_id).first()
        if not mat:
            raise ValueError(f"Không tìm thấy vật tư có ID {mat_id}")
        if mat.stock_quantity < qty:
            raise ValueError(f"Vật tư '{mat.name}' không đủ tồn kho (Cần: {qty} {mat.unit}, Hiện còn: {mat.stock_quantity} {mat.unit})")

    # 2. Tạo phiếu xuất
    total_amount = sum(float(item["quantity"]) * float(item.get("unit_price", 0.0)) for item in items)
    issue = InventoryIssue(
        code=code,
        date=issue_date,
        reason=reason,
        production_order_id=production_order_id,
        total_amount=total_amount,
        note=note,
        created_by_id=user_id
    )
    db.add(issue)
    db.flush()

    for item in items:
        mat_id = int(item["material_id"])
        qty = float(item["quantity"])
        mat = db.query(Material).filter(Material.id == mat_id).first()
        price = float(item.get("unit_price", mat.unit_price))
        line_total = qty * price

        detail = InventoryIssueDetail(
            issue_id=issue.id,
            material_id=mat_id,
            quantity=qty,
            unit_price=price,
            total_price=line_total
        )
        db.add(detail)

        # Trừ tồn kho
        new_qty = mat.stock_quantity - qty
        mat.stock_quantity = new_qty

        # Ghi log biến động
        tx = InventoryTransaction(
            material_id=mat.id,
            transaction_type="Xuất kho",
            reference_code=issue.code,
            quantity_change=-qty,
            balance_after=new_qty,
            note=f"Xuất kho lý do: {reason} (Phiếu {issue.code})"
        )
        db.add(tx)

    db.commit()
    db.refresh(issue)
    return issue
