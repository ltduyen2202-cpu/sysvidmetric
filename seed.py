"""
seed.py - Tao du lieu mau cho co so du lieu
Chay: python seed.py
"""
from datetime import date, datetime, timedelta
import random

try:
    from app import app
except ImportError:
    app = None

from model import (db, User, Platform, Category, Product,
                   Campaign, Video, VideoStat,
                   VIDEO_PUBLISHED, VIDEO_ARCHIVED, VIDEO_DRAFT,
                   CAMPAIGN_PLANNED, CAMPAIGN_RUNNING, CAMPAIGN_ENDED)

def seed(flask_app=None):
    _app = flask_app or app
    with _app.app_context():
        db.create_all()

        # ---- Users ----
        # Tai khoan quan tri chinh - Ly Thi Duyen
        owner = User(username='0868648311', email='admin@sysvietnam.com',
                     full_name='Lý Thị Duyên', role='admin',
                     phone='0868648311', status='active', is_verified=True)
        owner.set_password('Duyen@2005')

        manager = User(username='manager1', email='manager1@sysvn.com',
                       full_name='Trần Thị Lan', role='manager',
                       phone='0912345678', status='active', is_verified=True)
        manager.set_password('manager123')

        viewer = User(username='viewer1', email='viewer1@sysvn.com',
                      full_name='Lê Minh Tú', role='viewer',
                      phone='0923456789', status='active', is_verified=True)
        viewer.set_password('viewer123')

        db.session.add_all([owner, manager, viewer])
        db.session.commit()

        # ---- Platforms ----
        platforms_data = [
            ('TikTok',          'tiktok',   '#010101', 'https://tiktok.com'),
            ('YouTube Shorts',  'youtube',  '#FF0000', 'https://youtube.com/shorts'),
            ('Facebook Reels',  'facebook', '#1877F2', 'https://facebook.com/reels'),
            ('Instagram Reels', 'instagram','#E4405F', 'https://instagram.com/reels'),
            ('Shopee Video',    'shopee',   '#EE4D2D', 'https://shopee.vn'),
        ]
        platforms = []
        for name, icon, color, url in platforms_data:
            p = Platform(name=name, icon=icon, color=color, base_url=url,
                         description=f'Nền tảng video ngắn {name}')
            db.session.add(p)
            platforms.append(p)
        db.session.commit()

        # ---- Categories ----
        cats_data = ['Thời trang', 'Mỹ phẩm & Làm đẹp', 'Điện tử & Phụ kiện',
                     'Thực phẩm & Đồ uống', 'Gia dụng', 'Thể thao']
        categories = []
        for n in cats_data:
            c = Category(name=n, description=f'Danh mục sản phẩm {n}')
            db.session.add(c)
            categories.append(c)
        db.session.commit()

        # ---- Products ----
        products_data = [
            ('Áo thun basic unisex', 199000, 0, 'SKU001', 350),
            ('Quần jean slim fit',   489000, 0, 'SKU002', 210),
            ('Son môi lì matte',     250000, 1, 'SKU003', 580),
            ('Kem dưỡng da ban đêm', 320000, 1, 'SKU004', 420),
            ('Tai nghe bluetooth',  599000, 2, 'SKU005', 190),
            ('Ốp lưng điện thoại',   89000, 2, 'SKU006', 760),
            ('Trà sữa đóng gói',     45000, 3, 'SKU007', 920),
            ('Cà phê rang xay',      85000, 3, 'SKU008', 440),
            ('Nồi chiên không dầu', 890000, 4, 'SKU009', 130),
            ('Đèn tích điện',       150000, 4, 'SKU010', 310),
            ('Bình nước gym 1L',     95000, 5, 'SKU011', 540),
            ('Băng đeo cổ tay',      55000, 5, 'SKU012', 680),
        ]
        products = []
        for name, price, cat_idx, sku, sold in products_data:
            pr = Product(name=name, price=price, category_id=categories[cat_idx].id,
                         sku=sku, stock=random.randint(50, 500),
                         sold=sold, status='active',
                         description=f'Sản phẩm chất lượng cao - {name}')
            db.session.add(pr)
            products.append(pr)
        db.session.commit()

        # ---- Campaigns ----
        campaigns_data = [
            ('Tết Nguyên Đán 2026',       CAMPAIGN_ENDED,   date(2026,1,15), date(2026,2,10), 50000000),
            ('Valentine 2026',             CAMPAIGN_ENDED,   date(2026,2,1),  date(2026,2,15), 20000000),
            ('Sale 8/3 Phụ nữ',           CAMPAIGN_ENDED,   date(2026,3,1),  date(2026,3,10), 30000000),
            ('Flash Sale Tháng 4',         CAMPAIGN_RUNNING, date(2026,4,1),  date(2026,4,30), 40000000),
            ('Ra mắt sản phẩm mới Q2',    CAMPAIGN_RUNNING, date(2026,5,1),  date(2026,5,31), 25000000),
            ('Sale hè Tháng 6',           CAMPAIGN_PLANNED, date(2026,6,1),  date(2026,6,30), 35000000),
        ]
        campaigns = []
        for name, st, sd, ed, budget in campaigns_data:
            c = Campaign(name=name, status=st, start_date=sd, end_date=ed,
                         budget=budget, description=f'Chiến dịch {name}')
            db.session.add(c)
            campaigns.append(c)
        db.session.commit()

        # ---- Videos ----
        video_titles = [
            'Review áo thun basic hot nhất 2026',
            'Combo outfit đi làm siêu xinh',
            'Son lì 24h không lem - test thực tế',
            'Routine dưỡng da buổi tối chuẩn Hàn',
            'Tai nghe bluetooth dưới 600k nghe tốt',
            'Ốp lưng trendy cho iPhone 15',
            'Trà sữa tự làm tại nhà 15 phút',
            'Cà phê sáng thơm ngon dễ pha',
            'Nồi chiên không dầu - gà giòn 10 phút',
            'Đèn tích điện - giải pháp mất điện',
            'Bình nước gym đẹp bền giá rẻ',
            'Băng cổ tay tập gym đúng cách',
            'Haul thời trang Tết siêu rẻ',
            'Valentine makeup look nhẹ nhàng',
            'Quà 8/3 ý nghĩa cho mẹ và chị',
            'Flash sale 4/4 - đừng bỏ lỡ',
            'Unboxing sản phẩm mới về kho',
            'TOP 5 sản phẩm bán chạy tháng 5',
            'Combo skincare dưới 500k',
            'Outfit đi biển mùa hè 2026',
        ]

        videos = []
        users_list = [owner, manager, viewer]
        status_pool = ([VIDEO_PUBLISHED]*14 + [VIDEO_ARCHIVED]*4 + [VIDEO_DRAFT]*2)

        for i, title in enumerate(video_titles):
            plat = platforms[i % len(platforms)]
            prod = products[i % len(products)]
            camp = campaigns[i % len(campaigns)]
            user = users_list[i % len(users_list)]

            vw = random.randint(5000, 80000)
            lk = int(vw * random.uniform(0.03, 0.12))
            cm = int(vw * random.uniform(0.005, 0.03))
            sh = int(vw * random.uniform(0.01, 0.05))
            sv = int(vw * random.uniform(0.01, 0.04))
            ord_count = int(vw * random.uniform(0.001, 0.008))
            ctr_val  = round(random.uniform(2.5, 12.0), 2)
            conv_val = round(random.uniform(0.5, 5.0),  2)
            rev_val  = ord_count * prod.price

            st = status_pool[i]
            pub = datetime.utcnow() - timedelta(days=random.randint(5, 120)) if st != VIDEO_DRAFT else None

            v = Video(
                title=title, platform_id=plat.id, product_id=prod.id,
                campaign_id=camp.id, user_id=user.id,
                views=vw, likes=lk, comments=cm, shares=sh, saves=sv,
                orders=ord_count, ctr=ctr_val, conversion_rate=conv_val,
                revenue=rev_val, duration=random.randint(15, 60),
                status=st, published_at=pub,
                description=f'Video quảng bá sản phẩm {prod.name} trên {plat.name}',
                tags=f'viral,trending,{prod.name.split()[0].lower()},sysvietnam',
                video_url=f'https://{plat.name.split()[0].lower()}.com/watch?v=demo{i+1}',
            )
            db.session.add(v)
            videos.append(v)
        db.session.commit()

        # ---- VideoStats (30 ngay gan nhat cho moi video da dang) ----
        today = date.today()
        for v in videos:
            if v.status == VIDEO_PUBLISHED:
                for d in range(29, -1, -1):
                    day = today - timedelta(days=d)
                    factor = random.uniform(0.5, 1.5)
                    daily_views = max(10, int(v.views / 30 * factor))
                    stat = VideoStat(
                        video_id=v.id, date=day,
                        views=daily_views,
                        likes=max(1, int(v.likes / 30 * factor)),
                        comments=max(0, int(v.comments / 30 * factor)),
                        shares=max(0, int(v.shares / 30 * factor)),
                        saves=max(0, int(v.saves / 30 * factor)),
                        orders=max(0, int(v.orders / 30 * factor)),
                    )
                    db.session.add(stat)
        db.session.commit()

        print("=== Seed hoan thanh! ===")
        print(f"Users    : {User.query.count()}")
        print(f"Platforms: {Platform.query.count()}")
        print(f"Products : {Product.query.count()}")
        print(f"Campaigns: {Campaign.query.count()}")
        print(f"Videos   : {Video.query.count()}")
        print(f"Stats    : {VideoStat.query.count()}")
        print("\nTai khoan chinh (Quan tri vien):")
        print("  0868648311 / Duyen@2005  -> Quan tri vien chinh")
        print("\nTai khoan phu (demo):")
        print("  manager1 / manager123    -> Quan ly")
        print("  viewer1  / viewer123     -> Nguoi xem")


if __name__ == '__main__':
    from app import app as flask_app
    seed(flask_app)
