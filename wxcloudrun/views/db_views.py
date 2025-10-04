from datetime import datetime
import logging
from flask import Blueprint
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response

# 初始化日志
logger = logging.getLogger('log')

# 创建蓝图
db_bp = Blueprint('db', __name__, url_prefix='/api')

@db_bp.route('/init-db', methods=['POST'])
def init_database():
    """
    初始化数据库表
    :return: 初始化结果
    """
    try:
        from wxcloudrun import db
        db.create_all()
        return make_succ_response({'message': '数据库表创建成功'})
    except Exception as e:
        return make_err_response(f'数据库初始化失败: {str(e)}')


@db_bp.route('/check-tables', methods=['GET'])
def check_tables():
    """
    检查数据库表结构
    :return: 表结构信息
    """
    try:
        from wxcloudrun import db
        from wxcloudrun.model import Users, DigitalAvatar, TravelPartner, TravelSettings
        
        # 检查表是否存在
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        result = {
            'tables_exist': tables,
            'models': []
        }
        
        # 检查每个模型对应的表
        for model in [Users, DigitalAvatar, TravelPartner, TravelSettings]:
            table_name = model.__tablename__
            if table_name in tables:
                columns = inspector.get_columns(table_name)
                result['models'].append({
                    'table_name': table_name,
                    'columns': [col['name'] for col in columns]
                })
            else:
                result['models'].append({
                    'table_name': table_name,
                    'status': 'NOT_EXISTS'
                })
        
        return make_succ_response(result)
        
    except Exception as e:
        return make_err_response(f'检查表结构失败: {str(e)}')


@db_bp.route('/test-db', methods=['GET'])
def test_database():
    """
    测试数据库连接
    :return: 测试结果
    """
    try:
        from wxcloudrun import db
        from wxcloudrun.model import Users, DigitalAvatar
        
        # 测试查询
        user_count = Users.query.count()
        avatar_count = DigitalAvatar.query.count()
        
        # 列出所有用户记录
        users = Users.query.all()
        user_list = []
        for user in users:
            user_list.append({
                'id': user.id,
                'user_id': user.user_id,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        return make_succ_response({
            'message': '数据库连接正常',
            'user_count': user_count,
            'avatar_count': avatar_count,
            'users': user_list
        })
    except Exception as e:
        return make_err_response(f'数据库测试失败: {str(e)}')

# 注册蓝图
app.register_blueprint(db_bp)
