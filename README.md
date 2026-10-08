# Hệ Thống Web App Quản Lý Xưởng Gỗ Phúc Thịnh

Hệ thống phần mềm quản lý toàn diện dành cho xưởng sản xuất và gia công nội thất gỗ, được xây dựng theo kiến trúc hiện đại, tinh gọn và tối ưu trải nghiệm người dùng.

---

## 🛠️ Công Nghệ Sử Dụng

- **Backend:** Python 3.11+ / Python 3.14, FastAPI, SQLAlchemy ORM, Uvicorn
- **Cơ sở dữ liệu:** SQLite (file `wood_factory.db`)
- **Frontend:** Jinja2 Templates + Tailwind CSS (CDN) + HTMX + Chart.js, chuẩn responsive, định dạng tiền tệ VNĐ (`1.250.000 đ`) và ngày tháng (`dd/mm/yyyy`)
- **Môi trường & Đóng gói:** Nix Flakes (`flake.nix`, `flake.lock`) tái lập 100% môi trường dev
- **Báo cáo & Xuất file:** `openpyxl` (Xuất Excel tồn kho, sổ quỹ)
- **Kiểm thử tự động:** `pytest`, `httpx` (Coverage luồng Auth, Kho, Đơn hàng, Lệnh sản xuất)

---

## 📦 Cấu Trúc Dự Án

```
xuong-go/
├── flake.nix                       # Khai báo môi trường Nix Flake
├── flake.lock                      # Khóa phiên bản gói phụ thuộc của Nix
├── requirements.txt                # Danh sách thư viện Python
├── run.sh                          # Script khởi chạy ứng dụng 1 chạm
├── pytest.ini                      # Cấu hình kiểm thử tự động
├── wood_factory.db                 # Database SQLite chính
├── tests/                          # Bộ kiểm thử pytest
│   ├── conftest.py
│   ├── test_auth.py                # Test đăng nhập, hash bcrypt
│   ├── test_inventory.py           # Test nhập/xuất kho, biến động tồn
│   ├── test_orders.py              # Test đơn hàng, cọc, công nợ
│   └── test_production.py          # Test BOM, LSX, 6 công đoạn
├── app/
│   ├── config.py                   # Cấu hình đường dẫn, khóa bảo mật, xưởng
│   ├── database.py                 # Khởi tạo kết nối SQLite & Session
│   ├── init_db.py                  # Script khởi tạo DB & nạp dữ liệu mẫu
│   ├── utils.py                    # Format VNĐ, dd/mm/yyyy, bcrypt
│   ├── main.py                     # Entrypoint FastAPI, routes, middleware
│   ├── models/                     # Các bảng SQLAlchemy
│   │   ├── user.py                 # Users & phân quyền
│   │   ├── inventory.py            # Nguyên vật liệu, NCC, PNK, PXK, Thẻ kho
│   │   ├── sales.py                # Thành phẩm, BOM, Khách hàng, Đơn hàng
│   │   ├── production.py           # Lệnh sản xuất, 6 công đoạn, Thợ, Chấm công
│   │   └── finance.py              # Sổ quỹ, Phiếu thu, Phiếu chi
│   ├── services/                   # Logic nghiệp vụ
│   │   ├── auth_service.py         # Xác thực & phân quyền
│   │   ├── inventory_service.py    # Xử lý kho & đối soát tồn
│   │   ├── production_service.py   # Tính toán BOM, trừ kho, tính lương
│   │   ├── finance_service.py      # Dòng tiền, công nợ & báo cáo tài chính
│   │   └── excel_service.py        # Xuất báo cáo Excel
│   ├── routes/                     # Các endpoints API & Web UI
│   ├── static/                     # CSS, JS, ảnh upload sản phẩm
│   └── templates/                  # Giao diện Jinja2 + Tailwind CSS
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Ứng Dụng

### Cách 1: Sử dụng Nix Flakes (Khuyên Dùng)

Dự án đã có sẵn `flake.nix` và `flake.lock`. Chỉ cần chạy:

1. **Khởi chạy môi trường và app nhanh:**
   ```bash
   ./run.sh
   ```

2. **Hoặc tự vào môi trường dev:**
   ```bash
   nix develop
   # Khởi tạo database nếu chưa có:
   python3 -m app.init_db
   # Chạy dev server:
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Chạy kiểm thử pytest:**
   ```bash
   nix develop --command pytest -v
   ```

---

### Cách 2: Sử dụng Python Virtualenv truyền thống

1. **Tạo môi trường ảo:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Khởi tạo dữ liệu mẫu ban đầu:**
   ```bash
   python3 -m app.init_db
   ```

4. **Chạy server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

Truy cập trình duyệt: **http://localhost:8000** (Tự động chuyển về Dashboard)

---

## 🔑 Tài Khoản Mặc Định

Hệ thống đã phân quyền sẵn 4 vai trò chính:

