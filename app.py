"""
app.py - Flask Application chính
He thong quan ly va phan tich hieu qua Short Video da nen tang
Cong ty SYS Viet Nam
"""
import os
import re
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify)
from sqlalchemy import func, desc
from datetime import date, timedelta, datetime

from config import Config
from model import (db, User, Platform, Category, Product,
                   Campaign, Video, VideoStat,
                   ROLES, ROLE_DESCRIPTIONS, VIDEO_STATUSES, CAMPAIGN_STATUSES,
                   VIDEO_DRAFT, VIDEO_PUBLISHED, VIDEO_ARCHIVED,
                   CAMPAIGN_PLANNED, CAMPAIGN_RUNNING, CAMPAIGN_ENDED)

# ---------------------------------------------------------------------------
# Khoi tao ung dung
# ---------------------------------------------------------------------------
app = Flask(__name__)
import time

@app.route("/test-server")
def test_server():
    return "Flask hoat dong binh thuong", 200

app.config.from_object(Config)
db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ---------------------------------------------------------------------------
# Context processor: truyen bien dung chung vao moi template
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    pending = 0
    if 'user_id' in session:
        u = User.query.get(session['user_id'])
        if u and u.is_admin():
            pending = User.query.filter_by(status='pending').count()
    return dict(pending_count_nav=pending)

# ---------------------------------------------------------------------------
# Helper: Decorators
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vui lòng đăng nhập để tiếp tục.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        u = User.query.get(session['user_id'])
        if not u or not u.is_admin():
            flash('Bạn không có quyền truy cập trang này.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        u = User.query.get(session['user_id'])
        if not u or not u.is_manager():
            flash('Bạn không có quyền thực hiện thao tác này.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


# --- Validation helpers ---
def _valid_email(email):
    return re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email) is not None

def _valid_password(pw):
    """Toi thieu 8 ky tu, co chu hoa, chu thuong, so"""
    return (len(pw) >= 8 and
            any(c.isupper() for c in pw) and
            any(c.islower() for c in pw) and
            any(c.isdigit() for c in pw))

MAX_LOGIN_ATTEMPTS = 5          # khoa sau 5 lan sai
LOCK_MINUTES       = 15         # khoa 15 phut


# ===========================================================================
# AUTH ROUTES
# ===========================================================================

# ---------------------------------------------------------------------------
# Dang ky
# ---------------------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username  = request.form.get('username',  '').strip().lower()
        email     = request.form.get('email',     '').strip().lower()
        phone     = request.form.get('phone',     '').strip()
        password  = request.form.get('password',  '')
        confirm   = request.form.get('confirm',   '')
        role      = request.form.get('role',      'viewer')

        # --- Validation ---
        errors = []
        if not full_name or len(full_name) < 2:
            errors.append('Họ tên phải có ít nhất 2 ký tự.')
        if not username or len(username) < 3:
            errors.append('Tên đăng nhập phải có ít nhất 3 ký tự.')
        if not re.match(r'^[a-z0-9_.]+$', username):
            errors.append('Tên đăng nhập chỉ được dùng chữ thường, số, dấu chấm và dấu gạch dưới.')
        if not _valid_email(email):
            errors.append('Email không hợp lệ.')
        if not _valid_password(password):
            errors.append('Mật khẩu phải có ít nhất 8 ký tự, gồm chữ hoa, chữ thường và số.')
        if password != confirm:
            errors.append('Xác nhận mật khẩu không khớp.')
        if role not in ('admin', 'manager', 'viewer'):
            errors.append('Loại tài khoản không hợp lệ.')
        if User.query.filter_by(username=username).first():
            errors.append('Tên đăng nhập đã tồn tại.')
        if User.query.filter_by(email=email).first():
            errors.append('Email đã được sử dụng.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html',
                role_descriptions=ROLE_DESCRIPTIONS,
                form_data=request.form)

        # --- Tao tai khoan ---
        # Neu dang ky Admin hoac Manager -> cho duyet (pending)
        # Neu dang ky Viewer -> active ngay
        if role in ('admin', 'manager'):
            account_status = 'pending'
            is_verified_val = False
        else:
            account_status = 'active'
            is_verified_val = True

        u = User(
            username    = username,
            email       = email,
            full_name   = full_name,
            phone       = phone,
            role        = role,
            status      = account_status,
            is_verified = is_verified_val,
        )
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        if role in ('admin', 'manager'):
            flash(f'Đăng ký thành công! Tài khoản <strong>{full_name}</strong> '
                  f'đang chờ quản trị viên xét duyệt. Bạn sẽ nhận thông báo khi được duyệt.', 'warning')
        else:
            flash(f'🎉 Đăng ký thành công! Chào mừng <strong>{full_name}</strong>. Hãy đăng nhập.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html',
        role_descriptions=ROLE_DESCRIPTIONS,
        form_data={})


# ---------------------------------------------------------------------------
# Dang nhap
# ---------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        u = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        # Kiem tra tai khoan co ton tai khong
        if not u:
            flash('Tài khoản không tồn tại. Hãy đăng ký trước.', 'danger')
            return render_template('login.html', username_val=username)

        # Kiem tra bi khoa
        if u.is_locked():
            remaining = int((u.locked_until - datetime.utcnow()).total_seconds() / 60) + 1
            flash(f'Tài khoản bị khóa tạm thời do đăng nhập sai quá nhiều lần. '
                  f'Thử lại sau {remaining} phút.', 'danger')
            return render_template('login.html', username_val=username)

        # Kiem tra trang thai
        if u.status == 'pending':
            flash('Tài khoản đang chờ quản trị viên xét duyệt. '
                  'Vui lòng chờ email thông báo hoặc liên hệ admin.', 'warning')
            return render_template('login.html', username_val=username)

        if u.status != 'active':
            flash('Tài khoản bị vô hiệu hóa. Liên hệ quản trị viên.', 'danger')
            return render_template('login.html', username_val=username)

        # Kiem tra mat khau
        if not u.check_password(password):
            u.login_attempts = (u.login_attempts or 0) + 1
            if u.login_attempts >= MAX_LOGIN_ATTEMPTS:
                u.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_MINUTES)
                u.login_attempts = 0
                db.session.commit()
                flash(f'Đăng nhập sai {MAX_LOGIN_ATTEMPTS} lần liên tiếp. '
                      f'Tài khoản bị khóa {LOCK_MINUTES} phút.', 'danger')
            else:
                db.session.commit()
                remaining_tries = MAX_LOGIN_ATTEMPTS - u.login_attempts
                flash(f'Mật khẩu không đúng. Còn {remaining_tries} lần thử trước khi bị khóa.', 'danger')
            return render_template('login.html', username_val=username)

        # --- Dang nhap thanh cong ---
        u.login_attempts = 0
        u.locked_until   = None
        u.last_login     = datetime.utcnow()
        u.last_ip        = request.remote_addr
        db.session.commit()

        # Tao session an toan
        session.clear()
        session['user_id']        = u.id
        session['user_role']      = u.role
        session['user_name']      = u.full_name
        session['_user_agent']    = request.headers.get('User-Agent', '')[:100]
        session.permanent         = bool(remember)  # "Ghi nho dang nhap"

        flash(f'Chào mừng trở lại, <strong>{u.full_name}</strong>! 👋', 'success')
        next_url = request.args.get('next')
        return redirect(next_url if next_url and next_url.startswith('/') else url_for('dashboard'))

    return render_template('login.html', username_val='')


