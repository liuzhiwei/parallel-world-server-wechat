import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import Users, DigitalAvatar, TravelPartner, TravelSettings

# 初始化日志
logger = logging.getLogger('log')


# 用户相关DAO函数
def insert_user(user):
    """
    插入用户实体
    :param user: Users实体
    """
    logger.info(f"=== insert_user 开始 ===")
    logger.info(f"用户数据: user_id={user.user_id}")
    
    try:
        db.session.add(user)
        db.session.commit()
        logger.info(f"用户插入成功，ID: {user.id}")
    except Exception as e:
        logger.error(f"用户插入失败: {str(e)}")
        db.session.rollback()
        raise e
    
    logger.info(f"=== insert_user 结束 ===")


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
    logger.info(f"=== ensure_user_exists 开始 ===")
    logger.info(f"查找用户: {user_id}")
    
    user = get_user_by_user_id(user_id)
    logger.info(f"查找结果: {user}")
    
    if not user:
        logger.info(f"用户不存在，创建新用户: {user_id}")
        user = Users(user_id=user_id)
        try:
            insert_user(user)
            logger.info(f"用户创建成功，ID: {user.id}")
        except Exception as e:
            logger.error(f"用户创建失败: {str(e)}")
            raise e
    else:
        logger.info(f"用户已存在，ID: {user.id}")
    
    logger.info(f"=== ensure_user_exists 结束 ===")
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
    logger.info(f"=== insert_travel_settings 开始 ===")
    logger.info(f"设置数据: user_id={settings.user_id}, destination={settings.destination}, days={settings.days}")
    
    try:
        db.session.add(settings)
        db.session.commit()
        logger.info(f"旅行设置插入成功，ID: {settings.id}")
    except Exception as e:
        logger.error(f"旅行设置插入失败: {str(e)}")
        db.session.rollback()
        raise e
    
    logger.info(f"=== insert_travel_settings 结束 ===")


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


# def get_conversation_history(user_id, session_id, limit=10):
#     """
#     获取用户对话历史
#     :param user_id: 用户ID
#     :param session_id: 会话ID
#     :param limit: 限制条数
#     :return: 对话历史列表
#     """
#     return AIConversation.query.filter(
#         AIConversation.user_id == user_id,
#         AIConversation.session_id == session_id
#     ).order_by(AIConversation.created_at.desc()).limit(limit).all()
