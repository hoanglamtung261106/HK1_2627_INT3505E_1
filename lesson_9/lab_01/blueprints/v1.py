from flask import Blueprint
from .users_data import get_user

# Lưu ý: register_blueprint(v1_bp, url_prefix="/api/v1") ghi đè url_prefix của Blueprint,
# nên route đặt "/users/<int:uid>" để gọi đúng /api/v1/users/<id> như ví dụ trên slide.
bp = Blueprint("v1", __name__)


@bp.route("/users/<int:uid>")
def get(uid):
    u = get_user(uid)
    if not u:
        return {"error": "nf"}, 404
    return {
        "id": uid,
        "full_name": f"{u['f']} {u['l']}",
        "email": u["email"],
    }
