# Bộ Prompt: Web App Quản Lý Xưởng Gỗ

**Công nghệ:** Python (FastAPI) + SQLite

## Cách sử dụng

1. Mở một cuộc trò chuyện mới với AI, dán **Prompt bối cảnh** trước.
2. Gửi lần lượt từng phase, chạy thử và kiểm tra checklist xong mới sang phase tiếp theo.
3. Nếu cuộc trò chuyện quá dài, mở chat mới, dán lại Prompt bối cảnh kèm cấu trúc thư mục và schema hiện tại rồi gửi phase tiếp theo.
4. Xưởng không cần module nào thì xóa bớt để AI tập trung làm kỹ phần còn lại.

| Phase | Nội dung |
|---|---|
| 0 | Prompt bối cảnh |
| 1 | Nền tảng & đăng nhập |
| 2 | Kho & nhà cung cấp |
| 3 | Sản phẩm, khách hàng, đơn hàng |
| 4 | Sản xuất & nhân công |
| 5 | Thu chi & báo cáo |
| 6 | Dashboard & hoàn thiện |

---

## Phase 0 – Prompt bối cảnh (gửi đầu tiên)

```
Tôi muốn xây dựng web app QUẢN LÝ XƯỞNG GỖ (sản xuất nội thất gỗ). Chúng ta sẽ làm theo từng phase, tôi sẽ gửi yêu cầu từng phase một. Chỉ làm đúng phase tôi yêu cầu, không làm trước phase sau.

Công nghệ cố định cho toàn dự án:
- Python 3.11+, FastAPI, SQLAlchemy ORM, SQLite (file wood_factory.db)
- Frontend: Jinja2 + Tailwind CSS (CDN) + HTMX, giao diện tiếng Việt, responsive
- Tiền VNĐ dạng 1.250.000 đ, ngày dd/mm/yyyy
- Code đầy đủ, không viết tắt "...", comment tiếng Việt ở chỗ quan trọng
- Cuối mỗi phase: liệt kê file đã tạo/sửa, cách chạy thử, và checklist kiểm tra

Trả lời "Đã hiểu" và chờ Phase 1.
```

---

## Phase 1 – Nền tảng & đăng nhập

```
PHASE 1: Nền tảng dự án
- Cấu trúc thư mục: app/models, app/routes, app/services, app/templates, app/static
- Kết nối SQLite, file config, requirements.txt, README
- Layout chung: sidebar menu (để sẵn link các module sau), header, thông báo flash
- Bảng users + phân quyền: Admin, Quản lý kho, Quản đốc, Kế toán
- Đăng nhập/đăng xuất, hash mật khẩu bcrypt, chặn truy cập theo quyền
- Trang quản lý tài khoản (Admin)
- Script tạo DB + tài khoản admin mặc định
```

---

## Phase 2 – Kho & nhà cung cấp

```
PHASE 2: Kho nguyên liệu và nhà cung cấp
- Nguyên liệu gỗ: loại gỗ, đơn vị (m³, tấm, cây), kích thước, tồn kho, đơn giá, mức tồn tối thiểu
- Phụ kiện/vật tư: bản lề, ốc vít, sơn, keo...
- Nhà cung cấp: thông tin liên hệ, lịch sử nhập
- Phiếu nhập kho (nhiều dòng), phiếu xuất kho, tự cập nhật tồn
- Lịch sử giao dịch kho, cảnh báo sắp hết hàng
- Tìm kiếm, lọc, phân trang. Thêm dữ liệu mẫu.
```

---

## Phase 3 – Sản phẩm, khách hàng, đơn hàng

```
PHASE 3: Bán hàng
- Sản phẩm: mã, tên, kích thước, loại gỗ, giá bán, ảnh upload
- Định mức nguyên liệu (BOM) cho mỗi sản phẩm, liên kết bảng nguyên liệu Phase 2
- Khách hàng: thông tin, lịch sử đơn
- Đơn hàng: nhiều sản phẩm, đặt cọc, ngày giao, trạng thái (Mới → Đang sản xuất → Hoàn thiện → Đã giao → Đã thanh toán)
- In báo giá/hóa đơn (trang in được)
- Công nợ khách hàng
```

---

## Phase 4 – Sản xuất & nhân công

```
PHASE 4: Sản xuất và nhân công
- Lệnh sản xuất tạo từ đơn hàng, tự tính nguyên liệu theo BOM, kiểm tra đủ kho rồi trừ kho
- Công đoạn: Pha phôi → Gia công → Lắp ráp → Chà nhám → Sơn → Đóng gói; giao thợ phụ trách, cập nhật tiến độ
- Đồng bộ trạng thái đơn hàng khi sản xuất xong
- Nhân công: hồ sơ thợ, chấm công theo ngày, lương theo ngày hoặc theo sản phẩm, ứng lương
- Bảng lương tháng
```

---

## Phase 5 – Thu chi & báo cáo

```
PHASE 5: Tài chính và báo cáo
- Phiếu thu/chi, danh mục chi phí, sổ quỹ
- Tự tạo phiếu thu khi khách đặt cọc/thanh toán, phiếu chi khi nhập kho/trả lương
- Công nợ nhà cung cấp
- Báo cáo: doanh thu, lợi nhuận theo đơn/sản phẩm, tồn kho, công nợ; lọc theo khoảng ngày
- Xuất Excel (openpyxl)
```

---

## Phase 6 – Dashboard & hoàn thiện

```
PHASE 6: Hoàn thiện
- Dashboard: doanh thu tháng, đơn đang làm, đơn sắp đến hạn, nguyên liệu sắp hết, biểu đồ doanh thu 12 tháng (Chart.js)
- Sao lưu/khôi phục file database
- Rà soát toàn bộ: validate dữ liệu, xử lý lỗi, bảo mật, tối ưu truy vấn
- Viết test cơ bản (pytest) cho các luồng chính: đăng nhập, nhập kho, tạo đơn, tạo lệnh sản xuất
- Cập nhật README đầy đủ
```

---

## Prompt nối tiếp khi mở chat mới (tùy chọn)

```
[Dán Prompt bối cảnh Phase 0 ở trên]

Dự án đã hoàn thành đến Phase X. Đây là cấu trúc thư mục và schema database hiện tại:
[Dán cấu trúc thư mục]
[Dán nội dung file models]

Hãy đọc kỹ, xác nhận đã nắm dự án, rồi chờ tôi gửi Phase tiếp theo.
```
