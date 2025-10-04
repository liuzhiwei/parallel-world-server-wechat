"""
React模式对话系统的API接口
"""

import logging
import json
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


@react_chat_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        logger.info(f"[REACT_API] ========== 收到健康检查请求 ==========")
        logger.info(f"[REACT_API] 请求来源: {request.remote_addr}")
        logger.info(f"[REACT_API] 请求方法: {request.method}")
        logger.info(f"[REACT_API] 请求URL: {request.url}")
        
        response_data = {
            'status': 'healthy',
            'message': 'React API is working',
            'timestamp': datetime.now().isoformat(),
            'routes': [
                '/api/react_chat/health',
                '/api/react_chat/auto',
                '/api/react_chat/debug',
                '/api/react_chat/reset'
            ]
        }
        
        logger.info(f"[REACT_API] 健康检查成功，返回数据: {response_data}")
        return make_succ_response(response_data)
    except Exception as e:
        logger.error(f'[REACT_API] 健康检查失败: {str(e)}')
        import traceback
        logger.error(f'[REACT_API] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'健康检查失败: {str(e)}')


@react_chat_bp.route('/test', methods=['POST'])
def test_react_api():
    """测试React API接口"""
    try:
        logger.info(f"[REACT_API] ========== 收到测试请求 ==========")
        logger.info(f"[REACT_API] 请求来源: {request.remote_addr}")
        logger.info(f"[REACT_API] 请求方法: {request.method}")
        logger.info(f"[REACT_API] 请求URL: {request.url}")
        logger.info(f"[REACT_API] 请求头: {dict(request.headers)}")
        
        params = request.get_json()
        logger.info(f"[REACT_API] 请求参数: {params}")
        
        response_data = {
            'status': 'success',
            'message': 'React API test successful',
            'received_params': params,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"[REACT_API] 测试成功，返回数据: {response_data}")
        return make_succ_response(response_data)
    except Exception as e:
        logger.error(f'[REACT_API] 测试失败: {str(e)}')
        import traceback
        logger.error(f'[REACT_API] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'测试失败: {str(e)}')


@react_chat_bp.route('/simple', methods=['POST'])
def simple_test():
    """简单测试接口"""
    try:
        logger.info(f"[SIMPLE_API] 收到简单测试请求")
        
        response_data = {
            'message': '简单测试成功',
            'data': {
                'messages': [
                    {
                        'speaker_type': 'avatar',
                        'message': '这是一个简单的测试消息',
                        'created_at': datetime.now().isoformat()
                    }
                ],
                'total_messages': 1,
                'mode': 'simple'
            }
        }
        
        logger.info(f"[SIMPLE_API] 准备返回简单响应")
        response = make_succ_response(response_data)
        logger.info(f"[SIMPLE_API] 响应构造完成")
        return response
        
    except Exception as e:
        logger.error(f'[SIMPLE_API] 简单测试失败: {str(e)}')
        return make_err_response(f'简单测试失败: {str(e)}')


@react_chat_bp.route('/auto', methods=['POST'])
def start_react_auto_conversation():
    """
    开始React模式自动对话 - 使用WebSocket推送消息
    :return: 立即返回成功状态，通过WebSocket推送消息
    """
    try:
        logger.info(f"[REACT_API] ========== 收到React自动对话请求 ==========")
        logger.info(f"[REACT_API] 请求来源: {request.remote_addr}")
        logger.info(f"[REACT_API] 请求方法: {request.method}")
        logger.info(f"[REACT_API] 请求URL: {request.url}")
        logger.info(f"[REACT_API] 请求头: {dict(request.headers)}")
        logger.info(f"[REACT_API] 请求数据大小: {len(request.get_data())} 字节")
        
        params = request.get_json()
        logger.info(f"[REACT_API] 请求参数: {params}")
        
        if not params:
            logger.warning(f"[REACT_API] 请求参数为空")
            return make_err_response('请求参数不能为空')
        
        required_fields = ['user_id', 'session_id']
        for field in required_fields:
            if field not in params:
                logger.error(f"[REACT_API] 缺少必需参数: {field}")
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        session_id = params['session_id']
        
        logger.info(f"[REACT_API] 用户ID: {user_id}, 会话ID: {session_id}")
        
        if not user_id.strip():
            logger.error("[REACT_API] 用户ID为空")
            return make_err_response('用户ID不能为空')
        if not session_id.strip():
            logger.error("[REACT_API] 会话ID为空")
            return make_err_response('会话ID不能为空')
        
        # 获取对话历史
        logger.info(f"[REACT_API] 开始获取对话历史")
        conversation_history = get_chat_messages_by_session(user_id, session_id, limit=20)
        history_data = []
        for msg in conversation_history:
            history_data.append({
                'speaker_type': msg.speaker_type,
                'message': msg.message,
                'created_at': msg.created_at.isoformat()
            })
        
        logger.info(f"[REACT_API] 对话历史数量: {len(history_data)}")
        
        # 创建智能体管理器
        logger.info(f"[REACT_API] 开始创建智能体管理器")
        agent_manager = AgentManager(user_id)
        
        min_rounds = params.get('min_rounds', 3)
        max_rounds = params.get('max_rounds', 6)
        logger.info(f"[REACT_API] 对话参数: min_rounds={min_rounds}, max_rounds={max_rounds}")
        
        logger.info(f"[REACT_API] 开始生成WebSocket对话")
        
        # 立即返回成功，然后通过WebSocket推送消息
        response_data = {
            'message': 'WebSocket连接已建立，开始推送消息',
            'session_id': session_id,
            'status': 'connected'
        }
        
        logger.info(f"[REACT_API] 返回连接成功响应，准备推送WebSocket消息")
        
        # 异步推送消息到WebSocket
        import threading
        def push_messages():
            import time
            time.sleep(1)  # 等待连接建立
            
            # 测试用固定消息
            test_messages = [
                {
                    'speaker_type': 'avatar',
                    'message': '你好！我是你的旅行分身，很高兴为你规划这次旅行！',
                    'created_at': datetime.now().isoformat(),
                    'avatar_url': 'https://example.com/avatar.png',
                    'name': '旅行分身',
                    'metadata': {'test': True, 'round': 1}
                }
            ]
            
            # 通过WebSocket推送消息
            from wxcloudrun import socketio
            for i, msg in enumerate(test_messages):
                time.sleep(1)  # 模拟消息间隔
                
                logger.info(f"[REACT_API] WebSocket推送消息 {i+1}/{len(test_messages)}: {msg['speaker_type']}")
                
                # 发送消息事件
                socketio.emit('message', {
                    'type': 'message',
                    'data': msg,
                    'index': i + 1,
                    'total': len(test_messages)
                }, room=session_id)
            
            # 发送完成事件
            logger.info(f"[REACT_API] WebSocket发送完成事件")
            socketio.emit('message', {
                'type': 'complete',
                'total_messages': len(test_messages)
            }, room=session_id)
        
        # 启动异步线程推送消息
        thread = threading.Thread(target=push_messages)
        thread.start()
        
        return make_succ_response(response_data)
        
        # 注释掉原来的AI生成逻辑，用于测试
        """
        logger.info(f"[REACT_API] 开始生成React对话")
        result = agent_manager.generate_react_conversation_sync(
            min_rounds=min_rounds,
            max_rounds=max_rounds
        )
        logger.info(f"[REACT_API] React对话生成完成，消息数量: {result.get('total_messages', 0)}")
        
        # 保存消息到数据库
        logger.info(f"[REACT_API] 开始保存消息到数据库")
        messages = []
        saved_count = 0
        for message_data in result['messages']:
            # 过滤掉系统消息，只处理对话消息
            if message_data['speaker_type'] == 'system':
                logger.info(f"[REACT_API] 跳过系统消息")
                continue
                
            # 保存到数据库
            try:
                msg = ChatMessages(
                    user_id=user_id,
                    session_id=session_id,
                    speaker_type=message_data['speaker_type'],
                    message=message_data['message']
                )
                insert_chat_message(msg)
                saved_count += 1
                logger.info(f"[REACT_API] 保存消息成功: {message_data['speaker_type']}")
            except Exception as e:
                logger.error(f"[REACT_API] 保存消息失败: {str(e)}")
            
            # 添加到消息列表
            messages.append({
                'speaker_type': message_data['speaker_type'],
                'message': message_data['message'],
                'created_at': datetime.now().isoformat(),
                'metadata': message_data.get('metadata', {})
            })
        
        logger.info(f"[REACT_API] 消息保存完成，保存数量: {saved_count}, 返回数量: {len(messages)}")
        
        response_data = {
            'message': 'React模式自动对话生成成功',
            'data': {
                'messages': messages,
                'total_messages': len(messages),
                'conversation_summary': result['summary'],
                'mode': 'react'
            }
        }
        
        logger.info(f"[REACT_API] 准备返回响应，消息数量: {len(messages)}")
        return make_succ_response(response_data)
        """
        
    except Exception as e:
        logger.error(f'[REACT_API] React模式自动对话生成失败: {str(e)}')
        logger.error(f'[REACT_API] 错误类型: {type(e).__name__}')
        import traceback
        logger.error(f'[REACT_API] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'React模式自动对话生成失败: {str(e)}')


# WebSocket 事件处理
from wxcloudrun import socketio

@socketio.on('connect')
def handle_connect():
    logger.info('[WEBSOCKET] 客户端连接')
    return True

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('[WEBSOCKET] 客户端断开连接')

@socketio.on('join')
def handle_join(data):
    session_id = data.get('session_id')
    if session_id:
        from flask_socketio import join_room
        join_room(session_id)
        logger.info(f'[WEBSOCKET] 客户端加入房间: {session_id}')
        socketio.emit('joined', {'room': session_id}, room=session_id)

# 蓝图注册在 wxcloudrun/__init__.py 中完成
