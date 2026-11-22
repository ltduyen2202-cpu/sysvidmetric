"""
model.py - Dinh nghia cac model SQLAlchemy
He thong quan ly va phan tich hieu qua Short Video da nen tang
Cong ty SYS Viet Nam
"""
from datetime import datetime
import secrets
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

# --- Constants ---
ROLE_ADMIN   = 'admin'
ROLE_MANAGER = 'manager'
ROLE_VIEWER  = 'viewer'
ROLES = [(ROLE_ADMIN, 'Quản trị viên'), (ROLE_MANAGER, 'Quản lý'), (ROLE_VIEWER, 'Người xem')]

# Mo ta chi tiet 3 loai tai khoan dang ky
ROLE_DESCRIPTIONS = {
    ROLE_ADMIN: {
        'label': 'Quản trị viên',
        'icon': 'fa-shield-halved',
        'color': '#EF4444',
        'desc': 'Toàn quyền hệ thống: quản lý người dùng, nền tảng, cấu hình.',
        'features': ['Quản lý người dùng', 'Cấu hình nền tảng', 'Xem mọi báo cáo', 'Phân quyền tài khoản'],
    },
    ROLE_MANAGER: {
        'label': 'Quản lý',
        'icon': 'fa-user-tie',
        'color': '#2563EB',
        'desc': 'Quản lý nội dung, video, chiến dịch và sản phẩm thương mại.',
        'features': ['Thêm/sửa/xóa video', 'Quản lý chiến dịch', 'Quản lý sản phẩm', 'Xem phân tích'],
    },
    ROLE_VIEWER: {
        'label': 'Người xem',
        'icon': 'fa-eye',
        'color': '#10B981',
        'desc': 'Xem báo cáo, thống kê và phân tích hiệu quả video.',
        'features': ['Xem dashboard', 'Xem báo cáo', 'Xem phân tích', 'Xuất dữ liệu'],
    },
}

VIDEO_DRAFT     = 'draft'
VIDEO_PUBLISHED = 'published'
VIDEO_ARCHIVED  = 'archived'
VIDEO_STATUSES  = [(VIDEO_DRAFT, 'Bản nháp'), (VIDEO_PUBLISHED, 'Đã đăng'), (VIDEO_ARCHIVED, 'Lưu trữ')]

