import logging

from sqlalchemy.exc import OperationalError

from wxcloudrun import db
# from wxcloudrun.model import Counters, AIConversation

# 初始化日志
logger = logging.getLogger('log')


def query_counterbyid(id):
    """
    根据ID查询计数实体
    :param id: 计数ID
    :return: 计数实体
    """
    return Counters.query.filter(Counters.id == id).first()


def delete_counterbyid(id):
    """
    根据ID删除计数实体
    :param id: 计数ID
    """
    counter = Counters.query.filter(Counters.id == id).first()
    if counter is None:
        return
    db.session.delete(counter)
    db.session.commit()


def insert_counter(counter):
    """
    插入计数实体
    :param counter: Counters实体
    """
    db.session.add(counter)
    db.session.commit()


def update_counterbyid(counter):
    """
    根据ID更新计数实体
    :param counter: Counters实体
    """
    db.session.commit()


# def insert_ai_conversation(conversation):
#     """
#     插入AI对话记录
#     :param conversation: AIConversation实体
#     """
#     db.session.add(conversation)
#     db.session.commit()


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
