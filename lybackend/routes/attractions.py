from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc, or_
from models import db, Attraction, UserBrowseHistory, UserFavorite
from utils.redis_client import redis_client
from config import Config
import jieba
from collections import Counter

attractions_bp = Blueprint('attractions', __name__, url_prefix='/api/attractions')

@attractions_bp.route('/list', methods=['GET'])
def get_attractions_list():
    """获取景点列表（支持分页、搜索、筛选）"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', Config.PAGE_SIZE, type=int)
    keyword = request.args.get('keyword', '')
    city = request.args.get('city', '')
    min_score = request.args.get('min_score', 0, type=float)
    is_free = request.args.get('is_free', '')
    sort_by = request.args.get('sort_by', 'heat_score')  # heat_score, comment_score, comment_count
    
    # 构建缓存key
    cache_key = f"attractions:list:{page}:{page_size}:{keyword}:{city}:{min_score}:{is_free}:{sort_by}"
    
    # 尝试从缓存获取
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    # 构建查询
    query = Attraction.query
    
    if keyword:
        query = query.filter(
            or_(
                Attraction.poi_name.like(f'%{keyword}%'),
                Attraction.tag_list.like(f'%{keyword}%')
            )
        )
    
    if city:
        query = query.filter(Attraction.city == city)
    
    if min_score > 0:
        query = query.filter(Attraction.comment_score >= min_score)
    
    if is_free == 'true':
        query = query.filter(Attraction.is_free == True)
    
    # 排序
    if sort_by == 'comment_score':
        query = query.order_by(desc(Attraction.comment_score))
    elif sort_by == 'comment_count':
        query = query.order_by(desc(Attraction.comment_count))
    else:
        query = query.order_by(desc(Attraction.heat_score))
    
    # 分页
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    result = {
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'items': [item.to_dict() for item in pagination.items]
    }
    
    # 缓存结果
    redis_client.set(cache_key, result, expire=300)
    
    return jsonify({'code': 200, 'data': result})

@attractions_bp.route('/<poi_id>', methods=['GET'])
@jwt_required(optional=True)
def get_attraction_detail(poi_id):
    """获取景点详情（无需登录即可访问）"""
    attraction = Attraction.query.filter_by(poi_id=poi_id).first()
    
    if not attraction:
        return jsonify({'code': 404, 'message': '景点不存在'}), 404
    
    # 记录浏览历史（仅当用户已登录时）
    try:
        user_id = get_jwt_identity()
        if user_id:
            try:
                # 确保user_id是整数
                user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                history = UserBrowseHistory(user_id=user_id_int, poi_id=poi_id)
                db.session.add(history)
                db.session.commit()
            except Exception as e:
                # 如果记录历史失败，不影响主要功能
                print(f"记录浏览历史失败: {e}")
                db.session.rollback()
    except Exception:
        # Token无效或用户未登录，继续执行（这是正常的，因为optional=True）
        pass
    
    return jsonify({
        'code': 200,
        'data': attraction.to_dict()
    })

@attractions_bp.route('/cities', methods=['GET'])
def get_cities():
    """获取所有城市列表"""
    cache_key = "attractions:cities"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    cities = db.session.query(
        Attraction.city,
        func.count(Attraction.id).label('count')
    ).group_by(Attraction.city).all()
    
    result = [{'city': city, 'count': count} for city, count in cities]
    
    redis_client.set(cache_key, result, expire=3600)
    
    return jsonify({'code': 200, 'data': result})

@attractions_bp.route('/favorite', methods=['POST'])
@jwt_required()
def add_favorite():
    """添加收藏"""
    user_id = get_jwt_identity()
    data = request.get_json()
    poi_id = data.get('poi_id')
    
    if not poi_id:
        return jsonify({'code': 400, 'message': '景点ID不能为空'}), 400
    
    # 检查是否已收藏
    existing = UserFavorite.query.filter_by(user_id=user_id, poi_id=poi_id).first()
    if existing:
        return jsonify({'code': 400, 'message': '已收藏该景点'}), 400
    
    favorite = UserFavorite(user_id=user_id, poi_id=poi_id)
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '收藏成功'})

@attractions_bp.route('/favorite/<poi_id>', methods=['DELETE'])
@jwt_required()
def remove_favorite(poi_id):
    """取消收藏"""
    user_id = get_jwt_identity()
    
    favorite = UserFavorite.query.filter_by(user_id=user_id, poi_id=poi_id).first()
    if not favorite:
        return jsonify({'code': 404, 'message': '未收藏该景点'}), 404
    
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({'code': 200, 'message': '取消收藏成功'})

@attractions_bp.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    """获取用户收藏列表"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', Config.PAGE_SIZE, type=int)
    
    favorites = UserFavorite.query.filter_by(user_id=user_id).all()
    poi_ids = [f.poi_id for f in favorites]
    
    query = Attraction.query.filter(Attraction.poi_id.in_(poi_ids))
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    
    result = {
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'items': [item.to_dict() for item in pagination.items]
    }
    
    return jsonify({'code': 200, 'data': result})

@attractions_bp.route('/history', methods=['GET'])
@jwt_required()
def get_browse_history():
    """获取浏览历史"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', Config.PAGE_SIZE, type=int)
    
    # 获取最近的浏览记录（去重）
    subquery = db.session.query(
        UserBrowseHistory.poi_id,
        func.max(UserBrowseHistory.browse_time).label('latest_time')
    ).filter_by(user_id=user_id).group_by(UserBrowseHistory.poi_id).subquery()
    
    history_query = db.session.query(Attraction).join(
        subquery, Attraction.poi_id == subquery.c.poi_id
    ).order_by(desc(subquery.c.latest_time))
    
    pagination = history_query.paginate(page=page, per_page=page_size, error_out=False)
    
    result = {
        'total': pagination.total,
        'page': page,
        'page_size': page_size,
        'items': [item.to_dict() for item in pagination.items]
    }
    
    return jsonify({'code': 200, 'data': result})
