# Lab 4 — Phân tích kết quả Load Test với Locust

## 1. Bảng số liệu đo thực tế (Localhost: Flask Dev Server + SQLite)

| Kịch bản | Users | Spawn rate | Duration | Tổng Reqs | p50 (ms) | p95 (ms) | Failure rate | RPS |
|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| **A (Baseline)** | 10 | 2/s | 30s | 130 | 13 ms | **380 ms** | 0.00% (0/130) | 4.61 |
| **B (Load test)** | 50 | 5/s | 60s | 1,364 | 13 ms | **48 ms** | 0.07% (1/1,364) | 23.32 |
| **C (Spike test)** | 200 | 50/s | 30s | 2,733 | 28 ms | **210 ms** | 0.18% (5/2,733) | 96.08 |

### Chi tiết theo từng Endpoint:
- **Kịch bản A (10u, 30s):** `GET /books` (p95=400ms, max=617ms), `GET /books/{id}` (p95=58ms), `GET /books?year=[year]` (p95=26ms), `POST /books` (p95=560ms, 16 reqs).
- **Kịch bản B (50u, 60s):** `GET /books` (p95=38ms), `GET /books/{id}` (p95=34ms), `GET /books?year=[year]` (p95=37ms, 1 fail), `POST /books` (p95=61ms).
- **Kịch bản C (200u, 30s):** `GET /books` (p95=240ms), `GET /books/{id}` (p95=190ms), `GET /books?year=[year]` (p95=200ms, 5 fails), `POST /books` (p95=260ms, max=539ms).

---

## 2. Trả lời các câu hỏi phân tích

### Câu 1: Trong 3 kịch bản, kịch bản nào có p95 cao nhất? Vì sao?
- **Theo số liệu đo thực tế:** **Kịch bản A có p95 cao nhất (380 ms)**, dù chỉ chạy 10 users — cao hơn cả Kịch bản C (**210 ms**) và Kịch bản B (**48 ms**).
- **Giải thích dựa trên số liệu quan sát:**
  1. **Nhiễu do cỡ mẫu nhỏ (Small Sample Size) ở Kịch bản A:** Kịch bản A chỉ phát sinh tổng cộng `130` requests (`POST /books` chỉ có 16 requests, `GET /books` có 53 requests). Ở những giây đầu tiên khi kết nối DB/CPU vừa khởi động, có vài request outlier chậm (`563 ms` ở POST, `617 ms` ở GET). Vì 5% của 130 chỉ tương ứng ~6-7 requests, vài outlier đầu tiên đã kéo p95 vọt lên `380 ms`, dù trung vị (`p50`) vẫn rất nhanh là `13 ms`.
  2. **So sánh xu hướng khi tăng tải ổn định (từ B sang C, mẫu > 1.300 requests):** Khi tăng từ 50 users (B) lên 200 users ramp nhanh 50 user/s (C), hệ thống bắt đầu chịu áp lực rõ rệt: **p50 tăng hơn 2 lần (`13 ms` $\rightarrow$ `28 ms`)** và **p95 tăng hơn 4,3 lần (`48 ms` $\rightarrow$ `210 ms`)**. Đặc biệt trong 3 giây đầu ramp-up 200 users của Kịch bản C, thời gian đáp ứng trung bình vọt lên `219 ms`, và endpoint ghi `POST /books` luôn có p95 cao nhất (`260 ms`) do khóa ghi SQLite.

---

