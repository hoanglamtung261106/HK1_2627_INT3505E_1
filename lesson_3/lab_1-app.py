from flask import Flask, request, jsonify

app = Flask(__name__)

# Giả lập database trong bộ nhớ
posts_db = {
    1: {"id": 1, "title": "Giới thiệu REST API", "body": "Nội dung bài 1", "author_id": 10, "tags": ["soa", "api"]},
    2: {"id": 2, "title": "HTTP Semantics", "body": "Nội dung bài 2", "author_id": 11, "tags": ["http", "web"]}
}
current_id = 2

# 1. GET /api/v1/posts: Lấy danh sách bài viết (hỗ trợ filtering)
@app.get("/api/v1/posts")
def get_posts():
    tag_filter = request.args.get("tag")
    author_filter = request.args.get("author_id", type=int)

    results = list(posts_db.values())

    if tag_filter:
        results = [p for p in results if tag_filter in p["tags"]]
    if author_filter:
        results = [p for p in results if p["author_id"] == author_filter]

    return jsonify({"data": results, "total": len(results)}), 200


# 2. POST /api/v1/posts: Tạo mới một bài viết
@app.post("/api/v1/posts")
def create_post():
    data = request.get_json()

    # Kiểm tra payload cơ bản
    if not data or "title" not in data or "body" not in data:
        return jsonify({
            "type": "https://api.example.com/probs/bad-request",
            "title": "Invalid Payload",
            "detail": "Thiếu trường 'title' hoặc 'body'."
        }), 400

    global current_id
    current_id += 1
    new_post = {
        "id": current_id,
        "title": data["title"],
        "body": data["body"],
        "author_id": data.get("author_id", 1),
        "tags": data.get("tags", [])
    }
    posts_db[current_id] = new_post

    # Chuẩn REST: Trả 201 Created kèm header Location
    response = jsonify(new_post)
    response.status_code = 201
    response.headers["Location"] = f"/api/v1/posts/{current_id}"
    return response


# 3. GET /api/v1/posts/{id}: Xem chi tiết 1 bài viết
@app.get("/api/v1/posts/<int:post_id>")
def get_post_detail(post_id):
    post = posts_db.get(post_id)
    if not post:
        return jsonify({
            "type": "https://api.example.com/probs/not-found",
            "title": "Post Not Found",
            "detail": f"Không tìm thấy bài viết có id = {post_id}"
        }), 404
    return jsonify(post), 200


# 4. PATCH /api/v1/posts/{id}: Cập nhật một phần
@app.patch("/api/v1/posts/<int:post_id>")
def update_post(post_id):
    post = posts_db.get(post_id)
    if not post:
        return jsonify({"title": "Post Not Found"}), 404

    data = request.get_json() or {}
    if "title" in data:
        post["title"] = data["title"]
    if "body" in data:
        post["body"] = data["body"]
    if "tags" in data:
        post["tags"] = data["tags"]

    return jsonify(post), 200


# 5. DELETE /api/v1/posts/{id}: Xóa bài viết
@app.delete("/api/v1/posts/<int:post_id>")
def delete_post(post_id):
    if post_id in posts_db:
        del posts_db[post_id]
    # Idempotent: Dù có hay không, kết quả cuối cùng đều là bài viết không còn tồn tại -> 204
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)