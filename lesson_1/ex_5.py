from flask import Flask, jsonify

# Khởi tạo
app = Flask(__name__)

ORDERS = {
    "1": {"item": "Bàn phím cơ", "status": "pending"},
    "2": {"item": "Chuột không dây", "status": "shipped"},
    "3": {"item": "Màn hình 24 inch", "status": "delivered"}
}
# DELETE /orders/<order_id>
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)

    # 404 — không tìm thấy
    if order is None:
        return {"error": "not found"}, 404
    
    # 409 — business rule
    if order["status"] in ("shipped", "delivered"):
        return {"error":"cannot delete"}, 409
    
    ORDERS.pop(order_id, None)
    # 204 — success, no body
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)