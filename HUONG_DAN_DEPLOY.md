# Hướng dẫn Deploy SYS VidMetric
## Để người khác truy cập qua sysvidmetric.com.vn

---

## CÁCH 1: Deploy miễn phí lên Render.com (Khuyên dùng)

### Bước 1: Tạo tài khoản
- Vào https://render.com → Sign up miễn phí

### Bước 2: Tạo file cần thiết
Tạo file `requirements.txt` (đã có) và file `Procfile`:
```
web: python run_production.py
```

### Bước 3: Đẩy code lên GitHub
```bash
git init
git add .
git commit -m "SYS VidMetric deploy"
git remote add origin https://github.com/tenban/sysvidmetric.git
git push -u origin main
```

### Bước 4: Tạo Web Service trên Render
- New → Web Service → kết nối GitHub repo
- Build Command: `pip install -r requirements.txt`
- Start Command: `python run_production.py`
- Render cấp domain miễn phí: `sysvidmetric.onrender.com`

### Bước 5: Gắn domain sysvidmetric.com.vn
- Mua domain tại: Tên Miền Việt (tenmien.vn) hoặc PA Vietnam
- Trên Render: Settings → Custom Domain → thêm sysvidmetric.com.vn
- Trên nhà cung cấp domain: thêm CNAME record trỏ về Render

---

## CÁCH 2: Deploy lên VPS (DigitalOcean/Vultr)

### Bước 1: Thuê VPS
- DigitalOcean: $6/tháng → https://digitalocean.com
- Vultr: $6/tháng → https://vultr.com

### Bước 2: Cài đặt trên VPS (Ubuntu)
```bash
sudo apt update && sudo apt install python3 python3-pip nginx -y
pip3 install flask flask-sqlalchemy werkzeug openpyxl gunicorn
```

### Bước 3: Upload code và chạy
```bash
# Upload code lên VPS
scp -r . root@IP_VPS:/var/www/sysvidmetric/

# SSH vào VPS
ssh root@IP_VPS
cd /var/www/sysvidmetric
python3 seed.py  # tạo dữ liệu
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

### Bước 4: Cấu hình Nginx
```nginx
server {
    listen 80;
    server_name sysvidmetric.com.vn www.sysvidmetric.com.vn;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Bước 5: Cài SSL miễn phí
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d sysvidmetric.com.vn
```

---

## CÁCH 3: Deploy nhanh với ngrok (Test tạm, miễn phí)
Cho người khác xem demo ngay không cần domain:

```bash
# Cài ngrok: https://ngrok.com/download
ngrok http 8080
# Ngrok sẽ cấp URL: https://abc123.ngrok.io
# Gửi URL đó cho người khác là vào được
```

---

## Mua domain .com.vn
1. Vào https://tenmien.vn hoặc https://pa.vn
2. Tìm kiếm: sysvidmetric.com.vn
3. Đăng ký (~200.000đ/năm)
4. Trỏ DNS về server của bạn

---

*SYS VidMetric © 2026 - Công ty SYS Việt Nam*
