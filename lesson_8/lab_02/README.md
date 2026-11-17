# Lab 2 — Lint OpenAPI bằng Spectral

## 1. Mục tiêu
Sử dụng công cụ **Stoplight Spectral** để kiểm tra tính hợp lệ và chuẩn mực của hợp đồng giao tiếp API (OpenAPI Specification 3.0), phát hiện và sửa 3 lỗi cố ý, đồng thời bổ sung custom rule.

---

## 2. 3 Lỗi cố ý và cách khắc phục trong `openapi.yaml`

| STT | Lỗi cố ý | Nguyên nhân | Cách khắc phục |
|---|---|---|---|
| **1** | `GET /books` thiếu `operationId` | Thiếu định danh thao tác làm các tool sinh client/docs không xác định được tên hàm. | Thêm `operationId: listBooks` |
| **2** | `DELETE /books/{id}` khai báo body cho response 204 | Chuẩn HTTP 204 (*No Content*) không được phép có body (`content`). | Xóa toàn bộ block `content: application/json` ở response 204. |
| **3** | `Book.year` có `type: string` | Sai kiểu dữ liệu với mô hình database (model Book lưu `year` là `Integer`). | Sửa thành `type: integer, nullable: true, minimum: 1450, maximum: 2100`. |

---

## 3. Cấu hình `.spectral.yml` & Custom Rule

File `.spectral.yml` kế thừa bộ quy tắc nền `spectral:oas` và bổ sung các rule sau:
1. `no-204-body`: Bắt lỗi response 204 khai báo body.
2. `book-year-integer`: Bắt lỗi trường `Book.year` không phải kiểu số nguyên.
3. **Custom Rule theo yêu cầu:** `response-200-has-schema-fields`:
   - **Giải thích:** Bắt trường hợp lập trình viên khai báo endpoint trả về mã `200 OK` nhưng lại định nghĩa schema rỗng (chỉ ghi `{type: object}` chung chung hoặc bỏ trống), không mô tả các trường bên trong (`properties`, `items`, hoặc `$ref`). Rule này bắt buộc phải mô tả cấu trúc trường dữ liệu để client có thể parse được.

---

## 4. Trả lời câu hỏi trong slide:
> **"Nếu spec hợp lệ Spectral-pass nhưng code Flask trả sai field — test nào bắt được? Bạn sẽ viết gì?"**

### Phân tích:
- **Tại sao Spectral không bắt được?** Spectral chỉ là công cụ **linter tĩnh (static analysis)** trên file spec `openapi.yaml`. Nó **không chạy code Flask thật**, nên nếu backend code lúc runtime trả sai trường, thiếu trường hoặc thừa trường bí mật (`password_hash`, `internal_score`) thì Spectral hoàn toàn không thể biết.
- **Loại test bắt được:** Cần viết **Contract Test / Schema Validation Test** bằng `pytest` kết hợp `jsonschema`.

### Đoạn test cụ thể:
```python
import pytest
from jsonschema import validate, ValidationError
import yaml

# Lấy schema từ openapi.yaml
with open("openapi.yaml", "r", encoding="utf-8") as f:
    spec = yaml.safe_load(f)
book_schema = spec["components"]["schemas"]["Book"]

def test_flask_response_matches_contract(client):
    # 1. Gọi endpoint Flask thực tế
    response = client.get("/books/1")
    assert response.status_code == 200
    data = response.get_json()

    # 2. Xác thực response khớp chuẩn với schema
    validate(instance=data, schema=book_schema)

    # 3. Giả lập trường hợp Flask trả sai / thừa field lạ (nhờ additionalProperties: false)
    bad_data = dict(data)
    bad_data["unknown_leak_field"] = "secret"
    with pytest.raises(ValidationError):
        validate(instance=bad_data, schema=book_schema)
```

---

## 5. Hướng dẫn chạy và Output log

**Cách 1: Dùng sẵn `spectral.exe` trong thư mục này (không cần Node.js):**
```powershell
.\spectral lint openapi.yaml --ruleset .spectral.yml
```

**Cách 2: Cài qua Node.js / npm (yêu cầu Node.js >= 18):**
```bash
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml --ruleset .spectral.yml
```

Xem chi tiết output log nộp bài tại: `reports/spectral_output.log` (`No results with a severity of 'error' found!`).
