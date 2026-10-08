from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class TransactionType:
    THU = "Thu"
    CHI = "Chi"

class TransactionCategory:
    # Danh mục thu
    THU_COC_DON_HANG = "Thu đặt cọc đơn hàng"
    THU_THANH_TOAN_DON = "Thu thanh toán đơn hàng"
    THU_BAN_PHU_PHAM = "Thu bán phế liệu/mùn cưa"
    THU_KHAC = "Thu khác"

    # Danh mục chi
    CHI_NHAP_NVL = "Chi mua nguyên vật liệu"
    CHI_LUONG_THO = "Chi trả lương/tạm ứng thợ"
    CHI_DIEN_NUOC_XUONG = "Chi điện nước xưởng"
    CHI_MAT_BANG = "Chi thuê mặt bằng xưởng"
    CHI_SUA_CHUA_MAY = "Chi sửa chữa máy móc thiết bị"
    CHI_VAN_CHUYEN = "Chi vận chuyển & giao hàng"
    CHI_KHAC = "Chi phí khác"

    ALL_INCOME = [THU_COC_DON_HANG, THU_THANH_TOAN_DON, THU_BAN_PHU_PHAM, THU_KHAC]
    ALL_EXPENSE = [CHI_NHAP_NVL, CHI_LUONG_THO, CHI_DIEN_NUOC_XUONG, CHI_MAT_BANG, CHI_SUA_CHUA_MAY, CHI_VAN_CHUYEN, CHI_KHAC]

class PaymentMethod:
    TIEN_MAT = "Tiền mặt"
    CHUYEN_KHOAN = "Chuyển khoản"

class CashTransaction(Base):
    """Sổ quỹ thu chi tiền mặt và tài khoản ngân hàng."""
    __tablename__ = "cash_transactions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # PT-xxx hoặc PC-xxx
    transaction_type = Column(String(20), nullable=False)              # "Thu" hoặc "Chi"
    category = Column(String(100), nullable=False)                     # Danh mục thu chi
    amount = Column(Float, nullable=False, default=0.0)                # Số tiền (VNĐ)
    transaction_date = Column(Date, default=date.today, nullable=False)
    payment_method = Column(String(50), default=PaymentMethod.TIEN_MAT)
    payer_or_receiver = Column(String(150), nullable=True)             # Người nộp tiền hoặc người nhận tiền
    reference_code = Column(String(50), nullable=True)                 # Mã đơn hàng / Mã phiếu nhập / Mã thợ
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    receipt_id = Column(Integer, ForeignKey("inventory_receipts.id", ondelete="SET NULL"), nullable=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="SET NULL"), nullable=True)
    note = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    created_by = relationship("User")
    order = relationship("Order")
    receipt = relationship("InventoryReceipt")
    worker = relationship("Worker")
