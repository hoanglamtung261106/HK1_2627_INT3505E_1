# Báo cáo thực hành Lesson 9 — API Versioning & Lifecycle (Lab 02, 03, 04)

Báo cáo tổng hợp kết quả triển khai và chạy kiểm thử 3 bài thực hành (trang 21–23 của slide `SOA - B9 - API_Versioning (1).pdf`).

---

## 1. Lab 02 — Header Versioning với decorator `@api_version`

- **Mã nguồn:** [lab_02/app.py](lab_02/app.py)
- **Cơ chế hoạt động:**
  - Dùng chung một URL `GET /users/<uid>`, client chọn phiên bản qua HTTP header `X-API-Version`.
  - Thiếu header $\rightarrow$ dùng phiên bản mặc định `LATEST = "2"`.
  - Phiên bản không thuộc `SUPPORTED = {"1", "2", "2024-06-20"}` $\rightarrow$ trả về `400 Bad Request`, không fallback.
  - Response luôn gắn header `X-API-Version-Served` để phục vụ debug và đo lượng truy cập theo version.

### Lệnh test & Kết quả chạy thực tế:

| Trường hợp test | Header gửi lên | HTTP Status | `X-API-Version-Served` | Response Body |
|---|---|---|---|---|
| Mặc định (thiếu header) | *(không có)* | `200 OK` | `2` | `{"id": 1, "first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"}` |
| Chỉ định v1 | `X-API-Version: 1` | `200 OK` | `1` | `{"id": 1, "full_name": "Văn Nguyễn"}` |
| Date-based version | `X-API-Version: 2024-06-20` | `200 OK` | `2024-06-20` | `{"id": 1, "first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"}` |
| Version không hợp lệ | `X-API-Version: 99` | `400 Bad Request` | *(không có)* | `{"error": "unsupported version"}` |

```powershell
curl.exe -i http://127.0.0.1:5000/users/1
curl.exe -i -H "X-API-Version: 1" http://127.0.0.1:5000/users/1
curl.exe -i -H "X-API-Version: 2024-06-20" http://127.0.0.1:5000/users/1
curl.exe -i -H "X-API-Version: 99" http://127.0.0.1:5000/users/1
```

---

## 2. Lab 03 — Sunset Middleware với decorator `@deprecate_at`

- **Mã nguồn:** [lab_03/sunset.py](lab_03/sunset.py), [lab_03/app.py](lab_03/app.py)
- **Cơ chế hoạt động:**
  - **Trước ngày Sunset** (`V1_SUNSET = 2026-12-31 23:59:59 UTC`): Vẫn trả `200 OK` kèm 3 header chuẩn RFC 8594 / RFC 9745 (`Sunset`, `Deprecation: true`, `Link: </api/v2/users>; rel="successor-version"`) và ghi server log `WARNING`.
  - **Từ ngày Sunset trở đi** (`V0_SUNSET = 2025-01-01 00:00:00 UTC` ở route `/api/v0/users/<id>`): Ngừng phục vụ và trả về `410 Gone` kèm `sunset` và `use_instead`.

### Kết quả chạy thực tế:

1. **Trước Sunset (`GET /api/v1/users/1`):**
   - **Status:** `200 OK`
   - **Headers:**
     - `Sunset: Thu, 31 Dec 2026 23:59:59 GMT`
     - `Deprecation: true`
     - `Link: </api/v2/users>; rel="successor-version"`
   - **Body:** `{"id": 1, "full_name": "Nguyễn Văn A"}`
   - **Server Log:** `WARNING:sunset:deprecated_call /api/v1/users/1 127.0.0.1`

2. **Sau Sunset (`GET /api/v0/users/1`):**
   - **Status:** `410 Gone`
   - **Body:** `{"error": "gone", "sunset": "Wed, 01 Jan 2025 00:00:00 GMT", "use_instead": "/api/v2/users"}`

```powershell
curl.exe -i http://127.0.0.1:5000/api/v1/users/1
curl.exe -i http://127.0.0.1:5000/api/v0/users/1
```

---

## 3. Lab 04 — Blue-Green Routing (`POST /orders`)

- **Mã nguồn:** [lab_04/handlers.py](lab_04/handlers.py), [lab_04/gateway.py](lab_04/gateway.py), [lab_04/app.py](lab_04/app.py)
- **Cơ chế hoạt động:**
  - Cùng URL `POST /orders`, gateway định tuyến theo thứ tự ưu tiên 3 tầng:
    1. Header `X-Cohort` thuộc `{"beta", "internal"}` $\rightarrow$ `v2`
    2. `account_id` thuộc allow-list `{"acct_42", "acct_99"}` $\rightarrow$ `v2`
    3. Hash MD5 xác định theo `account_id` với tỉ lệ `V2_PERCENT = 5%` $\rightarrow$ `v2`, còn lại $\rightarrow$ `v1`
  - Gắn response header `X-Order-Handler: v1 | v2` (trả `201` với `v2`, `200` với `v1`).

### Kết quả chạy thực tế:

| Case test | Điều kiện đầu vào | HTTP Status | `X-Order-Handler` | Response Body |
|---|---|---|---|---|
| 1. Cohort beta | Header `X-Cohort: beta`, `account_id: "any"` | `201 Created` | `v2` | `{"handler": "v2", "order_id": "ord_v2_001", "account_id": "any", "status": "pending_fulfillment", "items": []}` |
| 2. Allow-list account | `account_id: "acct_42"` | `201 Created` | `v2` | `{"handler": "v2", "order_id": "ord_v2_001", "account_id": "acct_42", "status": "pending_fulfillment", "items": []}` |
| 3. Tài khoản thường (`5%` bucket) | `account_id: "acct_1"` | `200 OK` | `v1` | `{"handler": "v1", "order_id": "ord_v1_001", "account_id": "acct_1", "status": "created"}` |

```powershell
curl.exe -i -X POST -H "X-Cohort: beta" -H "Content-Type: application/json" -d "{\"account_id\":\"any\"}" http://127.0.0.1:5000/orders
curl.exe -i -X POST -H "Content-Type: application/json" -d "{\"account_id\":\"acct_42\"}" http://127.0.0.1:5000/orders
curl.exe -i -X POST -H "Content-Type: application/json" -d "{\"account_id\":\"acct_1\"}" http://127.0.0.1:5000/orders
```
