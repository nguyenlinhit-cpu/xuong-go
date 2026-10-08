from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class OrderStatus:
    MOI = "Mới"
    DANG_SAN_XUAT = "Đang sản xuất"
    HOAN_THIEN = "Hoàn thiện"
    DA_GIAO = "Đã giao"
    DA_THANH_TOAN = "Đã thanh toán"
    HUY = "Đã hủy"

    ALL = [MOI, DANG_SAN_XUAT, HOAN_THIEN, DA_GIAO, DA_THANH_TOAN, HUY]

class Product(Base):
    """Bảng thành phẩm nội thất gỗ."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)   # SP-001, BA-SO-01
    name = Column(String(200), nullable=False)                           # Bàn ăn gỗ sồi 6 ghế
    wood_type = Column(String(100), nullable=True)                       # Gỗ sồi Nga
    dimensions = Column(String(100), nullable=True)                      # 1600 x 800 x 750 mm
    price = Column(Float, default=0.0, nullable=False)                   # Giá bán niêm yết (VNĐ)
    image_url = Column(String(255), nullable=True)                      # Đường dẫn ảnh sản phẩm
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Quan hệ
    bom_items = relationship("BillOfMaterials", back_populates="product", cascade="all, delete-orphan")
    order_details = relationship("OrderDetail", back_populates="product")
    production_orders = relationship("ProductionOrder", back_populates="product")

class BillOfMaterials(Base):
    """Định mức nguyên vật liệu (BOM) cho 1 đơn vị sản phẩm."""
    __tablename__ = "bill_of_materials"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0) # Số lượng NVL cần cho 1 sản phẩm
    note = Column(String(255), nullable=True)

    product = relationship("Product", back_populates="bom_items")
    material = relationship("Material", back_populates="bom_items")

class Customer(Base):
    """Bảng khách hàng."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)   # KH-001
    name = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    debt_amount = Column(Float, default=0.0)                             # Công nợ phải thu (VNĐ)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")

class Order(Base):
    """Đơn hàng bán ra."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)   # DH-YYYYMMDD-xxx
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_date = Column(Date, default=date.today, nullable=False)
    delivery_date = Column(Date, nullable=True)                          # Ngày hẹn giao hàng
    status = Column(String(50), default=OrderStatus.MOI, nullable=False)
    total_amount = Column(Float, default=0.0)                            # Tổng tiền hàng
    discount = Column(Float, default=0.0)                                # Giảm giá (VNĐ)
    final_amount = Column(Float, default=0.0)                            # Sau giảm giá
    deposit_amount = Column(Float, default=0.0)                          # Đã đặt cọc / trả
    remaining_amount = Column(Float, default=0.0)                        # Còn lại phải thanh toán
    note = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    created_by = relationship("User")
    details = relationship("OrderDetail", back_populates="order", cascade="all, delete-orphan")
    production_orders = relationship("ProductionOrder", back_populates="order")

class OrderDetail(Base):
    """Chi tiết từng sản phẩm trong đơn hàng."""
    __tablename__ = "order_details"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False, default=0.0)
    total_price = Column(Float, nullable=False, default=0.0)
    custom_requirements = Column(Text, nullable=True) # Yêu cầu quy cách riêng của khách

    order = relationship("Order", back_populates="details")
    product = relationship("Product", back_populates="order_details")
