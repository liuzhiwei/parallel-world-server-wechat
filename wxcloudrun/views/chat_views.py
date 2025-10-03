from datetime import datetime
import json
import logging
from flask import request, Response
from run import app
from wxcloudrun.dao import insert_chat_message, get_chat_messages_by_session, get_user_sessions
from wxcloudrun.model import ChatMessages
from wxcloudrun.agent_manager import AgentManager
from wxcloudrun.response import make_succ_response, make_err_response

# 初始化日志
logger = logging.getLogger('log')

# 创建蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/send', methods=['POST'])
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


@chat_bp.route('/history', methods=['GET'])
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


@chat_bp.route('/sessions', methods=['GET'])
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


@chat_bp.route('/test', methods=['POST'])
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


@chat_bp.route('/multi-round', methods=['POST'])
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


@chat_bp.route('/test-plan', methods=['POST'])
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


@chat_bp.route('/test-simple', methods=['GET'])
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


@chat_bp.route('/auto', methods=['POST'])
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
        
        # 准备返回数据，包含历史消息和新消息
        all_messages = []
        
        # 添加历史消息
        for msg in conversation_history:
            all_messages.append({
                'speaker_type': msg.speaker_type,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        # 添加新生成的消息
        if 'avatar_message' in responses:
            all_messages.append({
                'speaker_type': 'avatar',
                'message': responses['avatar_message'],
                'created_at': datetime.now().isoformat()
            })
        
        if 'partner_response' in responses:
            all_messages.append({
                'speaker_type': 'partner',
                'message': responses['partner_response'],
                'created_at': datetime.now().isoformat()
            })
        
        if 'avatar_response' in responses:
            all_messages.append({
                'speaker_type': 'avatar',
                'message': responses['avatar_response'],
                'created_at': datetime.now().isoformat()
            })
        
        return make_succ_response({
            'message': '自动对话生成成功',
            'data': {
                'messages': all_messages,
                'new_responses': responses
            }
        })
        
    except Exception as e:
        logger.error(f'自动对话生成失败: {str(e)}')
        return make_err_response(f'自动对话生成失败: {str(e)}')

# 注册蓝图
app.register_blueprint(chat_bp)
