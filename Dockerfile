# Sử dụng Python 3.11 slim tối ưu dung lượng và tốc độ
FROM python:3.11-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Biến môi trường tối ưu cho Python trong Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Cài đặt gói curl và sqlite3
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt các thư viện Python từ requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn ứng dụng vào container
COPY . .

# Phân quyền thực thi cho entrypoint script
RUN chmod +x docker-entrypoint.sh

# Cổng truy cập của ứng dụng
EXPOSE 8000

# Kiểm tra trạng thái hoạt động (Healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/login || exit 1

# Khởi động ứng dụng thông qua entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]
