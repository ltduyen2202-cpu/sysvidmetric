"""
run_simple.py - Khoi chay SYS VidMetric
"""
from app import app

print("=" * 55)
print("  SYS VidMetric - He thong quan ly Short Video")
print("  Cong ty SYS Viet Nam - 2026")
print("=" * 55)
print("  Local : http://127.0.0.1:8080")
print("  Tai khoan: 0868648311 / Duyen@2005")
print("=" * 55)

app.run(
    host='0.0.0.0',
    port=8080,
    debug=False,
    use_reloader=False,
    threaded=True,
)
