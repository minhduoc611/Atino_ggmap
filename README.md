# Google Maps Review Scraper

Tự động scrape reviews từ Google Maps và đồng bộ vào Lark Base mỗi ngày.

### 4. Test chạy thủ công

- Vào **Actions** → **Daily Google Maps Review Scraper**
- Click **"Run workflow"** → **"Run workflow"**

## ⏰ Lịch chạy tự động

- **Mỗi ngày lúc 2:00 AM UTC** (9:00 AM giờ Việt Nam)
- Có thể thay đổi trong file `.github/workflows/daily-scraper.yml`

## 📋 Cấu trúc bảng Lark Base

### Table 1: Cửa hàng (LARK_TABLE_ID)
- `Cửa hàng` (Text)
- `Link map` (Text)

### Table 2: Reviews (LARK_TABLE_REVIEW_ID)
- `Cửa hàng` (Text)
- `Review ID` (Text) - Unique
- `Tên người review` (Text)
- `Xếp hạng` (Text)
- `Thời gian đăng` (Text)
- `Bài viết` (Text)

## 🔧 Chạy local

```bash
# Cài đặt dependencies
pip install selenium webdriver-manager requests

# Tạo file lark_config.py với thông tin của bạn
# Chạy
python main_scraper.py
```

## 📊 Giới hạn GitHub Actions

- **2000 phút/tháng** (free account)
- Mỗi lần chạy ~30-60 phút tùy số lượng cửa hàng
- Đủ để chạy hàng ngày

## 🛠️ Troubleshooting

### Lỗi "Chrome not found"
→ Workflow đã tự động cài Chrome, không cần lo

### Lỗi timeout
→ Tăng `timeout-minutes` trong workflow file

### Scraper bị Google block
→ Thêm delay giữa các cửa hàng (đã có `time.sleep(2)`)
