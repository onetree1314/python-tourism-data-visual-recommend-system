from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.minio_client import minio_client
from werkzeug.utils import secure_filename
import uuid
import os

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """检查文件扩展名"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/image', methods=['POST'])
@jwt_required()
def upload_image():
    """上传图片到MinIO"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'code': 400, 'message': '文件名为空'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'code': 400, 'message': '不支持的文件类型'}), 400
    
    try:
        # 生成唯一文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # 读取文件数据
        file_data = file.read()
        
        # 上传到MinIO
        url = minio_client.upload_file(
            file_data,
            filename,
            content_type=file.content_type
        )
        
        if url:
            return jsonify({
                'code': 200,
                'message': '上传成功',
                'data': {
                    'url': url,
                    'filename': filename
                }
            })
        else:
            return jsonify({'code': 500, 'message': '上传失败'}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': f'上传失败: {str(e)}'}), 500

@upload_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """上传用户头像"""
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有文件'}), 400
    
    file = request.files['file']
    
    if not allowed_file(file.filename):
        return jsonify({'code': 400, 'message': '不支持的文件类型'}), 400
    
    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"avatars/{user_id}_{uuid.uuid4().hex}.{ext}"
        
        file_data = file.read()
        
        url = minio_client.upload_file(
            file_data,
            filename,
            content_type=file.content_type
        )
        
        if url:
            # 更新用户头像
            from models import db, User
            user = User.query.get(user_id)
            if user:
                user.avatar = url
                db.session.commit()
            
            return jsonify({
                'code': 200,
                'message': '上传成功',
                'data': {'url': url}
            })
        else:
            return jsonify({'code': 500, 'message': '上传失败'}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': f'上传失败: {str(e)}'}), 500
