from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import selectinload

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ==============================================================================
# MODELS: Quan hệ 1-N giữa Order và OrderItem
# ==============================================================================
class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="pending")
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# ==============================================================================
# 1. ENDPOINT POST: Tạo Order kèm nhiều OrderItem
# ==============================================================================
@app.post("/api/v1/orders")
def create_order():
    data = request.get_json() or {}
    items_data = data.get("items", [])
    if not items_data:
        return jsonify({"error": "Đơn hàng phải có ít nhất 1 item"}), 400

    order = Order()
    order.status = "pending"
    db.session.add(order)

    for item in items_data:
        db.session.add(OrderItem(
            order=order,
            name=item["name"],
            quantity=item.get("quantity", 1),
            price=item.get("price", 0.0)
        ))

    db.session.commit()
    return jsonify({"message": "Tạo đơn hàng thành công", "order_id": order.id}), 201

# ==============================================================================
# 2. ENDPOINT GET: Lấy danh sách có EAGER LOADING (selectinload) tránh N+1 Query
# ==============================================================================
@app.get("/api/v1/orders")
def get_orders():
    # Dùng selectinload để eager load toàn bộ OrderItem chỉ bằng 1 câu SELECT phụ thay vì N câu
    stmt = db.select(Order).options(selectinload(Order.items))
    orders = db.session.execute(stmt).scalars().all()

    result = [
        {
            "id": o.id,
            "status": o.status,
            "items": [{"name": i.name, "quantity": i.quantity, "price": i.price} for i in o.items]
        }
        for o in orders
    ]
    return jsonify(result), 200

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

