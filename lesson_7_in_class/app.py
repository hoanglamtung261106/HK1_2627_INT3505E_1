from flask import Flask
from flask.views import MethodView
from flask_smorest import Api, Blueprint
from marshmallow import Schema, fields

app = Flask(__name__)

# Cấu hình tối thiểu để Swagger UI hiển thị
app.config["API_TITLE"] = "Demo Code-First API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)
blp = Blueprint("products", __name__, url_prefix="/products")

# 1. Schema: Vừa validate dữ liệu, vừa tự động sinh tài liệu Swagger
class ProductSchema(Schema):
    id = fields.Int(dump_only=True)      # Chỉ xuất ra (GET/POST response)
    name = fields.Str(required=True)     # Bắt buộc có khi gửi POST
    price = fields.Float(required=True)

# 2. Database giả lập trong RAM
products = [
    {"id": 1, "name": "But bi", "price": 5000.0},
    {"id": 2, "name": "Vo ke ngang", "price": 10000.0}
]

# 3. Định nghĩa API Endpoints
@blp.route("")
class ProductList(MethodView):
    @blp.response(200, ProductSchema(many=True))
    def get(self):
        """Lấy danh sách tất cả sản phẩm"""
        return products

    @blp.arguments(ProductSchema)
    @blp.response(201, ProductSchema)
    def post(self, data):
        """Thêm sản phẩm mới"""
        data["id"] = len(products) + 1
        products.append(data)
        return data

api.register_blueprint(blp)

if __name__ == "__main__":
    print("Mở Swagger UI tại: http://127.0.0.1:5000/swagger-ui")
    app.run(debug=True)
