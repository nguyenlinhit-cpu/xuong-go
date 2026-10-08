from datetime import date
from app.models.sales import Product, Customer, Order, OrderDetail, OrderStatus

def test_order_creation_and_balance(db_session):
    customer = Customer(
        code="KH-TEST-01",
        name="Khách Hàng Test",
        phone="0988776655"
    )
    product = Product(
        code="SP-TEST-01",
        name="Bàn ghế test",
        price=10000000.0
    )
    db_session.add_all([customer, product])
    db_session.commit()

    order = Order(
        code="DH-TEST-001",
        customer_id=customer.id,
        order_date=date.today(),
        status=OrderStatus.MOI,
        total_amount=20000000.0,
        discount=1000000.0,
        final_amount=19000000.0,
        deposit_amount=5000000.0,
        remaining_amount=14000000.0
    )
    db_session.add(order)
    db_session.flush()

    detail = OrderDetail(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=10000000.0,
        total_price=20000000.0
    )
    db_session.add(detail)
    db_session.commit()

    assert order.id is not None
    assert len(order.details) == 1
    assert order.final_amount == 19000000.0
    assert order.remaining_amount == 14000000.0
