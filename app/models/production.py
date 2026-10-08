from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class ProductionOrderStatus:
    CHUA_KHOI_DONG = "Chưa khởi động"
    DANG_THUC_HIEN = "Đang thực hiện"
    HOAN_THANH = "Hoàn thành"
    HUY = "Hủy"

    ALL = [CHUA_KHOI_DONG, DANG_THUC_HIEN, HOAN_THANH, HUY]

class ProductionStageName:
    PHA_PHOI = "Pha phôi"
    GIA_CONG = "Gia công"
    LAP_RAP = "Lắp ráp"
    CHA_NHAM = "Chà nhám"
    SON = "Sơn"
    DONG_GOI = "Đóng gói"

    DEFAULT_STAGES = [PHA_PHOI, GIA_CONG, LAP_RAP, CHA_NHAM, SON, DONG_GOI]

class StageStatus:
    CHUA_LAM = "Chưa làm"
    DANG_LAM = "Đang làm"
    HOAN_THANH = "Hoàn thành"

class ProductionOrder(Base):
    """Lệnh sản xuất thành phẩm."""
    __tablename__ = "production_orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # LSX-YYYYMMDD-xxx
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True) # Liên kết đơn hàng (nếu có)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)              # Số lượng cần sản xuất
    start_date = Column(Date, default=date.today)
    due_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    status = Column(String(50), default=ProductionOrderStatus.CHUA_KHOI_DONG, nullable=False)
    materials_deducted = Column(Boolean, default=False)                # Đã trừ kho nguyên liệu chưa
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="production_orders")
    product = relationship("Product", back_populates="production_orders")
    stages = relationship("ProductionStage", back_populates="production_order", cascade="all, delete-orphan", order_by="ProductionStage.order_seq")
    inventory_issues = relationship("InventoryIssue", back_populates="production_order")

class ProductionStage(Base):
    """Công đoạn sản xuất chi tiết."""
    __tablename__ = "production_stages"

    id = Column(Integer, primary_key=True, index=True)
    production_order_id = Column(Integer, ForeignKey("production_orders.id"), nullable=False)
    order_seq = Column(Integer, default=1)                             # Thứ tự công đoạn: 1, 2, 3...
    name = Column(String(100), nullable=False)                         # Pha phôi, Gia công, Lắp ráp...
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True) # Thợ phụ trách
    status = Column(String(50), default=StageStatus.CHUA_LAM)          # Chưa làm, Đang làm, Hoàn thành
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)                                # Đánh giá chất lượng / kiểm tra KCS

    production_order = relationship("ProductionOrder", back_populates="stages")
    worker = relationship("Worker", back_populates="assigned_stages")

class WorkerSalaryType:
    NGAY = "Lương ngày"
    SAN_PHAM = "Lương sản phẩm"

class Worker(Base):
    """Hồ sơ thợ / nhân công xưởng mộc."""
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False) # THO-001
    full_name = Column(String(150), nullable=False)
    phone = Column(String(50), nullable=True)
    skill_level = Column(String(100), nullable=True)                   # Thợ mộc chính, Thợ phụ, Thợ sơn PU, Thợ đục...
    salary_type = Column(String(50), default=WorkerSalaryType.NGAY)    # Lương ngày / Lương sản phẩm
    base_salary_rate = Column(Float, default=400000.0)                 # Mức lương theo ngày hoặc theo đơn giá sản phẩm
    start_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_stages = relationship("ProductionStage", back_populates="worker")
    timesheets = relationship("Timesheet", back_populates="worker", cascade="all, delete-orphan")
    salary_advances = relationship("SalaryAdvance", back_populates="worker", cascade="all, delete-orphan")

class Timesheet(Base):
    """Chấm công thợ theo ngày."""
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    work_date = Column(Date, default=date.today, nullable=False)
    work_units = Column(Float, default=1.0) # 1.0 = Cả ngày, 0.5 = Nửa ngày, 0 = Nghỉ
    overtime_hours = Column(Float, default=0.0) # Số giờ tăng ca
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="timesheets")

class SalaryAdvance(Base):
    """Tạm ứng lương thợ."""
    __tablename__ = "salary_advances"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    advance_date = Column(Date, default=date.today, nullable=False)
    amount = Column(Float, nullable=False, default=0.0) # Số tiền tạm ứng (VNĐ)
    reason = Column(String(255), nullable=True)
    is_deducted = Column(Boolean, default=False)        # Đã trừ vào bảng lương tháng chưa
    created_at = Column(DateTime, default=datetime.utcnow)

    worker = relationship("Worker", back_populates="salary_advances")
