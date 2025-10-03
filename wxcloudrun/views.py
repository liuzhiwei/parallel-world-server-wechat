from datetime import datetime
import os
import uuid
import logging
from flask import render_template, request
from werkzeug.utils import secure_filename
from run import app
from wxcloudrun.dao import insert_digital_avatar, get_digital_avatar_by_user_id, update_digital_avatar, insert_travel_partner, get_travel_partner_by_user_id, update_travel_partner, insert_travel_settings, get_travel_settings_by_user_id, update_travel_settings, ensure_user_exists
from wxcloudrun.model import DigitalAvatar, TravelPartner, TravelSettings
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.wechat_config import WeChatCloudConfig

# 初始化日志
logger = logging.getLogger('log')


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/init-db', methods=['POST'])
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


@app.route('/api/check-tables', methods=['GET'])
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


@app.route('/api/test-db', methods=['GET'])
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


@app.route('/api/user', methods=['POST'])
def create_user():
    """
    创建/更新用户记录
    :return: 创建结果
    """
    try:
        params = request.get_json()
        
        if not params or 'user_id' not in params:
            return make_err_response('缺少用户ID')
        
        user_id = params['user_id']
        
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 确保用户存在
        user = ensure_user_exists(user_id)
        
        return make_succ_response({
            'message': '用户记录创建成功',
            'user_id': user_id,
            'user_db_id': user.id
        })
        
    except Exception as e:
        logger.error(f"创建用户记录失败: {str(e)}")
        return make_err_response(f'创建用户记录失败: {str(e)}')


@app.route('/api/save-all', methods=['POST'])
def save_all_data():
    """
    一次性保存所有数据（分身+伙伴+设置）
    :return: 保存结果
    """
    try:
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'avatar', 'partner', 'settings']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        avatar_data = params['avatar']
        partner_data = params['partner']
        settings_data = params['settings']
        
        # 验证用户ID
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 确保用户存在
        ensure_user_exists(user_id)
        
        # 保存分身信息
        avatar = DigitalAvatar(
            user_id=user_id,
            name=avatar_data['name'],
            description=avatar_data['description'],
            avatar_url=avatar_data['avatar_url']
        )
        insert_digital_avatar(avatar)
        
        # 保存旅行伙伴信息
        partner = TravelPartner(
            user_id=user_id,
            partner_name=partner_data['partner_name'],
            partner_description=partner_data['partner_description'],
            partner_avatar_url=partner_data['partner_avatar_url']
        )
        insert_travel_partner(partner)
        
        # 保存旅行设置信息
        settings = TravelSettings(
            user_id=user_id,
            destination=settings_data['destination'],
            days=settings_data['days'],
            preference=settings_data['preference']
        )
        insert_travel_settings(settings)
        
        return make_succ_response({
            'message': '所有数据保存成功',
            'data': {
                'avatar_id': avatar.id,
                'partner_id': partner.id,
                'settings_id': settings.id
            }
        })
        
    except Exception as e:
        logger.error(f'保存所有数据失败: {str(e)}')
        return make_err_response(f'保存所有数据失败: {str(e)}')


@app.route('/api/upload', methods=['POST'])
def upload_avatar():
    """
    头像上传接口
    :return: 上传后的文件URL
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return make_err_response('没有上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return make_err_response('没有选择文件')
        
        # 检查文件类型
        if not WeChatCloudConfig.is_allowed_file(file.filename):
            return make_err_response('不支持的文件格式，请上传图片文件')
        
        # 检查上传类型
        upload_type = request.form.get('type', '')
        if upload_type != 'avatar':
            return make_err_response('上传类型错误')
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # 创建上传目录（微信云托管环境）
        upload_folder = os.path.join(WeChatCloudConfig.get_upload_path(), 'avatars')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # 生成访问URL（微信云托管格式）
        avatar_url = WeChatCloudConfig.get_file_url(f"avatars/{unique_filename}")
        
        return make_succ_response({'url': avatar_url})
        
    except Exception as e:
        return make_err_response(f'文件上传失败: {str(e)}')






@app.route('/api/profile', methods=['POST'])
def create_profile():
    """
    创建数字分身接口（已废弃，请使用 /api/save-all）
    :return: 创建结果
    """
    return make_err_response('此接口已废弃，请使用 /api/save-all 接口')


@app.route('/api/travel-partner', methods=['POST'])
def create_travel_partner():
    """
    创建旅行伙伴接口（已废弃，请使用 /api/save-all）
    :return: 创建结果
    """
    return make_err_response('此接口已废弃，请使用 /api/save-all 接口')


@app.route('/api/travel-settings', methods=['POST'])
def create_travel_settings():
    """
    创建旅行设置接口（已废弃，请使用 /api/save-all）
    :return: 创建结果
    """
    return make_err_response('此接口已废弃，请使用 /api/save-all 接口')


@app.route('/api/user-profile/<user_id>', methods=['GET'])
def get_user_complete_profile(user_id):
    """
    获取用户完整信息（分身+伙伴+设置）
    :param user_id: 用户ID
    :return: 用户完整信息
    """
    try:
        # 查询分身信息
        avatar = get_digital_avatar_by_user_id(user_id)
        # 查询伙伴信息
        partner = get_travel_partner_by_user_id(user_id)
        # 查询设置信息
        settings = get_travel_settings_by_user_id(user_id)
        
        profile_data = {
            'user_id': user_id,
            'avatar': None,
            'partner': None,
            'settings': None
        }
        
        if avatar:
            profile_data['avatar'] = {
                'id': avatar.id,
                'name': avatar.name,
                'description': avatar.description,
                'avatar_url': avatar.avatar_url,
                'created_at': avatar.created_at.isoformat(),
                'updated_at': avatar.updated_at.isoformat()
            }
        
        if partner:
            profile_data['partner'] = {
                'id': partner.id,
                'partner_name': partner.partner_name,
                'partner_description': partner.partner_description,
                'partner_avatar_url': partner.partner_avatar_url,
                'created_at': partner.created_at.isoformat(),
                'updated_at': partner.updated_at.isoformat()
            }
        
        if settings:
            profile_data['settings'] = {
                'id': settings.id,
                'destination': settings.destination,
                'days': settings.days,
                'preference': settings.preference,
                'created_at': settings.created_at.isoformat(),
                'updated_at': settings.updated_at.isoformat()
            }
        
        return make_succ_response(profile_data)
        
    except Exception as e:
        return make_err_response(f'获取用户信息失败: {str(e)}')
