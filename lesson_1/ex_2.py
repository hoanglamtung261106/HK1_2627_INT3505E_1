from flask import Flask, request, jsonify

# Khởi tạo 1 đối tượng ứng dụng Flask
app = Flask(__name__)

# GET /health - Kiểm tra server còn sống hay không
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

# POST /echo - Trả cái client gửi
@app.route("/echo", methods=["POST"])
def echo():
    data = request.get_json(silent=True) or {}
    return jsonify({"you_sent": data}), 200

# Phần main, chạy chương trình
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