| Tên đăng nhập | Mật khẩu | Họ tên | Vai trò | Quyền hạn |
|---|---|---|---|---|
| **admin** | `admin123` | Quản Trị Viên | **Admin** | Toàn quyền cấu hình, tài khoản, backup |
| **kho** | `kho123` | Nguyễn Văn Kho | **Quản lý kho** | Quản lý vật tư, NCC, lập PNK, PXK |
| **quandoc** | `quandoc123` | Trần Văn Quản Đốc | **Quản đốc** | Quản lý sản xuất, gán công đoạn, chấm công |
| **ketoan** | `ketoan123` | Lê Thị Kế Toán | **Kế toán** | Thu chi sổ quỹ, tính lương, báo cáo tài chính |

---

## 📌 Các Tính Năng Đã Hoàn Thành Theo Các Phase

### Phase 1: Nền tảng & Đăng nhập
- Kết nối SQLite đa luồng an toàn.
- Phân quyền RBAC (Role-Based Access Control) cho 4 nhóm người dùng.
- Mã hóa mật khẩu an toàn với thư viện `bcrypt`.
- Trang quản trị tài khoản: thêm user, đổi vai trò, khóa/kích hoạt và đổi mật khẩu.

### Phase 2: Kho & Nhà cung cấp
- Danh mục nguyên vật liệu: Gỗ tự nhiên (Sồi, Gõ đỏ, Xoan đào...), Gỗ công nghiệp (MDF, HDF...), Phụ kiện (Bản lề, ray bi), Vật tư phụ (Sơn PU, keo Titebond, ốc vít).
- Quản lý nhà cung cấp và theo dõi công nợ đối tác.
- Lập **Phiếu Nhập Kho (PNK)** đa dòng linh hoạt: tự động cộng dồn kho, cập nhật giá vốn bình quân và ghi sổ quỹ.
- Lập **Phiếu Xuất Kho (PXK)**: kiểm tra đủ tồn kho, trừ kho an toàn.
- **Thẻ kho (Lịch sử giao dịch)** ghi nhận thời gian thực biến động tồn.
- Cảnh báo mặt hàng sắp hết khi tồn $\le$ mức tồn tối thiểu.
- Xuất danh sách tồn kho ra file **Excel (.xlsx)**.

### Phase 3: Sản phẩm, Khách hàng & Đơn hàng
- Danh mục sản phẩm thành phẩm (Bàn ăn, Giường ngủ, Tủ áo, Kệ tivi...) kèm ảnh tải lên.
- **Cấu hình Định mức nguyên liệu (BOM - Bill of Materials)** chi tiết cho từng sản phẩm.
- Hồ sơ khách hàng và theo dõi công nợ phải thu.
- Tạo đơn hàng nhiều sản phẩm, tính chiết khấu, tiền đặt cọc và còn lại.
- **Trang in Báo giá / Hóa đơn chuyên nghiệp**: chuẩn in ấn A4 `@media print` có logo xưởng, bảng chi tiết và chữ ký hai bên.

### Phase 4: Sản xuất & Nhân công
- Mở **Lệnh sản xuất (LSX)** từ đơn hàng bán hoặc sản xuất dự trữ kho.
- Tự động tính toán lượng nguyên liệu cần dùng theo định mức BOM $\times$ số lượng.
- Nút **Xuất kho NVL theo BOM**: tự động kiểm tra đủ tồn và xuất vật tư cho phân xưởng.
- Quản lý quy trình **6 công đoạn sản xuất tiêu chuẩn**:
  `Pha phôi` &rarr; `Gia công` &rarr; `Lắp ráp` &rarr; `Chà nhám` &rarr; `Sơn PU` &rarr; `Đóng gói`.
- Phân công thợ mộc phụ trách từng công đoạn, ghi chú KCS kiểm tra chất lượng.
- Tự động đồng bộ trạng thái đơn hàng sang *Hoàn thiện* khi tất cả công đoạn hoàn tất.
- Quản lý thợ mộc, chấm công hàng ngày (1 công, nửa công, nghỉ, tăng ca).
- Tạm ứng lương thợ (tự sinh phiếu chi sổ quỹ).
- **Bảng lương tháng**: tự động tính ngày công, tăng ca $\times 1.5$, trừ tiền tạm ứng ra thực lĩnh, có nút chi trả lương lập phiếu chi.

### Phase 5: Tài chính & Báo cáo
- Sổ quỹ tiền mặt và tài khoản ngân hàng thời gian thực (Thu / Chi / Tồn quỹ).
- Tự động sinh phiếu thu khi khách cọc hoặc thanh toán đơn hàng.
- Tự động sinh phiếu chi khi mua vật tư hoặc trả lương thợ.
- Báo cáo tài chính tổng hợp: Doanh thu, Chi phí, Lợi nhuận ước tính, Giá trị kho hàng, Công nợ khách hàng & NCC.
- Xuất Sổ quỹ ra file **Excel (.xlsx)**.

### Phase 6: Dashboard & Hoàn thiện
- Bàn làm việc thông minh: 4 thẻ KPI, biểu đồ doanh thu 12 tháng bằng **Chart.js**, danh sách đơn sắp hẹn giao, cảnh báo vật tư sắp hết.
- **Sao lưu & Khôi phục Database**: Tạo file backup `.db`, tải về máy và khôi phục an toàn.
- Bộ test tự động `pytest` chạy thông qua 100%.
