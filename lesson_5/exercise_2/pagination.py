import base64
import json
from datetime import datetime
from sqlalchemy import desc, asc, tuple_, and_, or_
from models import Book

# Whitelist các trường cho phép sắp xếp và ánh xạ tới ORM column
SORT_MAP = {
    "id": Book.id,
    "price": Book.price_vnd,
    "title": Book.title,
    "created_at": Book.created_at
}

def parse_multi_sort(raw_sort: str):
    """
    Parse chuỗi dạng: "-price,title"
    Trả về:
      - order_clauses: danh sách mệnh đề sắp xếp trong order_by()
      - sort_fields: danh sách tuple (tên_thuộc_tính, cột_orm, is_desc)
    """
    if not raw_sort:
        raw_sort = "-id"

    order_clauses = []
    sort_fields = []
    has_id = False

    for part in raw_sort.split(","):
        part = part.strip()
        if not part:
            continue

        is_desc = part.startswith("-")
        field_name = part.lstrip("-")

        if field_name not in SORT_MAP:
            return None, None, f"Trường sắp xếp không hợp lệ: '{field_name}'"

        col = SORT_MAP[field_name]
        order_clauses.append(desc(col) if is_desc else asc(col))
        sort_fields.append((field_name, col, is_desc))

        if field_name == "id":
            has_id = True

    # Tie-breaker: Luôn thêm id ở cuối nếu chưa có để đảm bảo thứ tự xác định
    if not has_id:
        order_clauses.append(desc(Book.id) if sort_fields[0][2] else asc(Book.id))
        sort_fields.append(("id", Book.id, sort_fields[0][2]))

    return order_clauses, sort_fields, None

def encode_cursor(payload: dict) -> str:
    """Mã hóa dictionary chứa state thành chuỗi URL-safe Base64 không padding."""
    dumped = json.dumps(payload, separators=(',', ':'))
    return base64.urlsafe_b64encode(dumped.encode()).decode().rstrip("=")

def decode_cursor(token: str) -> dict:
    """Giải mã token Base64 với xử lý tự động bù padding '='."""
    pad = "=" * (-len(token) % 4)
    return json.loads(base64.urlsafe_b64decode(token + pad))

def extract_field_value(book_instance, field_name: str):
    """Lấy giá trị thực tế của thực thể để nhúng vào cursor state."""
    if field_name == "price":
        return book_instance.price_vnd
    val = getattr(book_instance, field_name)
    if isinstance(val, datetime):
        return val.isoformat()
    return val

def build_cursor_filter(sort_fields, last_values):
    """
    Tạo biểu thức điều kiện lọc SQLAlchemy cho Keyset pagination đa trường sắp xếp.
    """
    conditions = []
    for i in range(len(sort_fields)):
        match_preceding = []
        for j in range(i):
            _, prev_col, _ = sort_fields[j]
            prev_val = last_values[j]
            if sort_fields[j][0] == "created_at" and isinstance(prev_val, str):
                prev_val = datetime.fromisoformat(prev_val)
            match_preceding.append(prev_col == prev_val)

        field_name, curr_col, is_desc = sort_fields[i]
        curr_val = last_values[i]
        if field_name == "created_at" and isinstance(curr_val, str):
            curr_val = datetime.fromisoformat(curr_val)

        op = curr_col < curr_val if is_desc else curr_col > curr_val

        if match_preceding:
            conditions.append(and_(*match_preceding, op))
        else:
            conditions.append(op)

    if len(conditions) == 1:
        return conditions[0]
    return or_(*conditions)