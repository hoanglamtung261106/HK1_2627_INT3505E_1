from flask import Flask, jsonify, request

app = Flask("__name__")
BOOKS = []
next_id = 1

def find_by_id(book_id: int):
    return next((book for book in BOOKS if book["id"] == book_id), None)

# GET /books
@app.route("/books", methods=["GET"])
def list_books():
    return jsonify({"data": BOOKS, "length": len(BOOKS)}), 200

# GET /book/<book_id> - lấy 1 sách
@app.route("/books/<book_id>", methods=['GET'])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

# POST /books (create)
@app.route("/books", methods=["POST"])
def create_book():
    global next_id
    if not request.is_json:
        return jsonify(error="expected JSON"), 415

    book = request.get_json(silent=True) or {}
    title = (book.get("title") or "").strip()
    author = (book.get("author") or "").strip()  

    if not title or not author:
        return jsonify(error="title and author required"), 422

    new_book = {"id": next_id, "title": title, "author": author}
    BOOKS.append(new_book)
    next_id += 1
    return jsonify(new_book), 201, {"Location": f"/books/{new_book['id']}"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)


