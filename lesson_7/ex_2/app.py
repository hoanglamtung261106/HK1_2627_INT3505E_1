from flask import Flask, Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///orders.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ==============================================================================
# 1. MODELS: Product, Order và OrderItem (liên kết Order và Product)
# ==============================================================================
class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    qty_in_stock = db.Column(db.Integer, default=10)

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="pending")
    # 1 Order có nhiều OrderItem (tránh gán 1 Product duy nhất cho Order)
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)

    product = db.relationship("Product")

# ==============================================================================
# 2. BLUEPRINT RIÊNG: /api/v1/orders
# ==============================================================================
orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")

# Lấy danh sách đơn hàng kèm chi tiết các OrderItem
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

# Tạo đơn hàng mới gồm nhiều sản phẩm thông qua OrderItem
@orders_bp.post("")
def create_order():
    data = request.get_json() or {}
    items_data = data.get("items", [])

    if not items_data:
        return jsonify({"error": "Đơn hàng phải có ít nhất 1 sản phẩm"}), 400

    order = Order(status="pending")
    db.session.add(order)

    for item in items_data:
        p_id = item.get("product_id")
        qty = item.get("quantity", 1)

        product = db.session.get(Product, p_id)
        if not product:
            db.session.rollback()
            return jsonify({"error": f"Sản phẩm ID {p_id} không tồn tại"}), 404

        if product.qty_in_stock < qty:
            db.session.rollback()
            return jsonify({"error": f"Sản phẩm '{product.name}' chỉ còn {product.qty_in_stock} trong kho"}), 409

        # Trừ tồn kho và tạo OrderItem liên kết
        product.qty_in_stock -= qty
        order_item = OrderItem(
            order=order,
            product=product,
            quantity=qty,
            unit_price=product.price
        )
        db.session.add(order_item)

    db.session.commit()
    return jsonify({"message": "Tạo đơn hàng thành công", "order_id": order.id}), 201

# Đăng ký blueprint vào Flask app
app.register_blueprint(orders_bp)

# ==============================================================================
# 3. KHỞI TẠO VÀ CHẠY
# ==============================================================================
with app.app_context():
    db.create_all()
    # Thêm sản phẩm mẫu nếu database trống để tiện test
    if not Product.query.first():
        db.session.add_all([
            Product(name="But bi", price=5000, qty_in_stock=50),
            Product(name="Vo ke ngang", price=10000, qty_in_stock=20),
            Product(name="Thuoc ke", price=3000, qty_in_stock=10)
        ])
        db.session.commit()

if __name__ == "__main__":
    print("\nAPI Orders đang chạy tại: http://127.0.0.1:5000/api/v1/orders\n")
    app.run(debug=True, port=5000)

