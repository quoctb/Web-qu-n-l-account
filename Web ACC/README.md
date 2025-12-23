# Website Quản Lý Bán Account Game

Website quản lý bán account game được xây dựng bằng Python (Flask) với kết nối cơ sở dữ liệu SQLite và dashboard với biểu đồ matplotlib.

## Tính Năng

- 📊 **Dashboard**: Hiển thị thống kê tổng quan và biểu đồ doanh thu
- 🎮 **Quản Lý Account**: Thêm, sửa, xóa, tìm kiếm và lọc account game
- 💰 **Quản Lý Bán Hàng**: Ghi nhận giao dịch bán account
- 📈 **Biểu Đồ Thống Kê**:
  - Doanh thu theo ngày (30 ngày gần nhất)
  - Số lượng account theo game
  - Doanh thu theo game

## Yêu Cầu Hệ Thống

- Python 3.7 trở lên
- pip (Python package manager)

## Cài Đặt

1. **Cài đặt các thư viện cần thiết:**

```bash
pip install -r requirements.txt
```

2. **Chạy ứng dụng:**

```bash
python app.py
```

3. **Truy cập website:**

Mở trình duyệt và truy cập: `http://localhost:5000`

## Cấu Trúc Dự Án

```
Web ACC/
├── app.py                 # File chính chứa Flask app và routes
├── requirements.txt       # Danh sách các thư viện cần thiết
├── README.md             # File hướng dẫn
├── templates/            # Thư mục chứa các template HTML
│   ├── base.html        # Template cơ sở
│   ├── dashboard.html   # Trang dashboard
│   ├── accounts.html    # Trang quản lý account
│   ├── add_account.html # Trang thêm account
│   ├── edit_account.html # Trang sửa account
│   ├── sell_account.html # Trang bán account
│   └── sales.html       # Trang lịch sử bán hàng
└── game_accounts.db     # File database SQLite (tự động tạo)
```

## Sử Dụng

### Dashboard
- Xem tổng quan số lượng account, doanh thu
- Xem các biểu đồ thống kê

### Quản Lý Account
- **Thêm Account**: Click nút "Thêm Account Mới" và điền thông tin
- **Sửa Account**: Click icon bút chì ở cột "Thao Tác"
- **Xóa Account**: Click icon thùng rác ở cột "Thao Tác"
- **Bán Account**: Click icon giỏ hàng ở cột "Thao Tác" (chỉ với account đang có sẵn)
- **Lọc Account**: Sử dụng bộ lọc theo trạng thái hoặc game

### Lịch Sử Bán Hàng
- Xem tất cả các giao dịch đã thực hiện

## Cơ Sở Dữ Liệu

Website sử dụng SQLite với 2 bảng chính:

- **GameAccount**: Lưu thông tin account game
  - id, game_name, account_name, level, price, status, description, created_at, sold_at

- **Sale**: Lưu thông tin giao dịch bán hàng
  - id, account_id, buyer_name, sale_price, sale_date

Database sẽ tự động được tạo khi chạy ứng dụng lần đầu.

## Công Nghệ Sử Dụng

- **Flask**: Web framework
- **SQLAlchemy**: ORM cho database
- **SQLite**: Database
- **Matplotlib**: Tạo biểu đồ
- **Bootstrap 5**: Framework CSS cho giao diện

## Lưu Ý

- Database file `game_accounts.db` sẽ được tạo tự động trong thư mục dự án
- Để thay đổi port, sửa dòng `app.run(debug=True, host='0.0.0.0', port=5000)` trong `app.py`
- Trong môi trường production, nên thay đổi `SECRET_KEY` và tắt debug mode

## Tác Giả

Website được phát triển để quản lý bán account game một cách hiệu quả.

