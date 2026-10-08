#!/usr/bin/env bash
set -e

# Tự động nạp dữ liệu mẫu nếu chưa có file database
if [ ! -f "wood_factory.db" ]; then
    echo "📦 Chưa tìm thấy cơ sở dữ liệu, đang khởi tạo bảng và dữ liệu mẫu..."
    python -m app.init_db
fi

echo "🚀 Khởi chạy Web App Quản Lý Xưởng Gỗ tại cổng ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
