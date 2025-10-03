from datetime import datetime
import json
import logging
from flask import request, Response, Blueprint
from run import app
from wxcloudrun.dao import insert_chat_message, get_chat_messages_by_session
from wxcloudrun.model import ChatMessages
from wxcloudrun.agents.agent_manager import AgentManager
from wxcloudrun.response import make_succ_response, make_err_response

# 初始化日志
logger = logging.getLogger('log')

# 创建蓝图
chat_test_bp = Blueprint('chat_test', __name__, url_prefix='/api/chat/test')


@chat_test_bp.route('/agents', methods=['POST'])
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


@chat_test_bp.route('/multi-round', methods=['POST'])
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


@chat_test_bp.route('/plan', methods=['POST'])
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


@chat_test_bp.route('/simple', methods=['GET'])
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
                'user_message': responses['user_message'],
                'partner_response': responses['partner_response'],
                'test_time': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f'简单智能体对话测试失败: {str(e)}')
        return make_err_response(f'简单智能体对话测试失败: {str(e)}')


# 注册蓝图
app.register_blueprint(chat_test_bp)
