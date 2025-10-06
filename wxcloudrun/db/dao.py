import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.db.model import Users, DigitalAvatar, TravelPartner, TravelSettings, ChatMessages, ChatSession, ChatTopics

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



# 聊天消息相关DAO函数
def insert_chat_message(message):
    """
    插入聊天消息
    :param message: ChatMessages实体
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 检查是否已存在完全相同的消息（防止重复插入）
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
            # 处理完整性错误（重复键）
            if "Duplicate entry" in str(e) and "idx_user_session" in str(e):
                logger.warning(f"检测到重复键错误，可能是数据库索引问题: {str(e)}")
                # 尝试删除有问题的索引
                try:
                    db.session.execute("DROP INDEX IF EXISTS idx_user_session ON ChatMessages")
                    db.session.commit()
                    logger.info("已删除有问题的 idx_user_session 索引")
                    # 重试插入
                    if attempt < max_retries - 1:
                        continue
                except Exception as drop_error:
                    logger.error(f"删除索引失败: {str(drop_error)}")
            
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


def insert_chat_session(session):
    """
    插入聊天会话
    :param session: ChatSession实体
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db.session.add(session)
            db.session.commit()
            logger.info(f"会话插入成功: {session.session_id}")
            return session
            
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
                logger.error(f"会话插入失败，已重试 {max_retries} 次: {str(e)}")
                raise e
                
        except Exception as e:
            logger.error(f"会话插入失败: {str(e)}")
            db.session.rollback()
            raise e


def get_chat_session_by_id(session_id):
    """
    根据session_id获取聊天会话
    :param session_id: 会话ID
    """
    return ChatSession.query.filter(ChatSession.session_id == session_id).first()


def get_user_sessions(user_id, limit=10):
    """
    获取用户的聊天会话列表
    :param user_id: 用户ID
    :param limit: 限制数量
    """
    return ChatSession.query.filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.created_at.desc()).limit(limit).all()


def insert_chat_topic(topic):
    """
    插入聊天话题
    :param topic: ChatTopics实体
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            db.session.add(topic)
            db.session.commit()
            logger.info(f"话题插入成功: {topic.topic[:50] if topic.topic else 'None'}...")
            return topic
            
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
                logger.error(f"话题插入失败，已重试 {max_retries} 次: {str(e)}")
                raise e
                
        except Exception as e:
            logger.error(f"话题插入失败: {str(e)}")
            db.session.rollback()
            raise e


def get_session_topics(session_id, limit=10):
    """
    获取会话的话题列表，按destination分组
    :param session_id: 会话ID
    :param limit: 限制数量
    :return: 按destination分组的topics字典 {"destination_1": ["topic_1", "topic_2"], ...}
    """
    topics = ChatTopics.query.filter(
        ChatTopics.session_id == session_id
    ).order_by(ChatTopics.created_at.desc()).limit(limit).all()
    
    # 按destination分组topics
    topics_by_destination = {}
    for topic in topics:
        if topic.destination and topic.topic:
            destination = topic.destination
            if destination not in topics_by_destination:
                topics_by_destination[destination] = []
            topics_by_destination[destination].append(topic.topic)
    
    return topics_by_destination


def get_user_topics(user_id, limit=10):
    """
    获取用户的话题列表
    :param user_id: 用户ID
    :param limit: 限制数量
    """
    return ChatTopics.query.filter(
        ChatTopics.user_id == user_id
    ).order_by(ChatTopics.created_at.desc()).limit(limit).all()


