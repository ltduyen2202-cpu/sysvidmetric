# Các bước deploy SYS VidMetric lên internet

## BƯỚC 1: Cài Git
Tải tại: https://git-scm.com/download/win
Cài xong mở CMD mới

## BƯỚC 2: Tạo tài khoản GitHub
Vào: https://github.com/signup

## BƯỚC 3: Tạo repo GitHub
- Vào github.com → New repository
- Tên: sysvidmetric
- Public → Create

## BƯỚC 4: Chạy các lệnh này trong CMD
cd "c:\Users\Acer\OneDrive\Tài liệu\doantotnghiep"
git init
git add .
git commit -m "SYS VidMetric v1.0"
git branch -M main
git remote add origin https://github.com/TEN_GITHUB_CUA_BAN/sysvidmetric.git
git push -u origin main

## BƯỚC 5: Deploy lên Render.com
- Vào: https://render.com → Sign up miễn phí
- New → Web Service → Connect GitHub
- Chọn repo sysvidmetric
- Build: pip install -r requirements.txt
- Start: gunicorn app:app
- Deploy! → Render cấp link: https://sysvidmetric.onrender.com

## BƯỚC 6: Mua domain (tùy chọn)
- Vào tenmien.vn tìm sysvidmetric.com.vn (~200k/năm)
- Sau khi mua: Render → Settings → Custom Domain
- Thêm: sysvidmetric.com.vn
- Trên tenmien.vn: thêm CNAME trỏ về Render
