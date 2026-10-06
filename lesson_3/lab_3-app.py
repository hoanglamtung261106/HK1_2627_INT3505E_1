import base64
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
app.json.ensure_ascii = False


# Giả lập Database gồm 10 đơn hàng
ORDERS_DB = [
    {"id": 1, "customer_id": 101, "status": "paid", "total": 150.0, "created_at": "2026-01-01T10:00:00Z"},
    {"id": 2, "customer_id": 102, "status": "pending", "total": 85.0, "created_at": "2026-01-02T11:00:00Z"},
    {"id": 3, "customer_id": 101, "status": "paid", "total": 220.0, "created_at": "2026-01-03T09:30:00Z"},
    {"id": 4, "customer_id": 103, "status": "cancelled", "total": 45.0, "created_at": "2026-01-04T15:00:00Z"},
    {"id": 5, "customer_id": 104, "status": "paid", "total": 310.0, "created_at": "2026-01-05T08:15:00Z"},
    {"id": 6, "customer_id": 102, "status": "paid", "total": 95.0, "created_at": "2026-01-06T12:00:00Z"},
    {"id": 7, "customer_id": 105, "status": "pending", "total": 120.0, "created_at": "2026-01-07T14:20:00Z"},
    {"id": 8, "customer_id": 101, "status": "paid", "total": 500.0, "created_at": "2026-01-08T16:45:00Z"},
    {"id": 9, "customer_id": 103, "status": "paid", "total": 60.0, "created_at": "2026-01-09T18:10:00Z"},
    {"id": 10, "customer_id": 104, "status": "cancelled", "total": 75.0, "created_at": "2026-01-10T11:05:00Z"},
]

def encode_cursor(data: dict) -> str:
    """Mã hóa thông tin mốc tiếp theo thành chuỗi opaque cursor (Base64)."""
    json_bytes = json.dumps(data).encode("utf-8")
    return base64.urlsafe_b64encode(json_bytes).decode("utf-8")

def decode_cursor(cursor_str: str) -> dict:
    """Giải mã cursor. Nếu lỗi định dạng hoặc hỏng chuỗi thì ném ValueError."""
    try:
        json_bytes = base64.urlsafe_b64decode(cursor_str.encode("utf-8"))
        return json.loads(json_bytes.decode("utf-8"))
    except Exception as e:
        raise ValueError("Cursor không hợp lệ hoặc bị hỏng") from e

def bad_request_problem(detail: str):
    """Phản hồi lỗi 400 theo cấu trúc RFC 7807."""
    response = jsonify({
        "type": "https://api.example.com/probs/bad-request",
        "title": "Bad Request",
        "status": 400,
        "detail": detail,
        "instance": request.path
    })
    response.status_code = 400
    response.headers["Content-Type"] = "application/problem+json"
    return response

@app.get("/orders")
def get_orders():
    # 1. PARSE VÀ KIỂM TRA THAM SỐ PHÂN TRANG (PAGINATION)
    try:
        limit = min(int(request.args.get("limit", 5)), 100)  # Mặc định 5, trần tối đa 100
        if limit <= 0:
            return bad_request_problem("Tham số limit phải là số nguyên dương lớn hơn 0.")
    except ValueError:
        return bad_request_problem("Tham số limit phải là một số nguyên.")

    last_id = None
    raw_cursor = request.args.get("cursor")
    if raw_cursor:
        try:
            cursor_data = decode_cursor(raw_cursor)
            last_id = cursor_data.get("id")
            if last_id is None:
                return bad_request_problem("Cursor thiếu trường định danh id.")
        except ValueError as err:
            return bad_request_problem(str(err))  # Trả về 400 nếu cursor hỏng

    # 2. FILTERING
    status_filter = request.args.get("status")
    customer_id_filter = request.args.get("customer_id")

    items = ORDERS_DB
    if status_filter:
        items = [o for o in items if o["status"].lower() == status_filter.lower()]
    if customer_id_filter:
        try:
            cid = int(customer_id_filter)
            items = [o for o in items if o["customer_id"] == cid]
        except ValueError:
            return bad_request_problem("Tham số customer_id phải là số nguyên.")

    # 3. SORTING
    sort_param = request.args.get("sort", "id")
    reverse = False
    if sort_param.startswith("-"):
        reverse = True
        sort_key = sort_param[1:]
    else:
        sort_key = sort_param

    if items and sort_key in items[0]:
        items = sorted(items, key=lambda x: x[sort_key], reverse=reverse)

    # ÁP DỤNG CURSOR (KEYSET FILTERING)
    if last_id is not None:
        # Lấy các phần tử nằm sau ID của cursor
        if reverse:
            items = [o for o in items if o["id"] < last_id]
        else:
            items = [o for o in items if o["id"] > last_id]

    # Cắt danh sách theo limit (+1 để kiểm tra còn trang sau không)
    has_more = len(items) > limit
    page_data = items[:limit]

    # Tính next_cursor nếu còn dữ liệu
    next_cursor = None
    if has_more and page_data:
        next_cursor = encode_cursor({"id": page_data[-1]["id"]})

    # 4. SPARSE FIELDSETS
    fields_param = request.args.get("fields")
    if fields_param:
        requested_fields = [f.strip() for f in fields_param.split(",") if f.strip()]
        filtered_page_data = []
        for item in page_data:
            filtered_item = {k: item[k] for k in requested_fields if k in item}
            filtered_page_data.append(filtered_item)
        page_data = filtered_page_data

    # Response chuẩn hóa
    return jsonify({
        "data": page_data,
        "pagination": {
            "limit": limit,
            "has_more": has_more,
            "next_cursor": next_cursor
        }
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)