CAMPAIGN_PLANNED = 'planned'
CAMPAIGN_RUNNING = 'running'
CAMPAIGN_ENDED   = 'ended'
CAMPAIGN_STATUSES = [(CAMPAIGN_PLANNED, 'Lên kế hoạch'), (CAMPAIGN_RUNNING, 'Đang chạy'), (CAMPAIGN_ENDED, 'Kết thúc')]


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(150), nullable=False)
    role          = db.Column(db.String(20),  nullable=False, default=ROLE_VIEWER)
    phone         = db.Column(db.String(20))
    avatar        = db.Column(db.String(255))
    status        = db.Column(db.String(20),  default='active')
    # Bao mat & xac thuc
    is_verified       = db.Column(db.Boolean, default=False)
    verify_token      = db.Column(db.String(64), unique=True)
    reset_token       = db.Column(db.String(64), unique=True)
    reset_token_exp   = db.Column(db.DateTime)
    login_attempts    = db.Column(db.Integer, default=0)
    locked_until      = db.Column(db.DateTime)
    last_login        = db.Column(db.DateTime)
    last_ip           = db.Column(db.String(45))
    # Duyet tai khoan
    approved_by       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at       = db.Column(db.DateTime, nullable=True)
    reject_reason     = db.Column(db.String(255), nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    videos = db.relationship('Video', backref='creator', lazy='dynamic')

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def is_admin(self):    return self.role == ROLE_ADMIN
    def is_manager(self):  return self.role in (ROLE_ADMIN, ROLE_MANAGER)

    def generate_verify_token(self):
        self.verify_token = secrets.token_urlsafe(32)
        return self.verify_token

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        from datetime import timedelta
        self.reset_token_exp = datetime.utcnow() + timedelta(hours=1)
        return self.reset_token

    def is_locked(self):
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    @property
    def role_name(self): return dict(ROLES).get(self.role, self.role)

    def to_dict(self):
        return {
            'id': self.id, 'username': self.username, 'email': self.email,
            'full_name': self.full_name, 'role': self.role, 'role_name': self.role_name,
            'phone': self.phone or '', 'status': self.status,
            'is_verified': self.is_verified,
            'last_login': self.last_login.strftime('%d/%m/%Y %H:%M') if self.last_login else '',
            'created_at': self.created_at.strftime('%d/%m/%Y') if self.created_at else '',
        }


# ---------------------------------------------------------------------------
# Platform
# ---------------------------------------------------------------------------
class Platform(db.Model):
    __tablename__ = 'platforms'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(80),  unique=True, nullable=False)
    icon        = db.Column(db.String(50))
    color       = db.Column(db.String(20), default='#4A90D9')
    base_url    = db.Column(db.String(255))
    description = db.Column(db.Text)
    status      = db.Column(db.String(20), default='active')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    videos = db.relationship('Video', backref='platform', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'icon': self.icon or '',
            'color': self.color, 'base_url': self.base_url or '',
            'description': self.description or '', 'status': self.status,
            'video_count': self.videos.count(),
            'total_views': db.session.query(db.func.sum(Video.views)).filter(Video.platform_id==self.id).scalar() or 0,
            'created_at': self.created_at.strftime('%d/%m/%Y') if self.created_at else '',
        }


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------
class Category(db.Model):
    __tablename__ = 'categories'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'description': self.description or '',
            'product_count': self.products.count(),
            'created_at': self.created_at.strftime('%d/%m/%Y') if self.created_at else '',
        }


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------
class Product(db.Model):
    __tablename__ = 'products'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price       = db.Column(db.Float, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    image       = db.Column(db.String(255))
    stock       = db.Column(db.Integer, default=0)
    sku         = db.Column(db.String(50))
    status      = db.Column(db.String(20), default='active')
    sold        = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    videos = db.relationship('Video', backref='product', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id, 'name': self.name, 'description': self.description or '',
            'price': self.price,
            'price_fmt': '{:,.0f} đ'.format(self.price).replace(',', '.'),
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Chưa phân loại',
            'image': self.image or '', 'stock': self.stock, 'sku': self.sku or '',
            'status': self.status, 'sold': self.sold,
            'video_count': self.videos.count(),
            'created_at': self.created_at.strftime('%d/%m/%Y') if self.created_at else '',
        }


# ---------------------------------------------------------------------------
# Campaign
# ---------------------------------------------------------------------------
class Campaign(db.Model):
    __tablename__ = 'campaigns'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_date  = db.Column(db.Date)
    end_date    = db.Column(db.Date)
    budget      = db.Column(db.Float, default=0)
    status      = db.Column(db.String(20), default=CAMPAIGN_PLANNED)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    videos = db.relationship('Video', backref='campaign', lazy='dynamic')

    @property
    def status_name(self): return dict(CAMPAIGN_STATUSES).get(self.status, self.status)

    def to_dict(self):
        total_views = db.session.query(db.func.sum(Video.views)).filter(Video.campaign_id==self.id).scalar() or 0
        total_rev   = db.session.query(db.func.sum(Video.revenue)).filter(Video.campaign_id==self.id).scalar() or 0
        return {
            'id': self.id, 'name': self.name, 'description': self.description or '',
            'start_date': self.start_date.strftime('%d/%m/%Y') if self.start_date else '',
            'end_date':   self.end_date.strftime('%d/%m/%Y')   if self.end_date   else '',
            'budget': self.budget,
            'budget_fmt': '{:,.0f} đ'.format(self.budget).replace(',', '.'),
            'status': self.status, 'status_name': self.status_name,
            'video_count': self.videos.count(),
            'total_views': total_views, 'total_revenue': total_rev,
            'created_at': self.created_at.strftime('%d/%m/%Y') if self.created_at else '',
        }


# ---------------------------------------------------------------------------
# Video
# ---------------------------------------------------------------------------
class Video(db.Model):
    __tablename__ = 'videos'
    id              = db.Column(db.Integer, primary_key=True)
    title           = db.Column(db.String(255), nullable=False)
    description     = db.Column(db.Text)
    video_url       = db.Column(db.String(500))
    thumbnail       = db.Column(db.String(255))
    duration        = db.Column(db.Integer, default=30)
    platform_id     = db.Column(db.Integer, db.ForeignKey('platforms.id'))
    product_id      = db.Column(db.Integer, db.ForeignKey('products.id'))
    campaign_id     = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'))
    views           = db.Column(db.Integer, default=0)
    likes           = db.Column(db.Integer, default=0)
    comments        = db.Column(db.Integer, default=0)
    shares          = db.Column(db.Integer, default=0)
    saves           = db.Column(db.Integer, default=0)
    ctr             = db.Column(db.Float, default=0.0)
    conversion_rate = db.Column(db.Float, default=0.0)
    revenue         = db.Column(db.Float, default=0.0)
    orders          = db.Column(db.Integer, default=0)
    status          = db.Column(db.String(20), default=VIDEO_DRAFT)
    tags            = db.Column(db.String(255))
    published_at    = db.Column(db.DateTime)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stats = db.relationship('VideoStat', backref='video', lazy='dynamic',
                            cascade='all, delete-orphan')

    @property
    def status_name(self): return dict(VIDEO_STATUSES).get(self.status, self.status)

    @property
    def engagement_rate(self):
        total = self.likes + self.comments + self.shares + self.saves
        return round(total / self.views * 100, 2) if self.views > 0 else 0.0

    @property
    def performance_score(self):
        """Tinh diem hieu qua tong hop 0-100 dua tren chi so thuc."""
        if self.views == 0:
            return 0
        eng  = self.engagement_rate                            # ty le tuong tac
        op1k = self.orders / self.views * 1000 if self.views else 0  # don/1000 views
        viral = (self.shares + self.saves) / self.views * 100 if self.views else 0

        # View score (0-30): benchmark TikTok TMDT
        if   self.views >= 1000000: vs = 30
        elif self.views >= 500000:  vs = 27
        elif self.views >= 100000:  vs = 22
        elif self.views >= 50000:   vs = 17
        elif self.views >= 10000:   vs = 12
        elif self.views >= 1000:    vs = 7
        else:                       vs = 2

        # Engagement score (0-30)
        if   eng >= 10: es = 30
        elif eng >= 7:  es = 25
        elif eng >= 5:  es = 20
        elif eng >= 3:  es = 14
        elif eng >= 1:  es = 7
        else:           es = 2

        # Commerce score (0-25)
        if   op1k >= 2:   cs = 25
        elif op1k >= 1:   cs = 20
        elif op1k >= 0.5: cs = 14
        elif op1k > 0:    cs = 7
        else:             cs = 0

        # Viral score (0-15)
        if   viral >= 5:   vrs = 15
        elif viral >= 3:   vrs = 12
        elif viral >= 1.5: vrs = 8
        elif viral >= 0.5: vrs = 4
        else:              vrs = 1

        return min(100, vs + es + cs + vrs)

    @property
    def performance_grade(self):
        """Xep loai hieu qua: Xuất sắc / Tốt / Khá / Yếu / Rất yếu."""
        s = self.performance_score
        if   s >= 85: return ('Xuất sắc', 'success',  '🏆')
        elif s >= 70: return ('Tốt',       'info',     '✅')
        elif s >= 50: return ('Khá',       'warning',  '📈')
        elif s >= 30: return ('Yếu',       'danger',   '⚠️')
        else:         return ('Rất yếu',   'secondary','❌')

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'description': self.description or '',
            'video_url': self.video_url or '', 'thumbnail': self.thumbnail or '',
            'duration': self.duration,
            'platform_id': self.platform_id,
            'platform_name': self.platform.name if self.platform else '',
            'platform_color': self.platform.color if self.platform else '#4A90D9',
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else '',
            'campaign_id': self.campaign_id,
            'campaign_name': self.campaign.name if self.campaign else '',
            'creator_name': self.creator.full_name if self.creator else '',
            'views': self.views, 'likes': self.likes, 'comments': self.comments,
            'shares': self.shares, 'saves': self.saves, 'orders': self.orders,
            'ctr': self.ctr, 'conversion_rate': self.conversion_rate,
            'revenue': self.revenue,
            'revenue_fmt': '{:,.0f} đ'.format(self.revenue).replace(',', '.'),
            'engagement_rate': self.engagement_rate,
            'status': self.status, 'status_name': self.status_name,
            'tags': self.tags or '',
            'published_at': self.published_at.strftime('%d/%m/%Y') if self.published_at else '',
            'created_at': self.created_at.strftime('%d/%m/%Y') if self.created_at else '',
        }


# ---------------------------------------------------------------------------
# VideoStat - Chi so theo ngay
# ---------------------------------------------------------------------------
class VideoStat(db.Model):
    __tablename__ = 'video_stats'
    id       = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False, index=True)
    date     = db.Column(db.Date, nullable=False, index=True)
    views    = db.Column(db.Integer, default=0)
    likes    = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares   = db.Column(db.Integer, default=0)
    saves    = db.Column(db.Integer, default=0)
    orders   = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id, 'video_id': self.video_id,
            'date': self.date.strftime('%d/%m/%Y') if self.date else '',
            'views': self.views, 'likes': self.likes, 'comments': self.comments,
            'shares': self.shares, 'saves': self.saves, 'orders': self.orders,
        }