# ---------------------------------------------------------------------------
# Dang xuat
# ---------------------------------------------------------------------------
@app.route('/logout')
def logout():
    name = session.get('user_name', '')
    session.clear()
    flash(f'Bạn đã đăng xuất thành công. Hẹn gặp lại{", " + name.split()[0] if name else ""}! 👋', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def dashboard():
    total_videos    = Video.query.count()
    total_views     = db.session.query(func.sum(Video.views)).scalar() or 0
    total_orders    = db.session.query(func.sum(Video.orders)).scalar() or 0
    total_revenue   = db.session.query(func.sum(Video.revenue)).scalar() or 0
    total_likes     = db.session.query(func.sum(Video.likes)).scalar() or 0
    total_comments  = db.session.query(func.sum(Video.comments)).scalar() or 0
    total_shares    = db.session.query(func.sum(Video.shares)).scalar() or 0
    total_saves     = db.session.query(func.sum(Video.saves)).scalar() or 0
    total_interactions = total_likes + total_comments + total_shares + total_saves
    engagement_rate = round(total_interactions / total_views * 100, 2) if total_views else 0
    orders_per_1000 = round(total_orders / total_views * 1000, 2) if total_views else 0

    # Hieu suat theo nen tang
    platform_stats = []
    for plat in Platform.query.filter_by(status='active').all():
        v = db.session.query(func.sum(Video.views)).filter_by(platform_id=plat.id).scalar() or 0
        platform_stats.append({'name': plat.name, 'color': plat.color, 'views': v})
    platform_stats.sort(key=lambda x: x['views'], reverse=True)
    max_views = platform_stats[0]['views'] if platform_stats else 1

    # Top 5 video
    top_videos = Video.query.filter_by(status=VIDEO_PUBLISHED)\
                       .order_by(desc(Video.views)).limit(5).all()

    # Chien dich dang chay
    running_campaigns = Campaign.query.filter_by(status=CAMPAIGN_RUNNING).all()

    # Bieu do 30 ngay (views tong hop)
    chart_labels, chart_data = [], []
    today = date.today()
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        total = db.session.query(func.sum(VideoStat.views))\
                    .filter(VideoStat.date == d).scalar() or 0
        chart_labels.append(d.strftime('%d/%m'))
        chart_data.append(total)

    # Phan phoi trang thai video
    published_count = Video.query.filter_by(status=VIDEO_PUBLISHED).count()
    draft_count     = Video.query.filter_by(status=VIDEO_DRAFT).count()
    archived_count  = Video.query.filter_by(status=VIDEO_ARCHIVED).count()

    # Recent videos
    recent_videos = Video.query.order_by(desc(Video.created_at)).limit(8).all()

    return render_template('index.html',
        user=current_user(),
        total_videos=total_videos,
        total_views=total_views,
        total_orders=total_orders,
        total_revenue=total_revenue,
        total_interactions=total_interactions,
        engagement_rate=engagement_rate,
        orders_per_1000=orders_per_1000,
        platform_stats=platform_stats,
        max_views=max_views,
        top_videos=top_videos,
        running_campaigns=running_campaigns,
        chart_labels=chart_labels,
        chart_data=chart_data,
        published_count=published_count,
        draft_count=draft_count,
        archived_count=archived_count,
        recent_videos=recent_videos,
    )


# ---------------------------------------------------------------------------
# Videos
# ---------------------------------------------------------------------------
@app.route('/videos')
@login_required
def videos():
    q         = request.args.get('q', '')
    plat_id   = request.args.get('platform', '', type=str)
    status_f  = request.args.get('status', '')
    camp_f    = request.args.get('campaign', '', type=str)
    period    = request.args.get('period', '')
    date_from_s = request.args.get('date_from', '')
    date_to_s   = request.args.get('date_to', '')
    page      = request.args.get('page', 1, type=int)

    today = date.today()
    d_from = d_to = None

    if period == 'today':
        d_from = d_to = today
    elif period == 'week':
        d_from = today - timedelta(days=today.weekday()); d_to = today
    elif period == 'month':
        d_from = today.replace(day=1); d_to = today
    elif period == 'quarter':
        qm = ((today.month-1)//3)*3+1
        d_from = today.replace(month=qm, day=1); d_to = today
    elif period == 'year':
        d_from = today.replace(month=1, day=1); d_to = today
    elif period == 'custom' and date_from_s and date_to_s:
        try:
            d_from = datetime.strptime(date_from_s, '%Y-%m-%d').date()
            d_to   = datetime.strptime(date_to_s,   '%Y-%m-%d').date()
        except:
            pass

    query = Video.query
    if q:
        query = query.filter(Video.title.ilike(f'%{q}%'))
    if plat_id:
        query = query.filter(Video.platform_id == int(plat_id))
    if status_f:
        query = query.filter(Video.status == status_f)
    if camp_f:
        query = query.filter(Video.campaign_id == int(camp_f))
    if d_from and d_to:
        query = query.filter(Video.published_at >= datetime.combine(d_from, datetime.min.time()),
                             Video.published_at <= datetime.combine(d_to,   datetime.max.time()))
    elif d_from:
        query = query.filter(Video.published_at >= datetime.combine(d_from, datetime.min.time()))

    pagination = query.order_by(desc(Video.created_at))\
                      .paginate(page=page, per_page=app.config['PER_PAGE'], error_out=False)

    return render_template('videos.html',
        user=current_user(),
        videos=pagination.items,
        pagination=pagination,
        platforms=Platform.query.filter_by(status='active').all(),
        campaigns=Campaign.query.all(),
        video_statuses=VIDEO_STATUSES,
        q=q, plat_id=plat_id, status_f=status_f, camp_f=camp_f,
        period=period,
        date_from=date_from_s,
        date_to=date_to_s,
    )


@app.route('/videos/import', methods=['GET', 'POST'])
@manager_required
def video_import():
    if request.method == 'POST':
        file = request.files.get('excel_file')
        if not file or not file.filename:
            flash('Vui lòng chọn file Excel.', 'danger')
            return redirect(url_for('video_import'))
        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Chỉ chấp nhận file .xlsx hoặc .xls', 'danger')
            return redirect(url_for('video_import'))
        try:
            import openpyxl, io
            wb = openpyxl.load_workbook(io.BytesIO(file.read()))
            ws = wb.active
            imported = 0; skipped = 0; errors = []

            for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                if not row or not row[0]:
                    continue
                try:
                    title        = str(row[0]).strip()
                    plat_name    = str(row[1]).strip() if row[1] else ''
                    views        = int(str(row[2]).replace(',','').replace('.','').strip()) if row[2] else 0
                    likes        = int(str(row[3]).replace(',','').replace('.','').strip()) if row[3] else 0
                    comments     = int(str(row[4]).replace(',','').replace('.','').strip()) if row[4] else 0
                    shares       = int(str(row[5]).replace(',','').replace('.','').strip()) if row[5] else 0
                    saves        = int(str(row[6]).replace(',','').replace('.','').strip()) if row[6] else 0
                    orders       = int(str(row[7]).replace(',','').replace('.','').strip()) if row[7] else 0
                    revenue      = float(str(row[8]).replace(',','').replace('.','').strip()) if row[8] else 0
                    ctr          = float(str(row[9]).replace(',','.').strip()) if row[9] else 0
                    conv_rate    = float(str(row[10]).replace(',','.').strip()) if row[10] else 0
                    video_url    = str(row[11]).strip() if row[11] else ''
                    tags         = str(row[12]).strip() if row[12] else ''
                    status_val   = str(row[13]).strip().lower() if row[13] else 'published'
                    camp_name    = str(row[14]).strip() if row[14] else ''
                    prod_name    = str(row[15]).strip() if row[15] else ''

                    if not title:
                        skipped += 1; continue

                    # Tim platform theo ten
                    plat = Platform.query.filter(Platform.name.ilike(f'%{plat_name}%')).first() if plat_name else None

                    # Tim campaign
                    camp = Campaign.query.filter(Campaign.name.ilike(f'%{camp_name}%')).first() if camp_name else None

                    # Tim product
                    prod = Product.query.filter(Product.name.ilike(f'%{prod_name}%')).first() if prod_name else None

                    # Map status
                    if status_val in ('published', 'da dang', 'đã đăng', '1'):
                        st = VIDEO_PUBLISHED
                    elif status_val in ('archived', 'luu tru', 'lưu trữ'):
                        st = VIDEO_ARCHIVED
                    else:
                        st = VIDEO_PUBLISHED  # mac dinh la da dang

                    v = Video(
                        title=title,
                        platform_id=plat.id if plat else None,
                        views=views, likes=likes, comments=comments,
                        shares=shares, saves=saves, orders=orders,
                        revenue=revenue, ctr=ctr, conversion_rate=conv_rate,
                        video_url=video_url, tags=tags, status=st,
                        campaign_id=camp.id if camp else None,
                        product_id=prod.id if prod else None,
                        user_id=session['user_id'],
                        published_at=datetime.utcnow() if st == VIDEO_PUBLISHED else None,
                    )
                    db.session.add(v)
                    imported += 1
                except Exception as e:
                    errors.append(f'Dòng {i}: {str(e)}')
                    skipped += 1

            db.session.commit()
            msg = f'Import thành công <strong>{imported}</strong> video'
            if skipped: msg += f', bỏ qua <strong>{skipped}</strong> dòng'
            flash(msg, 'success')
            for e in errors[:5]: flash(e, 'warning')
            return redirect(url_for('videos'))
        except Exception as e:
            flash(f'Lỗi đọc file: {str(e)}', 'danger')
            return redirect(url_for('video_import'))

    return render_template('video_import.html',
        user=current_user(),
        platforms=Platform.query.filter_by(status='active').all(),
        campaigns=Campaign.query.all(),
    )


@app.route('/videos/template')
@manager_required
def video_template():
    import openpyxl, io
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from flask import make_response

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Danh sách video'

    headers = [
        'Tiêu đề video *', 'Nền tảng *', 'Lượt xem', 'Lượt thích',
        'Bình luận', 'Chia sẻ', 'Lượt lưu', 'Đơn hàng',
        'Doanh thu (đ)', 'CTR (%)', 'Tỷ lệ chuyển đổi (%)',
        'URL video', 'Tags', 'Trạng thái', 'Chiến dịch', 'Sản phẩm'
    ]
    widths = [35,18,12,12,12,12,12,12,15,10,20,35,25,15,25,25]

    hdr_fill = PatternFill('solid', fgColor='2563EB')
    hdr_font = Font(bold=True, color='FFFFFF', size=11)
    thin = Side(style='thin', color='E2E8F0')
    bdr  = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col, (h, w) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = hdr_font; cell.fill = hdr_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = bdr
        ws.column_dimensions[get_column_letter(col)].width = w
    ws.row_dimensions[1].height = 30

    # Du lieu mau
    samples = [
        ('Review áo thun basic hot nhất', 'TikTok', 50000, 3000, 500, 800, 400, 25, 4975000, 5.2, 2.1, 'https://tiktok.com/@user/video/123', 'viral,review,thoitrang', 'published', 'Flash Sale Tháng 4', 'Áo thun basic unisex'),
        ('Son lì 24h không lem - test thực tế', 'Facebook Reels', 30000, 2500, 300, 600, 350, 18, 4500000, 4.8, 1.8, 'https://facebook.com/reels/456', 'son,makeup,review', 'published', 'Sale 8/3 Phụ nữ', 'Son môi lì matte'),
        ('Tai nghe bluetooth dưới 600k', 'YouTube Shorts', 20000, 1800, 200, 400, 250, 10, 5990000, 3.5, 1.2, 'https://youtube.com/shorts/789', 'tainghe,review,unghe', 'published', '', 'Tai nghe bluetooth'),
    ]

    data_font = Font(size=10)
    for r, row in enumerate(samples, 2):
        for c, val in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.font = data_font; cell.border = bdr
            cell.alignment = Alignment(vertical='center')
            if isinstance(val, (int, float)):
                cell.alignment = Alignment(horizontal='right', vertical='center')
        ws.row_dimensions[r].height = 20

    # Sheet huong dan
    ws2 = wb.create_sheet('Hướng dẫn')
    ws2.column_dimensions['A'].width = 28
    ws2.column_dimensions['B'].width = 55
    guide = [
        ('Cột', 'Mô tả & Giá trị hợp lệ'),
        ('A - Tiêu đề video *', 'Bắt buộc. Tên video đầy đủ'),
        ('B - Nền tảng *', 'TikTok / YouTube Shorts / Facebook Reels / Instagram Reels / Shopee Video'),
        ('C - Lượt xem', 'Chỉ nhập số nguyên, không có dấu phẩy'),
        ('D - Lượt thích', 'Số nguyên'),
        ('E - Bình luận', 'Số nguyên'),
        ('F - Chia sẻ', 'Số nguyên'),
        ('G - Lượt lưu', 'Số nguyên'),
        ('H - Đơn hàng', 'Số đơn hàng từ video này'),
        ('I - Doanh thu', 'Doanh thu (đồng), chỉ nhập số'),
        ('J - CTR (%)', 'Tỷ lệ nhấp link, ví dụ: 5.2'),
        ('K - Tỷ lệ chuyển đổi (%)', 'Ví dụ: 2.1'),
        ('L - URL video', 'Link gốc trên nền tảng'),
        ('M - Tags', 'Các tag phân cách bằng dấu phẩy'),
        ('N - Trạng thái', 'published / draft / archived'),
        ('O - Chiến dịch', 'Tên chiến dịch (phải tồn tại trong hệ thống)'),
        ('P - Sản phẩm', 'Tên sản phẩm (phải tồn tại trong hệ thống)'),
        ('', ''),
        ('Lưu ý', 'Dòng 1 là tiêu đề — không xóa'),
        ('Lưu ý', 'Nền tảng không khớp sẽ để trống'),
        ('Lưu ý', 'Có thể xóa 3 dòng mẫu và nhập dữ liệu thực'),
    ]
    hf = Font(bold=True, color='2563EB')
    for r, (a, b) in enumerate(guide, 1):
        ws2.cell(row=r, column=1, value=a).font = hf if r == 1 else Font(bold=(r==1))
        ws2.cell(row=r, column=2, value=b)

    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)
    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    resp.headers['Content-Disposition'] = 'attachment; filename=template_video_SYS.xlsx'
    return resp


@app.route('/videos/add', methods=['GET', 'POST'])
@manager_required
def video_add():
    if request.method == 'POST':
        v = Video(
            title        = request.form['title'],
            description  = request.form.get('description', ''),
            video_url    = request.form.get('video_url', ''),
            duration     = int(request.form.get('duration', 30)),
            platform_id  = request.form.get('platform_id') or None,
            product_id   = request.form.get('product_id') or None,
            campaign_id  = request.form.get('campaign_id') or None,
            user_id      = session['user_id'],
            views        = int(request.form.get('views', 0)),
            likes        = int(request.form.get('likes', 0)),
            comments     = int(request.form.get('comments', 0)),
            shares       = int(request.form.get('shares', 0)),
            saves        = int(request.form.get('saves', 0)),
            orders       = int(request.form.get('orders', 0)),
            ctr          = float(request.form.get('ctr', 0)),
            conversion_rate = float(request.form.get('conversion_rate', 0)),
            revenue      = float(request.form.get('revenue', 0)),
            status       = request.form.get('status', VIDEO_DRAFT),
            tags         = request.form.get('tags', ''),
        )
        if v.status == VIDEO_PUBLISHED and not v.published_at:
            v.published_at = datetime.utcnow()
        db.session.add(v)
        db.session.commit()
        flash(f'Thêm video thành công! Điểm hiệu quả: <strong>{v.performance_score}/100 — {v.performance_grade[0]}</strong>', 'success')
        return redirect(url_for('video_detail', vid=v.id))

    return render_template('video_form.html',
        user=current_user(), video=None,
        platforms=Platform.query.filter_by(status='active').all(),
        products=Product.query.filter_by(status='active').all(),
        campaigns=Campaign.query.all(),
        video_statuses=VIDEO_STATUSES,
        title='Thêm video mới',
    )


@app.route('/videos/<int:vid>/edit', methods=['GET', 'POST'])
@manager_required
def video_edit(vid):
    v = Video.query.get_or_404(vid)
    if request.method == 'POST':
        v.title           = request.form['title']
        v.description     = request.form.get('description', '')
        v.video_url       = request.form.get('video_url', '')
        v.duration        = int(request.form.get('duration', 30))
        v.platform_id     = request.form.get('platform_id') or None
        v.product_id      = request.form.get('product_id') or None
        v.campaign_id     = request.form.get('campaign_id') or None
        v.views           = int(request.form.get('views', 0))
        v.likes           = int(request.form.get('likes', 0))
        v.comments        = int(request.form.get('comments', 0))
        v.shares          = int(request.form.get('shares', 0))
        v.saves           = int(request.form.get('saves', 0))
        v.orders          = int(request.form.get('orders', 0))
        v.ctr             = float(request.form.get('ctr', 0))
        v.conversion_rate = float(request.form.get('conversion_rate', 0))
        v.revenue         = float(request.form.get('revenue', 0))
        v.status          = request.form.get('status', VIDEO_DRAFT)
        v.tags            = request.form.get('tags', '')
        if v.status == VIDEO_PUBLISHED and not v.published_at:
            v.published_at = datetime.utcnow()
        db.session.commit()
        flash('Cập nhật video thành công!', 'success')
        return redirect(url_for('videos'))

    return render_template('video_form.html',
        user=current_user(), video=v,
        platforms=Platform.query.filter_by(status='active').all(),
        products=Product.query.filter_by(status='active').all(),
        campaigns=Campaign.query.all(),
        video_statuses=VIDEO_STATUSES,
        title='Chỉnh sửa video',
    )


@app.route('/videos/<int:vid>/delete', methods=['POST'])
@manager_required
def video_delete(vid):
    v = Video.query.get_or_404(vid)
    db.session.delete(v)
    db.session.commit()
    flash('Đã xóa video.', 'info')
    return redirect(url_for('videos'))


@app.route('/videos/<int:vid>')
@login_required
def video_detail(vid):
    v = Video.query.get_or_404(vid)
    # Chi so theo ngay (30 ngay)
    today = date.today()
    stat_labels, stat_views, stat_interactions = [], [], []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        s = VideoStat.query.filter_by(video_id=vid, date=d).first()
        stat_labels.append(d.strftime('%d/%m'))
        stat_views.append(s.views if s else 0)
        inter = (s.likes + s.comments + s.shares + s.saves) if s else 0
        stat_interactions.append(inter)

    return render_template('video_detail.html',
        user=current_user(), video=v,
        stat_labels=stat_labels,
        stat_views=stat_views,
        stat_interactions=stat_interactions,
    )


# ---------------------------------------------------------------------------
# Platforms
# ---------------------------------------------------------------------------
@app.route('/platforms')
@login_required
def platforms():
    all_platforms = Platform.query.all()
    return render_template('platforms.html',
        user=current_user(), platforms=all_platforms)


@app.route('/platforms/add', methods=['POST'])
@admin_required
def platform_add():
    p = Platform(
        name=request.form['name'], icon=request.form.get('icon', ''),
        color=request.form.get('color', '#4A90D9'),
        base_url=request.form.get('base_url', ''),
        description=request.form.get('description', ''),
    )
    db.session.add(p)
    db.session.commit()
    flash('Thêm nền tảng thành công!', 'success')
    return redirect(url_for('platforms'))


@app.route('/platforms/<int:pid>/edit', methods=['POST'])
@admin_required
def platform_edit(pid):
    p = Platform.query.get_or_404(pid)
    p.name        = request.form['name']
    p.icon        = request.form.get('icon', '')
    p.color       = request.form.get('color', '#4A90D9')
    p.base_url    = request.form.get('base_url', '')
    p.description = request.form.get('description', '')
    p.status      = request.form.get('status', 'active')
    db.session.commit()
    flash('Cập nhật nền tảng thành công!', 'success')
    return redirect(url_for('platforms'))


@app.route('/platforms/<int:pid>/delete', methods=['POST'])
@admin_required
def platform_delete(pid):
    p = Platform.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Đã xóa nền tảng.', 'info')
    return redirect(url_for('platforms'))


# ---------------------------------------------------------------------------
# Import san pham tu Excel
# ---------------------------------------------------------------------------
@app.route('/products/import', methods=['GET', 'POST'])
@manager_required
def product_import():
    if request.method == 'POST':
        file = request.files.get('excel_file')
        if not file or not file.filename:
            flash('Vui lòng chọn file Excel.', 'danger')
            return redirect(url_for('product_import'))

        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Chỉ chấp nhận file .xlsx hoặc .xls', 'danger')
            return redirect(url_for('product_import'))

        try:
            import openpyxl, io
            wb = openpyxl.load_workbook(io.BytesIO(file.read()))
            ws = wb.active

            imported = 0
            skipped  = 0
            errors   = []

            for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                # Cot: ten | gia | danh_muc | sku | ton_kho | mo_ta | trang_thai
                if not row or not row[0]:
                    continue
                try:
                    name     = str(row[0]).strip()
                    price    = float(str(row[1]).replace(',','').replace('.','').strip()) if row[1] else 0
                    cat_name = str(row[2]).strip() if row[2] else ''
                    sku      = str(row[3]).strip() if row[3] else ''
                    stock    = int(str(row[4]).replace(',','').strip()) if row[4] else 0
                    desc     = str(row[5]).strip() if row[5] else ''
                    status   = 'active' if not row[6] or str(row[6]).strip().lower() in ('active','còn hàng','co hang','1','true') else 'inactive'

                    if not name:
                        skipped += 1
                        continue

                    # Tim hoac tao danh muc
                    cat_id = None
                    if cat_name:
                        cat = Category.query.filter_by(name=cat_name).first()
                        if not cat:
                            cat = Category(name=cat_name, description=f'Nhập từ Excel')
                            db.session.add(cat)
                            db.session.flush()
                        cat_id = cat.id

                    # Kiem tra trung SKU
                    if sku and Product.query.filter_by(sku=sku).first():
                        skipped += 1
                        errors.append(f'Dòng {i}: SKU "{sku}" đã tồn tại — bỏ qua.')
                        continue

                    pr = Product(
                        name=name, price=price, category_id=cat_id,
                        sku=sku or None, stock=stock,
                        description=desc, status=status,
                    )
                    db.session.add(pr)
                    imported += 1

                except Exception as e:
                    errors.append(f'Dòng {i}: Lỗi — {str(e)}')
                    skipped += 1

            db.session.commit()

            msg = f'Import thành công <strong>{imported}</strong> sản phẩm'
            if skipped:
                msg += f', bỏ qua <strong>{skipped}</strong> dòng'
            flash(msg, 'success')
            for e in errors[:5]:
                flash(e, 'warning')
            return redirect(url_for('products'))

        except Exception as e:
            flash(f'Lỗi đọc file: {str(e)}', 'danger')
            return redirect(url_for('product_import'))

    # GET: render trang import
    categories = Category.query.order_by(Category.name).all()
    return render_template('product_import.html',
        user=current_user(), categories=categories)


@app.route('/products/template')
@manager_required
def product_template():
    """Tao file Excel mau de tai ve"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from flask import make_response
    import io

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Danh sách sản phẩm'

    # Header
    headers = ['Tên sản phẩm *', 'Giá bán (đ) *', 'Danh mục',
               'SKU / Mã SP', 'Tồn kho', 'Mô tả', 'Trạng thái']
    widths  = [35, 18, 22, 15, 12, 40, 15]

    header_fill = PatternFill('solid', fgColor='2563EB')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    thin = Side(style='thin', color='CCCCCC')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col, (h, w) in enumerate(zip(headers, widths), 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font   = header_font
        cell.fill   = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border
        ws.column_dimensions[cell.column_letter].width = w
    ws.row_dimensions[1].height = 30

    # Du lieu mau
    samples = [
        ('Áo thun basic unisex', 199000, 'Thời trang', 'SKU001', 100, 'Áo thun cotton 100%, form unisex', 'active'),
        ('Son môi lì matte',     250000, 'Mỹ phẩm & Làm đẹp', 'SKU002', 50, 'Màu sắc đa dạng, bền màu 8h', 'active'),
        ('Tai nghe bluetooth',   599000, 'Điện tử & Phụ kiện', 'SKU003', 30, 'Pin 20h, chống ồn chủ động', 'active'),
    ]

    data_font = Font(size=10)
    data_fill_odd  = PatternFill('solid', fgColor='F8FAFC')
    data_fill_even = PatternFill('solid', fgColor='FFFFFF')

    for r, row in enumerate(samples, 2):
        for c, val in enumerate(row, 1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.font   = data_font
            cell.fill   = data_fill_odd if r % 2 else data_fill_even
            cell.border = border
            cell.alignment = Alignment(vertical='center')
        ws.row_dimensions[r].height = 20

    # Sheet huong dan
    ws2 = wb.create_sheet('Hướng dẫn')
    ws2.column_dimensions['A'].width = 25
    ws2.column_dimensions['B'].width = 55
    guide = [
        ('Cột', 'Mô tả'),
        ('Tên sản phẩm *', 'Bắt buộc. Tên đầy đủ của sản phẩm'),
        ('Giá bán (đ) *',  'Bắt buộc. Chỉ nhập số, không có dấu chấm/phẩy'),
        ('Danh mục',        'Tên danh mục. Tự tạo mới nếu chưa có'),
        ('SKU / Mã SP',     'Mã sản phẩm (nếu trùng sẽ bỏ qua dòng đó)'),
        ('Tồn kho',         'Số lượng hàng hiện có'),
        ('Mô tả',           'Mô tả chi tiết sản phẩm'),
        ('Trạng thái',      '"active" = Còn hàng | "inactive" = Ngừng bán'),
        ('', ''),
        ('Lưu ý', 'Dòng đầu tiên là tiêu đề — không được xóa'),
        ('Lưu ý', 'File phải ở định dạng .xlsx'),
        ('Lưu ý', 'Có thể xóa 3 dòng mẫu và nhập dữ liệu thực'),
    ]
    h_font = Font(bold=True, color='2563EB')
    for r, (a, b) in enumerate(guide, 1):
        ws2.cell(row=r, column=1, value=a).font = h_font if r == 1 else Font()
        ws2.cell(row=r, column=2, value=b)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    resp.headers['Content-Disposition'] = 'attachment; filename=template_san_pham_SYS.xlsx'
    return resp


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
@app.route('/products')
@login_required
def products():
    q      = request.args.get('q', '')
    cat_id = request.args.get('category', '')
    page   = request.args.get('page', 1, type=int)
    query  = Product.query
    if q:
        query = query.filter(Product.name.ilike(f'%{q}%'))
    if cat_id:
        query = query.filter(Product.category_id == int(cat_id))
    pagination = query.order_by(Product.name)\
                      .paginate(page=page, per_page=app.config['PER_PAGE'], error_out=False)
    return render_template('products.html',
        user=current_user(),
        products=pagination.items, pagination=pagination,
        categories=Category.query.all(),
        q=q, cat_id=cat_id,
    )


@app.route('/products/add', methods=['GET', 'POST'])
@manager_required
def product_add():
    if request.method == 'POST':
        pr = Product(
            name=request.form['name'],
            description=request.form.get('description', ''),
            price=float(request.form.get('price', 0)),
            category_id=request.form.get('category_id') or None,
            stock=int(request.form.get('stock', 0)),
            sku=request.form.get('sku', ''),
            status=request.form.get('status', 'active'),
        )
        db.session.add(pr)
        db.session.commit()
        flash('Thêm sản phẩm thành công!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html',
        user=current_user(), product=None,
        categories=Category.query.all(), title='Thêm sản phẩm mới')


@app.route('/products/<int:pid>/edit', methods=['GET', 'POST'])
@manager_required
def product_edit(pid):
    pr = Product.query.get_or_404(pid)
    if request.method == 'POST':
        pr.name        = request.form['name']
        pr.description = request.form.get('description', '')
        pr.price       = float(request.form.get('price', 0))
        pr.category_id = request.form.get('category_id') or None
        pr.stock       = int(request.form.get('stock', 0))
        pr.sku         = request.form.get('sku', '')
        pr.status      = request.form.get('status', 'active')
        db.session.commit()
        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html',
        user=current_user(), product=pr,
        categories=Category.query.all(), title='Chỉnh sửa sản phẩm')


@app.route('/products/<int:pid>/delete', methods=['POST'])
@manager_required
def product_delete(pid):
    pr = Product.query.get_or_404(pid)
    db.session.delete(pr)
    db.session.commit()
    flash('Đã xóa sản phẩm.', 'info')
    return redirect(url_for('products'))


# ---------------------------------------------------------------------------
# Campaigns
# ---------------------------------------------------------------------------
@app.route('/campaigns')
@login_required
def campaigns():
    status_f = request.args.get('status', '')
    query = Campaign.query
    if status_f:
        query = query.filter(Campaign.status == status_f)
    all_campaigns = query.order_by(desc(Campaign.created_at)).all()
    return render_template('campaigns.html',
        user=current_user(), campaigns=all_campaigns,
        campaign_statuses=CAMPAIGN_STATUSES, status_f=status_f)


@app.route('/campaigns/add', methods=['GET', 'POST'])
@manager_required
def campaign_add():
    if request.method == 'POST':
        c = Campaign(
            name=request.form['name'],
            description=request.form.get('description', ''),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None,
            budget=float(request.form.get('budget', 0)),
            status=request.form.get('status', CAMPAIGN_PLANNED),
        )
        db.session.add(c)
        db.session.commit()
        flash('Thêm chiến dịch thành công!', 'success')
        return redirect(url_for('campaigns'))
    return render_template('campaign_form.html',
        user=current_user(), campaign=None,
        campaign_statuses=CAMPAIGN_STATUSES, title='Thêm chiến dịch mới')


@app.route('/campaigns/<int:cid>/edit', methods=['GET', 'POST'])
@manager_required
def campaign_edit(cid):
    c = Campaign.query.get_or_404(cid)
    if request.method == 'POST':
        c.name        = request.form['name']
        c.description = request.form.get('description', '')
        c.start_date  = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date() if request.form.get('start_date') else None
        c.end_date    = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None
        c.budget      = float(request.form.get('budget', 0))
        c.status      = request.form.get('status', CAMPAIGN_PLANNED)
        db.session.commit()
        flash('Cập nhật chiến dịch thành công!', 'success')
        return redirect(url_for('campaigns'))
    return render_template('campaign_form.html',
        user=current_user(), campaign=c,
        campaign_statuses=CAMPAIGN_STATUSES, title='Chỉnh sửa chiến dịch')


@app.route('/campaigns/<int:cid>/delete', methods=['POST'])
@manager_required
def campaign_delete(cid):
    c = Campaign.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    flash('Đã xóa chiến dịch.', 'info')
    return redirect(url_for('campaigns'))


@app.route('/campaigns/<int:cid>')
@login_required
def campaign_detail(cid):
    c = Campaign.query.get_or_404(cid)
    camp_videos = Video.query.filter_by(campaign_id=cid).all()
    total_views  = sum(v.views for v in camp_videos)
    total_orders = sum(v.orders for v in camp_videos)
    total_rev    = sum(v.revenue for v in camp_videos)
    return render_template('campaign_detail.html',
        user=current_user(), campaign=c, camp_videos=camp_videos,
        total_views=total_views, total_orders=total_orders, total_rev=total_rev)


# ---------------------------------------------------------------------------
# Xuat Excel bao cao Analytics
# ---------------------------------------------------------------------------
@app.route('/analytics/export')
@login_required
def analytics_export():
    import openpyxl, io
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, PatternFill
    from openpyxl.utils import get_column_letter
    from flask import make_response

    period       = request.args.get('period', 'month')
    date_from_s  = request.args.get('date_from', '')
    date_to_s    = request.args.get('date_to', '')
    today = date.today()

    if period == 'today':    d_from = d_to = today
    elif period == 'week':   d_from = today - timedelta(days=today.weekday()); d_to = today
    elif period == 'month':  d_from = today.replace(day=1); d_to = today
    elif period == 'quarter':
        qm = ((today.month-1)//3)*3+1; d_from = today.replace(month=qm,day=1); d_to = today
    elif period == 'year':   d_from = today.replace(month=1,day=1); d_to = today
    elif period == 'custom' and date_from_s and date_to_s:
        try:
            d_from = datetime.strptime(date_from_s,'%Y-%m-%d').date()
            d_to   = datetime.strptime(date_to_s,  '%Y-%m-%d').date()
        except:
            d_from = today.replace(day=1); d_to = today
    else: d_from = today.replace(day=1); d_to = today

    wb = openpyxl.Workbook()

    # --- Màu & style ---
    HDR_FILL  = PatternFill('solid', fgColor='2563EB')
    HDR_FONT  = Font(bold=True, color='FFFFFF', size=11)
    SUB_FILL  = PatternFill('solid', fgColor='EFF6FF')
    SUB_FONT  = Font(bold=True, color='1D4ED8', size=10)
    TITLE_FONT= Font(bold=True, size=14, color='0F172A')
    thin = Side(style='thin', color='E2E8F0')
    bdr  = Border(left=thin, right=thin, top=thin, bottom=thin)
    ctr  = Alignment(horizontal='center', vertical='center')
    right= Alignment(horizontal='right',  vertical='center')

    def set_hdr(ws, row, cols):
        for col, val in enumerate(cols, 1):
            c = ws.cell(row=row, column=col, value=val)
            c.font = HDR_FONT; c.fill = HDR_FILL
            c.alignment = ctr; c.border = bdr

    def set_row(ws, row, vals, bold=False, fill=None):
        for col, val in enumerate(vals, 1):
            c = ws.cell(row=row, column=col, value=val)
            c.font = Font(bold=bold, size=10)
            if fill: c.fill = fill
            c.border = bdr
            if isinstance(val, (int, float)):
                c.alignment = right
            else:
                c.alignment = Alignment(vertical='center')

    period_names = {
        'today':'Hôm nay','week':'Tuần này','month':'Tháng này',
        'quarter':'Quý này','year':'Năm này','custom':'Tùy chỉnh'
    }

    # ============================================================
    # Sheet 1: Tổng quan nền tảng
    # ============================================================
    ws1 = wb.active
    ws1.title = 'Tổng quan nền tảng'
    ws1.merge_cells('A1:J1')
    ws1['A1'] = f'BÁO CÁO HIỆU SUẤT SHORT VIDEO — {period_names.get(period,"").upper()}'
    ws1['A1'].font = TITLE_FONT
    ws1['A1'].alignment = ctr
    ws1['A1'].fill = PatternFill('solid', fgColor='EFF6FF')

    ws1.merge_cells('A2:J2')
    ws1['A2'] = f'Từ {d_from.strftime("%d/%m/%Y")} đến {d_to.strftime("%d/%m/%Y")}  |  Xuất lúc: {datetime.utcnow().strftime("%d/%m/%Y %H:%M")}  |  SYS Việt Nam'
    ws1['A2'].font = Font(size=10, color='64748B', italic=True)
    ws1['A2'].alignment = ctr

    headers1 = ['Nền tảng','Số video','Lượt xem','Lượt thích',
                'Bình luận','Chia sẻ','Đơn hàng','Doanh thu (đ)',
                'Tỷ lệ tương tác%','CTR TB%']
    set_hdr(ws1, 4, headers1)
    widths1  = [20,10,15,12,12,12,12,18,18,10]
    for i,w in enumerate(widths1,1):
        ws1.column_dimensions[get_column_letter(i)].width = w

    row = 5
    total_v=total_l=total_c=total_s=total_o=total_r=0
    for plat in Platform.query.filter_by(status='active').all():
        videos  = Video.query.filter_by(platform_id=plat.id).all()
        vid_ids = [v.id for v in videos]
        if vid_ids:
            stats = VideoStat.query.filter(
                VideoStat.video_id.in_(vid_ids),
                VideoStat.date >= d_from, VideoStat.date <= d_to).all()
            vv = sum(s.views for s in stats); lv = sum(s.likes for s in stats)
            cv = sum(s.comments for s in stats); sv = sum(s.shares for s in stats)
            ov = sum(s.orders for s in stats)
        else:
            vv=lv=cv=sv=ov=0
        rv       = sum(v.revenue for v in videos)
        inter    = lv+cv+sv
        eng      = round(inter/vv*100,2) if vv else 0
        avg_ctr  = round(sum(v.ctr for v in videos)/len(videos),2) if videos else 0
        total_v+=vv;total_l+=lv;total_c+=cv;total_s+=sv;total_o+=ov;total_r+=rv
        set_row(ws1, row, [plat.name,len(videos),vv,lv,cv,sv,ov,rv,f'{eng}%',f'{avg_ctr}%'])
        row += 1

    # Tong cong
    tot_eng = round((total_l+total_c+total_s)/total_v*100,2) if total_v else 0
    set_row(ws1, row, ['TỔNG CỘNG','',total_v,total_l,total_c,total_s,total_o,total_r,f'{tot_eng}%',''],
            bold=True, fill=PatternFill('solid', fgColor='DBEAFE'))
    ws1.row_dimensions[1].height = 28
    ws1.row_dimensions[2].height = 18
    ws1.row_dimensions[4].height = 22

    # ============================================================
    # Sheet 2: Chi tiết theo ngày
    # ============================================================
    ws2 = wb.create_sheet('Chi tiet theo ngay')
    all_plats_ex = Platform.query.filter_by(status='active').all()
    merge_end = 1 + len(all_plats_ex) * 3 + 1
    ws2.merge_cells(start_row=1,start_column=1,end_row=1,end_column=merge_end)
    ws2.cell(row=1,column=1).value = 'CHI TIET THEO NGAY - ' + d_from.strftime('%d/%m/%Y') + ' den ' + d_to.strftime('%d/%m/%Y')
    ws2.cell(row=1,column=1).font = TITLE_FONT
    ws2.cell(row=1,column=1).alignment = ctr
    ws2.cell(row=1,column=1).fill = PatternFill('solid', fgColor='F0FDF4')
    # Header dong 2
    h2 = ['Ngay', 'Tong views']
    for plat in all_plats_ex:
        h2 += [plat.name + ' views', plat.name + ' orders', plat.name + ' revenue']
    set_hdr(ws2, 2, h2)
    for i in range(len(h2)):
        ws2.column_dimensions[get_column_letter(i+1)].width = 15
    # Du lieu
    row = 3; d = d_from
    while d <= d_to:
        tv = db.session.query(func.sum(VideoStat.views)).filter(VideoStat.date==d).scalar() or 0
        row_data = [d.strftime('%d/%m/%Y'), int(tv)]
        for plat in all_plats_ex:
            vids = [v.id for v in Video.query.filter_by(platform_id=plat.id).all()]
            sv = db.session.query(func.sum(VideoStat.views)).filter(VideoStat.video_id.in_(vids), VideoStat.date==d).scalar() or 0 if vids else 0
            so = db.session.query(func.sum(VideoStat.orders)).filter(VideoStat.video_id.in_(vids), VideoStat.date==d).scalar() or 0 if vids else 0
            sr = round(sum(v.revenue for v in Video.query.filter_by(platform_id=plat.id).all())/30) if vids else 0
            row_data += [int(sv), int(so), int(sr)]
        set_row(ws2, row, row_data)
        d += timedelta(days=1); row += 1

    # ============================================================
    # Sheet 3: Danh sach video
    # ============================================================
    ws3 = wb.create_sheet('Danh sách video')
    ws3.merge_cells('A1:K1')
    ws3['A1'] = 'DANH SÁCH VIDEO & CHỈ SỐ HIỆU QUẢ'
    ws3['A1'].font = TITLE_FONT; ws3['A1'].alignment = ctr
    ws3['A1'].fill = PatternFill('solid', fgColor='FEF9C3')

    hdrs3 = ['STT','Tiêu đề video','Nền tảng','Chiến dịch','Trạng thái',
             'Lượt xem','Thích','Bình luận','Chia sẻ','Đơn hàng','Doanh thu (đ)']
    set_hdr(ws3, 3, hdrs3)
    ws3.column_dimensions['A'].width = 5
    ws3.column_dimensions['B'].width = 40
    for i,w in enumerate([12,18,14,8,12,10,12,10,12,16],3):
        ws3.column_dimensions[get_column_letter(i)].width = w

    videos_all = Video.query.order_by(desc(Video.views)).all()
    for idx, v in enumerate(videos_all, 1):
        set_row(ws3, 3+idx, [
            idx, v.title,
            v.platform.name if v.platform else '',
            v.campaign.name if v.campaign else '',
            v.status_name,
            v.views, v.likes, v.comments, v.shares, v.orders, v.revenue,
        ])

    # ============================================================
    # Sheet 4: Hiệu suất theo tuần
    # ============================================================
    ws4 = wb.create_sheet('Theo tuan - Nen tang')
    all_plats_ex = Platform.query.filter_by(status='active').all()
    merge_end4 = 2 + len(all_plats_ex) * 2 + 1
    ws4.merge_cells(start_row=1,start_column=1,end_row=1,end_column=merge_end4)
    ws4.cell(row=1,column=1).value = 'HIEU SUAT THEO TUAN - ' + d_from.strftime('%d/%m/%Y') + ' den ' + d_to.strftime('%d/%m/%Y')
    ws4.cell(row=1,column=1).font = TITLE_FONT
    ws4.cell(row=1,column=1).alignment = ctr
    ws4.cell(row=1,column=1).fill = PatternFill('solid', fgColor='F5F3FF')
    # Header
    h4 = ['Tuan', 'Tu ngay', 'Den ngay']
    for plat in all_plats_ex:
        h4 += [plat.name + ' views', plat.name + ' orders']
    set_hdr(ws4, 2, h4)
    for i in range(len(h4)):
        ws4.column_dimensions[get_column_letter(i+1)].width = 15

    week_num = 1; row = 3; d = d_from
    while d <= d_to:
        wend = min(d + timedelta(days=6), d_to)
        row_data = ['Tuan ' + str(week_num), d.strftime('%d/%m/%Y'), wend.strftime('%d/%m/%Y')]
        for plat in all_plats_ex:
            vids = [v.id for v in Video.query.filter_by(platform_id=plat.id).all()]
            wv = db.session.query(func.sum(VideoStat.views)).filter(
                VideoStat.video_id.in_(vids),
                VideoStat.date >= d, VideoStat.date <= wend
            ).scalar() or 0 if vids else 0
            wo = db.session.query(func.sum(VideoStat.orders)).filter(
                VideoStat.video_id.in_(vids),
                VideoStat.date >= d, VideoStat.date <= wend
            ).scalar() or 0 if vids else 0
            row_data += [int(wv), int(wo)]
        set_row(ws4, row, row_data)
        d += timedelta(days=7); week_num += 1; row += 1

    # --- Xuat file ---
    buf = io.BytesIO()
    wb.save(buf); buf.seek(0)

    fname = f'BaoCao_SYS_{period}_{d_from.strftime("%d%m%Y")}_{d_to.strftime("%d%m%Y")}.xlsx'
    resp = make_response(buf.read())
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    resp.headers['Content-Disposition'] = f'attachment; filename={fname}'
    return resp


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@app.route('/analytics')
@login_required
def analytics():
    period        = request.args.get('period', 'month')
    date_from_str = request.args.get('date_from', '')
    date_to_str   = request.args.get('date_to', '')
    plat_filter   = request.args.get('platform', '')
    today = date.today()

    if period == 'today':    d_from = d_to = today
    elif period == 'week':   d_from = today - timedelta(days=today.weekday()); d_to = today
    elif period == 'month':  d_from = today.replace(day=1); d_to = today
    elif period == 'quarter':
        qm = ((today.month-1)//3)*3+1; d_from = today.replace(month=qm,day=1); d_to = today
    elif period == 'year':   d_from = today.replace(month=1,day=1); d_to = today
    elif period == 'custom' and date_from_str and date_to_str:
        try:
            d_from = datetime.strptime(date_from_str,'%Y-%m-%d').date()
            d_to   = datetime.strptime(date_to_str,  '%Y-%m-%d').date()
        except: d_from = today.replace(day=1); d_to = today
    else: d_from = today.replace(day=1); d_to = today

    if d_from > d_to: d_from, d_to = d_to, d_from
    dt_from = datetime.combine(d_from, datetime.min.time())
    dt_to   = datetime.combine(d_to,   datetime.max.time())

    all_platforms = Platform.query.filter_by(status='active').all()
    if plat_filter:
        try:
            sp = Platform.query.get(int(plat_filter))
            platforms_to_show = [sp] if sp else all_platforms
        except: platforms_to_show = all_platforms
    else: platforms_to_show = all_platforms

    # === KPI lay thang tu Video (du lieu nguoi dung nhap) ===
    platform_data = []
    for plat in platforms_to_show:
        videos_all = Video.query.filter_by(platform_id=plat.id).all()
        v_total  = sum(v.views    for v in videos_all)
        l_total  = sum(v.likes    for v in videos_all)
        c_total  = sum(v.comments for v in videos_all)
        s_total  = sum(v.shares   for v in videos_all)
        sv_total = sum(v.saves    for v in videos_all)
        o_total  = sum(v.orders   for v in videos_all)
        r_total  = sum(v.revenue  for v in videos_all)
        cnt      = len(videos_all)
        avg_ctr  = round(sum(v.ctr for v in videos_all)/cnt, 2) if cnt else 0
        inter    = l_total + c_total + s_total + sv_total
        eng_rate = round(inter/v_total*100, 2) if v_total else 0
        platform_data.append({
            'id': plat.id, 'name': plat.name, 'color': plat.color,
            'video_count': cnt,
            'views': v_total, 'likes': l_total, 'comments': c_total,
            'shares': s_total, 'orders': o_total, 'revenue': r_total,
            'engagement_rate': eng_rate, 'avg_ctr': avg_ctr,
        })
    platform_data.sort(key=lambda x: x['views'], reverse=True)

    total_views   = sum(p['views']   for p in platform_data)
    total_orders  = sum(p['orders']  for p in platform_data)
    total_revenue = sum(p['revenue'] for p in platform_data)
    total_inter   = sum(p['likes']+p['comments']+p['shares'] for p in platform_data)
    global_eng    = round(total_inter/total_views*100, 2) if total_views else 0

    # === Bieu do: lay tu Video.views phan bo deu theo ngay ===
    delta = (d_to - d_from).days
    chart_labels = []
    if delta <= 31:
        for i in range(delta+1):
            chart_labels.append((d_from + timedelta(days=i)).strftime('%d/%m'))
    else:
        d = d_from
        while d <= d_to:
            chart_labels.append(d.strftime('%d/%m')); d += timedelta(days=7)

    platform_chart_data = []
    for plat in platforms_to_show:
        vid_ids = [v.id for v in Video.query.filter_by(platform_id=plat.id).all()]
        # Thu VideoStat truoc
        series_views = []
        has_stat = False
        if delta <= 31:
            for i in range(delta+1):
                d = d_from + timedelta(days=i)
                sv = db.session.query(func.sum(VideoStat.views)).filter(
                    VideoStat.video_id.in_(vid_ids), VideoStat.date==d
                ).scalar() or 0 if vid_ids else 0
                series_views.append(int(sv))
                if sv > 0: has_stat = True
        else:
            d = d_from
            while d <= d_to:
                wend = min(d+timedelta(days=6), d_to)
                sv = db.session.query(func.sum(VideoStat.views)).filter(
                    VideoStat.video_id.in_(vid_ids),
                    VideoStat.date>=d, VideoStat.date<=wend
                ).scalar() or 0 if vid_ids else 0
                series_views.append(int(sv)); d += timedelta(days=7)
                if sv > 0: has_stat = True

        # Neu khong co VideoStat -> phan bo deu Video.views
        if not has_stat and vid_ids:
            total_v = sum(v.views for v in Video.query.filter_by(platform_id=plat.id).all())
            n = len(series_views)
            if n > 0:
                base = total_v // n
                rem  = total_v % n
                series_views = [base + (1 if i < rem else 0) for i in range(n)]

        platform_chart_data.append({'name': plat.name, 'color': plat.color, 'views': series_views})

    q_top = Video.query
    if plat_filter: q_top = q_top.filter(Video.platform_id==int(plat_filter))
    top10 = q_top.order_by(desc(Video.views)).limit(10).all()

    all_filtered_videos = []
    if plat_filter:
        all_filtered_videos = Video.query.filter(Video.platform_id==int(plat_filter))                                         .order_by(desc(Video.views)).all()

    month_labels = []
    for i in range(5,-1,-1):
        y=today.year; m=today.month-i
        while m<=0: m+=12; y-=1
        month_labels.append(f'{m:02d}/{y}')

    month_data = []
    for plat in platforms_to_show:
        vid_ids = [v.id for v in Video.query.filter_by(platform_id=plat.id).all()]
        series = []
        for lbl in month_labels:
            if vid_ids:
                mv = db.session.query(func.sum(VideoStat.views)).filter(
                    VideoStat.video_id.in_(vid_ids),
                    func.strftime('%m/%Y', VideoStat.date)==lbl
                ).scalar() or 0
            else: mv = 0
            if mv == 0:
                vids_m = Video.query.filter(
                    Video.platform_id==plat.id,
                    func.strftime('%m/%Y', Video.created_at)==lbl
                ).all()
                mv = sum(v.views for v in vids_m)
            series.append(int(mv))
        month_data.append({'name':plat.name,'color':plat.color,'views':series})

    selected_plat_name = ''
    if plat_filter:
        p_obj = Platform.query.get(int(plat_filter))
        selected_plat_name = p_obj.name if p_obj else ''

    return render_template('analytics.html',
        user=current_user(),
        all_platforms=all_platforms,
        platform_data=platform_data,
        platform_chart_data=platform_chart_data,
        top10=top10, all_filtered_videos=all_filtered_videos,
        chart_labels=chart_labels, month_labels=month_labels, month_data=month_data,
        total_views=total_views, total_orders=total_orders,
        total_revenue=total_revenue, global_eng=global_eng,
        period=period, plat_filter=plat_filter,
        selected_plat_name=selected_plat_name,
        date_from=d_from.strftime('%Y-%m-%d'),
        date_to=d_to.strftime('%Y-%m-%d'),
        date_from_disp=d_from.strftime('%d/%m/%Y'),
        date_to_disp=d_to.strftime('%d/%m/%Y'),
    )
# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
@app.route('/reports')
@login_required
def reports():
    # Tong quan nhanh
    total_videos   = Video.query.filter_by(status=VIDEO_PUBLISHED).count()
    total_views    = db.session.query(func.sum(Video.views)).filter_by(status=VIDEO_PUBLISHED).scalar() or 0
    total_orders   = db.session.query(func.sum(Video.orders)).filter_by(status=VIDEO_PUBLISHED).scalar() or 0
    total_revenue  = db.session.query(func.sum(Video.revenue)).filter_by(status=VIDEO_PUBLISHED).scalar() or 0
    total_likes    = db.session.query(func.sum(Video.likes)).scalar() or 0
    total_comments = db.session.query(func.sum(Video.comments)).scalar() or 0
    total_shares   = db.session.query(func.sum(Video.shares)).scalar() or 0

    # Top sản phẩm theo doanh thu
    top_products = db.session.query(
        Product.name,
        func.sum(Video.revenue).label('total_revenue'),
        func.sum(Video.orders).label('total_orders'),
        func.count(Video.id).label('video_count'),
    ).join(Video, Video.product_id == Product.id)\
     .filter(Video.status == VIDEO_PUBLISHED)\
     .group_by(Product.id)\
     .order_by(desc('total_revenue')).limit(5).all()

    # Hieu qua chien dich
    camp_perf = db.session.query(
        Campaign.name,
        func.sum(Video.views).label('total_views'),
        func.sum(Video.orders).label('total_orders'),
        func.sum(Video.revenue).label('total_revenue'),
        func.count(Video.id).label('video_count'),
    ).join(Video, Video.campaign_id == Campaign.id)\
     .filter(Video.status == VIDEO_PUBLISHED)\
     .group_by(Campaign.id)\
     .order_by(desc('total_revenue')).all()

    return render_template('reports.html',
        user=current_user(),
        total_videos=total_videos, total_views=total_views,
        total_orders=total_orders, total_revenue=total_revenue,
        total_likes=total_likes, total_comments=total_comments,
        total_shares=total_shares,
        top_products=top_products,
        camp_perf=camp_perf,
    )


# ---------------------------------------------------------------------------
# Duyet tai khoan (admin only)
# ---------------------------------------------------------------------------
@app.route('/users/pending')
@admin_required
def users_pending():
    pending_users = User.query.filter_by(status='pending').order_by(User.created_at.desc()).all()
    return render_template('users_pending.html',
        user=current_user(),
        pending_users=pending_users,
        pending_count=len(pending_users),
    )


@app.route('/users/<int:uid>/approve', methods=['POST'])
@admin_required
def user_approve(uid):
    u = User.query.get_or_404(uid)
    u.status      = 'active'
    u.is_verified = True
    u.approved_by = session['user_id']
    u.approved_at = datetime.utcnow()
    u.reject_reason = None
    db.session.commit()
    flash(f'Đã duyệt tài khoản <strong>{u.full_name}</strong> ({u.role_name}).', 'success')
    return redirect(url_for('users_pending'))


@app.route('/users/<int:uid>/reject', methods=['POST'])
@admin_required
def user_reject(uid):
    u = User.query.get_or_404(uid)
    reason = request.form.get('reason', 'Không đáp ứng yêu cầu.')
    u.status        = 'rejected'
    u.reject_reason = reason
    db.session.commit()
    flash(f'Đã từ chối tài khoản <strong>{u.full_name}</strong>.', 'info')
    return redirect(url_for('users_pending'))


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
@app.route('/users')
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html',
        user=current_user(), users=all_users, roles=ROLES)


@app.route('/users/add', methods=['POST'])
@admin_required
def user_add():
    if User.query.filter_by(username=request.form['username']).first():
        flash('Tên đăng nhập đã tồn tại.', 'danger')
        return redirect(url_for('users'))
    u = User(
        username  = request.form['username'],
        email     = request.form['email'],
        full_name = request.form['full_name'],
        role      = request.form.get('role', 'viewer'),
        phone     = request.form.get('phone', ''),
        status    = 'active',
    )
    u.set_password(request.form['password'])
    db.session.add(u)
    db.session.commit()
    flash('Thêm người dùng thành công!', 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:uid>/edit', methods=['POST'])
@admin_required
def user_edit(uid):
    u = User.query.get_or_404(uid)
    u.full_name = request.form['full_name']
    u.email     = request.form['email']
    u.role      = request.form.get('role', u.role)
    u.phone     = request.form.get('phone', '')
    u.status    = request.form.get('status', u.status)
    if request.form.get('password'):
        u.set_password(request.form['password'])
    db.session.commit()
    flash('Cập nhật người dùng thành công!', 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:uid>/delete', methods=['POST'])
@admin_required
def user_delete(uid):
    if uid == session['user_id']:
        flash('Không thể xóa tài khoản đang đăng nhập.', 'danger')
        return redirect(url_for('users'))
    u = User.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    flash('Đã xóa người dùng.', 'info')
    return redirect(url_for('users'))


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    u = current_user()
    if request.method == 'POST':
        u.full_name = request.form.get('full_name', u.full_name)
        u.email     = request.form.get('email', u.email)
        u.phone     = request.form.get('phone', '')
        old_pw = request.form.get('old_password', '')
        new_pw = request.form.get('new_password', '')
        if old_pw and new_pw:
            if u.check_password(old_pw):
                u.set_password(new_pw)
                flash('Đổi mật khẩu thành công!', 'success')
            else:
                flash('Mật khẩu cũ không đúng.', 'danger')
                return redirect(url_for('profile'))
        db.session.commit()
        flash('Cập nhật hồ sơ thành công!', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=u)


# ---------------------------------------------------------------------------
# API JSON (cho bieu do dong, AJAX)
# ---------------------------------------------------------------------------
@app.route('/api/stats/overview')
@login_required
def api_stats_overview():
    plat_id = request.args.get('platform', '')
    query = Video.query.filter_by(status=VIDEO_PUBLISHED)
    if plat_id:
        query = query.filter(Video.platform_id == int(plat_id))
    videos_q = query.all()
    total_views  = sum(v.views  for v in videos_q)
    total_orders = sum(v.orders for v in videos_q)
    total_inter  = sum(v.likes + v.comments + v.shares + v.saves for v in videos_q)
    eng_rate     = round(total_inter / total_views * 100, 2) if total_views else 0
    op1k         = round(total_orders / total_views * 1000, 2) if total_views else 0
    return jsonify({
        'total_videos': len(videos_q),
        'total_views': total_views,
        'total_interactions': total_inter,
        'total_orders': total_orders,
        'engagement_rate': eng_rate,
        'orders_per_1000': op1k,
    })


@app.route('/api/chart/daily')
@login_required
def api_chart_daily():
    days = request.args.get('days', 30, type=int)
    today = date.today()
    labels, data_views, data_orders = [], [], []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        v = db.session.query(func.sum(VideoStat.views)).filter(VideoStat.date == d).scalar() or 0
        o = db.session.query(func.sum(VideoStat.orders)).filter(VideoStat.date == d).scalar() or 0
        labels.append(d.strftime('%d/%m'))
        data_views.append(v)
        data_orders.append(o)
    return jsonify({'labels': labels, 'views': data_views, 'orders': data_orders})


@app.route('/api/chart/platform')
@login_required
def api_chart_platform():
    result = db.session.query(
        Platform.name, Platform.color,
        func.sum(Video.views).label('views'),
        func.sum(Video.orders).label('orders'),
    ).join(Video, Video.platform_id == Platform.id)\
     .filter(Video.status == VIDEO_PUBLISHED)\
     .group_by(Platform.id).all()
    return jsonify([{
        'name': r.name, 'color': r.color,
        'views': r.views or 0, 'orders': r.orders or 0,
    } for r in result])


# ---------------------------------------------------------------------------
# Khoi tao DB
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()
    # Tu dong seed neu chua co du lieu
    if User.query.count() == 0:
        from seed import seed
        seed()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
