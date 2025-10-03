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


@react_chat_bp.route('/auto', methods=['POST'])
def start_react_auto_conversation():
    """
    开始React模式自动对话
    :return: React模式自动对话结果
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
        
        # 创建智能体管理器并生成React对话
        logger.info(f"[REACT_API] 开始创建智能体管理器")
        agent_manager = AgentManager(user_id)
        
        min_rounds = params.get('min_rounds', 3)
        max_rounds = params.get('max_rounds', 6)
        logger.info(f"[REACT_API] 对话参数: min_rounds={min_rounds}, max_rounds={max_rounds}")
        
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
        
    except Exception as e:
        logger.error(f'[REACT_API] React模式自动对话生成失败: {str(e)}')
        logger.error(f'[REACT_API] 错误类型: {type(e).__name__}')
        import traceback
        logger.error(f'[REACT_API] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'React模式自动对话生成失败: {str(e)}')


@react_chat_bp.route('/auto/stream', methods=['POST'])
def start_react_auto_conversation_stream():
    """
    开始React模式自动对话流（SSE）
    :return: React模式自动对话流
    """
    try:
        logger.info(f"[REACT_API_STREAM] 收到React自动对话流请求")
        logger.info(f"[REACT_API_STREAM] 请求来源: {request.remote_addr}")
        
        params = request.get_json()
        logger.info(f"[REACT_API_STREAM] 请求参数: {params}")
        
        if not params:
            logger.error("[REACT_API_STREAM] 请求体为空")
            return make_err_response('请求体不能为空')
        
        required_fields = ['user_id', 'session_id']
        for field in required_fields:
            if field not in params:
                logger.error(f"[REACT_API_STREAM] 缺少必需参数: {field}")
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        session_id = params['session_id']
        
        logger.info(f"[REACT_API_STREAM] 用户ID: {user_id}, 会话ID: {session_id}")
        
        if not user_id.strip():
            logger.error("[REACT_API_STREAM] 用户ID为空")
            return make_err_response('用户ID不能为空')
        if not session_id.strip():
            logger.error("[REACT_API_STREAM] 会话ID为空")
            return make_err_response('会话ID不能为空')
        
        def generate_stream():
            try:
                logger.info(f"[REACT_API_STREAM] 开始生成流式对话")
                # 创建智能体管理器
                agent_manager = AgentManager(user_id)
                
                min_rounds = params.get('min_rounds', 3)
                max_rounds = params.get('max_rounds', 6)
                logger.info(f"[REACT_API_STREAM] 对话参数: min_rounds={min_rounds}, max_rounds={max_rounds}")
                
                message_count = 0
                # 生成React对话流
                for message_data in agent_manager.generate_react_conversation_stream(
                    min_rounds=min_rounds,
                    max_rounds=max_rounds
                ):
                    # 过滤掉系统消息，只处理对话消息
                    if message_data['speaker_type'] == 'system':
                        logger.info(f"[REACT_API_STREAM] 跳过系统消息")
                        continue
                    
                    message_count += 1
                    logger.info(f"[REACT_API_STREAM] 处理消息 #{message_count}: {message_data['speaker_type']}")
                    
                    # 保存到数据库
                    try:
                        msg = ChatMessages(
                            user_id=user_id,
                            session_id=session_id,
                            speaker_type=message_data['speaker_type'],
                            message=message_data['message']
                        )
                        insert_chat_message(msg)
                        logger.info(f"[REACT_API_STREAM] 消息保存成功")
                    except Exception as e:
                        logger.error(f"[REACT_API_STREAM] 消息保存失败: {str(e)}")
                    
                    # 发送SSE事件
                    event_data = {
                        'speaker_type': message_data['speaker_type'],
                        'message': message_data['message'],
                        'timestamp': datetime.now().isoformat(),
                        'metadata': message_data.get('metadata', {})
                    }
                    
                    logger.info(f"[REACT_API_STREAM] 发送SSE事件: {message_data['speaker_type']}")
                    yield f"data: {event_data}\n\n"
                
                logger.info(f"[REACT_API_STREAM] 流式对话完成，总消息数: {message_count}")
                # 发送结束事件
                yield f"data: {None}\n\n"
                
            except Exception as e:
                logger.error(f'[REACT_API_STREAM] React对话流生成异常: {str(e)}')
                logger.error(f'[REACT_API_STREAM] 错误类型: {type(e).__name__}')
                import traceback
                logger.error(f'[REACT_API_STREAM] 错误堆栈: {traceback.format_exc()}')
                yield f"data: {{'error': '对话流生成失败: {str(e)}'}}\n\n"
        
        return Response(generate_stream(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        })
        
    except Exception as e:
        logger.error(f'[REACT_API_STREAM] React模式自动对话流启动失败: {str(e)}')
        logger.error(f'[REACT_API_STREAM] 错误类型: {type(e).__name__}')
        import traceback
        logger.error(f'[REACT_API_STREAM] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'React模式自动对话流启动失败: {str(e)}')


@react_chat_bp.route('/debug', methods=['POST'])
def get_react_conversation_debug():
    """
    获取React对话调试信息
    :return: 调试信息
    """
    try:
        logger.info(f"[REACT_API_DEBUG] 收到调试信息请求")
        logger.info(f"[REACT_API_DEBUG] 请求来源: {request.remote_addr}")
        
        params = request.get_json()
        logger.info(f"[REACT_API_DEBUG] 请求参数: {params}")
        
        if not params:
            logger.error("[REACT_API_DEBUG] 请求体为空")
            return make_err_response('请求体不能为空')
        
        user_id = params.get('user_id')
        if not user_id:
            logger.error("[REACT_API_DEBUG] 缺少用户ID")
            return make_err_response('缺少用户ID')
        
        logger.info(f"[REACT_API_DEBUG] 用户ID: {user_id}")
        
        # 创建智能体管理器
        logger.info(f"[REACT_API_DEBUG] 开始获取调试信息")
        agent_manager = AgentManager(user_id)
        debug_info = agent_manager.get_react_conversation_debug()
        
        logger.info(f"[REACT_API_DEBUG] 调试信息获取成功")
        return make_succ_response({
            'message': '调试信息获取成功',
            'data': debug_info
        })
        
    except Exception as e:
        logger.error(f'[REACT_API_DEBUG] 获取React对话调试信息失败: {str(e)}')
        logger.error(f'[REACT_API_DEBUG] 错误类型: {type(e).__name__}')
        import traceback
        logger.error(f'[REACT_API_DEBUG] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'获取React对话调试信息失败: {str(e)}')


@react_chat_bp.route('/reset', methods=['POST'])
def reset_react_conversation():
    """
    重置React对话
    :return: 重置结果
    """
    try:
        logger.info(f"[REACT_API_RESET] 收到重置对话请求")
        logger.info(f"[REACT_API_RESET] 请求来源: {request.remote_addr}")
        
        params = request.get_json()
        logger.info(f"[REACT_API_RESET] 请求参数: {params}")
        
        if not params:
            logger.error("[REACT_API_RESET] 请求体为空")
            return make_err_response('请求体不能为空')
        
        user_id = params.get('user_id')
        if not user_id:
            logger.error("[REACT_API_RESET] 缺少用户ID")
            return make_err_response('缺少用户ID')
        
        logger.info(f"[REACT_API_RESET] 用户ID: {user_id}")
        
        # 创建智能体管理器
        logger.info(f"[REACT_API_RESET] 开始重置对话")
        agent_manager = AgentManager(user_id)
        agent_manager.reset_react_conversation()
        
        logger.info(f"[REACT_API_RESET] 对话重置成功")
        return make_succ_response({
            'message': 'React对话重置成功',
            'data': {'user_id': user_id}
        })
        
    except Exception as e:
        logger.error(f'[REACT_API_RESET] 重置React对话失败: {str(e)}')
        logger.error(f'[REACT_API_RESET] 错误类型: {type(e).__name__}')
        import traceback
        logger.error(f'[REACT_API_RESET] 错误堆栈: {traceback.format_exc()}')
        return make_err_response(f'重置React对话失败: {str(e)}')


# 蓝图注册在 wxcloudrun/__init__.py 中完成
