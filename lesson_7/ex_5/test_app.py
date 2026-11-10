import pytest
from sqlalchemy import event
from app import app, db, Order

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

# ==============================================================================
# 1. TEST POST ENDPOINT: Tạo đơn hàng
# ==============================================================================
def test_post_create_order(client):
    payload = {
        "items": [
            {"name": "Bút bi", "quantity": 2, "price": 5000.0},
            {"name": "Vở viết", "quantity": 1, "price": 10000.0}
        ]
    }
    res = client.post("/api/v1/orders", json=payload)
    assert res.status_code == 201
    assert "order_id" in res.get_json()

    # Kiểm tra trong DB
    with app.app_context():
        order = db.session.get(Order, 1)
        assert order is not None
        assert len(order.items) == 2

# ==============================================================================
# 2. TEST GET ENDPOINT VÀ ĐẾM SỐ TRUY VẤN (PHÁT HIỆN BẪY N+1)
# ==============================================================================
def test_get_orders_eager_loading_avoids_n1(client):
    # Tạo sẵn 10 đơn hàng, mỗi đơn hàng có 2 sản phẩm
    for i in range(10):
        client.post("/api/v1/orders", json={
            "items": [
                {"name": f"Item A-{i}", "quantity": 1, "price": 1000},
                {"name": f"Item B-{i}", "quantity": 2, "price": 2000}
            ]
        })

    queries = []
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        if statement.strip().upper().startswith("SELECT"):
            queries.append(statement)

    # Lắng nghe các câu lệnh SQL thực thi
    event.listen(db.engine, "before_cursor_execute", count_queries)

    try:
        res = client.get("/api/v1/orders")
        assert res.status_code == 200
        data = res.get_json()
        assert len(data) == 10

        # GIẢI THÍCH KIỂM TRA N+1:
        # Nếu bị lỗi N+1 (lazy loading): sẽ phát sinh 1 query lấy 10 orders + 10 query lấy items = 11 queries!
        # Nhờ eager loading (selectinload): chỉ phát sinh ĐÚNG 2 queries (1 lấy orders + 1 lấy items IN (...))!
        assert len(queries) == 2, f"Phát hiện lỗi N+1! Số truy vấn phát sinh là {len(queries)} (mong đợi: 2)"
    finally:
        event.remove(db.engine, "before_cursor_execute", count_queries)

