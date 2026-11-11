"""Shared fixtures for all exercises; each test receives a fresh SQLite database."""
import sys
from pathlib import Path

# Thêm đường dẫn tới thư mục lab08-starter vào sys.path để import app và models
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lab08-starter"))

import pytest
from app import create_app  # type: ignore
from models import Book, db  # type: ignore


@pytest.fixture()
def app(tmp_path):
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
    })
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_book(app):
    with app.app_context():
        book = Book(title="API Design Patterns", author="J.J. Geewax", year=2021)
        db.session.add(book)
        db.session.commit()
        return book.id
