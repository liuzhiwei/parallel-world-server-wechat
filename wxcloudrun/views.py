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


@app.route('/api/test-log', methods=['GET'])
def test_log():
    """
    测试日志输出
    :return: 测试结果
    """
    try:
        logger.info("=== 日志测试开始 ===")
        logger.warning("这是一个警告日志")
        logger.error("这是一个错误日志")
        logger.info("=== 日志测试结束 ===")
        
        return make_succ_response({
            'message': '日志测试完成，请检查后端日志'
        })
    except Exception as e:
        return make_err_response(f'日志测试失败: {str(e)}')


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


@app.route('/api/test-insert', methods=['POST'])
def test_insert_user():
    """
    直接测试插入用户记录
    :return: 插入结果
    """
    try:
        from wxcloudrun import db
        from wxcloudrun.model import Users
        from datetime import datetime
        
        # 创建测试用户
        test_user_id = f"test_user_{int(datetime.now().timestamp())}"
        logger.info(f"=== 直接测试插入用户 ===")
        logger.info(f"test_user_id: {test_user_id}")
        
        # 直接创建用户对象
        user = Users(user_id=test_user_id)
        logger.info(f"用户对象创建: {user}")
        
        # 直接插入数据库
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"用户插入成功，ID: {user.id}")
        
        # 验证插入结果
        inserted_user = Users.query.filter(Users.user_id == test_user_id).first()
        if inserted_user:
            logger.info(f"验证成功: 找到用户 ID={inserted_user.id}")
            return make_succ_response({
                'message': '直接插入测试成功',
                'user_id': test_user_id,
                'user_db_id': inserted_user.id
            })
        else:
            logger.error("验证失败: 未找到插入的用户")
            return make_err_response('插入验证失败')
        
    except Exception as e:
        logger.error(f"直接插入测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return make_err_response(f'直接插入测试失败: {str(e)}')


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
        
        logger.info(f"=== 创建用户API被调用 ===")
        logger.info(f"user_id: {user_id}")
        logger.info(f"=========================")
        
        # 确保用户存在
        user = ensure_user_exists(user_id)
        
        # 验证用户是否真的被创建
        if user and user.id:
            logger.info(f"用户创建验证成功: ID={user.id}, user_id={user.user_id}")
            return make_succ_response({
                'message': '用户记录创建成功',
                'user_id': user_id,
                'user_db_id': user.id
            })
        else:
            logger.error("用户创建失败：用户对象为空或没有ID")
            return make_err_response('用户创建失败')
        
    except Exception as e:
        logger.error(f"创建用户记录失败: {str(e)}")
        import traceback
        traceback.print_exc()
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
        
        logger.info(f"=== 一次性保存所有数据 ===")
        logger.info(f"user_id: {user_id}")
        logger.info(f"avatar_data: {avatar_data}")
        logger.info(f"partner_data: {partner_data}")
        logger.info(f"settings_data: {settings_data}")
        logger.info(f"=========================")
        
        # 保存分身信息
        avatar = DigitalAvatar()
        avatar.user_id = user_id
        avatar.name = avatar_data['name']
        avatar.description = avatar_data['description']
        avatar.avatar_url = avatar_data['avatar_url']
        avatar.created_at = datetime.now()
        avatar.updated_at = datetime.now()
        
        try:
            insert_digital_avatar(avatar)
            logger.info(f"分身创建成功，ID: {avatar.id}")
        except Exception as e:
            logger.error(f"分身创建失败: {str(e)}")
            return make_err_response(f'创建分身失败: {str(e)}')
        
        # 保存旅行伙伴信息
        partner = TravelPartner()
        partner.user_id = user_id
        partner.partner_name = partner_data['partner_name']
        partner.partner_description = partner_data['partner_description']
        partner.partner_avatar_url = partner_data['partner_avatar_url']
        partner.created_at = datetime.now()
        partner.updated_at = datetime.now()
        
        try:
            insert_travel_partner(partner)
            logger.info(f"旅行伙伴创建成功，ID: {partner.id}")
        except Exception as e:
            logger.error(f"旅行伙伴创建失败: {str(e)}")
            return make_err_response(f'创建旅行伙伴失败: {str(e)}')
        
        # 保存旅行设置信息
        settings = TravelSettings()
        settings.user_id = user_id
        settings.destination = settings_data['destination']
        settings.days = settings_data['days']
        settings.preference = settings_data['preference']
        settings.created_at = datetime.now()
        settings.updated_at = datetime.now()
        
        try:
            insert_travel_settings(settings)
            logger.info(f"旅行设置创建成功，ID: {settings.id}")
        except Exception as e:
            logger.error(f"旅行设置创建失败: {str(e)}")
            return make_err_response(f'创建旅行设置失败: {str(e)}')
        
        return make_succ_response({
            'message': '所有数据保存成功',
            'data': {
                'avatar_id': avatar.id,
                'partner_id': partner.id,
                'settings_id': settings.id
            }
        })
        
    except Exception as e:
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
    创建数字分身接口
    :return: 创建结果
    """
    try:
        # 获取请求参数
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'name', 'description', 'avatar_url']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        name = params['name']
        description = params['description']
        avatar_url = params['avatar_url']
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        if not name.strip():
            return make_err_response('分身名称不能为空')
        if not description.strip():
            return make_err_response('性格描述不能为空')
        if not avatar_url.strip():
            return make_err_response('头像URL不能为空')
        
        # 确保用户存在
        try:
            ensure_user_exists(user_id)
            print("用户存在检查完成")
        except Exception as e:
            print(f"用户存在检查失败: {str(e)}")
            return make_err_response(f'用户检查失败: {str(e)}')
        
        # 添加调试日志
        print(f"=== 创建分身API被调用 ===")
        print(f"user_id: {user_id}")
        print(f"name: {name}")
        print(f"description: {description}")
        print(f"avatar_url: {avatar_url}")
        print(f"=========================")
        
        # 检查是否已存在该用户的分身
        existing_avatar = get_digital_avatar_by_user_id(user_id)
        
        if existing_avatar:
            # 更新现有分身
            existing_avatar.name = name
            existing_avatar.description = description
            existing_avatar.avatar_url = avatar_url
            existing_avatar.updated_at = datetime.now()
            update_digital_avatar(existing_avatar)
            
            return make_succ_response({
                'ok': True,
                'message': '分身信息更新成功',
                'avatar': {
                    'id': existing_avatar.id,
                    'user_id': existing_avatar.user_id,
                    'name': existing_avatar.name,
                    'description': existing_avatar.description,
                    'avatar_url': existing_avatar.avatar_url,
                    'created_at': existing_avatar.created_at.isoformat(),
                    'updated_at': existing_avatar.updated_at.isoformat()
                }
            })
        else:
            # 创建新分身
            print("创建新分身记录")
            avatar = DigitalAvatar()
            avatar.user_id = user_id
            avatar.name = name
            avatar.description = description
            avatar.avatar_url = avatar_url
            avatar.created_at = datetime.now()
            avatar.updated_at = datetime.now()
            
            try:
                insert_digital_avatar(avatar)
                print("分身创建成功，ID:", avatar.id)
            except Exception as e:
                print(f"分身创建失败: {str(e)}")
                return make_err_response(f'创建分身失败: {str(e)}')
            
            return make_succ_response({
                'ok': True,
                'message': '分身创建成功',
                'avatar': {
                    'id': avatar.id,
                    'user_id': avatar.user_id,
                    'name': avatar.name,
                    'description': avatar.description,
                    'avatar_url': avatar.avatar_url,
                    'created_at': avatar.created_at.isoformat(),
                    'updated_at': avatar.updated_at.isoformat()
                }
            })
        
    except Exception as e:
        return make_err_response(f'创建分身失败: {str(e)}')


@app.route('/api/travel-partner', methods=['POST'])
def create_travel_partner():
    """
    创建旅行伙伴接口
    :return: 创建结果
    """
    try:
        # 获取请求参数
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'partner_name', 'partner_description', 'partner_avatar_url']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        partner_name = params['partner_name']
        partner_description = params['partner_description']
        partner_avatar_url = params['partner_avatar_url']
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        if not partner_name.strip():
            return make_err_response('伙伴名称不能为空')
        if not partner_description.strip():
            return make_err_response('伙伴性格描述不能为空')
        if not partner_avatar_url.strip():
            return make_err_response('伙伴头像URL不能为空')
        
        # 确保用户存在
        ensure_user_exists(user_id)
        
        # 检查是否已存在
        existing_partner = get_travel_partner_by_user_id(user_id)
        
        if existing_partner:
            # 更新现有记录
            existing_partner.partner_name = partner_name
            existing_partner.partner_description = partner_description
            existing_partner.partner_avatar_url = partner_avatar_url
            update_travel_partner(existing_partner)
            
            return make_succ_response({
                'message': '旅行伙伴更新成功',
                'partner': {
                    'id': existing_partner.id,
                    'user_id': existing_partner.user_id,
                    'partner_name': existing_partner.partner_name,
                    'partner_description': existing_partner.partner_description,
                    'partner_avatar_url': existing_partner.partner_avatar_url,
                    'created_at': existing_partner.created_at.isoformat(),
                    'updated_at': existing_partner.updated_at.isoformat()
                }
            })
        else:
            # 创建新记录
            partner = TravelPartner(
                user_id=user_id,
                partner_name=partner_name,
                partner_description=partner_description,
                partner_avatar_url=partner_avatar_url
            )
            
            insert_travel_partner(partner)
            
            return make_succ_response({
                'message': '旅行伙伴创建成功',
                'partner': {
                    'id': partner.id,
                    'user_id': partner.user_id,
                    'partner_name': partner.partner_name,
                    'partner_description': partner.partner_description,
                    'partner_avatar_url': partner.partner_avatar_url,
                    'created_at': partner.created_at.isoformat(),
                    'updated_at': partner.updated_at.isoformat()
                }
            })
        
    except Exception as e:
        return make_err_response(f'创建旅行伙伴失败: {str(e)}')


@app.route('/api/travel-settings', methods=['POST'])
def create_travel_settings():
    """
    创建旅行设置接口
    :return: 创建结果
    """
    try:
        # 获取请求参数
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        destination = params.get('destination', '')
        days = params.get('days', None)
        preference = params.get('preference', '')
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 确保用户存在
        ensure_user_exists(user_id)
        
        # 检查是否已存在
        existing_settings = get_travel_settings_by_user_id(user_id)
        
        if existing_settings:
            # 更新现有记录
            existing_settings.destination = destination
            existing_settings.days = days
            existing_settings.preference = preference
            update_travel_settings(existing_settings)
            
            return make_succ_response({
                'message': '旅行设置更新成功',
                'settings': {
                    'id': existing_settings.id,
                    'user_id': existing_settings.user_id,
                    'destination': existing_settings.destination,
                    'days': existing_settings.days,
                    'preference': existing_settings.preference,
                    'created_at': existing_settings.created_at.isoformat(),
                    'updated_at': existing_settings.updated_at.isoformat()
                }
            })
        else:
            # 创建新记录
            settings = TravelSettings(
                user_id=user_id,
                destination=destination,
                days=days,
                preference=preference
            )
            
            insert_travel_settings(settings)
            
            return make_succ_response({
                'message': '旅行设置创建成功',
                'settings': {
                    'id': settings.id,
                    'user_id': settings.user_id,
                    'destination': settings.destination,
                    'days': settings.days,
                    'preference': settings.preference,
                    'created_at': settings.created_at.isoformat(),
                    'updated_at': settings.updated_at.isoformat()
                }
            })
        
    except Exception as e:
        return make_err_response(f'创建旅行设置失败: {str(e)}')


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
