import os
from flask import Flask, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Đọc URL database từ biến môi trường (mặc định dùng SQLite nếu chạy local)
db_url = os.environ.get("DATABASE_URL", "sqlite:///app.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ==============================================================================
# 1. MODELS: Product, Order và OrderItem
# ==============================================================================
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty_in_stock = db.Column(db.Integer, default=10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    product = db.relationship("Product")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# ==============================================================================
# 2. BLUEPRINT: /api/v1/orders
# ==============================================================================
orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")

@orders_bp.get("")
def get_orders():
    orders = Order.query.all()
    result = []
    for o in orders:
        result.append({
            "order_id": o.id,
            "status": o.status,
            "items": [
                {
                    "product_id": item.product_id,
                    "product_name": item.product.name if item.product else None,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total": item.quantity * item.unit_price
                }
                for item in o.items
            ]
        })
    return jsonify(result), 200

@orders_bp.post("")
def create_order():
    data = request.get_json() or {}
    items_data = data.get("items", [])
    if not items_data:
        return jsonify({"error": "Đơn hàng phải có ít nhất 1 sản phẩm"}), 400

    order = Order()
    order.status = "pending"
    db.session.add(order)

    for item in items_data:
        product = db.session.get(Product, item.get("product_id"))
        if not product:
            db.session.rollback()
            return jsonify({"error": f"Sản phẩm ID {item.get('product_id')} không tồn tại"}), 404

        qty = item.get("quantity", 1)
        if product.qty_in_stock < qty:
            db.session.rollback()
            return jsonify({"error": f"Sản phẩm '{product.name}' không đủ số lượng"}), 409

        product.qty_in_stock -= qty
        db.session.add(OrderItem(order=order, product=product, quantity=qty, unit_price=product.price))

    db.session.commit()
    return jsonify({"message": "Tạo đơn hàng thành công", "order_id": order.id}), 201

app.register_blueprint(orders_bp)

# Trang chủ kiểm tra nhanh trên trình duyệt
@app.get("/")
def home():
    return jsonify({
        "message": "Service dang chay thanh cong!",
        "endpoints": {
            "orders": "/api/v1/orders",
            "healthz": "/healthz"
        }
    }), 200

# Healthcheck probe (Chuẩn 12-factor & Docker)
@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

# ==============================================================================
# 3. KHỞI TẠO VÀ CHẠY
# ==============================================================================
with app.app_context():
    db.create_all()
    if not Product.query.first():
        db.session.add_all([
            Product(name="Bút bi", price=5000, qty_in_stock=50),
            Product(name="Vở kẻ ngang", price=10000, qty_in_stock=20),
            Product(name="Thước kẻ", price=3000, qty_in_stock=10)
        ])
        db.session.commit()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

