# Minh chứng thực hành Lesson 9 — Lab 01: URI Path Versioning với Flask Blueprint

## 1. Cấu trúc triển khai
- [app.py](app.py): Khởi tạo Flask app, cấu hình `app.json.ensure_ascii = False` (hiển thị tiếng Việt UTF-8) và đăng ký 2 Blueprint với `url_prefix="/api/v1"` và `url_prefix="/api/v2"`.
- [blueprints/v1.py](blueprints/v1.py): Endpoint `GET /api/v1/users/<id>` trả về schema v1 (`full_name`).
- [blueprints/v2.py](blueprints/v2.py): Endpoint `GET /api/v2/users/<id>` trả về schema v2 (`first_name`, `last_name` — breaking change).
- [blueprints/users_data.py](blueprints/users_data.py): Nguồn dữ liệu mẫu `USERS` dùng chung.

---

## 2. Kết quả kiểm thử

### Ảnh minh chứng chạy thực tế:
![Minh chứng Lab 01](minh%20chứng%20lab_01.jpg)
