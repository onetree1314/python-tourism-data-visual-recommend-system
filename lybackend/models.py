from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Attraction(db.Model):
    """景点模型"""
    __tablename__ = 'attractions'
    
    id = db.Column(db.Integer, primary_key=True)
    poi_id = db.Column(db.String(50), unique=True, nullable=False)
    zone_name = db.Column(db.String(100))
    poi_name = db.Column(db.String(200), nullable=False)
    comment_count = db.Column(db.Integer, default=0)
    comment_score = db.Column(db.Numeric(3, 1), default=0)
    is_advertisement = db.Column(db.Boolean, default=False)
    is_recommend = db.Column(db.Boolean, default=False)
    district_name = db.Column(db.String(100))
    cover_image_url = db.Column(db.Text)
    distance_str = db.Column(db.String(50))
    tag_list = db.Column(db.Text)
    detail_url = db.Column(db.Text)
    market_price = db.Column(db.Numeric(10, 2))
    preferential_price = db.Column(db.Numeric(10, 2))
    preferential_desc = db.Column(db.String(200))
    price = db.Column(db.String(50))
    price_type = db.Column(db.String(50))
    price_type_desc = db.Column(db.String(100))
    is_free = db.Column(db.Boolean, default=False)
    latitude = db.Column(db.Numeric(10, 6))
    longitude = db.Column(db.Numeric(10, 6))
    heat_score = db.Column(db.Integer, default=0)
    city = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'poi_id': self.poi_id,
            'zone_name': self.zone_name,
            'poi_name': self.poi_name,
            'comment_count': self.comment_count,
            'comment_score': float(self.comment_score) if self.comment_score else 0,
            'is_advertisement': self.is_advertisement,
            'is_recommend': self.is_recommend,
            'district_name': self.district_name,
            'cover_image_url': self.cover_image_url,
            'distance_str': self.distance_str,
            'tag_list': self.tag_list,
            'detail_url': self.detail_url,
            'market_price': float(self.market_price) if self.market_price else 0,
            'preferential_price': float(self.preferential_price) if self.preferential_price else 0,
            'preferential_desc': self.preferential_desc,
            'price': self.price,
            'price_type': self.price_type,
            'price_type_desc': self.price_type_desc,
            'is_free': self.is_free,
            'latitude': float(self.latitude) if self.latitude else 0,
            'longitude': float(self.longitude) if self.longitude else 0,
            'heat_score': self.heat_score,
            'city': self.city
        }

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100))
    role = db.Column(db.Enum('admin', 'user'), default='user')
    avatar = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)
    status = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'avatar': self.avatar,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'status': self.status
        }

class UserBrowseHistory(db.Model):
    """用户浏览历史"""
    __tablename__ = 'user_browse_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    poi_id = db.Column(db.String(50), nullable=False)
    browse_time = db.Column(db.DateTime, default=datetime.now)

class UserFavorite(db.Model):
    """用户收藏"""
    __tablename__ = 'user_favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    poi_id = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class SpiderTask(db.Model):
    """爬虫任务记录"""
    __tablename__ = 'spider_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50), nullable=False)
    page_num = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('pending', 'success', 'failed'), default='pending')
    crawl_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class SystemLog(db.Model):
    """系统日志"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(100))
    ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)
