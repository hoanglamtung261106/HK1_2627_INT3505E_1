from flask import Flask, jsonify, request
app = Flask(__name__)

next_id = 2
STUDENTS = [{"id":1, "name": "Tung", "gpa": "3.4"}]

def find(student_id):
    return next((student for student in STUDENTS if student["id"] == student_id), None)

# LIST — GET /STUDENTS
@app.route("/students", methods=["GET"])
def list_books():
    n = int(request.args.get("limit", 100))
    return jsonify(STUDENTS[:n]), 200

# DETAIL — GET /students/<int:student_id>
@app.route("/students/<int:student_id>", methods=["GET"])
def get_book(student_id):
    student = find(student_id)
    if not student: 
        return {"error":"not found"}, 404
    return jsonify(student), 200

# CREATE — POST /students
@app.route("/students", methods=["POST"])
def create_book():
    global next_id
    body = request.get_json(silent=True) or {}
    name, gpa = body.get("name"), body.get("gpa")
    if not name or not gpa:
        return {"error":"need name and gpa"}, 400
    student = {"id": next_id, "name": name, "gpa": gpa}
    next_id += 1
    STUDENTS.append(student)
    return jsonify(student), 201, {"Location":f"/STUDENTS/{student['id']}"}

# UPDATE — PUT, DELETE — DELETE (xem bên phải)
@app.route("/students/<int:student_id>", methods=["PUT", "DELETE"])
def modify_book(student_id):
    student = find(student_id)
    if not student: return {"error":"not found"}, 404

    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        name = body.get("name")
        gpa = body.get("gpa")
        student["name"] = str(name)
        student["gpa"] = float(gpa)
        return jsonify(student), 200

    STUDENTS.remove(student)
    return"", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)