### Câu 2: Endpoint nào tăng failure rate? Phân biệt lỗi HTTP thực và lỗi đánh dấu trong Locust.
- **Endpoint có failure rate tăng:** `GET /books?year=[year]` tăng từ **0.00%** (A: 0/24) $\rightarrow$ **0.31%** (B: 1/318) $\rightarrow$ **0.73%** (C: 5/689).
- **Phân biệt bản chất lỗi:**
  1. **Lỗi đánh dấu nhân tạo phía client (Locust `response.failure()`):** Toàn bộ `1` lỗi ở Kịch bản B và `5` lỗi ở Kịch bản C đều có thông báo `Simulated 1% client-side failure (artificial 500 error)`. Thực tế server Flask vẫn trả về **HTTP 200**, nhưng code Locust chủ động đánh dấu fail với xác suất 1%. Khi số request tăng (24 $\rightarrow$ 318 $\rightarrow$ 689), số lỗi quan sát được tăng lên và tiệm cận tỷ lệ kỳ vọng 1%.
  2. **Lỗi HTTP thực tế từ server:** Tất cả các endpoint còn lại (`GET /books`, `GET /books/{id}`, `POST /books`) đều có **0.00% failure** — không có lỗi HTTP 500 thực tế nào phát sinh từ Flask/SQLite trong các lần chạy này. *(Lưu ý: `GET /books/{id}` có trả 404 với ID chưa tồn tại nhưng đã được `catch_response=True` đánh dấu `response.success()` vì đây là hành vi nghiệp vụ đúng).*

---

### Câu 3: Với SLO giả định p95 < 300 ms, kịch bản nào đạt? Đề xuất baseline & nêu giới hạn phép đo.
- **Đánh giá theo SLO `p95 < 300 ms`:**
  - **Kịch bản B (p95 = 48 ms)** và **Kịch bản C (p95 = 210 ms)**: **Đạt** trên môi trường đo cục bộ.
  - **Kịch bản A (p95 = 380 ms)**: **Không đạt** do bị nhiễu bởi cỡ mẫu nhỏ và cold-start outlier (dù p50 chỉ 13 ms).
- **Đề xuất baseline cho CI gate:**
  - Cần đủ thời gian/số lượng request để p95 ổn định (tương đương **Kịch bản B: 50 users, 60s**, thu > 1.000 requests).
  - Ngưỡng CI gate đề xuất: `p95 < 250 ms` và `actual server error rate (5xx) = 0%` (tách biệt với các lỗi giả lập test).
- **Giới hạn của phép đo:**
  - Chạy trên `127.0.0.1` (localhost) nên bỏ qua hoàn toàn độ trễ mạng (network latency, TLS handshake).
  - Dùng Flask development server (Werkzeug) + SQLite chạy cùng máy với Locust (hai tiến trình cạnh tranh CPU/RAM), và bảng `books` dung lượng nhỏ nên **không thể khẳng định hiệu năng production** từ kết quả này.

---

### Câu 4 (Bonus): Nếu connection pool bị giới hạn ở 5, điều gì xảy ra khi 200 user truy cập đồng thời? Làm thế nào để xác nhận bằng Locust?
- **Điều gì xảy ra:**
  - Khi 200 user cùng truy cập mà database connection pool chỉ cho phép tối đa 5 kết nối (`pool_size=5, max_overflow=0`), tối đa chỉ có 5 request giữ kết nối DB cùng lúc.
  - 195 user còn lại phải đứng chờ trong hàng đợi (`pool_timeout`), làm **latency p95/p99 tăng vọt** lên bằng thời gian chờ timeout.
  - Khi thời gian chờ vượt quá `pool_timeout`, SQLAlchemy ném ngoại lệ `sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 0 reached`, khiến server trả về hàng loạt **HTTP 500** thật và failure rate tăng đột biến.
- **Cách xác nhận bằng Locust:**
  1. Cấu hình giới hạn pool trong `app.py` (khi dùng DB hỗ trợ QueuePool như PostgreSQL/MySQL hoặc cấu hình `SQLALCHEMY_ENGINE_OPTIONS = {"pool_size": 5, "max_overflow": 0, "pool_timeout": 3}`).
  2. Chạy Locust kịch bản spike 200 users:
     ```bash
     locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u 200 -r 50 -t 30s --html reports/pool_limit.html
     ```
  3. Quan sát bảng **Errors/Failures** và biểu đồ **Response Time** trong `pool_limit.html`: sẽ thấy `p95` nhảy vọt sát mức `pool_timeout` (3.000+ ms) kèm hàng loạt lỗi HTTP 500 thực tế từ server (khác hẳn với lỗi giả lập của `search_by_year`).
