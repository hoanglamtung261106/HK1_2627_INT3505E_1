"""Lab 4: Locust load test for Books API with weighted tasks and simulated 1% failure.

Chạy thử kịch bản:
- Kịch bản A: locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u 10 -r 2 -t 30s --html reports/A.html
- Kịch bản B: locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u 50 -r 5 -t 60s --html reports/B.html
- Kịch bản C: locust -f locustfile.py --headless -H http://127.0.0.1:5000 -u 200 -r 50 -t 30s --html reports/C.html
"""
import itertools
import random
from locust import HttpUser, between, task

_counter = itertools.count(1)


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_books(self):
        """Lấy danh sách sách (thao tác đọc phổ biến nhất, weight=3)."""
        self.client.get("/books", name="GET /books")

    @task(2)
    def read_book(self):
        """Đọc chi tiết một sách ngẫu nhiên (weight=2)."""
        book_id = random.randint(1, 50)
        with self.client.get(
            f"/books/{book_id}", name="GET /books/{id}", catch_response=True
        ) as response:
            # 404 là hành vi hợp lệ khi ID không tồn tại trong DB mẫu, không tính là lỗi server sập
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def create_book(self):
        """Tạo sách mới với ID tăng dần tránh conflict ISBN (weight=1)."""
        unique = next(_counter)
        self.client.post(
            "/books",
            json={"title": f"Load test book {unique}", "author": "locust", "year": 2021},
            name="POST /books",
        )

    @task(2)
    def search_by_year(self):
        """Tìm kiếm sách theo năm xuất bản có 1% fail rate giả lập lỗi 500 (weight=2)."""
        year = random.choice([2017, 2020, 2021, 2022, 2025])
        with self.client.get(
            f"/books?year={year}", name="GET /books?year=[year]", catch_response=True
        ) as response:
            if response.status_code == 200:
                # Giả lập 1% failure rate theo yêu cầu đề bài
                if random.random() < 0.01:
                    response.failure("Simulated 1% client-side failure (artificial 500 error)")
                else:
                    response.success()
            else:
                response.failure(f"Server returned status {response.status_code}")
