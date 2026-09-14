import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False  # Hỗ trợ in tiếng Việt chuẩn UTF-8

# Bộ nhớ tạm (In-memory database) để lưu trữ danh sách sinh viên
STUDENTS = []

@app.route("/students", methods=["POST"])
def create_student():
    # 1. Đọc an toàn payload từ client
    data = request.get_json(silent=True) or {}

    # 2. Kiểm tra dữ liệu đầu vào (Validation)
    name = data.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        # Thiếu trường bắt buộc -> Báo lỗi 400 Bad Request
        return jsonify({"error": "Trường 'name' là bắt buộc và không được để trống"}), 400

    # 3. Tạo ID ngẫu nhiên 128-bit và đóng gói đối tượng
    student_id = str(uuid.uuid4())
    new_student = {
        "id": student_id,
        "name": name.strip()
    }
    STUDENTS.append(new_student)

    # 4. Trả về tuple 3 phần tử: (Body, 201 Created, Response Headers)
    headers = {"Location": f"/students/{student_id}"}
    return jsonify(new_student), 201, headers

# Entry point
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)