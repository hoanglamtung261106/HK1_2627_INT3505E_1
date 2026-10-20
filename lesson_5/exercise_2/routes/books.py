from flask import Blueprint, request, jsonify
from models import Book, Category
from pagination import (
    parse_multi_sort,
    encode_cursor,
    decode_cursor,
    extract_field_value,
    build_cursor_filter,
)

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

@bp.route("", methods=["GET"])
@bp.route("/", methods=["GET"])
def get_books():
    # 1. Parse sorting
    raw_sort = request.args.get("sort")
    order_clauses, sort_fields, err = parse_multi_sort(raw_sort)
    if err:
        return jsonify({"error": "bad_sort", "message": err}), 400

    effective_sort = raw_sort if raw_sort else "-id"

    # 2. Base query & filters
    query = Book.query

    genre = request.args.get("genre")
    if genre:
        query = query.join(Book.category).filter(Category.slug == genre)

    # 3. Strategy and limit
    strategy = request.args.get("strategy")
    raw_cursor = request.args.get("cursor")
    if not strategy:
        strategy = "cursor" if raw_cursor else "offset"

    try:
        limit = int(request.args.get("limit", 20))
    except ValueError:
        return jsonify({"error": "bad_request", "message": "limit must be an integer"}), 400

    if strategy == "offset":
        try:
            offset = int(request.args.get("offset", 0))
        except ValueError:
            return jsonify({"error": "bad_request", "message": "offset must be an integer"}), 400

        total = query.count()
        books = query.order_by(*order_clauses).offset(offset).limit(limit).all()
        has_more = (offset + limit) < total

        return jsonify({
            "data": [b.to_dict() for b in books],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": has_more
            }
        }), 200

    elif strategy == "cursor":
        if raw_cursor:
            try:
                cursor_data = decode_cursor(raw_cursor)
            except Exception:
                return jsonify({"error": "invalid_cursor", "message": "Malformed cursor"}), 400

            # Verify that sort order hasn't changed
            if cursor_data.get("sort") and cursor_data.get("sort") != effective_sort:
                return jsonify({"error": "sort_changed", "message": "Sort parameter changed"}), 400

            last_values = cursor_data.get("last_values")
            if last_values:
                filter_cond = build_cursor_filter(sort_fields, last_values)
                query = query.filter(filter_cond)

        # Keyset pagination: query limit + 1 to check if there is a next page
        books = query.order_by(*order_clauses).limit(limit + 1).all()
        has_more = len(books) > limit
        page_books = books[:limit]

        next_cursor = None
        if has_more and page_books:
            last_book = page_books[-1]
            last_values = [extract_field_value(last_book, f[0]) for f in sort_fields]
            next_cursor = encode_cursor({
                "sort": effective_sort,
                "last_values": last_values
            })

        return jsonify({
            "data": [b.to_dict() for b in page_books],
            "page_info": {
                "has_more": has_more,
                "next_cursor": next_cursor
            }
        }), 200

    else:
        return jsonify({"error": "bad_request", "message": f"Unsupported strategy '{strategy}'"}), 400