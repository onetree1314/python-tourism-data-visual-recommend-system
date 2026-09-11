from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models import db
from routes.auth import auth_bp
from routes.attractions import attractions_bp
from routes.analytics import analytics_bp
from routes.recommendation import recommendation_bp
from routes.admin import admin_bp
from routes.media import media_bp
# from routes.upload import upload_bp  # 暂时禁用MinIO上传功能
from utils.spider_scheduler import init_scheduler
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
import os

def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    CORS(app, resources={r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }})
    db.init_app(app)
    jwt = JWTManager(app)
    
    # JWT错误处理 - 必须在注册蓝图之前
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'code': 401, 'message': 'Token已过期'}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        # 对于optional=True的路由，无效token不应该阻止访问
        # 检查请求路径，如果是可选认证的路由，允许继续
        from flask import request
        optional_routes = ['/api/attractions/', '/api/analytics/', '/api/recommendation/hot']
        path = request.path if hasattr(request, 'path') else ''
        if any(path.startswith(route) for route in optional_routes):
            # 对于可选认证的路由，返回None让路由继续执行（不验证token）
            return None
        # 对于必需认证的路由，返回401
        return jsonify({'code': 401, 'message': 'Token无效，请重新登录'}), 401
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({'code': 401, 'message': '未授权访问'}), 401
    
    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(attractions_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(media_bp)
    # app.register_blueprint(upload_bp)  # 暂时禁用
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'code': 404, 'message': '资源不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'code': 500, 'message': '服务器内部错误'}), 500
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        # 处理422错误（通常是JWT验证失败，如Subject must be a string）
        # 检查请求路径，如果是可选认证的路由，允许继续访问
        from flask import request
        optional_routes = ['/api/attractions/', '/api/analytics/', '/api/recommendation/hot']
        path = request.path if hasattr(request, 'path') else ''
        if any(path.startswith(route) for route in optional_routes):
            # 对于可选认证的路由，返回200允许继续访问
            # 注意：这不会真正执行路由，需要让JWT装饰器处理
            # 更好的方法是修复token问题，或者让invalid_token_loader处理
            pass
        # 默认返回422，让调用方知道token有问题
        return jsonify({'code': 422, 'message': 'Token格式错误，请清除后重试'}), 422
    
    # 健康检查
    @app.route('/api/health')
    def health_check():
        return jsonify({'code': 200, 'message': 'OK'})
    
    # 初始化爬虫调度器
    scheduler_instance = init_scheduler(app)
    
    # 配置定时任务
    scheduler = BackgroundScheduler()
    
    def run_spider_task():
        """运行爬虫任务"""
        with app.app_context():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(scheduler_instance.crawl_random_data())
            loop.close()
    
    # 每5分钟执行一次爬虫任务
    scheduler.add_job(
        func=run_spider_task,
        trigger='interval',
        minutes=Config.SPIDER_INTERVAL_MINUTES,
        id='spider_task',
        max_instances=1
    )
    
    # 启动调度器
    scheduler.start()
    
    # 检查数据库是否有数据，如果没有才进行首次爬取
    with app.app_context():
        from models import Attraction
        attraction_count = Attraction.query.count()
        if attraction_count == 0:
            print("\n" + "=" * 60)
            print("检测到数据库为空，开始首次数据初始化...")
            print("这将随机选择16个城市，每个城市爬取15页数据")
            print("预计需要5-10分钟，请耐心等待...")
            print("=" * 60 + "\n")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(scheduler_instance.initial_crawl())
            loop.close()
        else:
            print(f"\n数据库已有 {attraction_count} 条景点数据，跳过首次爬取")
            print("定时任务将每5分钟随机爬取30条数据（每天最多20次）\n")
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
