from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Attraction, SystemLog, SpiderTask
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(fn):
    """管理员权限装饰器"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        try:
            user_id = get_jwt_identity()
            if not user_id:
                return jsonify({'code': 401, 'message': '未授权访问'}), 401
            user = User.query.get(int(user_id))
            if not user or user.role != 'admin':
                return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'code': 500, 'message': f'服务器错误: {str(e)}'}), 500
    return wrapper

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    
    query = User.query
    
    if keyword:
        query = query.filter(
            (User.username.like(f'%{keyword}%')) |
            (User.email.like(f'%{keyword}%'))
        )
    
    pagination = query.order_by(desc(User.created_at)).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    result = {
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'items': [user.to_dict() for user in pagination.items]
    }
    
    return jsonify({'code': 200, 'data': result})

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户信息"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    data = request.get_json()
    
    if 'status' in data:
        user.status = data['status']
    if 'role' in data:
        user.role = data['role']
    if 'email' in data:
        user.email = data['email']
    
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '更新成功', 'data': user.to_dict()})

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    if user.role == 'admin':
        return jsonify({'code': 400, 'message': '不能删除管理员账户'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '删除成功'})

@admin_bp.route('/attractions', methods=['GET'])
@admin_required
def get_attractions_admin():
    """管理员获取景点列表"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    keyword = request.args.get('keyword', '')
    
    query = Attraction.query
    
    if keyword:
        query = query.filter(Attraction.poi_name.like(f'%{keyword}%'))
    
    pagination = query.order_by(desc(Attraction.created_at)).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    result = {
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'items': [item.to_dict() for item in pagination.items]
    }
    
    return jsonify({'code': 200, 'data': result})

@admin_bp.route('/attractions/<int:attraction_id>', methods=['DELETE'])
@admin_required
def delete_attraction(attraction_id):
    """删除景点"""
    attraction = Attraction.query.get(attraction_id)
    if not attraction:
        return jsonify({'code': 404, 'message': '景点不存在'}), 404
    
    db.session.delete(attraction)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '删除成功'})

@admin_bp.route('/spider-tasks', methods=['GET'])
@admin_required
def get_spider_tasks():
    """获取爬虫任务记录"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    pagination = SpiderTask.query.order_by(desc(SpiderTask.created_at)).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    result = {
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'items': [
            {
                'id': task.id,
                'city': task.city,
                'page_num': task.page_num,
                'status': task.status,
                'crawl_date': task.crawl_date.strftime('%Y-%m-%d'),
                'created_at': task.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for task in pagination.items
        ]
    }
    
    return jsonify({'code': 200, 'data': result})

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_system_logs():
    """获取系统日志"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    
    pagination = SystemLog.query.order_by(desc(SystemLog.created_at)).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    result = {
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'items': [
            {
                'id': log.id,
                'user_id': log.user_id,
                'action': log.action,
                'ip': log.ip,
                'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for log in pagination.items
        ]
    }
    
    return jsonify({'code': 200, 'data': result})

@admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """获取系统统计数据"""
    # 用户统计
    total_users = User.query.count()
    active_users = User.query.filter_by(status=True).count()
    
    # 景点统计
    total_attractions = Attraction.query.count()
    
    # 今日新增
    today = datetime.now().date()
    today_users = User.query.filter(
        func.date(User.created_at) == today
    ).count()
    today_attractions = Attraction.query.filter(
        func.date(Attraction.created_at) == today
    ).count()
    
    # 最近7天登录趋势
    seven_days_ago = datetime.now() - timedelta(days=7)
    login_trend = db.session.query(
        func.date(SystemLog.created_at).label('date'),
        func.count(SystemLog.id).label('count')
    ).filter(
        SystemLog.action == 'login',
        SystemLog.created_at >= seven_days_ago
    ).group_by(func.date(SystemLog.created_at)).all()
    
    result = {
        'total_users': total_users,
        'active_users': active_users,
        'total_attractions': total_attractions,
        'today_users': today_users,
        'today_attractions': today_attractions,
        'login_trend': [
            {
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            } for date, count in login_trend
        ]
    }
    
    return jsonify({'code': 200, 'data': result})

@admin_bp.route('/province-statistics', methods=['GET'])
@admin_required
def get_province_statistics():
    """获取省份景点统计数据（用于地图可视化）"""
    # 省份名称映射（将城市名映射到省份）
    province_mapping = {
        '北京市': '北京', '上海市': '上海', '重庆市': '重庆', '天津市': '天津',
        '广东省': '广东', '浙江省': '浙江', '江苏省': '江苏', '四川省': '四川',
        '湖北省': '湖北', '湖南省': '湖南', '河北省': '河北', '山西省': '山西',
        '辽宁省': '辽宁', '吉林省': '吉林', '黑龙江省': '黑龙江', '安徽省': '安徽',
        '福建省': '福建', '江西省': '江西', '山东省': '山东', '河南省': '河南',
        '海南省': '海南', '贵州省': '贵州', '云南省': '云南', '陕西省': '陕西',
        '甘肃省': '甘肃', '青海省': '青海', '台湾省': '台湾',
        '内蒙古自治区': '内蒙古', '广西壮族自治区': '广西', '西藏自治区': '西藏',
        '宁夏回族自治区': '宁夏', '新疆维吾尔自治区': '新疆',
        '香港特别行政区': '香港', '澳门特别行政区': '澳门'
    }
    
    # 按城市统计景点数量
    city_stats = db.session.query(
        Attraction.city,
        func.count(Attraction.id).label('count')
    ).group_by(Attraction.city).all()
    
    # 将城市数据聚合到省份
    province_data = {}
    for city, count in city_stats:
        # 尝试从映射中获取省份名，如果没有则使用城市名
        province = province_mapping.get(city, city)
        if province not in province_data:
            province_data[province] = 0
        province_data[province] += count
    
    # ECharts地图使用的标准省份名称（需要与地图JSON中的名称完全匹配）
    # 标准名称映射（确保与地图数据一致）
    standard_names = {
        '北京': '北京', '上海': '上海', '重庆': '重庆', '天津': '天津',
        '广东': '广东', '浙江': '浙江', '江苏': '江苏', '四川': '四川',
        '湖北': '湖北', '湖南': '湖南', '河北': '河北', '山西': '山西',
        '辽宁': '辽宁', '吉林': '吉林', '黑龙江': '黑龙江', '安徽': '安徽',
        '福建': '福建', '江西': '江西', '山东': '山东', '河南': '河南',
        '海南': '海南', '贵州': '贵州', '云南': '云南', '陕西': '陕西',
        '甘肃': '甘肃', '青海': '青海', '台湾': '台湾',
        '内蒙古': '内蒙古', '广西': '广西', '西藏': '西藏',
        '宁夏': '宁夏', '新疆': '新疆',
        '香港': '香港', '澳门': '澳门'
    }
    
    # 转换为列表格式，用于ECharts地图
    result = []
    for province, count in province_data.items():
        # 使用标准名称（如果存在），否则使用原名称
        standard_name = standard_names.get(province, province)
        result.append({
            'name': standard_name,
            'value': count
        })
    
    # 添加调试信息
    print(f"省份统计数据: 共{len(result)}个省份")
    for item in result[:5]:  # 打印前5个
        print(f"  {item['name']}: {item['value']}个景点")
    
    return jsonify({'code': 200, 'data': result})