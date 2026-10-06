import uuid
from flask import jsonify, request

ERROR_BASE_URL = "https://api.example.com/probs"

class ApiProblem(Exception):
    """Custom exception dùng cho các lỗi nghiệp vụ trong API."""
    def __init__(self, status, title, detail=None, type_path=None, **extra):
        super().__init__(title)
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.extra = extra

def make_problem_response(status, title, detail=None, type_path=None, **extra):
    """Hàm tạo response chuẩn application/problem+json theo RFC 7807."""
    body = {
        "type": f"{ERROR_BASE_URL}/{type_path}" if type_path else "about:blank",
        "title": title,
        "status": status,
        "instance": request.path,
        "trace_id": str(uuid.uuid4())
    }
    if detail:
        body["detail"] = detail
    
    # Bổ sung các metadata mở rộng (ví dụ: resource_id, invalid_fields)
    body.update(extra)

    response = jsonify(body)
    response.status_code = status
    response.headers["Content-Type"] = "application/problem+json"
    return response