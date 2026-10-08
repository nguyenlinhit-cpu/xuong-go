#!/usr/bin/env bash
set -e

# Đảm bảo database đã được khởi tạo
if [ ! -f "wood_factory.db" ]; then
    echo "📦 Khởi tạo cơ sở dữ liệu mẫu..."
    nix develop --command python3 -m app.init_db
fi

echo "🚀 Đang khởi động Web App Quản Lý Xưởng Gỗ tại http://localhost:8000 ..."
nix develop --command uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
