"""
run.py - Khoi chay ung dung
Lenh: python run.py
"""
from app import app

if __name__ == '__main__':
    print("=" * 55)
    print("  SYS Video Analytics - He thong quan ly Short Video")
    print("  Cong ty SYS Viet Nam - Do an tot nghiep 2026")
    print("=" * 55)
    print("  URL: http://127.0.0.1:5000")
    print("  Tai khoan: admin / admin123")
    print("=" * 55)
    app.run(debug=True, host='0.0.0.0', port=5000)
