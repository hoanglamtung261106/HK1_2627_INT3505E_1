from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///health.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ==============================================================================
# BÀI TẬP 4: HEALTH CHECK PROBES (LIVENESS vs READINESS - KHÔNG GỘP CHUNG)
# ==============================================================================

# 1. /healthz (Liveness Probe - "Tôi còn sống không?")
# Siêu nhẹ, KHÔNG phụ thuộc Database hay service ngoài.
# Trả về 200 nếu server còn phản hồi. Orchestrator (K8s/Docker) dùng để quyết định có restart pod không.
@app.get("/healthz")
def liveness():
    return jsonify({
        "status": "ok",
        "type": "liveness",
        "message": "Service process is alive"
    }), 200


# 2. /ready (Readiness Probe - "Tôi nhận traffic được chưa?")
# Kiểm tra các dependency thiết yếu (Database, Cache...).
# Trả về 200 nếu sẵn sàng nhận request, hoặc 503 nếu dependency lỗi (để tạm ngưng định tuyến traffic).
@app.get("/ready")
def readiness():
    checks = {}
    try:
        # Kiểm tra truy vấn nhẹ tới Database
        db.session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    is_ready = all(v == "ok" for v in checks.values())
    status_code = 200 if is_ready else 503

    return jsonify({
        "status": "ok" if is_ready else "degraded",
        "type": "readiness",
        "checks": checks
    }), status_code


# Route trang chủ demo
@app.get("/")
def home():
    return jsonify({
        "message": "Lesson 7 - Exercise 4 (Health Check Probes)",
        "endpoints": {
            "liveness": "/healthz",
            "readiness": "/ready"
        }
    }), 200


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    print("\n[EX_4] Healthcheck server đang chạy tại:")
    print(" - Trang chủ        : http://127.0.0.1:5000/")
    print(" - Liveness probe   : http://127.0.0.1:5000/healthz")
    print(" - Readiness probe  : http://127.0.0.1:5000/ready\n")
    app.run(debug=True, port=5000)

