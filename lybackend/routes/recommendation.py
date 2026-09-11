from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Attraction, UserBrowseHistory, UserFavorite
from utils.ai_service import ai_service
from utils.redis_client import redis_client
from sqlalchemy import func, desc, or_, and_
import json

recommendation_bp = Blueprint('recommendation', __name__, url_prefix='/api/recommendation')

@recommendation_bp.route('/intelligent', methods=['POST'])
@jwt_required()
def get_intelligent_recommendation():
    """智能推荐（基于DeepSeek分析）"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    preferences = data.get('preferences', {})  # 用户偏好
    limit = data.get('limit', 10)
    
    # 获取用户浏览历史
    browse_history = db.session.query(Attraction).join(
        UserBrowseHistory, Attraction.poi_id == UserBrowseHistory.poi_id
    ).filter(UserBrowseHistory.user_id == user_id).limit(20).all()
    
    # 获取用户收藏
    favorites = db.session.query(Attraction).join(
        UserFavorite, Attraction.poi_id == UserFavorite.poi_id
    ).filter(UserFavorite.user_id == user_id).all()
    
    # 构建用户数据
    user_data = {
        'browse_history': [
            {
                'poi_name': a.poi_name,
                'city': a.city,
                'tag_list': a.tag_list,
                'comment_score': float(a.comment_score)
            } for a in browse_history
        ],
        'favorites': [
            {
                'poi_name': a.poi_name,
                'city': a.city,
                'tag_list': a.tag_list
            } for a in favorites
        ],
        'preferences': preferences
    }
    
    # 根据用户偏好筛选候选景点
    query = Attraction.query
    
    # 城市筛选
    if preferences.get('city'):
        query = query.filter(Attraction.city == preferences.get('city'))
    
    # 最低评分筛选
    min_score = preferences.get('min_score', 0)
    if min_score > 0:
        query = query.filter(Attraction.comment_score >= min_score)
    else:
        # 如果没有设置最低评分，默认筛选4.0分以上
        query = query.filter(Attraction.comment_score >= 4.0)
    
    # 价格范围筛选
    min_price = preferences.get('min_price', 0)
    max_price = preferences.get('max_price', 9999)
    if min_price > 0 or max_price < 9999:
        # 价格筛选：优先使用preferential_price，如果没有则使用market_price
        if min_price > 0:
            query = query.filter(
                or_(
                    and_(
                        Attraction.preferential_price.isnot(None),
                        Attraction.preferential_price >= min_price,
                        Attraction.preferential_price <= max_price
                    ),
                    and_(
                        Attraction.preferential_price.is_(None),
                        Attraction.market_price.isnot(None),
                        Attraction.market_price >= min_price,
                        Attraction.market_price <= max_price
                    ),
                    Attraction.is_free == True  # 免费景点也包含在内
                )
            )
        else:
            query = query.filter(
                or_(
                    and_(
                        Attraction.preferential_price.isnot(None),
                        Attraction.preferential_price <= max_price
                    ),
                    and_(
                        Attraction.preferential_price.is_(None),
                        Attraction.market_price.isnot(None),
                        Attraction.market_price <= max_price
                    ),
                    Attraction.is_free == True
                )
            )
    
    # 获取候选景点（扩大候选池，确保有足够的景点供AI选择）
    candidate_attractions = query.order_by(desc(Attraction.heat_score)).limit(100).all()
    
    attractions_data = [
        {
            'poi_id': a.poi_id,
            'poi_name': a.poi_name,
            'city': a.city,
            'comment_score': float(a.comment_score),
            'tag_list': a.tag_list,
            'price': a.price,
            'heat_score': a.heat_score
        } for a in candidate_attractions
    ]
    
    # 调用DeepSeek进行推荐分析
    try:
        ai_result = ai_service.get_deepseek_recommendation(user_data, attractions_data, limit)
        
        # 解析AI返回结果
        if ai_result:
            # 保存AI返回的推荐理由（poi_id -> reason映射）
            recommendation_reasons = {}
            
            # 尝试提取JSON
            try:
                # 查找JSON部分
                start_idx = ai_result.find('{')
                end_idx = ai_result.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = ai_result[start_idx:end_idx]
                    recommendations_data = json.loads(json_str)
                    ai_recommendations = recommendations_data.get('recommendations', [])
                    # 提取poi_id和推荐理由
                    recommended_poi_ids = []
                    for r in ai_recommendations:
                        poi_id = r.get('poi_id')
                        reason = r.get('reason', '')
                        if poi_id:
                            recommended_poi_ids.append(poi_id)
                            recommendation_reasons[poi_id] = reason
                else:
                    recommended_poi_ids = []
            except Exception as e:
                print(f"解析AI返回结果失败: {e}")
                recommended_poi_ids = []
        
            # 如果AI推荐失败或数量不足，使用基于协同过滤的推荐补充
            if not recommended_poi_ids or len(recommended_poi_ids) < limit:
                # 获取已推荐的poi_id，避免重复
                existing_ids = set(recommended_poi_ids)
                # 从候选景点中补充，直到达到limit数量
                for a in attractions_data:
                    if len(recommended_poi_ids) >= limit:
                        break
                    if a['poi_id'] not in existing_ids:
                        recommended_poi_ids.append(a['poi_id'])
                        existing_ids.add(a['poi_id'])
                        # 如果没有AI推荐理由，生成默认理由
                        if a['poi_id'] not in recommendation_reasons:
                            recommendation_reasons[a['poi_id']] = f"根据您的偏好，为您推荐这个评分{a['comment_score']}分的优质景点"
            
            # 限制推荐数量为limit
            recommended_poi_ids = recommended_poi_ids[:limit]
            
            # 获取推荐景点详情
            recommended_attractions = Attraction.query.filter(
                Attraction.poi_id.in_(recommended_poi_ids)
            ).all()
            
            # 按照recommended_poi_ids的顺序排序，保持AI推荐的优先级
            attraction_dict = {a.poi_id: a for a in recommended_attractions}
            ordered_attractions = []
            for poi_id in recommended_poi_ids:
                if poi_id in attraction_dict:
                    attraction = attraction_dict[poi_id]
                    attraction_dict_data = attraction.to_dict()
                    # 添加推荐理由
                    attraction_dict_data['recommend_reason'] = recommendation_reasons.get(poi_id, '')
                    ordered_attractions.append(attraction_dict_data)
            
            result = {
                'recommendations': ordered_attractions,
                'ai_analysis': ai_result
            }
            
            return jsonify({'code': 200, 'data': result})
        else:
            # AI调用失败，使用默认推荐
            return jsonify({
                'code': 200,
                'data': {
                    'recommendations': [a.to_dict() for a in candidate_attractions[:limit]],
                    'ai_analysis': '使用默认推荐算法'
                }
            })
    except Exception as e:
        print(f"Recommendation error: {e}")
        return jsonify({
            'code': 200,
            'data': {
                'recommendations': [a.to_dict() for a in candidate_attractions[:limit]],
                'ai_analysis': '推荐系统暂时不可用，显示热门景点'
            }
        })

@recommendation_bp.route('/similar/<poi_id>', methods=['GET'])
def get_similar_attractions(poi_id):
    """相似景点推荐"""
    cache_key = f"recommendation:similar:{poi_id}"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    # 获取当前景点
    attraction = Attraction.query.filter_by(poi_id=poi_id).first()
    if not attraction:
        return jsonify({'code': 404, 'message': '景点不存在'}), 404
    
    # 基于标签和城市推荐相似景点
    similar_attractions = Attraction.query.filter(
        Attraction.poi_id != poi_id,
        Attraction.city == attraction.city
    ).order_by(desc(Attraction.comment_score)).limit(10).all()
    
    result = [a.to_dict() for a in similar_attractions]
    
    redis_client.set(cache_key, result, expire=1800)
    
    return jsonify({'code': 200, 'data': result})

@recommendation_bp.route('/hot', methods=['GET'])
def get_hot_recommendations():
    """热门推荐"""
    cache_key = "recommendation:hot"
    
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify({'code': 200, 'data': cached_data})
    
    limit = request.args.get('limit', 20, type=int)
    
    # 综合热度和评分推荐
    hot_attractions = Attraction.query.filter(
        Attraction.comment_score >= 4.0
    ).order_by(
        desc(Attraction.heat_score),
        desc(Attraction.comment_score)
    ).limit(limit).all()
    
    result = [a.to_dict() for a in hot_attractions]
    
    redis_client.set(cache_key, result, expire=600)
    
    return jsonify({'code': 200, 'data': result})

@recommendation_bp.route('/travel-plan', methods=['POST'])
@jwt_required()
def generate_travel_plan():
    """生成旅游规划（基于BigModel）"""
    data = request.get_json()
    
    destination = data.get('destination')
    days = data.get('days', 3)
    preferences = data.get('preferences', '')
    
    if not destination:
        return jsonify({'code': 400, 'message': '目的地不能为空'}), 400
    
    # 获取目的地的景点信息
    attractions = Attraction.query.filter(
        Attraction.city.like(f'%{destination}%')
    ).order_by(desc(Attraction.comment_score)).limit(20).all()
    
    attractions_info = '\n'.join([
        f"- {a.poi_name}（评分：{a.comment_score}，标签：{a.tag_list}）"
        for a in attractions
    ])
    
    # 调用BigModel生成旅游规划
    try:
        full_preferences = f"{preferences}\n\n可选景点：\n{attractions_info}"
        plan = ai_service.get_bigmodel_travel_plan(destination, days, full_preferences)
        
        if plan:
            return jsonify({
                'code': 200,
                'data': {
                    'plan': plan,
                    'attractions': [a.to_dict() for a in attractions]
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': 'AI规划服务暂时不可用'
            }), 500
    except Exception as e:
        print(f"Travel plan error: {e}")
        return jsonify({
            'code': 500,
            'message': f'生成旅游规划失败: {str(e)}'
        }), 500

@recommendation_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat_with_ai():
    """AI聊天助手（基于BigModel）"""
    user_id = get_jwt_identity()
    from models import User, UserBrowseHistory, UserFavorite, SpiderTask
    from sqlalchemy import func
    
    data = request.get_json()
    messages = data.get('messages', [])
    current_message = data.get('message', '')
    
    if not current_message:
        return jsonify({'code': 400, 'message': '消息不能为空'}), 400
    
    # 获取用户信息
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 401, 'message': '用户不存在'}), 401
    
    is_admin = user.role == 'admin'
    
    # 根据角色构建不同的数据上下文
    context_data = ""
    
    if is_admin:
        # 管理员：系统数据、用户统计、爬虫状态等
        total_users = User.query.count()
        total_attractions = Attraction.query.count()
        active_users = User.query.filter_by(status=True).count()
        
        # 爬虫任务统计
        today_tasks = SpiderTask.query.filter(
            func.date(SpiderTask.created_at) == func.curdate()
        ).count()
        
        # 热门城市TOP5
        top_cities = db.session.query(
            Attraction.city,
            func.count(Attraction.id).label('count')
        ).group_by(Attraction.city).order_by(desc(func.count(Attraction.id))).limit(5).all()
        
        context_data = f"""
