"""
React模式对话系统的API接口
"""

import logging
from datetime import datetime
from flask import request, Response, Blueprint
from run import app
from wxcloudrun.dao import insert_chat_message, get_chat_messages_by_session
from wxcloudrun.model import ChatMessages
from wxcloudrun.agents.agent_manager import AgentManager
from wxcloudrun.response import make_succ_response, make_err_response

# 初始化日志
logger = logging.getLogger('log')

# 创建蓝图
react_chat_bp = Blueprint('react_chat', __name__, url_prefix='/api/react_chat')


@react_chat_bp.route('/auto', methods=['POST'])
def start_react_auto_conversation():
    """
    开始React模式自动对话
    :return: React模式自动对话结果
    """
    try:
        params = request.get_json()
        if not params:
            return make_err_response('请求体不能为空')
        
        required_fields = ['user_id', 'session_id']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        session_id = params['session_id']
        
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
        
        # 创建智能体管理器并生成React对话
        agent_manager = AgentManager(user_id)
        result = agent_manager.generate_react_conversation_sync(
            min_rounds=params.get('min_rounds', 3),
            max_rounds=params.get('max_rounds', 6)
        )
        
        # 保存消息到数据库
        messages = []
        for message_data in result['messages']:
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
            
            # 添加到消息列表
            messages.append({
                'speaker_type': message_data['speaker_type'],
                'message': message_data['message'],
                'created_at': datetime.now().isoformat(),
                'metadata': message_data.get('metadata', {})
            })
        
        return make_succ_response({
            'message': 'React模式自动对话生成成功',
            'data': {
                'messages': messages,
                'total_messages': len(messages),
                'conversation_summary': result['summary'],
                'mode': 'react'
            }
        })
        
    except Exception as e:
        logger.error(f'React模式自动对话生成失败: {str(e)}')
        return make_err_response(f'React模式自动对话生成失败: {str(e)}')


@react_chat_bp.route('/auto/stream', methods=['POST'])
def start_react_auto_conversation_stream():
    """
    开始React模式自动对话流（SSE）
    :return: React模式自动对话流
    """
    try:
        params = request.get_json()
        if not params:
            return make_err_response('请求体不能为空')
        
        required_fields = ['user_id', 'session_id']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        session_id = params['session_id']
        
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        if not session_id.strip():
            return make_err_response('会话ID不能为空')
        
        def generate_stream():
            try:
                # 创建智能体管理器
                agent_manager = AgentManager(user_id)
                
                # 生成React对话流
                for message_data in agent_manager.generate_react_conversation_stream(
                    min_rounds=params.get('min_rounds', 3),
                    max_rounds=params.get('max_rounds', 6)
                ):
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
                    
                    # 发送SSE事件
                    event_data = {
                        'speaker_type': message_data['speaker_type'],
                        'message': message_data['message'],
                        'timestamp': datetime.now().isoformat(),
                        'metadata': message_data.get('metadata', {})
                    }
                    
                    yield f"data: {event_data}\n\n"
                
                # 发送结束事件
                yield f"data: {None}\n\n"
                
            except Exception as e:
                logger.error(f'React对话流生成异常: {str(e)}')
                yield f"data: {{'error': '对话流生成失败: {str(e)}'}}\n\n"
        
        return Response(generate_stream(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        })
        
    except Exception as e:
        logger.error(f'React模式自动对话流启动失败: {str(e)}')
        return make_err_response(f'React模式自动对话流启动失败: {str(e)}')


@react_chat_bp.route('/debug', methods=['POST'])
def get_react_conversation_debug():
    """
    获取React对话调试信息
    :return: 调试信息
    """
    try:
        params = request.get_json()
        if not params:
            return make_err_response('请求体不能为空')
        
        user_id = params.get('user_id')
        if not user_id:
            return make_err_response('缺少用户ID')
        
        # 创建智能体管理器
        agent_manager = AgentManager(user_id)
        debug_info = agent_manager.get_react_conversation_debug()
        
        return make_succ_response({
            'message': '调试信息获取成功',
            'data': debug_info
        })
        
    except Exception as e:
        logger.error(f'获取React对话调试信息失败: {str(e)}')
        return make_err_response(f'获取React对话调试信息失败: {str(e)}')


@react_chat_bp.route('/reset', methods=['POST'])
def reset_react_conversation():
    """
    重置React对话
    :return: 重置结果
    """
    try:
        params = request.get_json()
        if not params:
            return make_err_response('请求体不能为空')
        
        user_id = params.get('user_id')
        if not user_id:
            return make_err_response('缺少用户ID')
        
        # 创建智能体管理器
        agent_manager = AgentManager(user_id)
        agent_manager.reset_react_conversation()
        
        return make_succ_response({
            'message': 'React对话重置成功',
            'data': {'user_id': user_id}
        })
        
    except Exception as e:
        logger.error(f'重置React对话失败: {str(e)}')
        return make_err_response(f'重置React对话失败: {str(e)}')


# 蓝图注册在 wxcloudrun/__init__.py 中完成
