"""
config.py - Cau hinh ung dung Flask
SYS VidMetric - Cong ty SYS Viet Nam
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Database: dung PostgreSQL tren Render, SQLite o local
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        'sqlite:///' + os.path.join(BASE_DIR, 'sys_video.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get('SECRET_KEY', 'sys-vidmetric-2026-secret')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    PER_PAGE = 10
    COMPANY_NAME = 'SYS VidMetric'
    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
