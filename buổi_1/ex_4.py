from flask import Flask, jsonify

# Khởi tạo instance ứng dụng Flask
app = Flask(__name__)

# Hiện thị đúng ký tự Pháp
app.json.ensure_ascii = False

BOOKS = [
    {
        "id": "1", 
        "name": "Hands-On Machine Learning", 
        "author": "Aurélien Géron", 
        "publisher": "O'Reilly"
    }
]

#Duyệt mảng tìm sinh viên theo ID, trả về dict hoặc None
def find_by_id(book_id: str):
    for book in BOOKS:
        if book.get("id") == book_id:
            return book
    return None

# /books/<id> — id là string
@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

# Ép kiểu int ngay từ URL
@app.route("/items/<int:item_id>", methods=['GET'])
def get_item(item_id): # int sẵn
    return jsonify({"id": item_id}), 200

# Entry point
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)