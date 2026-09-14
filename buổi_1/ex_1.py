from flask import Flask

# Khởi tạo instance ứng dụng Flask
app = Flask(__name__)

# Đăng ký định tuyến (routing) cho endpoint /
@app.route('/', methods=['GET'])
def index():
    return {"Tên": "Hoàng Lâm Tùng", "DOB": "26/11/2006"}, 200

# Phần main, chạy chương trình
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
