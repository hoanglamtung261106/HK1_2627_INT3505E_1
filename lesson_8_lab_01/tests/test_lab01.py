"""LAB 1 — 4 tests cơ bản theo yêu cầu."""


def test_get_books_empty_db(client):
    """A. GET /books khi CSDL rỗng trả về mảng rỗng [] (không phải null)"""
    response = client.get("/books")
    assert response.status_code == 200
    assert response.get_json() == []


def test_get_book_not_found(client):
    """B. GET /books/<id> với id không tồn tại trả về 404 + JSON chứa "code": "NOT_FOUND" """
    response = client.get("/books/9999")
    assert response.status_code == 404
    data = response.get_json()
    assert data.get("code") == "NOT_FOUND"


def test_post_book_missing_title(client):
    """C. POST /books thiếu title trả về 400 + trong errors có field "title" """
    response = client.post("/books", json={"author": "Nguyen Van A"})
    assert response.status_code == 400
    data = response.get_json()
    error_fields = [err["field"] for err in data.get("errors", [])]
    assert "title" in error_fields


def test_delete_then_get_same_id(client):
    """D. Xoá rồi GET cùng id — phải trả về 404"""
    # Tạo sách hợp lệ
    create_res = client.post(
        "/books", json={"title": "Clean Code", "author": "Robert C. Martin"}
    )
    assert create_res.status_code == 201
    book_id = create_res.get_json()["id"]

    # Xoá sách
    delete_res = client.delete(f"/books/{book_id}")
    assert delete_res.status_code == 204

    # GET lại cùng id
    get_res = client.get(f"/books/{book_id}")
    assert get_res.status_code == 404
