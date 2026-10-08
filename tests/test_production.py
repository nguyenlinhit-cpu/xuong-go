from datetime import date
from app.models.sales import Product, BillOfMaterials, Order, OrderStatus
from app.models.inventory import Material, MaterialCategory
from app.models.production import (
    ProductionOrder, ProductionOrderStatus, StageStatus,
    ProductionStageName
)
from app.services.production_service import (
    create_production_order,
    calculate_materials_needed_for_order,
    deduct_materials_for_production,
    update_stage_progress
)

def test_production_and_bom_flow(db_session):
    # 1. Tạo vật tư và sản phẩm kèm BOM
    wood = Material(
        code="NL-GO-TEST",
        name="Gỗ thử nghiệm",
        category=MaterialCategory.GO_TU_NHIEN,
        unit="m³",
        stock_quantity=10.0,
        unit_price=15000000.0,
        min_stock_alert=1.0
    )
    product = Product(
        code="SP-GO-TEST",
        name="Tủ thử nghiệm",
        price=8000000.0
    )
    db_session.add_all([wood, product])
    db_session.commit()

    bom = BillOfMaterials(
        product_id=product.id,
        material_id=wood.id,
        quantity=0.5 # Mỗi tủ cần 0.5 m³
    )
    db_session.add(bom)
    db_session.commit()

    # 2. Tạo lệnh sản xuất 2 tủ -> Cần 1.0 m³ gỗ
    p_order = create_production_order(
        db=db_session,
        code="LSX-TEST-001",
        product_id=product.id,
        quantity=2,
        start_date=date.today(),
        due_date=None
    )
    assert p_order.id is not None
    assert len(p_order.stages) == 6 # 6 công đoạn

    # 3. Tính toán nguyên liệu theo BOM
    needed = calculate_materials_needed_for_order(db_session, product.id, 2)
    assert len(needed) == 1
    assert needed[0]["required_qty"] == 1.0
    assert needed[0]["is_sufficient"] is True

    # 4. Trừ kho sản xuất
    deduct_materials_for_production(db_session, p_order.id, user_id=1)
    assert p_order.materials_deducted is True
    assert wood.stock_quantity == 9.0 # 10.0 - 1.0

    # 5. Cập nhật các công đoạn sang Hoàn thành
    for st in p_order.stages:
        update_stage_progress(db_session, st.id, StageStatus.HOAN_THANH)

    assert p_order.status == ProductionOrderStatus.HOAN_THANH
