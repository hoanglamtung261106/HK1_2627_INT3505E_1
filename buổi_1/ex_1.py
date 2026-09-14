from flask import Flask

#Khai báo 1 đối tượng
app = Flask(__name__)

#Decorator của hàm index
@app.route('/', methods=['GET'])
def index():
    return {"Tên": "Hoàng Lâm Tùng", "DOB": "26/11/2006"}, 200

#Phần main, chạy chương trình
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
