# SYS Video Analytics
## Hệ thống quản lý và phân tích hiệu quả Short Video đa nền tảng
### Công ty SYS Việt Nam — Đồ án tốt nghiệp 2026

---

## Mô tả
Hệ thống web quản lý và phân tích hiệu quả Short Video trên các nền tảng:
TikTok, YouTube Shorts, Facebook Reels, Instagram Reels — phục vụ hoạt động
thương mại điện tử tại Công ty SYS Việt Nam.

---

## Cài đặt & Khởi chạy

### 1. Cài thư viện
```bash
python -m pip install flask flask-sqlalchemy werkzeug
```

### 2. Tạo dữ liệu mẫu
```bash
python seed.py
```

### 3. Chạy ứng dụng
```bash
python run.py
```
Mở trình duyệt tại: **http://127.0.0.1:5000**

---

## Tài khoản đăng nhập

| Tài khoản   | Mật khẩu     | Vai trò          |
|-------------|--------------|------------------|
| admin       | admin123     | Quản trị viên    |
| manager1    | manager123   | Quản lý          |
| viewer1     | viewer123    | Người xem        |

---

## Cấu trúc dự án

```
doantotnghiep/
├── app.py              # Flask routes, API, auth
├── model.py            # SQLAlchemy models
├── config.py           # Cấu hình ứng dụng
├── seed.py             # Tạo dữ liệu mẫu
├── run.py              # Khởi chạy server
├── sys_video.db        # SQLite database (tự tạo)
├── requirements.txt    # Thư viện Python
├── static/
│   ├── css/style.css   # Giao diện CSS
│   └── js/main.js      # JavaScript
└── templates/
    ├── base.html           # Layout khung chung
    ├── login.html          # Trang đăng nhập
    ├── index.html          # Dashboard tổng quan
    ├── videos.html         # Danh sách video
    ├── video_form.html     # Thêm/sửa video
    ├── video_detail.html   # Chi tiết video
    ├── analytics.html      # Phân tích hiệu quả
    ├── campaigns.html      # Danh sách chiến dịch
    ├── campaign_form.html  # Thêm/sửa chiến dịch
    ├── campaign_detail.html# Chi tiết chiến dịch
    ├── platforms.html      # Quản lý nền tảng
    ├── products.html       # Danh sách sản phẩm
    ├── product_form.html   # Thêm/sửa sản phẩm
    ├── reports.html        # Báo cáo tổng hợp
    ├── users.html          # Quản lý người dùng
    └── profile.html        # Hồ sơ cá nhân
```

---

## Tính năng chính

### Dashboard
- Thống kê tổng quan: video, lượt xem, tương tác, đơn hàng
- Lọc theo nền tảng (TikTok, YouTube Shorts, Facebook Reels, Instagram Reels)
- Biểu đồ lượt xem 30 ngày với Chart.js
- Hiệu suất theo nền tảng (progress bar)
- Top 5 video nổi bật, chiến dịch đang chạy
- Chỉ số: Tỷ lệ tương tác & Đơn hàng/1000 lượt xem

### Quản lý Video
- CRUD đầy đủ (thêm, sửa, xóa, xem)
- Lọc theo nền tảng, trạng thái, chiến dịch
- Phân trang
- Chi tiết video với biểu đồ 30 ngày
- Tracking: views, likes, comments, shares, saves, orders, CTR, revenue

### Phân tích hiệu quả
- Bảng so sánh chi tiết theo nền tảng
- Biểu đồ cột lượt xem & đơn hàng
- Xu hướng theo tháng (6 tháng)
- Top 10 video hiệu quả nhất

### Chiến dịch Marketing
- Quản lý vòng đời: Lên kế hoạch → Đang chạy → Kết thúc
- Xem chi tiết video trong chiến dịch
- Thống kê tổng quan mỗi chiến dịch

### Quản lý Sản phẩm
- Liên kết sản phẩm với video
- Phân loại theo danh mục
- Theo dõi tồn kho và số lượng bán

### Báo cáo
- Thống kê toàn hệ thống
- Top sản phẩm theo doanh thu
- Hiệu quả từng chiến dịch

### Hệ thống & Phân quyền
- 3 cấp quyền: Quản trị viên / Quản lý / Người xem
- Quản lý tài khoản người dùng
- Hồ sơ cá nhân, đổi mật khẩu

---

## Công nghệ sử dụng

| Thành phần   | Công nghệ                |
|--------------|--------------------------|
| Backend      | Python 3, Flask          |
| Database     | SQLite + SQLAlchemy ORM  |
| Frontend     | HTML5, CSS3, JavaScript  |
| Biểu đồ      | Chart.js 4.4             |
| Icons        | Font Awesome 6.5         |
| Font         | Inter (Google Fonts)     |

---

*© 2026 SYS Việt Nam · Đồ án tốt nghiệp*
