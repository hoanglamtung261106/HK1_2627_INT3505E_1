import pytest
from flask import Flask
from models import db, Book, Category
from routes.books import bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        # Seed categories
        cat_tech = Category(name="Technology", slug="tech")
        cat_lit = Category(name="Literature", slug="lit")
        db.session.add_all([cat_tech, cat_lit])
        db.session.commit()

        # Seed 45 cuốn sách với giá đa dạng
        books = []
        for i in range(1, 46):
            books.append(Book(
                title=f"Book Title {i:02d}",
                isbn=f"9780000000{i:03d}",
                price_vnd=(i % 5) * 10000 + 50000,
                stock=10,
                category_id=cat_tech.id if i <= 30 else cat_lit.id
            ))
        db.session.add_all(books)
        db.session.commit()

    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_offset_pagination_success(client):
    res = client.get("/api/v1/books?strategy=offset&limit=10&offset=0")
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) == 10
    assert data["pagination"]["total"] == 45
    assert data["pagination"]["has_more"] is True

def test_cursor_pagination_walkthrough(client):
    """Kiểm tra duyệt liên tục qua cursor gom đủ 45 bản ghi, không trùng ID."""
    collected_ids = set()
    cursor = None

    while True:
        url = "/api/v1/books?strategy=cursor&limit=10"
        if cursor:
            url += f"&cursor={cursor}"
        res = client.get(url)
        assert res.status_code == 200
        payload = res.get_json()

        for item in payload["data"]:
            assert item["id"] not in collected_ids  # Chống trùng lặp
            collected_ids.add(item["id"])

        if not payload["page_info"]["has_more"]:
            break
        cursor = payload["page_info"]["next_cursor"]

    assert len(collected_ids) == 45

def test_genre_filter(client):
    res = client.get("/api/v1/books?genre=lit")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) == 15
    for item in data:
        assert item["category"]["slug"] == "lit"

def test_sort_changed_invalidates_cursor(client):
    # Lấy cursor với sort mặc định
    res = client.get("/api/v1/books?strategy=cursor&sort=-id&limit=5")
    cursor = res.get_json()["page_info"]["next_cursor"]

    # Đổi sort sang price nhưng dùng lại cursor cũ -> phải trả 400
    res_bad = client.get(f"/api/v1/books?strategy=cursor&sort=price&cursor={cursor}")
    assert res_bad.status_code == 400
    assert res_bad.get_json()["error"] == "sort_changed"

def test_bad_sort_column(client):
    res = client.get("/api/v1/books?sort=password,drop_table")
    assert res.status_code == 400
    assert res.get_json()["error"] == "bad_sort"