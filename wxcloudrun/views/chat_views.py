from datetime import datetime
import json
import logging
from flask import request, Response, Blueprint
from run import app
from wxcloudrun.dao import insert_chat_message, get_chat_messages_by_session, get_user_sessions
from wxcloudrun.model import ChatMessages
from wxcloudrun.agents.agent_manager import AgentManager
from wxcloudrun.response import make_succ_response, make_err_response

# 初始化日志
logger = logging.getLogger('log')

# 创建蓝图
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


def _generate_auto_conversation_stream(user_id, session_id, history_data):
    """生成自动对话流（内部函数）"""
    try:
        # 创建智能体管理器
        agent_manager = AgentManager(user_id)
        
        # 发送开始信号
        start_event = {
            'type': 'start',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        yield f"data: {json.dumps(start_event)}\n\n"
        
        # 生成自动对话流
        message_count = 0
        for message_data in agent_manager.generate_multi_round_conversation_stream(history_data):
            # 过滤掉系统消息，只处理对话消息
            if message_data['speaker_type'] == 'system':
                continue
                
            # 保存到数据库
            msg = ChatMessages(
                user_id=user_id,
                session_id=session_id,
                speaker_type=message_data['speaker_type'],
                message=message_data['message']
            )
            insert_chat_message(msg)
            
            # 发送到前端
            message_event = {
                'type': 'message',
                'speaker_type': message_data['speaker_type'],
                'message': message_data['message'],
                'timestamp': datetime.now().isoformat()
            }
            yield f"data: {json.dumps(message_event)}\n\n"
            message_count += 1
        
        # 发送结束信号
        end_event = {
            'type': 'end',
            'total_messages': message_count,
            'timestamp': datetime.now().isoformat()
        }
        yield f"data: {json.dumps(end_event)}\n\n"
        
    except Exception as e:
        error_event = {
            'type': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        yield f"data: {json.dumps(error_event)}\n\n"


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
        
        # 记录用户消息（用户替分身说话）
        user_msg = ChatMessages(
            user_id=user_id,
            session_id=session_id,
            speaker_type='user',
            message=message
        )
        insert_chat_message(user_msg)
        
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
                'user_message': responses['user_message'],
                'partner_response': responses['partner_response']
            }
        })
        
    except Exception as e:
        logger.error(f'发送聊天消息失败: {str(e)}')
        return make_err_response(f'发送聊天消息失败: {str(e)}')



@chat_bp.route('/auto', methods=['POST'])
def start_auto_conversation():
    """
    开始自动对话（分身和伙伴自动聊天）
    :return: 流式响应
    """
    try:
        logger.info(f"[CHAT_API] 收到自动对话请求")
        logger.info(f"[CHAT_API] 请求来源: {request.remote_addr}")
        logger.info(f"[CHAT_API] 请求头: {dict(request.headers)}")
        
        params = request.get_json()
        logger.info(f"[CHAT_API] 请求参数: {params}")
        
        if not params:
            logger.error("[CHAT_API] 请求体为空")
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'session_id']
        for field in required_fields:
            if field not in params:
                logger.error(f"[CHAT_API] 缺少必需参数: {field}")
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        session_id = params['session_id']
        
        logger.info(f"[CHAT_API] 用户ID: {user_id}, 会话ID: {session_id}")
        
        # 验证参数
        if not user_id.strip():
            logger.error("[CHAT_API] 用户ID为空")
            return make_err_response('用户ID不能为空')
        if not session_id.strip():
            logger.error("[CHAT_API] 会话ID为空")
            return make_err_response('会话ID不能为空')
        
        # 获取对话历史
        logger.info(f"[CHAT_API] 开始获取对话历史")
        conversation_history = get_chat_messages_by_session(user_id, session_id, limit=20)
        history_data = []
        for msg in conversation_history:
            history_data.append({
                'speaker_type': msg.speaker_type,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        logger.info(f"[CHAT_API] 对话历史数量: {len(history_data)}")
        
        # 创建智能体管理器并生成所有消息
        logger.info(f"[CHAT_API] 开始创建智能体管理器")
        agent_manager = AgentManager(user_id)
        
        logger.info(f"[CHAT_API] 开始生成多轮对话")
        messages = []
        message_count = 0
        for message_data in agent_manager.generate_multi_round_conversation_stream(history_data):
            # 过滤掉系统消息，只处理对话消息
            if message_data['speaker_type'] == 'system':
                logger.info(f"[CHAT_API] 跳过系统消息")
                continue
            
            message_count += 1
            logger.info(f"[CHAT_API] 处理消息 #{message_count}: {message_data['speaker_type']}")
                
            # 保存到数据库
            try:
                msg = ChatMessages(
                    user_id=user_id,
                    session_id=session_id,
                    speaker_type=message_data['speaker_type'],
                    message=message_data['message']
                )
                insert_chat_message(msg)
                logger.info(f"[CHAT_API] 消息保存成功")
            except Exception as e:
                logger.error(f"[CHAT_API] 消息保存失败: {str(e)}")
            
            # 添加到消息列表
            messages.append({
                'speaker_type': message_data['speaker_type'],
                'message': message_data['message'],
                'created_at': datetime.now().isoformat()
            })
        
        logger.info(f"[CHAT_API] 对话生成完成，消息数量: {len(messages)}")
        
        response_data = {
            'message': '自动对话生成成功',
            'data': {
                'messages': messages,
                'total_messages': len(messages)
            }
        }
        
        logger.info(f"[CHAT_API] 准备返回响应，消息数量: {len(messages)}")
        return make_succ_response(response_data)
        
    except Exception as e:
        logger.error(f'[CHAT_API] 自动对话生成失败: {str(e)}')
        logger.error(f'[CHAT_API] 错误类型: {type(e).__name__}')
        import traceback
        logger.error(f'[CHAT_API] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'自动对话生成失败: {str(e)}')



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


# 注册蓝图
app.register_blueprint(chat_bp)
