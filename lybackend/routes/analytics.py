from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc, case
from models import db, Attraction
from utils.redis_client import redis_client
import jieba
from collections import Counter
from io import BytesIO
import base64

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@analytics_bp.route('/score-distribution', methods=['GET'])
def get_score_distribution():
    """评分情况分析"""
    cache_key = "analytics:score_distribution"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    # 评分区间统计
    score_ranges = [
        ('0-2分', 0, 2),
        ('2-3分', 2, 3),
        ('3-4分', 3, 4),
        ('4-4.5分', 4, 4.5),
        ('4.5-5分', 4.5, 5)
    ]
    
    distribution = []
    for label, min_score, max_score in score_ranges:
        count = Attraction.query.filter(
            Attraction.comment_score >= min_score,
            Attraction.comment_score < max_score
        ).count()
        distribution.append({'range': label, 'count': count})
    
    # 平均评分
    avg_score = db.session.query(func.avg(Attraction.comment_score)).scalar() or 0
    
    # 评分最高的景点
    top_attractions = Attraction.query.order_by(
        desc(Attraction.comment_score)
    ).limit(10).all()
    
    result = {
        'distribution': distribution,
        'avg_score': round(float(avg_score), 2),
        'top_attractions': [
            {
                'poi_name': a.poi_name,
                'comment_score': float(a.comment_score),
                'city': a.city
            } for a in top_attractions
        ]
    }
    
    redis_client.set(cache_key, result, expire=1800)
    
    return jsonify({'code': 200, 'data': result})

@analytics_bp.route('/city-analysis', methods=['GET'])
def get_city_analysis():
    """城市和景点等级分析"""
    cache_key = "analytics:city_analysis"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    # 按城市统计景点数量和平均评分
    city_stats = db.session.query(
        Attraction.city,
        func.count(Attraction.id).label('count'),
        func.avg(Attraction.comment_score).label('avg_score'),
        func.avg(Attraction.heat_score).label('avg_heat')
    ).group_by(Attraction.city).all()
    
    city_data = [
        {
            'city': city,
            'count': count,
            'avg_score': round(float(avg_score or 0), 2),
            'avg_heat': round(float(avg_heat or 0), 2)
        } for city, count, avg_score, avg_heat in city_stats
    ]
    
    # 按评分排序
    city_data_sorted = sorted(city_data, key=lambda x: x['avg_score'], reverse=True)
    
    # 景点等级分析（基于评分）
    level_stats = [
        {
            'level': '5A级（4.5分以上）',
            'count': Attraction.query.filter(Attraction.comment_score >= 4.5).count()
        },
        {
            'level': '4A级（4-4.5分）',
            'count': Attraction.query.filter(
                Attraction.comment_score >= 4,
                Attraction.comment_score < 4.5
            ).count()
        },
        {
            'level': '3A级（3-4分）',
            'count': Attraction.query.filter(
                Attraction.comment_score >= 3,
                Attraction.comment_score < 4
            ).count()
        },
        {
            'level': '其他（3分以下）',
            'count': Attraction.query.filter(Attraction.comment_score < 3).count()
        }
    ]
    
    result = {
        'city_data': city_data_sorted[:20],  # 返回前20个城市
        'level_stats': level_stats
    }
    
    redis_client.set(cache_key, result, expire=1800)
    
    return jsonify({'code': 200, 'data': result})

@analytics_bp.route('/price-sales-analysis', methods=['GET'])
def get_price_sales_analysis():
    """价格销量分析"""
    cache_key = "analytics:price_sales"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    # 免费vs收费景点统计
    free_count = Attraction.query.filter(Attraction.is_free == True).count()
    paid_count = Attraction.query.filter(Attraction.is_free == False).count()
    
    # 价格区间统计（收费景点）
    price_ranges = [
        ('0-50元', 0, 50),
        ('50-100元', 50, 100),
        ('100-200元', 100, 200),
        ('200-500元', 200, 500),
        ('500元以上', 500, 10000)
    ]
    
    price_distribution = []
    for label, min_price, max_price in price_ranges:
        count = Attraction.query.filter(
            Attraction.market_price >= min_price,
            Attraction.market_price < max_price
        ).count()
        price_distribution.append({'range': label, 'count': count})
    
    # 评论数最多的景点（代表热度/销量）
    hot_attractions = Attraction.query.order_by(
        desc(Attraction.comment_count)
    ).limit(20).all()
    
    # 价格与评分关系
    price_score_relation = db.session.query(
        case(
            (Attraction.is_free == True, '免费'),
            (Attraction.market_price < 50, '0-50元'),
            (Attraction.market_price < 100, '50-100元'),
            (Attraction.market_price < 200, '100-200元'),
            else_='200元以上'
        ).label('price_range'),
        func.avg(Attraction.comment_score).label('avg_score'),
        func.count(Attraction.id).label('count')
    ).group_by('price_range').all()
    
    result = {
        'free_vs_paid': {
            'free': free_count,
            'paid': paid_count
        },
        'price_distribution': price_distribution,
        'hot_attractions': [
            {
                'poi_name': a.poi_name,
                'comment_count': a.comment_count,
                'price': a.price,
                'city': a.city
            } for a in hot_attractions
        ],
        'price_score_relation': [
            {
                'price_range': pr,
                'avg_score': round(float(avg_score or 0), 2),
                'count': count
            } for pr, avg_score, count in price_score_relation
        ]
    }
    
    redis_client.set(cache_key, result, expire=1800)
    
    return jsonify({'code': 200, 'data': result})

@analytics_bp.route('/tag-analysis', methods=['GET'])
def get_tag_analysis():
    """标签分析（词云数据）"""
    cache_key = "analytics:tag_analysis"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    # 获取所有标签
    attractions = Attraction.query.all()
    all_tags = []
    
    for attraction in attractions:
        if attraction.tag_list:
            tags = attraction.tag_list.split(',')
            all_tags.extend([tag.strip() for tag in tags if tag.strip()])
    
    # 统计标签频率
    tag_counter = Counter(all_tags)
    top_tags = tag_counter.most_common(100)
    
    # 格式化为词云数据
    wordcloud_data = [
        {'name': tag, 'value': count}
        for tag, count in top_tags
    ]
    
    result = {
        'wordcloud_data': wordcloud_data,
        'total_tags': len(all_tags),
        'unique_tags': len(tag_counter)
    }
    
    redis_client.set(cache_key, result, expire=1800)
    
    return jsonify({'code': 200, 'data': result})

@analytics_bp.route('/overview', methods=['GET'])
def get_overview():
    """数据概览"""
    cache_key = "analytics:overview"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    total_attractions = Attraction.query.count()
    total_cities = db.session.query(func.count(func.distinct(Attraction.city))).scalar()
    avg_score = db.session.query(func.avg(Attraction.comment_score)).scalar() or 0
    total_comments = db.session.query(func.sum(Attraction.comment_count)).scalar() or 0
    
    result = {
        'total_attractions': total_attractions,
        'total_cities': total_cities,
        'avg_score': round(float(avg_score), 2),
        'total_comments': int(total_comments)
    }
    
    redis_client.set(cache_key, result, expire=600)
    
    return jsonify({'code': 200, 'data': result})
