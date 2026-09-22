from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False

next_id = 2
STUDENTS = [{"id": 1, "name": "Tung", "gender": "male", "gpa": 3.4}]


def find_student(student_id: int):
    return next((s for s in STUDENTS if s["id"] == student_id), None)


# LIST — GET /students
@app.route("/students", methods=["GET"])
def list_students():
    n = request.args.get("limit", 100, type=int)
    if n is None or n < 0:
        n = 100
    return jsonify(STUDENTS[:n]), 200


# DETAIL — GET /students/<int:student_id>
@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id: int):
    student = find_student(student_id)
    if not student:
        return jsonify({"error": "not found"}), 404
    return jsonify(student), 200


# CREATE — POST /students
@app.route("/students", methods=["POST"])
def create_student():
    global next_id
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    gender = body.get("gender", "unknown")
    gpa_raw = body.get("gpa")

    if not name or gpa_raw is None:
        return jsonify({"error": "need name and gpa"}), 400

    try:
        gpa = float(gpa_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "gpa must be a number"}), 400

    student = {
        "id": next_id,
        "name": str(name).strip(),
        "gender": str(gender).strip(),
        "gpa": gpa,
    }
    next_id += 1
    STUDENTS.append(student)
    return jsonify(student), 201, {"Location": f"/students/{student['id']}"}


# UPDATE — PUT, DELETE — DELETE
@app.route("/students/<int:student_id>", methods=["PUT", "DELETE"])
def modify_student(student_id: int):
    student = find_student(student_id)
    if not student:
        return jsonify({"error": "not found"}), 404

    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        name = body.get("name")
        gender = body.get("gender", student.get("gender", "unknown"))
        gpa_raw = body.get("gpa")

        if not name or gpa_raw is None:
            return jsonify({"error": "need name and gpa"}), 400

        try:
            student["gpa"] = float(gpa_raw)
        except (ValueError, TypeError):
            return jsonify({"error": "gpa must be a number"}), 400

        student["name"] = str(name).strip()
        student["gender"] = str(gender).strip()
        return jsonify(student), 200

    STUDENTS.remove(student)
    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)