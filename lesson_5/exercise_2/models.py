from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)

    books = db.relationship("Book", back_populates="category", lazy="select")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug
        }

class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    price_vnd = db.Column(db.Integer, nullable=False, default=0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

    category = db.relationship("Category", back_populates="books")

    def to_dict(self):
        dt = self.created_at or datetime.now(timezone.utc).replace(tzinfo=None)
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "price": {
                "amount": self.price_vnd,
                "currency": "VND"
            },
            "stock": self.stock,
            "category": self.category.to_dict() if self.category else None,
            "createdAt": dt.isoformat() + "Z"
        }