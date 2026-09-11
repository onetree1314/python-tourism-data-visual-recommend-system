import os
from datetime import timedelta

class Config:
    """配置类"""
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tourism-system-secret-key-2024'
    
    # MySQL数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '123456'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'tourism_system'
    
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or 'localhost'
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or None
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # AI API配置
    DEEPSEEK_API_KEY = 'your-api-key-here'
    DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
    
    BIGMODEL_API_KEY = 'your-api-key-here'
    BIGMODEL_BASE_URL = 'https://open.bigmodel.cn/api/paas/v4'
    
    # 爬虫配置
    SPIDER_MAX_DAILY_TASKS = 20  # 每天最多爬取20次
    SPIDER_INTERVAL_MINUTES = 5  # 每5分钟执行一次
    SPIDER_BATCH_SIZE = 30  # 每次随机爬取30条
    SPIDER_INITIAL_CITIES = 16  # 首次随机选择16个城市
    SPIDER_PAGES_PER_CITY = 15  # 每个城市爬取15页
    
    # MinIO配置
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT') or '127.0.0.1:9002'
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY') or 'hushuyuan'
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY') or 'hsy@20040124'
    MINIO_BUCKET = os.environ.get('MINIO_BUCKET') or 'tourism-images'
    MINIO_SECURE = False  # HTTP
    
    # 对外可访问的后端根地址（用于生成永不过期的图片/媒体 URL，指向 /api/media/... 代理）
    # 部署到公网时请改为实际域名，如 https://api.example.com
    PUBLIC_API_BASE_URL = os.environ.get('PUBLIC_API_BASE_URL') or 'http://127.0.0.1:5000'
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 分页配置
    PAGE_SIZE = 20
