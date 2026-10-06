import logging
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from errors import ApiProblem, make_problem_response


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.json.ensure_ascii = False

# Giả lập database
USERS_DB = {
    1: {"id": 1, "name": "Alice", "role": "admin"},
    2: {"id": 2, "name": "Bob", "role": "member"}
}

# 1. ĐĂNG KÝ CÁC ERROR HANDLER TẬP TRUNG

@app.errorhandler(ApiProblem)
def handle_api_problem(e):
    """Bắt các lỗi nghiệp vụ do lập trình viên chủ động raise."""
    return make_problem_response(
        status=e.status,
        title=e.title,
        detail=e.detail,
        type_path=e.type_path,
        **e.extra
    )

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Bắt fallback các lỗi HTTP mặc định của Werkzeug/Flask (404 route, 405...)."""
    return make_problem_response(
        status=e.code,
        title=e.name,
        detail=e.description,
        type_path=e.name.lower().replace(" ", "-")
    )

@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    """Bắt fallback lỗi hệ thống chưa kiểm soát: log nội bộ và giấu stack trace."""
    app.logger.error("Internal Server Error: %s", str(e), exc_info=True)
    return make_problem_response(
        status=500,
        title="Internal Server Error",
        detail="Đã xảy ra lỗi ngoài ý muốn. Vui lòng thử lại sau.",
        type_path="internal-server-error"
    )

# 2. CÁC ROUTES KIỂM THỬ

@app.get("/users/<int:id>")
def get_user(id):
    user = USERS_DB.get(id)
    if not user:
        # Ném lỗi 404 có cấu trúc
        raise ApiProblem(
            status=404,
            title="User Not Found",
            detail=f"Không tìm thấy người dùng với ID={id}",
            type_path="user-not-found",
            resource_id=id
        )
    return jsonify(user)

@app.get("/crash")
def simulate_crash():
    # Thử nghiệm lỗi 500 không bắt trước đó (ví dụ: chia cho 0)
    return 1 / 0

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)