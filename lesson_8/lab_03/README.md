# Lab 3 — Build Newman-runnable Collection

## 1. Mục tiêu
Tổ chức test suite tự động bằng **Postman Collection** và chạy trực tiếp từ dòng lệnh (CLI) bằng công cụ **Newman** để tích hợp CI/CD mà không cần mở giao diện Postman.

---

## 2. Cấu trúc Collection (`books-api.postman_collection.json`)

Collection được tổ chức theo cấu trúc 3 cấp chuẩn: **Collection $\rightarrow$ Folder $\rightarrow$ Request**.

### Folder 1: `books/` (5 Happy-path Requests)
1. `GET /books — initial list`: Xác nhận status `200 OK` và response body là một mảng `array`.
2. `POST /books — create`: Tạo sách mới với payload hợp lệ, kiểm tra status `201 Created`, `id > 0`. Đồng thời lưu `book_id` vào `collectionVariables`:
   ```javascript
   if (pm.response.code === 201) {
       pm.collectionVariables.set("book_id", pm.response.json().id);
   }
   ```
3. `GET /books/{id} — read`: Đọc chi tiết sách vừa tạo qua `{{base_url}}/books/{{book_id}}`, xác nhận `200 OK` và đủ 5 trường: `id`, `title`, `author`, `year`, `isbn`.
4. `PUT /books/{id} — replace`: Cập nhật toàn bộ thông tin sách, xác nhận `200 OK` và `title` được đổi.
5. `DELETE /books/{id} — delete`: Xóa sách với id trong biến `book_id`, xác nhận `204 No Content` và body rỗng.

### Folder 2: `error-cases/` (2 Error-path Requests)
1. `POST /books (missing title)`:
   - Gửi payload chỉ có `author` (thiếu `title` bắt buộc).
   - Test 1 (Status code): `400 Bad Request`.
   - Test 2 (Body): `code == "VALIDATION_ERROR"` và trong danh sách lỗi `errors` có chứa trường `"title"`.
2. `GET /books/9999 (missing id)`:
   - Gửi request đến ID không tồn tại.
   - Test 1 (Status code): `404 Not Found`.
   - Test 2 (Body): `code == "NOT_FOUND"`.

---

## 3. Cách chạy kiểm thử với Newman

### Bước 1: Khởi động Flask Books API
Mở một terminal và chạy API:
```bash
python -m app --port 5000
```

### Bước 2: Chạy Newman từ terminal
Tại thư mục `lesson_8/lab_03`:
```bash
# Cài đặt Newman (nếu chưa cài)
npm install -g newman

# Chạy collection với environment và xuất báo cáo JUnit XML
newman run books-api.postman_collection.json \
  -e local.postman_environment.json \
  -r cli,junit \
  --reporter-junit-export reports/junit.xml
```
*Hoặc trên Windows PowerShell, chạy script có sẵn:*
```powershell
.\run_newman.ps1
```

### Kết quả đầu ra:
- Toàn bộ 7 request (5 happy path + 2 error cases) đều `PASS`.
- File báo cáo kết quả được lưu tại [reports/junit.xml](file:///d:/cac_mon_hoc/SOA/practice/lesson_8/lab_03/reports/junit.xml).
