from datetime import date
import pytest
from app.models.inventory import Material, MaterialCategory, Supplier
from app.services.inventory_service import create_inventory_receipt, create_inventory_issue

def test_inventory_flow(db_session):
    # 1. Tạo nhà cung cấp và vật tư
    supplier = Supplier(
        code="NCC-TEST-01",
        name="Công ty Gỗ Test",
        phone="0911222333"
    )
    db_session.add(supplier)

    material = Material(
        code="NL-TEST-SO",
        name="Gỗ sồi test",
        category=MaterialCategory.GO_TU_NHIEN,
        unit="m³",
        stock_quantity=5.0,
        unit_price=18000000.0,
        min_stock_alert=2.0
    )
    db_session.add(material)
    db_session.commit()

    # 2. Nhập kho thêm 3 m³
    items = [{
        "material_id": material.id,
        "quantity": 3.0,
        "unit_price": 20000000.0
    }]
    receipt = create_inventory_receipt(
        db=db_session,
        code="PNK-TEST-001",
        supplier_id=supplier.id,
        receipt_date=date.today(),
        items=items,
        paid_amount=60000000.0,
        note="Nhập kho thử nghiệm",
        user_id=1,
        create_payment_voucher=False
    )
    assert receipt.id is not None
    assert material.stock_quantity == 8.0 # 5.0 + 3.0

    # 3. Xuất kho 2 m³
    issue_items = [{
        "material_id": material.id,
        "quantity": 2.0,
        "unit_price": material.unit_price
    }]
    issue = create_inventory_issue(
        db=db_session,
        code="PXK-TEST-001",
        issue_date=date.today(),
        reason="Sản xuất thử nghiệm",
        items=issue_items,
        production_order_id=None,
        note="Xuất kho test",
        user_id=1
    )
    assert issue.id is not None
    assert material.stock_quantity == 6.0 # 8.0 - 2.0

    # 4. Thử xuất vượt quá tồn kho -> Phải văng lỗi
    with pytest.raises(ValueError):
        create_inventory_issue(
            db=db_session,
            code="PXK-TEST-FAIL",
            issue_date=date.today(),
            reason="Xuất vượt tồn",
            items=[{"material_id": material.id, "quantity": 100.0}],
            production_order_id=None,
            note="Test fail",
            user_id=1
        )
