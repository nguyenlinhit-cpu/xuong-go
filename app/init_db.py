from datetime import date, datetime, timedelta
from app.database import engine, Base, SessionLocal
from app.models import (
    User, RoleEnum,
    Material, MaterialCategory,
    Supplier,
    Product, BillOfMaterials,
    Customer, Order, OrderDetail, OrderStatus,
    Worker, WorkerSalaryType,
    ProductionOrder, ProductionStage, ProductionOrderStatus, ProductionStageName, StageStatus,
    CashTransaction, TransactionType, TransactionCategory, PaymentMethod,
    InventoryReceipt, InventoryReceiptDetail, InventoryTransaction
)
from app.utils import hash_password

def init_database():
    """Tạo bảng và dữ liệu mẫu đầy đủ cho xưởng gỗ."""
    print("🚀 Đang khởi tạo các bảng cơ sở dữ liệu...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Kiểm tra nếu đã có admin thì không nạp lại
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("ℹ️ Dữ liệu đã được khởi tạo từ trước.")
            return

        print("👤 Đang tạo tài khoản người dùng mẫu...")
        users = [
            User(
                username="admin",
                hashed_password=hash_password("admin123"),
                full_name="Quản Trị Viên (Admin)",
                role=RoleEnum.ADMIN,
                is_active=True
            ),
            User(
                username="kho",
                hashed_password=hash_password("kho123"),
                full_name="Nguyễn Văn Kho",
                role=RoleEnum.KHO,
                is_active=True
            ),
            User(
                username="quandoc",
                hashed_password=hash_password("quandoc123"),
                full_name="Trần Văn Quản Đốc",
                role=RoleEnum.QUAN_DOC,
                is_active=True
            ),
            User(
                username="ketoan",
                hashed_password=hash_password("ketoan123"),
                full_name="Lê Thị Kế Toán",
                role=RoleEnum.KE_TOAN,
                is_active=True
            )
        ]
        db.add_all(users)
        db.commit()

        print("🏢 Đang tạo danh sách nhà cung cấp...")
        ncc1 = Supplier(
            code="NCC-01",
            name="Công Ty Gỗ Nhập Khẩu Bảo Phát",
            phone="0912.333.444",
            email="baophatwood@gmail.com",
            address="Khu Cảng Đình Vũ, Hải Phòng",
            tax_id="0201889911",
            debt_amount=15000000.0,
            note="Chuyên cung cấp gỗ Sồi, Gõ Đỏ, Óc Chó xẻ sấy quy cách"
        )
        ncc2 = Supplier(
            code="NCC-02",
            name="Công Ty CP Gỗ An Cường",
            phone="0274.3888.999",
            email="sales@ancuong.com",
            address="Bình Dương - Chi nhánh Hà Nội",
            tax_id="3700748131",
            debt_amount=0.0,
            note="Nhà cung cấp ván MDF, HDF, Melamine chính hãng"
        )
        ncc3 = Supplier(
            code="NCC-03",
            name="Phụ Kiện Nội Thất Hafele & Ivan Đại Hưng",
            phone="0988.555.666",
            email="phukiendaihung@gmail.com",
            address="Đê La Thành, Ba Đình, Hà Nội",
            tax_id="0107665544",
            debt_amount=4500000.0,
            note="Chuyên bản lề, ray trượt, ốc vít, tay nắm tủ"
        )
        ncc4 = Supplier(
            code="NCC-04",
            name="Tổng Đại Lý Sơn & Keo Đại Dương",
            phone="0977.111.222",
            email="daiduongpaint@gmail.com",
            address="Vạn Phúc, Hà Đông, Hà Nội",
            tax_id="0108223344",
            debt_amount=0.0,
            note="Sơn PU Oseven, keo dán Titebond"
        )
        db.add_all([ncc1, ncc2, ncc3, ncc4])
        db.commit()

        print("🪵 Đang tạo nguyên vật liệu kho...")
        materials = [
            Material(
                code="NL-SO-01",
                name="Gỗ Sồi Trắng Mỹ (White Oak)",
                category=MaterialCategory.GO_TU_NHIEN,
                wood_type="Sồi Mỹ",
                unit="m³",
                dimensions="Dài 2.5m - 3m, dày 26mm",
                stock_quantity=18.5,
                unit_price=18500000.0,
                min_stock_alert=5.0,
                description="Gỗ nhập khẩu xẻ sấy chuẩn độ ẩm 10-12%"
            ),
            Material(
                code="NL-GO-02",
                name="Gỗ Gõ Đỏ Nam Phi (Pachy)",
                category=MaterialCategory.GO_TU_NHIEN,
                wood_type="Gõ đỏ",
                unit="m³",
                dimensions="Hộp xẻ theo quy cách",
                stock_quantity=8.2,
                unit_price=32000000.0,
                min_stock_alert=3.0,
                description="Vân đẹp, tom gỗ mịn, không cong vênh"
            ),
            Material(
                code="NL-XD-03",
                name="Gỗ Xoan Đào Gia Lai",
                category=MaterialCategory.GO_TU_NHIEN,
                wood_type="Xoan đào",
                unit="m³",
                dimensions="Xẻ sấy tự nhiên",
                stock_quantity=3.5, # Tồn thấp cảnh báo
                unit_price=14500000.0,
                min_stock_alert=4.0, # <= min_stock_alert -> cảnh báo!
                description="Hàng nội địa Tây Nguyên chất lượng cao"
            ),
            Material(
                code="NL-MDF-04",
                name="Ván MDF Chống Ẩm An Cường 17mm",
                category=MaterialCategory.GO_CONG_NGHIEP,
                wood_type="MDF lõi xanh",
                unit="tấm",
                dimensions="1220 x 2440 x 17 mm",
                stock_quantity=60.0,
                unit_price=390000.0,
                min_stock_alert=20.0,
                description="Ván MDF phủ melamine chống ẩm chuẩn E1"
            ),
            Material(
                code="NL-HDF-05",
                name="Ván HDF Phủ Melamine Vân Sồi 18mm",
                category=MaterialCategory.GO_CONG_NGHIEP,
                wood_type="HDF",
                unit="tấm",
                dimensions="1220 x 2440 x 18 mm",
                stock_quantity=12.0, # Sắp hết
                unit_price=460000.0,
                min_stock_alert=15.0,
                description="Chịu lực cao, phủ bề mặt vân gỗ tự nhiên"
            ),
            Material(
                code="PK-BL-06",
                name="Bản Lề Giảm Chấn Hafele Inox 304",
                category=MaterialCategory.PHU_KIEN,
                wood_type=None,
                unit="cái",
                dimensions="Trùm ngoài, góc mở 105 độ",
                stock_quantity=240.0,
                unit_price=38000.0,
                min_stock_alert=50.0,
                description="Bản lề hơi giảm chấn cao cấp"
            ),
            Material(
                code="PK-RAY-07",
                name="Ray Trượt Bi 3 Tầng Ivan 450mm",
                category=MaterialCategory.PHU_KIEN,
                wood_type=None,
                unit="bộ",
                dimensions="Chiều dài 450mm, bản rộng 45mm",
                stock_quantity=45.0,
                unit_price=70000.0,
                min_stock_alert=20.0,
                description="Ray bi giảm chấn dùng cho hộc tủ"
            ),
            Material(
                code="VT-SON-08",
                name="Sơn Lót & Bóng PU Cao Cấp Oseven",
                category=MaterialCategory.VAT_TU,
                wood_type=None,
                unit="thùng",
                dimensions="Thùng 20 Lít kèm cứng",
                stock_quantity=8.0,
                unit_price=1350000.0,
                min_stock_alert=3.0,
                description="Hệ sơn lót PU và bóng 50% chống trầy xước"
            ),
            Material(
                code="VT-KEO-09",
                name="Keo Ghép Mộng Gỗ Titebond II Premium",
                category=MaterialCategory.VAT_TU,
                wood_type=None,
                unit="bình",
                dimensions="Bình 3.78 Lít (1 Gallon)",
                stock_quantity=14.0,
                unit_price=520000.0,
                min_stock_alert=4.0,
                description="Keo dán gỗ chống nước chuẩn ANSI Type II"
            ),
            Material(
                code="VT-VIT-10",
                name="Ốc Vít Bắt Gỗ Mạ Kẽm 4x30mm",
                category=MaterialCategory.VAT_TU,
                wood_type=None,
                unit="hộp",
                dimensions="Hộp 500 con vít tự khoan",
                stock_quantity=30.0,
                unit_price=65000.0,
                min_stock_alert=10.0,
                description="Vít bắt gỗ đuôi cá mạ kẽm ren sắc ngọt"
            )
        ]
        db.add_all(materials)
        db.commit()

        # Tạo bản ghi biến động tồn kho ban đầu
        for m in materials:
            tx = InventoryTransaction(
                material_id=m.id,
                transaction_type="Nhập kho",
                reference_code="PNK-DAUKY",
                quantity_change=m.stock_quantity,
                balance_after=m.stock_quantity,
                note="Tồn kho đầu kỳ khởi tạo hệ thống"
            )
            db.add(tx)
        db.commit()

        print("🪑 Đang tạo danh mục sản phẩm và BOM...")
        p1 = Product(
            code="SP-BA-01",
            name="Bộ Bàn Ăn Gỗ Sồi Nga 6 Ghế Mặt Liền",
            wood_type="Sồi Mỹ / Nga",
            dimensions="1600 x 800 x 750 mm (Bàn) + 6 Ghế",
            price=12500000.0,
            image_url="/static/images/ban-an-go-soi.jpg",
            description="Bàn ăn gỗ sồi tự nhiên sơn lau màu óc chó sang trọng, mặt bàn xử lý chống ẩm."
        )
        p2 = Product(
            code="SP-GN-02",
            name="Giường Ngủ Hoàng Gia Gỗ Gõ Đỏ 1m8 x 2m",
            wood_type="Gỗ Gõ Đỏ",
            dimensions="1800 x 2000 x 1100 mm",
            price=28000000.0,
            image_url="/static/images/giuong-go-do.jpg",
            description="Giường phản dạt nan gỗ gõ tuyển chọn, đục chạm hoạ tiết hoa lá tây tinh xảo."
        )
        p3 = Product(
            code="SP-TA-03",
            name="Tủ Quần Áo 4 Cánh Hiện Đại Gỗ MDF Chống Ẩm",
            wood_type="MDF Lõi Xanh An Cường",
            dimensions="2000 x 600 x 2200 mm",
            price=14500000.0,
            image_url="/static/images/tu-ao-mdf.jpg",
            description="Thiết kế kịch trần, bản lề giảm chấn, tay nắm nhôm định hình hiện đại."
        )
        p4 = Product(
            code="SP-KT-04",
            name="Kệ Tivi Phòng Khách Bắc Âu Gỗ Sồi 2m",
            wood_type="Sồi Mỹ",
            dimensions="2000 x 400 x 550 mm",
            price=7200000.0,
            image_url="/static/images/ke-tivi.jpg",
            description="Kệ tivi dáng chân vát Scandinavian, 3 ngăn kéo ray bi trượt êm ái."
        )
        db.add_all([p1, p2, p3, p4])
        db.commit()

        # Tạo định mức BOM
        m_soi = db.query(Material).filter(Material.code == "NL-SO-01").first()
        m_godo = db.query(Material).filter(Material.code == "NL-GO-02").first()
        m_mdf = db.query(Material).filter(Material.code == "NL-MDF-04").first()
        m_banle = db.query(Material).filter(Material.code == "PK-BL-06").first()
        m_ray = db.query(Material).filter(Material.code == "PK-RAY-07").first()
        m_son = db.query(Material).filter(Material.code == "VT-SON-08").first()
        m_keo = db.query(Material).filter(Material.code == "VT-KEO-09").first()
        m_vit = db.query(Material).filter(Material.code == "VT-VIT-10").first()

        bom_items = [
            # BOM Bàn ăn gỗ sồi (p1)
            BillOfMaterials(product_id=p1.id, material_id=m_soi.id, quantity=0.28, note="Gỗ sồi thành phẩm bàn + 6 ghế"),
            BillOfMaterials(product_id=p1.id, material_id=m_keo.id, quantity=0.3, note="Keo mộng"),
            BillOfMaterials(product_id=p1.id, material_id=m_son.id, quantity=0.15, note="Sơn PU hoàn thiện"),
            BillOfMaterials(product_id=p1.id, material_id=m_vit.id, quantity=0.1, note="Vít gia cố"),

            # BOM Giường ngủ gõ đỏ (p2)
            BillOfMaterials(product_id=p2.id, material_id=m_godo.id, quantity=0.65, note="Gỗ gõ đỏ thành phẩm"),
            BillOfMaterials(product_id=p2.id, material_id=m_keo.id, quantity=0.4, note="Keo ghép"),
            BillOfMaterials(product_id=p2.id, material_id=m_son.id, quantity=0.25, note="Sơn lót & PU"),
            BillOfMaterials(product_id=p2.id, material_id=m_vit.id, quantity=0.15, note="Ốc liên kết vai giường"),

            # BOM Tủ áo MDF (p3)
            BillOfMaterials(product_id=p3.id, material_id=m_mdf.id, quantity=6.0, note="6 tấm MDF 17mm thùng & cánh"),
            BillOfMaterials(product_id=p3.id, material_id=m_banle.id, quantity=16.0, note="16 bản lề giảm chấn cho 4 cánh"),
            BillOfMaterials(product_id=p3.id, material_id=m_ray.id, quantity=3.0, note="3 bộ ray hộc tủ trong"),
            BillOfMaterials(product_id=p3.id, material_id=m_vit.id, quantity=0.5, note="Vít liên kết cam chốt"),

            # BOM Kệ tivi gỗ sồi (p4)
            BillOfMaterials(product_id=p4.id, material_id=m_soi.id, quantity=0.12, note="Gỗ sồi thân kệ & chân"),
            BillOfMaterials(product_id=p4.id, material_id=m_ray.id, quantity=3.0, note="3 bộ ray ngăn kéo"),
            BillOfMaterials(product_id=p4.id, material_id=m_son.id, quantity=0.08, note="Sơn bóng mờ PU")
        ]
        db.add_all(bom_items)
        db.commit()

        print("👷 Đang tạo hồ sơ thợ & nhân công...")
        w1 = Worker(
            code="THO-01",
            full_name="Bác Lê Văn Mộc",
            phone="0982.112.233",
            skill_level="Thợ cả / Chuyền trưởng",
            salary_type=WorkerSalaryType.NGAY,
            base_salary_rate=550000.0,
            start_date=date(2023, 1, 15),
            note="Thợ lành nghề trên 20 năm kinh nghiệm mộc cổ truyền và hiện đại"
        )
        w2 = Worker(
            code="THO-02",
            full_name="Trần Văn Nam",
            phone="0973.224.455",
            skill_level="Thợ mộc máy & gia công",
            salary_type=WorkerSalaryType.NGAY,
            base_salary_rate=450000.0,
            start_date=date(2023, 6, 1),
            note="Vận hành máy tubi, máy cưa bàn trượt, bào liên hợp"
        )
        w3 = Worker(
            code="THO-03",
            full_name="Nguyễn Đình Sơn",
            phone="0964.335.566",
            skill_level="Thợ sơn PU chính",
            salary_type=WorkerSalaryType.NGAY,
            base_salary_rate=500000.0,
            start_date=date(2023, 3, 10),
            note="Pha màu sơn bệt, sơn lau, phủ bóng PU cao cấp"
        )
        w4 = Worker(
            code="THO-04",
            full_name="Phạm Quốc Toàn",
            phone="0985.446.677",
            skill_level="Thợ phụ & Chà nhám đóng gói",
            salary_type=WorkerSalaryType.NGAY,
            base_salary_rate=350000.0,
            start_date=date(2024, 2, 20),
            note="Làm nguội, đánh giáp mịn, bọc màng PE chống xước"
        )
        db.add_all([w1, w2, w3, w4])
        db.commit()

        print("👥 Đang tạo danh sách khách hàng...")
        c1 = Customer(
            code="KH-01",
            name="Anh Hoàng Minh Tuấn",
            phone="0904.112.233",
            email="tuan.hoang@gmail.com",
            address="Căn hộ 1205, Tòa R1 Vinhomes Royal City, Thanh Xuân, Hà Nội",
            debt_amount=5000000.0,
            note="Khách đặt combo bàn ăn và kệ tivi, thanh toán nhanh"
        )
        c2 = Customer(
            code="KH-02",
            name="Chị Đặng Thu Hà",
            phone="0915.223.344",
            email="thuha.ecopark@gmail.com",
            address="Biệt thự Vườn Mai 88, KĐT Ecopark, Văn Giang, Hưng Yên",
            debt_amount=0.0,
            note="Khách VIP chuộng đồ gỗ gõ đỏ tự nhiên nguyên khối"
        )
        c3 = Customer(
            code="KH-03",
            name="Công Ty CP Thiết Kế Nội Thất Nhà Xinh",
            phone="0983.445.566",
            email="contact@nhaxinhdecor.vn",
            address="Số 45 Trung Hòa, Cầu Giấy, Hà Nội",
            debt_amount=12000000.0,
            note="Đối tác thiết kế thi công nội thất căn hộ trọn gói"
        )
        db.add_all([c1, c2, c3])
        db.commit()

        print("📋 Đang tạo đơn hàng và lệnh sản xuất mẫu...")
        # Đơn hàng 1
        order1 = Order(
            code="DH-20261001-001",
            customer_id=c1.id,
            order_date=date.today() - timedelta(days=5),
            delivery_date=date.today() + timedelta(days=7),
            status=OrderStatus.DANG_SAN_XUAT,
            total_amount=19700000.0,
            discount=500000.0,
            final_amount=19200000.0,
            deposit_amount=14200000.0,
            remaining_amount=5000000.0,
            note="Giao và lắp đặt tại Royal City, giao trước 17h.",
            created_by_id=1
        )
        db.add(order1)
        db.commit()

        od1 = OrderDetail(
            order_id=order1.id,
            product_id=p1.id,
            quantity=1,
            unit_price=12500000.0,
            total_price=12500000.0,
            custom_requirements="Màu sơn lau hạt dẻ sáng, bo tròn góc mặt bàn"
        )
        od2 = OrderDetail(
            order_id=order1.id,
            product_id=p4.id,
            quantity=1,
            unit_price=7200000.0,
            total_price=7200000.0,
            custom_requirements="Kệ khoét sẵn lỗ luồn dây điện thiết bị"
        )
        db.add_all([od1, od2])
        db.commit()

        # Phiếu thu tiền cọc đơn 1
        pt1 = CashTransaction(
            code="PT-20261001-001",
            transaction_type=TransactionType.THU,
            category=TransactionCategory.THU_COC_DON_HANG,
            amount=14200000.0,
            transaction_date=date.today() - timedelta(days=5),
            payment_method=PaymentMethod.CHUYEN_KHOAN,
            payer_or_receiver=c1.name,
            reference_code=order1.code,
            order_id=order1.id,
            note="Khách chuyển khoản cọc đơn hàng DH-20261001-001",
            created_by_id=1
        )
        db.add(pt1)
        db.commit()

        # Lệnh sản xuất cho Bàn ăn đơn 1
        lsx1 = ProductionOrder(
            code="LSX-20261001-001",
            order_id=order1.id,
            product_id=p1.id,
            quantity=1,
            start_date=date.today() - timedelta(days=4),
            due_date=date.today() + timedelta(days=5),
            status=ProductionOrderStatus.DANG_THUC_HIEN,
            materials_deducted=True,
            note="Lệnh đóng bàn ăn 6 ghế cho đơn hàng " + order1.code
        )
        db.add(lsx1)
        db.commit()

        # Tạo 6 công đoạn sản xuất cho LSX 1
        stages_data = [
            (1, ProductionStageName.PHA_PHOI, w1.id, StageStatus.HOAN_THANH, "Xẻ phôi chuẩn kích thước bản vẽ"),
            (2, ProductionStageName.GIA_CONG, w2.id, StageStatus.HOAN_THANH, "Đánh mộng, soi chỉ cạnh bàn"),
            (3, ProductionStageName.LAP_RAP, w1.id, StageStatus.DANG_LAM, "Đang ghép khung bàn và vào keo cữ"),
            (4, ProductionStageName.CHA_NHAM, w4.id, StageStatus.CHUA_LAM, "Chờ lắp ráp xong"),
            (5, ProductionStageName.SON, w3.id, StageStatus.CHUA_LAM, "Chờ sơn lót và sơn lau hạt dẻ"),
            (6, ProductionStageName.DONG_GOI, w4.id, StageStatus.CHUA_LAM, "Bọc màng PE chuẩn bị giao")
        ]
        for seq, name, worker_id, status, notes in stages_data:
            st = ProductionStage(
                production_order_id=lsx1.id,
                order_seq=seq,
                name=name,
                worker_id=worker_id,
                status=status,
                notes=notes
            )
            db.add(st)
        db.commit()

        # Thêm một số phiếu chi vận hành xưởng
        pc1 = CashTransaction(
            code="PC-20261002-001",
            transaction_type=TransactionType.CHI,
            category=TransactionCategory.CHI_DIEN_NUOC_XUONG,
            amount=3850000.0,
            transaction_date=date.today() - timedelta(days=4),
            payment_method=PaymentMethod.CHUYEN_KHOAN,
            payer_or_receiver="Điện Lực Thạch Thất",
            reference_code="HD-D-1026",
            note="Thanh toán tiền điện 3 pha xưởng mộc tháng trước",
            created_by_id=1
        )
        pc2 = CashTransaction(
            code="PC-20261003-002",
            transaction_type=TransactionType.CHI,
            category=TransactionCategory.CHI_SUA_CHUA_MAY,
            amount=850000.0,
            transaction_date=date.today() - timedelta(days=2),
            payment_method=PaymentMethod.TIEN_MAT,
            payer_or_receiver="Thợ sửa cơ khí Tuấn Anh",
            reference_code="SC-MAY-01",
            note="Bảo dưỡng thay vòng bi máy cuốn và mài lưỡi bào",
            created_by_id=1
        )
        db.add_all([pc1, pc2])
        db.commit()

        print("✅ Khởi tạo dữ liệu mẫu thành công!")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
