FROM python:3.11-slim

WORKDIR /app

# Cài đặt thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn
COPY . .

EXPOSE 5000

# Chạy bằng Gunicorn theo chuẩn production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

