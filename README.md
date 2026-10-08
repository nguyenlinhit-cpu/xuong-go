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

### Cách 3: Chạy Bằng Docker Trên Windows (Khuyên Dùng Nếu Không Cài Python)

Chỉ cần cài đặt Docker Desktop, toàn bộ môi trường và dữ liệu sẽ chạy độc lập trong container mà không làm ảnh hưởng đến hệ điều hành Windows của bạn.

---

#### 1. Yêu Cầu Trước Khi Cài Đặt
- Windows 10 (64-bit: Pro, Enterprise hoặc Home từ build 19041 trở lên) hoặc Windows 11.
- Bật tính năng ảo hóa (**Hardware Virtualization** / VT-x hoặc AMD-V) trong BIOS/UEFI của máy tính (thường mặc định đã bật).
- Đã cài đặt **WSL 2** (Windows Subsystem for Linux 2).

---

#### 2. Các Bước Cài Đặt Docker Desktop Trên Windows

1. **Bật WSL 2 trên Windows (nếu chưa có):**
   - Mở **PowerShell** bằng quyền Administrator (chuột phải chọn *Run as Administrator*).
   - Chạy lệnh:
     ```powershell
     wsl --install
     ```
   - Nếu máy tính đã có WSL nhưng là bản cũ, chạy lệnh cập nhật:
     ```powershell
     wsl --update
     ```
   - Khởi động lại máy tính (Restart) nếu được yêu cầu.

2. **Tải bộ cài đặt Docker Desktop:**
   - 🔗 **Link tải chính thức từ Docker:** [https://docs.docker.com/desktop/setup/install/windows-install/](https://docs.docker.com/desktop/setup/install/windows-install/)
   - Hoặc tải trực tiếp file cài đặt: [Docker Desktop Installer for Windows (x86_64)](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe)

3. **Tiến hành cài đặt:**
   - Nhấp đúp vào file `Docker Desktop Installer.exe` vừa tải về.
   - Khi màn hình cài đặt hiện ra, đảm bảo tích chọn:
     -  **Use WSL 2 instead of Hyper-V (recommended)**
     -  **Add shortcut to desktop**
   - Nhấn **OK** và chờ quá trình cài đặt hoàn tất.
   - Nhấn **Close and restart** để khởi động lại máy tính.

4. **Khởi động Docker Desktop:**
   - Mở ứng dụng **Docker Desktop** từ màn hình Desktop hoặc menu Start.
   - Chấp nhận điều khoản sử dụng (**Accept Terms**).
   - Chờ khoảng 1-2 phút cho đến khi biểu tượng con cá voi ở góc dưới bên trái chuyển sang màu xanh lá cây (**Engine running**).

5. **Kiểm tra cài đặt thành công:**
   - Mở **PowerShell** hoặc **Command Prompt (CMD)** và gõ:
     ```powershell
     docker --version
     docker compose version
     ```
   - Nếu hiển thị thông tin phiên bản Docker (ví dụ `Docker version 27.x.x` hoặc mới hơn) là bạn đã cài đặt thành công!

---

#### 3. Khởi Chạy Ứng Dụng Xưởng Gỗ Trên Windows

Mở **PowerShell** hoặc **Terminal** tại thư mục dự án `xuong-go` trên Windows:

##### Cách nhanh nhất: Dùng Docker Compose (1 lệnh duy nhất)
```powershell
docker compose up -d --build
```
> Lệnh này sẽ tự động:
> - Tải môi trường Python 3.11-slim
> - Cài đặt tất cả thư viện
> - Khởi tạo database và dữ liệu mẫu nếu chưa có
> - Gắn volume thư mục để dữ liệu `wood_factory.db` và ảnh sản phẩm `uploads` được lưu an toàn trên máy tính của bạn
> - Mở cổng `8000` và chạy ứng dụng dưới nền (`-d`)

##### Dừng ứng dụng:
```powershell
docker compose down
```

##### Xem log hoạt động thực tế của web:
```powershell
docker compose logs -f
```

---

##### Hoặc chạy bằng lệnh Docker CLI thủ công:
```powershell
# 1. Build image:
docker build -t xuong-go-app:latest .

# 2. Khởi chạy container:
docker run -d `
  --name web-quan-ly-xuong-go `
  -p 8000:8000 `
  -v ${PWD}/wood_factory.db:/app/wood_factory.db `
  -v ${PWD}/app/static/uploads:/app/app/static/uploads `
  --restart unless-stopped `
  xuong-go-app:latest
```

---

#### 4. Truy Cập Ứng Dụng:
Mở trình duyệt (Chrome, Edge, Cốc Cốc...) trên Windows và truy cập:
👉 **[http://localhost:8000](http://localhost:8000)**

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
