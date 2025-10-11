import logging
import time
from functools import wraps

from sqlalchemy.exc import OperationalError, DisconnectionError

from wxcloudrun import db
from wxcloudrun.dbops.model import Users, DigitalAvatar, TravelPartner, TravelSettings, ChatMessages, ChatTopics

# 初始化日志
logger = logging.getLogger(__name__)

def _maybe_dispose_engine(e: OperationalError):
    try:
        code = getattr(getattr(e, "orig", None), "args", [None])[0]
        if code in (2006, 2013, 2014, 2045, 2055):  # MySQL 常见断连相关
            db.engine.dispose()  # 彻底丢弃连接池，重建
    except Exception:
        pass

def retry_db_operation(max_retries=3, delay=1):
    """
    数据库操作重试装饰器
    仅针对已知的 MySQL 断连错误（2006/2013/2014/2045/2055）进行重试
    其他错误直接抛出
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    # 检查是否是 MySQL 断连错误
                    code = getattr(getattr(e, "orig", None), "args", [None])[0]
                    is_disconnect = code in (2006, 2013, 2014, 2045, 2055)
                    
                    if not is_disconnect:
                        # 非断连错误，直接抛出不重试
                        logger.error(f"Database operation failed with non-disconnect error (code={code}): {e}")
                        raise
                    
                    # 断连错误，进行重试
                    if attempt == max_retries - 1:
                        logger.error(f"Database disconnect after {max_retries} retries (code={code}): {e}")
                        raise
                    
                    logger.warning(f"Database disconnect detected (code={code}, attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(delay * (attempt + 1))  # 递增延迟
                    
                    # 丢弃连接池并回滚会话
                    _maybe_dispose_engine(e)
                    try:
                        db.session.rollback()
                    except:
                        pass
            
            return None
        return wrapper
    return decorator


# 用户相关DAO函数
@retry_db_operation(max_retries=3, delay=1)
def insert_user(user_id):
    """
    插入用户实体，自动生成session_id
    :param user_id: 用户ID
    :return: 创建的用户实体
    """
    try:
        from ..idgeneration import id_gen
        session_id = id_gen.new_session_id()
        user = Users(user_id=user_id, session_id=session_id)
        
        db.session.add(user)
        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        raise e


@retry_db_operation(max_retries=3, delay=1)
def get_user_by_user_id(user_id):
    """
    根据用户ID获取最新的用户记录
    :param user_id: 用户ID
    :return: 用户实体（最新的记录）
    """
    return Users.query.filter(Users.user_id == user_id).order_by(Users.created_at.desc()).first()

@retry_db_operation(max_retries=3, delay=1)
def get_user_by_user_id_and_session_id(user_id, session_id):
    """
    根据用户ID和会话ID获取用户记录
    :param user_id: 用户ID
    :param session_id: 会话ID
    :return: 用户实体
    """
    return Users.query.filter(Users.user_id == user_id, Users.session_id == session_id).first()

@retry_db_operation(max_retries=3, delay=1)
def get_user_session_id(user_id):
    """
    从 Users 表获取用户的最新 session_id
    :param user_id: 用户ID
    :return: session_id 字符串，如果用户不存在返回 None
    """
    user = Users.query.filter(Users.user_id == user_id).order_by(Users.created_at.desc()).first()
    return user.session_id if user else None




# 数字分身相关DAO函数
@retry_db_operation(max_retries=3, delay=1)
def insert_digital_avatar(avatar):
    """
    插入数字分身实体
    :param avatar: DigitalAvatar实体
    """
    db.session.add(avatar)
    db.session.commit()


@retry_db_operation(max_retries=3, delay=1)
def get_digital_avatar_by_user_id(user_id):
    """
    根据用户ID获取数字分身
    :param user_id: 用户ID
    :return: 数字分身实体
    """
    return DigitalAvatar.query.filter(DigitalAvatar.user_id == user_id).first()


@retry_db_operation(max_retries=3, delay=1)
def update_digital_avatar(avatar):
    """
    更新数字分身实体
    :param avatar: DigitalAvatar实体
    """
    db.session.merge(avatar)
    db.session.commit()


# 旅行伙伴相关DAO函数
@retry_db_operation(max_retries=3, delay=1)
def insert_travel_partner(partner):
    """
    插入旅行伙伴实体
    :param partner: TravelPartner实体
    """
    db.session.add(partner)
    db.session.commit()


@retry_db_operation(max_retries=3, delay=1)
def get_travel_partner_by_user_id(user_id):
    """
    根据用户ID获取旅行伙伴
    :param user_id: 用户ID
    :return: 旅行伙伴实体
    """
    return TravelPartner.query.filter(TravelPartner.user_id == user_id).first()


@retry_db_operation(max_retries=3, delay=1)
def update_travel_partner(partner):
    """
    更新旅行伙伴实体
    :param partner: TravelPartner实体
    """
    db.session.merge(partner)
    db.session.commit()



# 旅行设置相关DAO函数
@retry_db_operation(max_retries=3, delay=1)
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


@retry_db_operation(max_retries=3, delay=1)
def get_travel_settings_by_user_id(user_id):
    """
    根据用户ID获取旅行设置
    :param user_id: 用户ID
    :return: 旅行设置实体
    """
    return TravelSettings.query.filter(TravelSettings.user_id == user_id).first()


@retry_db_operation(max_retries=3, delay=1)
def update_travel_settings(settings):
    """
    更新旅行设置实体
    :param settings: TravelSettings实体
    """
    db.session.merge(settings)
    db.session.commit()



# 聊天消息相关DAO函数
@retry_db_operation(max_retries=3, delay=1)
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


@retry_db_operation(max_retries=3, delay=1)
def get_chat_messages_by_user(user_id, limit=50):
    """
    根据用户ID获取聊天消息（自动从 Users 表获取 session_id）
    :param user_id: 用户ID
    :param limit: 限制数量
    :return: 聊天消息列表
    """
    # 从 Users 表获取 session_id
    session_id = get_user_session_id(user_id)
    if not session_id:
        return []
    
    return ChatMessages.query.filter(
        ChatMessages.user_id == user_id,
        ChatMessages.session_id == session_id
    ).order_by(ChatMessages.created_at.asc()).limit(limit).all()






@retry_db_operation(max_retries=3, delay=1)
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


@retry_db_operation(max_retries=3, delay=1)
def get_user_session_topics(user_id, limit=10):
    """
    获取用户会话的话题列表，按destination分组（自动从 Users 表获取 session_id）
    :param user_id: 用户ID
    :param limit: 限制数量
    :return: 按destination分组的topics字典 {"destination_1": ["topic_1", "topic_2"], ...}
    """
    # 从 Users 表获取 session_id
    session_id = get_user_session_id(user_id)
    if not session_id:
        return {}
    
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


@retry_db_operation(max_retries=3, delay=1)
def get_user_topics(user_id, limit=10):
    """
    获取用户的话题列表
    :param user_id: 用户ID
    :param limit: 限制数量
    """
    return ChatTopics.query.filter(
        ChatTopics.user_id == user_id
    ).order_by(ChatTopics.created_at.desc()).limit(limit).all()


