import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import Users, DigitalAvatar, TravelPartner, TravelSettings, ChatMessages

# 初始化日志
logger = logging.getLogger('log')


# 用户相关DAO函数
def insert_user(user):
    """
    插入用户实体
    :param user: Users实体
    """
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def get_user_by_user_id(user_id):
    """
    根据用户ID获取用户
    :param user_id: 用户ID
    :return: 用户实体
    """
    return Users.query.filter(Users.user_id == user_id).first()


def ensure_user_exists(user_id):
    """
    确保用户存在，如果不存在则创建
    :param user_id: 用户ID
    :return: 用户实体
    """
    user = get_user_by_user_id(user_id)
    
    if not user:
        user = Users(user_id=user_id)
        insert_user(user)
    
    return user


# 数字分身相关DAO函数
def insert_digital_avatar(avatar):
    """
    插入数字分身实体
    :param avatar: DigitalAvatar实体
    """
    db.session.add(avatar)
    db.session.commit()


def get_digital_avatar_by_user_id(user_id):
    """
    根据用户ID获取数字分身
    :param user_id: 用户ID
    :return: 数字分身实体
    """
    return DigitalAvatar.query.filter(DigitalAvatar.user_id == user_id).first()


def update_digital_avatar(avatar):
    """
    更新数字分身实体
    :param avatar: DigitalAvatar实体
    """
    db.session.commit()


def delete_digital_avatar_by_user_id(user_id):
    """
    根据用户ID删除数字分身
    :param user_id: 用户ID
    """
    avatar = DigitalAvatar.query.filter(DigitalAvatar.user_id == user_id).first()
    if avatar is not None:
        db.session.delete(avatar)
        db.session.commit()


# 旅行伙伴相关DAO函数
def insert_travel_partner(partner):
    """
    插入旅行伙伴实体
    :param partner: TravelPartner实体
    """
    db.session.add(partner)
    db.session.commit()


def get_travel_partner_by_user_id(user_id):
    """
    根据用户ID获取旅行伙伴
    :param user_id: 用户ID
    :return: 旅行伙伴实体
    """
    return TravelPartner.query.filter(TravelPartner.user_id == user_id).first()


def update_travel_partner(partner):
    """
    更新旅行伙伴实体
    :param partner: TravelPartner实体
    """
    db.session.commit()


def delete_travel_partner_by_user_id(user_id):
    """
    根据用户ID删除旅行伙伴
    :param user_id: 用户ID
    """
    partner = TravelPartner.query.filter(TravelPartner.user_id == user_id).first()
    if partner is not None:
        db.session.delete(partner)
        db.session.commit()


# 旅行设置相关DAO函数
def insert_travel_settings(settings):
    """
    插入旅行设置实体
    :param settings: TravelSettings实体
    """
    try:
        db.session.add(settings)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def get_travel_settings_by_user_id(user_id):
    """
    根据用户ID获取旅行设置
    :param user_id: 用户ID
    :return: 旅行设置实体
    """
    return TravelSettings.query.filter(TravelSettings.user_id == user_id).first()


def update_travel_settings(settings):
    """
    更新旅行设置实体
    :param settings: TravelSettings实体
    """
    db.session.commit()


def delete_travel_settings_by_user_id(user_id):
    """
    根据用户ID删除旅行设置
    :param user_id: 用户ID
    """
    settings = TravelSettings.query.filter(TravelSettings.user_id == user_id).first()
    if settings is not None:
        db.session.delete(settings)
        db.session.commit()


# 聊天消息相关DAO函数
def insert_chat_message(message):
    """
    插入聊天消息
    :param message: ChatMessages实体
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 检查是否已存在相同的消息（防止重复插入）
            existing = ChatMessages.query.filter(
                ChatMessages.user_id == message.user_id,
                ChatMessages.session_id == message.session_id,
                ChatMessages.speaker_type == message.speaker_type,
                ChatMessages.message == message.message
            ).first()
            
            if existing:
                logger.info(f"消息已存在，跳过插入: {message.message[:50]}...")
                return existing
            
            db.session.add(message)
            db.session.commit()
            logger.info(f"消息插入成功: {message.speaker_type}")
            return message
            
        except OperationalError as e:
            logger.warning(f"数据库操作异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            db.session.rollback()
            
            if attempt < max_retries - 1:
                # 重新创建session
                db.session.remove()
                import time
                time.sleep(0.1 * (attempt + 1))  # 递增延迟
                continue
            else:
                logger.error(f"消息插入失败，已重试 {max_retries} 次: {str(e)}")
                raise e
                
        except Exception as e:
            logger.error(f"插入消息失败: {str(e)}")
            db.session.rollback()
            raise e


def get_chat_messages_by_session(user_id, session_id, limit=50):
    """
    根据用户ID和会话ID获取聊天消息
    :param user_id: 用户ID
    :param session_id: 会话ID
    :param limit: 限制数量
    :return: 聊天消息列表
    """
    return ChatMessages.query.filter(
        ChatMessages.user_id == user_id,
        ChatMessages.session_id == session_id
    ).order_by(ChatMessages.created_at.asc()).limit(limit).all()


def get_user_sessions(user_id, limit=20):
    """
    获取用户的所有会话
    :param user_id: 用户ID
    :param limit: 限制数量
    :return: 会话列表
    """
    return ChatMessages.query.filter(
        ChatMessages.user_id == user_id
    ).order_by(ChatMessages.created_at.desc()).limit(limit).all()


