# Lesson 8 — API Testing & Quality Assurance

Thư mục bài thực hành Buổi 8 môn SOA (Kiểm thử API và Đảm bảo Chất lượng).

> Xem tổng hợp ảnh minh chứng & báo cáo tại: [minh_chung.md](minh_chung.md)

---

## Cấu trúc thư mục

```text
lesson_8/
├── SOA - B8 - API_Testing.pdf         # Slide bài giảng và đề bài thực hành
├── app.py                             # Flask Books API server
├── models.py                          # SQLAlchemy models
├── requirements.txt                   # Danh sách thư viện Python
│
├── lab_02/                            # Lab 2: Lint OpenAPI bằng Spectral
│   ├── openapi.yaml                   # File OpenAPI 3.0 đã sửa 3 lỗi cố ý
│   ├── .spectral.yml                  # Ruleset Spectral và Custom Rule
│   ├── README.md                      # Hướng dẫn & câu trả lời lý thuyết
│   └── reports/
│       └── spectral_output.log        # Log kết quả kiểm tra Spectral
│
├── lab_03/                            # Lab 3: Build Newman-runnable Collection
│   ├── books-api.postman_collection.json  # 5 Happy-paths + Folder error-cases (7 tests)
│   ├── local.postman_environment.json     # Môi trường chạy localhost:5000
│   ├── run_newman.ps1                 # Script chạy nhanh Newman trên PowerShell
│   ├── README.md                      # Hướng dẫn chạy và giải thích test script
│   └── reports/
│       └── junit.xml                  # Báo cáo kết quả kiểm thử dạng JUnit XML
│
└── lab_04/                            # Lab 4: Load test Books API với Locust
    ├── locustfile.py                  # Script kiểm thử tải có search_by_year (1% fail)
    ├── locustfile_realistic.py        # Kịch bản mô phỏng user journey
    ├── analysis.md                    # Báo cáo phân tích số liệu p95, RPS và SLO
    ├── README.md                      # Hướng dẫn chạy 3 kịch bản
    └── reports/
        ├── A.html                     # Báo cáo kịch bản A (Baseline 10 users)
        ├── B.html                     # Báo cáo kịch bản B (Load test 50 users)
        └── C.html                     # Báo cáo kịch bản C (Spike test 200 users)
```

---

## Tóm tắt nội dung các Lab

### 1. Lab 2 — Lint OpenAPI bằng Spectral (`lab_02/`)
- Sửa 3 lỗi trong [lab_02/openapi.yaml](file:///d:/cac_mon_hoc/SOA/practice/lesson_8/lab_02/openapi.yaml):
  1. Thêm `operationId: listBooks` cho `GET /books`.
  2. Bỏ khai báo body thừa ở response HTTP 204 của `DELETE /books/{id}`.
  3. Sửa kiểu dữ liệu trường `Book.year` từ `string` thành `integer`.
- Tạo file quy tắc [lab_02/.spectral.yml](file:///d:/cac_mon_hoc/SOA/practice/lesson_8/lab_02/.spectral.yml) kèm Custom Rule bắt response 200 không được để schema rỗng.
- Giải thích chi tiết câu hỏi về Contract Testing và code mẫu `pytest` + `jsonschema`.

### 2. Lab 3 — Postman & Newman Automation (`lab_03/`)
- Bổ sung folder `error-cases/` gồm `POST /books (missing title)` và `GET /books/9999 (missing id)`.
- Mỗi request có $\ge 2$ `pm.test` kiểm tra status code và body code/message.
- Quản lý truyền trạng thái `book_id` bằng biến `collectionVariables`.
- Xuất báo cáo chuẩn JUnit XML tại [lab_03/reports/junit.xml](file:///d:/cac_mon_hoc/SOA/practice/lesson_8/lab_03/reports/junit.xml).

### 3. Lab 4 — Locust Load Testing (`lab_04/`)
- Bổ sung task `search_by_year` có 1% fail rate giả lập lỗi 500.
- Đo tải qua 3 kịch bản:
  - **Kịch bản A (Baseline)**: 10 users, 2 users/s, 30s.
  - **Kịch bản B (Load test)**: 50 users, 5 users/s, 60s.
  - **Kịch bản C (Spike test)**: 200 users, 50 users/s, 30s.
- Báo cáo phân tích chuyên sâu tại [lab_04/analysis.md](file:///d:/cac_mon_hoc/SOA/practice/lesson_8/lab_04/analysis.md) giải thích hiện tượng tail latency (p95), nghẽn SQLite lock và hiện tượng Connection Pool exhaustion.
