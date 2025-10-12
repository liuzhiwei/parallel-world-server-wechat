from flask import Blueprint, request, jsonify
import logging
import time
from wxcloudrun.agent.dialogue_context import DialogueContext
from wxcloudrun import db
from wxcloudrun.dbops.model import Users, DigitalAvatar, TravelPartner, TravelSettings, ChatMessages, ChatTopics

logger = logging.getLogger(__name__)

# 创建测试蓝图
test_bp = Blueprint('test', __name__, url_prefix='/test')


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


@test_bp.route('/delete-user-data', methods=['POST'])
def delete_user_data():
    """
    删除指定用户的所有数据
    
    请求体示例:
    {
        "user_id": "oGhac7X9Q6EbWaDpzozJUZBL2Ax4"
    }
    
    返回示例:
    {
        "code": 0,
        "message": "success",
        "data": {
            "deleted_counts": {
                "Users": 2,
                "DigitalAvatar": 1,
                "TravelPartner": 1,
                "TravelSettings": 1,
                "ChatMessages": 15,
                "ChatTopics": 3
            }
        }
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': -1,
                'message': 'user_id is required',
                'data': None
            }), 400
        
        logger.info(f"开始删除用户 {user_id} 的所有数据")
        
        # 记录删除前的数量
        deleted_counts = {}
        
        # 1. 删除 ChatMessages
        chat_messages_count = ChatMessages.query.filter(ChatMessages.user_id == user_id).count()
        if chat_messages_count > 0:
            ChatMessages.query.filter(ChatMessages.user_id == user_id).delete()
            deleted_counts['ChatMessages'] = chat_messages_count
            logger.info(f"删除 ChatMessages: {chat_messages_count} 条")
        
        # 2. 删除 ChatTopics
        chat_topics_count = ChatTopics.query.filter(ChatTopics.user_id == user_id).count()
        if chat_topics_count > 0:
            ChatTopics.query.filter(ChatTopics.user_id == user_id).delete()
            deleted_counts['ChatTopics'] = chat_topics_count
            logger.info(f"删除 ChatTopics: {chat_topics_count} 条")
        
        # 3. 删除 DigitalAvatar
        digital_avatar_count = DigitalAvatar.query.filter(DigitalAvatar.user_id == user_id).count()
        if digital_avatar_count > 0:
            DigitalAvatar.query.filter(DigitalAvatar.user_id == user_id).delete()
            deleted_counts['DigitalAvatar'] = digital_avatar_count
            logger.info(f"删除 DigitalAvatar: {digital_avatar_count} 条")
        
        # 4. 删除 TravelPartner
        travel_partner_count = TravelPartner.query.filter(TravelPartner.user_id == user_id).count()
        if travel_partner_count > 0:
            TravelPartner.query.filter(TravelPartner.user_id == user_id).delete()
            deleted_counts['TravelPartner'] = travel_partner_count
            logger.info(f"删除 TravelPartner: {travel_partner_count} 条")
        
        # 5. 删除 TravelSettings
        travel_settings_count = TravelSettings.query.filter(TravelSettings.user_id == user_id).count()
        if travel_settings_count > 0:
            TravelSettings.query.filter(TravelSettings.user_id == user_id).delete()
            deleted_counts['TravelSettings'] = travel_settings_count
            logger.info(f"删除 TravelSettings: {travel_settings_count} 条")
        
        # 6. 删除 Users (最后删除，因为其他表可能依赖它)
        users_count = Users.query.filter(Users.user_id == user_id).count()
        if users_count > 0:
            Users.query.filter(Users.user_id == user_id).delete()
            deleted_counts['Users'] = users_count
            logger.info(f"删除 Users: {users_count} 条")
        
        # 提交事务
        db.session.commit()
        
        logger.info(f"用户 {user_id} 数据删除完成: {deleted_counts}")
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'deleted_counts': deleted_counts,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户数据失败: {e}", exc_info=True)
        return jsonify({
            'code': -1,
            'message': f'删除失败: {str(e)}',
            'data': None
        }), 500


@test_bp.route('/query-user-data', methods=['POST'])
def query_user_data():
    """
    查询指定用户的所有数据
    
    请求体示例:
    {
        "user_id": "oGhac7X9Q6EbWaDpzozJUZBL2Ax4"
    }
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({
                'code': -1,
                'message': 'user_id is required',
                'data': None
            }), 400
        
        logger.info(f"查询用户 {user_id} 的所有数据")
        
        # 查询各表的数据
        counts = {}
        details = {}
        
        # 1. 查询 Users
        users = Users.query.filter(Users.user_id == user_id).all()
        counts['Users'] = len(users)
        details['Users'] = [
            {
                'id': u.id,
                'user_id': u.user_id,
                'session_id': u.session_id,
                'created_at': u.created_at.isoformat() if u.created_at else None
            } for u in users
        ]
        
        # 2. 查询 DigitalAvatar
        avatars = DigitalAvatar.query.filter(DigitalAvatar.user_id == user_id).all()
        counts['DigitalAvatar'] = len(avatars)
        details['DigitalAvatar'] = [
            {
                'id': a.id,
                'user_id': a.user_id,
                'avatar_id': a.avatar_id,
                'name': a.name,
                'description': a.description,
                'avatar_url': a.avatar_url,
                'created_at': a.created_at.isoformat() if a.created_at else None
            } for a in avatars
        ]
        
        # 3. 查询 TravelPartner
        partners = TravelPartner.query.filter(TravelPartner.user_id == user_id).all()
        counts['TravelPartner'] = len(partners)
        details['TravelPartner'] = [
            {
                'id': p.id,
                'user_id': p.user_id,
                'partner_id': p.partner_id,
                'partner_name': p.partner_name,
                'partner_description': p.partner_description,
                'partner_avatar_url': p.partner_avatar_url,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in partners
        ]
        
        # 4. 查询 TravelSettings
        settings = TravelSettings.query.filter(TravelSettings.user_id == user_id).all()
        counts['TravelSettings'] = len(settings)
        details['TravelSettings'] = [
            {
                'id': s.id,
                'user_id': s.user_id,
                'destination': s.destination,
                'days': s.days,
                'preference': s.preference,
                'created_at': s.created_at.isoformat() if s.created_at else None
            } for s in settings
        ]
        
        # 5. 查询 ChatMessages (限制最近50条)
        messages = ChatMessages.query.filter(ChatMessages.user_id == user_id).order_by(ChatMessages.created_at.desc()).limit(50).all()
        counts['ChatMessages'] = ChatMessages.query.filter(ChatMessages.user_id == user_id).count()
        details['ChatMessages'] = [
            {
                'id': m.id,
                'user_id': m.user_id,
                'session_id': m.session_id,
                'message_id': m.message_id,
                'speaker_id': m.speaker_id,
                'speaker_type': m.speaker_type,
                'message_content': m.message_content,
                'created_at': m.created_at.isoformat() if m.created_at else None
            } for m in messages
        ]
        
        # 6. 查询 ChatTopics
        topics = ChatTopics.query.filter(ChatTopics.user_id == user_id).all()
        counts['ChatTopics'] = len(topics)
        details['ChatTopics'] = [
            {
                'id': t.id,
                'user_id': t.user_id,
                'session_id': t.session_id,
                'destination': t.destination,
                'topic': t.topic,
                'created_at': t.created_at.isoformat() if t.created_at else None
            } for t in topics
        ]
        
        logger.info(f"用户 {user_id} 数据查询完成: {counts}")
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'counts': counts,
                'details': details,
                'user_id': user_id
            }
        })
        
    except Exception as e:
        logger.error(f"查询用户数据失败: {e}", exc_info=True)
        return jsonify({
            'code': -1,
            'message': f'查询失败: {str(e)}',
            'data': None
        }), 500

