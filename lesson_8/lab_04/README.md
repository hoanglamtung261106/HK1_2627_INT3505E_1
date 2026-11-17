# Lab 4 — Load Test Books API với Locust

## 1. Mục tiêu
Thực hành đo lường hiệu năng, quan sát các chỉ số cốt lõi (RPS, latency p50/p95/p99, error rate) bằng công cụ **Locust** qua 3 kịch bản: Baseline, Load test và Spike test.

---

## 2. Kịch bản kiểm thử tải trong `locustfile.py`

File `locustfile.py` định nghĩa các task với trọng số:
- `@task(3) list_books`: `GET /books` (weight=3)
- `@task(2) read_book`: `GET /books/{id}` (weight=2, tự động chấp nhận 404 là hợp lệ)
- `@task(1) create_book`: `POST /books` (weight=1, tạo sách với ID tăng dần)
- `@task(2) search_by_year`: `GET /books?year=[year]` (weight=2, **bổ sung theo yêu cầu Slide 30 có 1% fail rate giả lập 500**).

---

## 3. Cách chạy 3 kịch bản đo tải

### Bước 1: Khởi động API Server
```bash
python -m app --port 5000
```

### Bước 2: Chạy Locust từ terminal (headless mode)

- **Kịch bản A — Baseline (tải nhẹ: 10 user, 2 user/s, 30s):**
  ```bash
  locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u 10 -r 2 -t 30s --html reports/A.html
  ```

- **Kịch bản B — Load test thông thường (50 user, 5 user/s, 60s):**
  ```bash
  locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u 50 -r 5 -t 60s --html reports/B.html
  ```

- **Kịch bản C — Spike test (tải đột biến: 200 user, 50 user/s, 30s):**
  ```bash
  locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u 200 -r 50 -t 30s --html reports/C.html
  ```

---

## 4. Báo cáo phân tích
Xem chi tiết báo cáo và câu trả lời phân tích tại file [analysis.md](file:///d:/cac_mon_hoc/SOA/practice/lesson_8/lab_04/analysis.md):
- Bảng tổng hợp số liệu p95, RPS, error rate.
- Phân tích nguyên nhân p95 tăng cao ở kịch bản C do SQLite lock và Flask dev server.
- Phân biệt lỗi HTTP 500 thực tế và lỗi gán nhãn giả lập.
- Đánh giá SLO p95 < 300ms và đề xuất baseline cho CI Quality Gate.
- Câu hỏi bonus về hiện tượng nghẽn Connection Pool khi pool_size = 5.
