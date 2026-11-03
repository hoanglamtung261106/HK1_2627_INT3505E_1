# src/product_api/api/products.py
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.product import Product
from ..errors import Conflict, NotFound
from ..schemas import ProductOut, ProductIn, ProductPatch, ReserveIn

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")

# 1. GET danh sách (có phân trang & lọc soft-delete)
@products_bp.get("")
def list_products():
    page = max(1, int(request.args.get("page", 1)))
    size = min(100, max(1, int(request.args.get("size", 20))))
    
    base = db.select(Product).where(Product.archived.is_(False))
    rows = db.session.execute(
        base.order_by(Product.id).offset((page - 1) * size).limit(size)
    ).scalars().all()
    
    total = db.session.scalar(
        db.select(db.func.count()).select_from(Product).where(Product.archived.is_(False))
    )
    
    return jsonify({
        "items": ProductOut(many=True).dump(rows),
        "page": page,
        "size": size,
        "total": total
    }), 200

# 2. GET chi tiết 1 sản phẩm (sinh viên tự thêm)
@products_bp.get("/<int:id>")
def get_product(id):
    p = db.session.execute(
        db.select(Product).where(Product.id == id, Product.archived.is_(False))
    ).scalar_one_or_none()
    if not p:
        raise NotFound(message="Product not found")
    return ProductOut().dump(p), 200

# 3. POST tạo sản phẩm
@products_bp.post("")
def create_product():
    body = ProductIn().load(request.get_json() or {})
    p = Product(**body)
    db.session.add(p)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict(message="sku already exists")
    return ProductOut().dump(p), 201

# 4. POST đặt trước sản phẩm / reserve (sinh viên tự thêm)
@products_bp.post("/<int:id>/reserve")
def reserve_product(id):
    body = ReserveIn().load(request.get_json() or {})
    qty = body["qty"]
    
    p = db.session.execute(
        db.select(Product).where(Product.id == id, Product.archived.is_(False))
    ).scalar_one_or_none()
    if not p:
        raise NotFound(message="Product not found")
        
    if p.qty_in_stock < qty:
        raise Conflict(message=f"Only {p.qty_in_stock} items left in stock")
        
    p.qty_in_stock -= qty
    db.session.commit()
    return ProductOut().dump(p), 200

# 5. PATCH cập nhật một phần
@products_bp.patch("/<int:id>")
def patch_product(id):
    body = ProductPatch().load(request.get_json() or {}, partial=True)
    p = db.session.execute(
        db.select(Product).where(Product.id == id, Product.archived.is_(False))
    ).scalar_one_or_none()
    if not p:
        raise NotFound(message="Product not found")
        
    for k, v in body.items():
        setattr(p, k, v)
        
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict(message="sku already exists")
        
    return ProductOut().dump(p), 200

# 6. DELETE xóa mềm
@products_bp.delete("/<int:id>")
def delete_product(id):
    p = db.session.execute(
        db.select(Product).where(Product.id == id, Product.archived.is_(False))
    ).scalar_one_or_none()
    if not p:
        raise NotFound(message="Product not found")
        
    p.archived = True
    db.session.commit()
    return "", 204