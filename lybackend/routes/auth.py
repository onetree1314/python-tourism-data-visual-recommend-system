from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import db, User, SystemLog
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
    
    # 检查用户是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'message': '用户名已存在'}), 400
    
    # 创建新用户
    user = User(username=username, email=email, role='user')
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '注册成功',
        'data': user.to_dict()
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空'}), 400
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'message': '用户名或密码错误'}), 401
    
    if not user.status:
        return jsonify({'code': 403, 'message': '账户已被禁用'}), 403
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.session.commit()
    
    # 记录登录日志
    log = SystemLog(
        user_id=user.id,
        action='login',
        ip=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    # 生成token - identity必须是字符串
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'user': user.to_dict(),
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    })

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(user_id))
    
    return jsonify({
        'code': 200,
        'data': {'access_token': access_token}
    })

@auth_bp.route('/info', methods=['GET'])
@jwt_required()
def get_user_info():
    """获取当前用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404
    
    return jsonify({
        'code': 200,
        'data': user.to_dict()
    })

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    user_id = get_jwt_identity()
    
    # 记录登出日志
    log = SystemLog(
        user_id=user_id,
        action='logout',
        ip=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'code': 200,
        'message': '登出成功'
    })
