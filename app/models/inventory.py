from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class MaterialCategory:
    GO_TU_NHIEN = "Gỗ tự nhiên"
    GO_CONG_NGHIEP = "Gỗ công nghiệp"
    PHU_KIEN = "Phụ kiện"
    VAT_TU = "Vật tư phụ"

    ALL = [GO_TU_NHIEN, GO_CONG_NGHIEP, PHU_KIEN, VAT_TU]

class Material(Base):
    """Bảng nguyên liệu gỗ và phụ kiện, vật tư kho."""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # VD: NL-GO-01, PK-BL-01
    name = Column(String(200), nullable=False)                         # VD: Gỗ sồi đỏ nhập khẩu
    category = Column(String(50), nullable=False, default=MaterialCategory.GO_TU_NHIEN)
    wood_type = Column(String(100), nullable=True)                     # VD: Sồi, Gõ đỏ, Xoan đào, MDF...
    unit = Column(String(50), nullable=False, default="m³")            # m³, tấm, cây, cái, bộ, kg, lít...
    dimensions = Column(String(100), nullable=True)                    # VD: 2440 x 1220 x 18 mm
    stock_quantity = Column(Float, default=0.0, nullable=False)       # Tồn kho hiện tại
    unit_price = Column(Float, default=0.0, nullable=False)           # Đơn giá vốn bình quân (VNĐ)
    min_stock_alert = Column(Float, default=0.0, nullable=False)      # Mức tồn tối thiểu cảnh báo
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    receipt_details = relationship("InventoryReceiptDetail", back_populates="material")
    issue_details = relationship("InventoryIssueDetail", back_populates="material")
    transactions = relationship("InventoryTransaction", back_populates="material", cascade="all, delete-orphan")
    bom_items = relationship("BillOfMaterials", back_populates="material")

    @property
    def is_low_stock(self) -> bool:
        """Kiểm tra có sắp hết hàng không."""
        return self.stock_quantity <= self.min_stock_alert

class Supplier(Base):
    """Bảng nhà cung cấp nguyên vật liệu."""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # VD: NCC-001
    name = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    tax_id = Column(String(50), nullable=True)
    debt_amount = Column(Float, default=0.0) # Công nợ phải trả NCC (VNĐ)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    receipts = relationship("InventoryReceipt", back_populates="supplier")

class InventoryReceipt(Base):
    """Phiếu nhập kho nguyên vật liệu."""
    __tablename__ = "inventory_receipts"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # PNK-YYYYMMDD-xxx
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    date = Column(Date, default=date.today, nullable=False)
    total_amount = Column(Float, default=0.0)                          # Tổng tiền nhập kho
    paid_amount = Column(Float, default=0.0)                           # Đã thanh toán cho NCC
    note = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    supplier = relationship("Supplier", back_populates="receipts")
    created_by = relationship("User")
    details = relationship("InventoryReceiptDetail", back_populates="receipt", cascade="all, delete-orphan")

class InventoryReceiptDetail(Base):
    """Chi tiết từng dòng nguyên vật liệu trên phiếu nhập kho."""
    __tablename__ = "inventory_receipt_details"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("inventory_receipts.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)

    # Relationships
    receipt = relationship("InventoryReceipt", back_populates="details")
    material = relationship("Material", back_populates="receipt_details")

class InventoryIssue(Base):
    """Phiếu xuất kho nguyên vật liệu."""
    __tablename__ = "inventory_issues"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # PXK-YYYYMMDD-xxx
    date = Column(Date, default=date.today, nullable=False)
    reason = Column(String(100), default="Sản xuất theo lệnh")         # Lý do xuất: Sản xuất, Hao hụt, Bán lẻ...
    production_order_id = Column(Integer, ForeignKey("production_orders.id", ondelete="SET NULL"), nullable=True)
    total_amount = Column(Float, default=0.0)
    note = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    created_by = relationship("User")
    production_order = relationship("ProductionOrder", back_populates="inventory_issues")
    details = relationship("InventoryIssueDetail", back_populates="issue", cascade="all, delete-orphan")

class InventoryIssueDetail(Base):
    """Chi tiết từng dòng trên phiếu xuất kho."""
    __tablename__ = "inventory_issue_details"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("inventory_issues.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)

    # Relationships
    issue = relationship("InventoryIssue", back_populates="details")
    material = relationship("Material", back_populates="issue_details")

class InventoryTransaction(Base):
    """Lịch sử biến động tồn kho chi tiết."""
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    transaction_type = Column(String(50), nullable=False)              # Nhập kho, Xuất kho, Điều chỉnh
    reference_code = Column(String(50), nullable=False)                # Mã phiếu PNK-xxx hoặc PXK-xxx
    quantity_change = Column(Float, nullable=False)                    # + hoặc -
    balance_after = Column(Float, nullable=False)                      # Tồn sau giao dịch
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("Material", back_populates="transactions")