系统数据概览：
- 用户总数：{total_users}
- 活跃用户：{active_users}
- 景点总数：{total_attractions}
- 今日爬虫任务：{today_tasks}

热门城市TOP5：
{chr(10).join([f"- {city}：{count}个景点" for city, count in top_cities])}

你可以回答关于系统数据、用户统计、爬虫状态、景点管理等问题。
"""
    else:
        # 普通用户：个人浏览历史、收藏、推荐等
        # 获取用户浏览历史
        browse_history = db.session.query(Attraction).join(
            UserBrowseHistory, Attraction.poi_id == UserBrowseHistory.poi_id
        ).filter(UserBrowseHistory.user_id == user_id).order_by(
            desc(UserBrowseHistory.browse_time)
        ).limit(10).all()
        
        # 获取用户收藏
        favorites = db.session.query(Attraction).join(
            UserFavorite, Attraction.poi_id == UserFavorite.poi_id
        ).filter(UserFavorite.user_id == user_id).limit(10).all()
        
        # 热门景点TOP10
        hot_attractions = Attraction.query.filter(
            Attraction.comment_score >= 4.0
        ).order_by(
            desc(Attraction.heat_score),
            desc(Attraction.comment_score)
        ).limit(10).all()
        
        context_data = f"""
用户信息：
- 用户名：{user.username}
- 浏览历史（最近10条）：
{chr(10).join([f"  - {a.poi_name}（{a.city}，评分{a.comment_score}）" for a in browse_history]) if browse_history else "  - 暂无浏览历史"}

- 收藏景点（最近10条）：
{chr(10).join([f"  - {a.poi_name}（{a.city}，评分{a.comment_score}）" for a in favorites]) if favorites else "  - 暂无收藏"}

- 热门景点推荐：
{chr(10).join([f"  - {a.poi_name}（{a.city}，评分{a.comment_score}，热度{a.heat_score}）" for a in hot_attractions])}

你可以回答关于景点推荐、旅游规划、城市选择、价格分析等问题。
"""
    
    # 添加当前消息到消息列表
    messages.append({"role": "user", "content": current_message})
    
    # 调用AI服务
    try:
        response = ai_service.chat_with_bigmodel(messages, context_data)
        
        if response:
            return jsonify({
                'code': 200,
                'data': {
                    'response': response
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': 'AI服务暂时不可用，请稍后重试'
            }), 500
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'code': 500,
            'message': f'AI聊天失败: {str(e)}'
        }), 500
