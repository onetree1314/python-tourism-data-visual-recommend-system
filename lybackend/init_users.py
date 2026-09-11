"""
初始化用户脚本
创建管理员和普通用户账号
"""
from app import app
from models import db, User
from datetime import datetime

def init_users():
    """初始化默认用户"""
    with app.app_context():
        # 检查是否已存在用户
        existing_admin = User.query.filter_by(username='admin').first()
        existing_user = User.query.filter_by(username='user').first()
        
        # 创建管理员账号
        if not existing_admin:
            admin = User(
                username='admin',
                email='admin@tourism.com',
                role='admin',
                status=True,
                created_at=datetime.now()
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print('✓ 管理员账号创建成功: admin / admin123')
        else:
            print('× 管理员账号已存在，跳过创建')
        
        # 创建普通用户账号
        if not existing_user:
            user = User(
                username='user',
                email='user@tourism.com',
                role='user',
                status=True,
                created_at=datetime.now()
            )
            user.set_password('123456')
            db.session.add(user)
            print('✓ 普通用户账号创建成功: user / 123456')
        else:
            print('× 普通用户账号已存在，跳过创建')
        
        # 提交到数据库
        try:
            db.session.commit()
            print('\n用户初始化完成！')
            print('=' * 50)
            print('管理员账号: admin / admin123')
            print('普通用户账号: user / 123456')
            print('=' * 50)
        except Exception as e:
            db.session.rollback()
            print(f'错误: 用户创建失败 - {str(e)}')

if __name__ == '__main__':
    print('开始初始化用户...\n')
    init_users()
