from flask import Blueprint, request, jsonify
import logging
import time
from wxcloudrun.agent.dialogue_context import DialogueContext

logger = logging.getLogger(__name__)

# 创建测试蓝图
test_bp = Blueprint('test', __name__, url_prefix='/test')


@test_bp.route('/ping', methods=['GET'])
def test_ping():
    """简单的ping测试"""
    return jsonify({
        'code': 0,
        'message': 'Test blueprint is working',
        'timestamp': time.time()
    })


@test_bp.route('/step', methods=['POST'])
def test_step():
    """
    测试 DialogueController 的 step 方法
    
    请求体示例:
    {
        "user_id": "test_user_123"
    }
    
    返回示例:
    {
        "code": 0,
        "data": {
            "reply": {...},
            "context": {...}
        }
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': -1,
                'errorMsg': 'user_id is required'
            }), 400
        
        # 创建 DialogueController 实例
        from wxcloudrun.agent.dialogue_controller import DialogueController
        controller = DialogueController()
        
        # 执行 step 方法
        reply = controller.step(user_id)
        
        if reply is None:
            return jsonify({
                'code': -1,
                'errorMsg': 'Step execution failed, check logs for details'
            }), 500
        
        # 获取上下文信息用于调试
        context = controller.user_context.get(user_id)
        context_info = {}
        if context:
            context_info = {
                'user_id': context.user_id,
                'current_topic': context.current_topic,
                'avatar_name': context.get_avatar_name(),
                'partner_name': context.get_partner_name(),
                'destination': context.get_travel_destination(),
                'history_count': len(context.history)
            }
        
        return jsonify({
            'code': 0,
            'data': {
                'reply': reply,
                'context': context_info
            }
        })
        
    except Exception as e:
        logger.error(f"Test step failed: {e}", exc_info=True)
        return jsonify({
            'code': -1,
            'errorMsg': f'Test failed: {str(e)}'
        }), 500


@test_bp.route('/context', methods=['POST'])
def test_context():
    """
    测试 DialogueContext 的构建
    
    请求体示例:
    {
        "user_id": "test_user_123"
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': -1,
                'errorMsg': 'user_id is required'
            }), 400
        
        # 创建并构建对话上下文
        context = DialogueContext(user_id)
        context.build()
        
        return jsonify({
            'code': 0,
            'data': {
                'user_id': context.user_id,
                'current_topic': context.current_topic,
                'topic_history': context.topic_history,
                'avatar': {
                    'name': context.get_avatar_name(),
                    'description': context.get_avatar_description()
                } if context.digital_avatar else None,
                'partner': {
                    'name': context.get_partner_name(),
                    'description': context.get_partner_description()
                } if context.travel_partner else None,
                'travel_settings': {
                    'destination': context.get_travel_destination(),
                    'days': context.get_travel_days(),
                    'preference': context.get_travel_preference()
                } if context.travel_settings else None,
                'history_count': len(context.history),
                'recent_history': [
                    {
                        'speaker_id': h.speaker_id,
                        'speaker_type': h.speaker_type,
                        'message': h.message_content
                    } for h in context.get_recent_history(5)
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Test context failed: {e}", exc_info=True)
        return jsonify({
            'code': -1,
            'errorMsg': f'Test failed: {str(e)}'
        }), 500

