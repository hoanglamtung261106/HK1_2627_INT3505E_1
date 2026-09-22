from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

next_id = 2
STUDENTS = [{"id": 1, "name": "Tung", "gender": "male", "gpa": 3.4}]


def find_student(student_id: int):
    return next((s for s in STUDENTS if s["id"] == student_id), None)


# GET /students: Tích hợp Lọc (?q=), Sắp xếp (?sort=) và Phân trang (?limit=)
@app.route("/students", methods=["GET"])
def list_students():
    results = list(STUDENTS)

    # 1. Tìm kiếm chuỗi con trong tên (?q=...)
    q = request.args.get("q", "").strip().lower()
    if q:
        results = [s for s in results if q in s["name"].lower()]

    # 2. Sắp xếp theo GPA tăng/giảm dần (?sort=gpa hoặc ?sort=-gpa)
    sort_by = request.args.get("sort")
    if sort_by == "gpa":
        results.sort(key=lambda s: float(s["gpa"]))
    elif sort_by == "-gpa":
        results.sort(key=lambda s: float(s["gpa"]), reverse=True)

    # 3. Giới hạn số lượng bản ghi (?limit=...)
    limit = request.args.get("limit", 100, type=int)
    if limit is None or limit < 0:
        limit = 100

    return jsonify(results[:limit]), 200


# GET /students/<id>: Lấy chi tiết 1 sinh viên
@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id: int):
    student = find_student(student_id)
    if not student:
        return jsonify({"error": "not found"}), 404
    return jsonify(student), 200


# POST /students: Tạo mới có validation gpa >= 3.0
@app.route("/students", methods=["POST"])
def create_student():
    global next_id
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    gender = body.get("gender", "unknown")
    gpa_raw = body.get("gpa")

    if not name or gpa_raw is None:
        return jsonify({"error": "Cần cung cấp đủ 'name' và 'gpa'"}), 400

    try:
        gpa = float(gpa_raw)
        if gpa < 3.0:
            return jsonify({"error": "gpa phải >= 3.0"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "gpa phải là một số hợp lệ"}), 400

    student = {
        "id": next_id,
        "name": str(name).strip(),
        "gender": str(gender).strip(),
        "gpa": gpa,
    }
    next_id += 1
    STUDENTS.append(student)
    return jsonify(student), 201, {"Location": f"/students/{student['id']}"}


# PUT & DELETE /students/<id>: Cập nhật hoặc Xóa
@app.route("/students/<int:student_id>", methods=["PUT", "DELETE"])
def modify_student(student_id: int):
    student = find_student(student_id)
    if not student:
        return jsonify({"error": "not found"}), 404

    # Cập nhật thông tin (PUT)
    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        name = body.get("name")
        gender = body.get("gender")
        gpa_raw = body.get("gpa")

        if not name or not gender or gpa_raw is None:
            return (
                jsonify(
                    {"error": "Thiếu các trường bắt buộc (name, gender, gpa)"}
                ),
                400,
            )

        try:
            gpa = float(gpa_raw)
            if gpa < 3.0:
                return jsonify({"error": "gpa phải >= 3.0"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "gpa phải là một số hợp lệ"}), 400

        student["name"] = str(name).strip()
        student["gender"] = str(gender).strip()
        student["gpa"] = gpa
        return jsonify(student), 200

    # Xóa bản ghi (DELETE)
    STUDENTS.remove(student)
    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)