from datetime import datetime
import os
import uuid
import logging
import json
from flask import render_template, request, Response
from werkzeug.utils import secure_filename
from run import app
from wxcloudrun.dao import insert_digital_avatar, get_digital_avatar_by_user_id, update_digital_avatar, insert_travel_partner, get_travel_partner_by_user_id, update_travel_partner, insert_travel_settings, get_travel_settings_by_user_id, update_travel_settings, ensure_user_exists, insert_chat_message, get_chat_messages_by_session, get_user_sessions
from wxcloudrun.model import DigitalAvatar, TravelPartner, TravelSettings, ChatMessages
from wxcloudrun.agent_manager import AgentManager
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


@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    """
    发送聊天消息
    :return: 发送结果
    """
    try:
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'session_id', 'message']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        session_id = params['session_id']
        message = params['message']
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        if not session_id.strip():
            return make_err_response('会话ID不能为空')
        if not message.strip():
            return make_err_response('消息内容不能为空')
        
        # 记录分身消息（用户替分身说话）
        avatar_msg = ChatMessages(
            user_id=user_id,
            session_id=session_id,
            speaker_type='avatar',
            message=message
        )
        insert_chat_message(avatar_msg)
        
        # 获取对话历史
        conversation_history = get_chat_messages_by_session(user_id, session_id, limit=20)
        history_data = []
        for msg in conversation_history:
            history_data.append({
                'speaker_type': msg.speaker_type,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        # 创建智能体管理器并生成回复
        agent_manager = AgentManager(user_id)
        responses = agent_manager.generate_responses_by_user_input(message, history_data)
        
        # 记录伙伴回复
        partner_msg = ChatMessages(
            user_id=user_id,
            session_id=session_id,
            speaker_type='partner',
            message=responses['partner_response']
        )
        insert_chat_message(partner_msg)
        
        return make_succ_response({
            'message': '消息发送成功',
            'data': {
                'avatar_message': responses['avatar_message'],
                'partner_response': responses['partner_response']
            }
        })
        
    except Exception as e:
        logger.error(f'发送聊天消息失败: {str(e)}')
        return make_err_response(f'发送聊天消息失败: {str(e)}')


@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """
    获取聊天历史
    :return: 聊天历史
    """
    try:
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        
        if not user_id:
            return make_err_response('缺少user_id参数')
        if not session_id:
            return make_err_response('缺少session_id参数')
        
        # 获取聊天消息
        messages = get_chat_messages_by_session(user_id, session_id, limit)
        
        # 格式化消息数据
        history_data = []
        for msg in messages:
            history_data.append({
                'id': msg.id,
                'speaker_type': msg.speaker_type,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        return make_succ_response({
            'message': '获取聊天历史成功',
            'data': {
                'history': history_data,
                'count': len(history_data)
            }
        })
        
    except Exception as e:
        logger.error(f'获取聊天历史失败: {str(e)}')
        return make_err_response(f'获取聊天历史失败: {str(e)}')


@app.route('/api/chat/sessions', methods=['GET'])
def get_user_chat_sessions():
    """
    获取用户的所有聊天会话
    :return: 会话列表
    """
    try:
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 20))
        
        if not user_id:
            return make_err_response('缺少user_id参数')
        
        # 获取用户会话
        sessions = get_user_sessions(user_id, limit)
        
        # 按会话ID分组
        session_dict = {}
        for msg in sessions:
            if msg.session_id not in session_dict:
                session_dict[msg.session_id] = {
                    'session_id': msg.session_id,
                    'title': msg.session_title or f'对话 {msg.session_id[:8]}',
                    'last_message': msg.message,
                    'last_time': msg.created_at.isoformat(),
                    'message_count': 0
                }
            session_dict[msg.session_id]['message_count'] += 1
        
        # 转换为列表
        sessions_list = list(session_dict.values())
        
        return make_succ_response({
            'message': '获取会话列表成功',
            'data': {
                'sessions': sessions_list,
                'count': len(sessions_list)
            }
        })
        
    except Exception as e:
        logger.error(f'获取会话列表失败: {str(e)}')
        return make_err_response(f'获取会话列表失败: {str(e)}')


@app.route('/api/chat/test', methods=['POST'])
def test_chat_agents():
    """
    测试两个智能体自动对话功能
    :return: 测试结果
    """
    try:
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 创建智能体管理器
        agent_manager = AgentManager(user_id)
        
        # 生成自动对话（不保存到数据库，仅测试）
        responses = agent_manager.generate_auto_conversation([])
        
        return make_succ_response({
            'message': '智能体自动对话测试成功',
            'data': {
                'user_id': user_id,
                'conversation': responses,
                'test_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f'智能体自动对话测试失败: {str(e)}')
        return make_err_response(f'智能体自动对话测试失败: {str(e)}')


@app.route('/api/chat/multi-round', methods=['POST'])
def test_multi_round_conversation():
    """
    测试多轮智能体对话（流式推送）
    :return: 流式响应
    """
    try:
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        min_rounds = params.get('min_rounds', 10)
        max_rounds = params.get('max_rounds', 20)
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 创建智能体管理器
        agent_manager = AgentManager(user_id)
        
        def generate_stream():
            try:
                # 发送开始信号
                yield f"data: {json.dumps({'type': 'start', 'min_rounds': min_rounds, 'max_rounds': max_rounds})}\n\n"
                
                # 逐句生成并推送对话
                message_count = 0
                for message in agent_manager.generate_multi_round_conversation_stream(min_rounds, max_rounds):
                    message_count += 1
                    yield f"data: {json.dumps({'type': 'message', 'data': message})}\n\n"
                    import time
                    time.sleep(1)  # 每句话间隔1秒，模拟真实对话节奏
                
                # 发送结束信号
                yield f"data: {json.dumps({'type': 'end', 'summary': {'total_messages': message_count}})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        logger.error(f'多轮对话测试失败: {str(e)}')
        return make_err_response(f'多轮对话测试失败: {str(e)}')


@app.route('/api/chat/test-plan', methods=['POST'])
def test_conversation_plan():
    """
    测试对话计划生成功能
    :return: 对话计划
    """
    try:
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'min_rounds', 'max_rounds']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        min_rounds = params['min_rounds']
        max_rounds = params['max_rounds']
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 创建智能体管理器
        agent_manager = AgentManager(user_id)
        
        # 生成对话计划
        plan = agent_manager.generate_conversation_plan(min_rounds, max_rounds)
        
        return make_succ_response({
            'message': '对话计划生成成功',
            'data': {
                'user_id': user_id,
                'plan': plan,
                'test_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f'对话计划测试失败: {str(e)}')
        return make_err_response(f'对话计划测试失败: {str(e)}')


@app.route('/api/chat/test-simple', methods=['GET'])
def test_chat_simple():
    """
    简单测试智能体对话功能（不需要用户数据）
    :return: 测试结果
    """
    try:
        # 从请求参数获取用户ID
        test_user_id = request.args.get('user_id')
        if not test_user_id:
            return make_err_response('缺少必需参数: user_id')
        
        # 创建智能体管理器
        agent_manager = AgentManager(test_user_id)
        
        # 测试消息
        test_message = "我们这次去哪里旅行呢？"
        
        # 生成伙伴回复
        responses = agent_manager.generate_responses_by_user_input(test_message, [])
        
        return make_succ_response({
            'message': '简单智能体对话测试成功',
            'data': {
                'test_user_id': test_user_id,
                'avatar_message': responses['avatar_message'],
                'partner_response': responses['partner_response'],
                'test_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f'简单智能体对话测试失败: {str(e)}')
        return make_err_response(f'简单智能体对话测试失败: {str(e)}')


@app.route('/api/chat/auto', methods=['POST'])
def start_auto_conversation():
    """
    开始自动对话（分身和伙伴自动聊天）
    :return: 自动对话结果
    """
    try:
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'session_id']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        session_id = params['session_id']
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        if not session_id.strip():
            return make_err_response('会话ID不能为空')
        
        # 获取对话历史
        conversation_history = get_chat_messages_by_session(user_id, session_id, limit=20)
        history_data = []
        for msg in conversation_history:
            history_data.append({
                'speaker_type': msg.speaker_type,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        # 创建智能体管理器并生成自动对话
        agent_manager = AgentManager(user_id)
        responses = agent_manager.generate_auto_conversation(history_data)
        
        # 记录自动对话消息
        if 'avatar_message' in responses:
            avatar_msg = ChatMessages(
                user_id=user_id,
                session_id=session_id,
                speaker_type='avatar',
                message=responses['avatar_message']
            )
            insert_chat_message(avatar_msg)
        
        if 'partner_response' in responses:
            partner_msg = ChatMessages(
                user_id=user_id,
                session_id=session_id,
                speaker_type='partner',
                message=responses['partner_response']
            )
            insert_chat_message(partner_msg)
        
        if 'avatar_response' in responses:
            avatar_continue_msg = ChatMessages(
                user_id=user_id,
                session_id=session_id,
                speaker_type='avatar',
                message=responses['avatar_response']
            )
            insert_chat_message(avatar_continue_msg)
        
        return make_succ_response({
            'message': '自动对话生成成功',
            'data': responses
        })
        
    except Exception as e:
        logger.error(f'自动对话生成失败: {str(e)}')
        return make_err_response(f'自动对话生成失败: {str(e)}')
