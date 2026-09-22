from flask import Flask, jsonify, make_response, request

app = Flask(__name__)
BOOKS = []

# ─── GET /books/<id> ─── cache 60s
@app.get("/books/<int:book_id>")
def fetch(book_id):
    i = next((k for k,b in enumerate(BOOKS) if b["id"]==book_id), None)
    if i is None: return jsonify(error="not found"), 404
    resp = make_response(jsonify(BOOKS[i]), 200)
    resp.headers["Cache-Control"]="max-age=60"
    return resp

# ─── PUT ─── thay toàn bộ, title+author bắt buộc
@app.put("/books/<int:book_id>")
def put(book_id):
    i = next((k for k,b in enumerate(BOOKS) if b["id"]==book_id), None)
    if i is None: 
        return jsonify(error="not found"), 404
    p = request.get_json(silent=True) or {}
    t, a = p.get("title"), p.get("author")

    if not isinstance(t, str) or not isinstance(a, str) or not t.strip() or not a.strip():
        return jsonify(error="need valid title+author"), 422
    
    BOOKS[i] = {"id": book_id, "title": t.strip(), "author": a.strip(),
                "isbn": p.get("isbn"), "price": p.get("price")}
    
    return jsonify(BOOKS[i]), 200

# ─── PATCH ─── chỉ cập nhật field có trong body
@app.patch("/books/<int:book_id>")
def patch(book_id):
    i = next((k for k,b in enumerate(BOOKS) if b["id"]==book_id), None)
    if i is None: return jsonify(error="not found"), 404
    p = request.get_json(silent=True) or {}
    if p.get("price", 0) < 0:
        return jsonify(error="price must be positive"), 422
    
    for k in " title author isbn price".split():
        if k in p: BOOKS[i][k] = p[k]
    return jsonify(BOOKS[i]), 200

# ─── DELETE ─── idempotent, trả 204
@app.delete("/books/<int:book_id>")
def delete(book_id):
    i = next((k for k,b in enumerate(BOOKS)
    if b["id"]==book_id), None)
    if i is None: return jsonify(error="not found"), 404
    BOOKS.pop(i); return"", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)