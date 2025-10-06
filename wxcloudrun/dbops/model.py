from datetime import datetime

from wxcloudrun import db


# 用户主表
class Users(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Users'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())


# 数字分身表
class DigitalAvatar(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'DigitalAvatar'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    avatar_id = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())


# 旅行伙伴表
class TravelPartner(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'TravelPartner'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    partner_id = db.Column(db.String(100), nullable=False, index=True)
    partner_name = db.Column(db.String(100), nullable=False)
    partner_description = db.Column(db.Text, nullable=True)
    partner_avatar_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())


# 旅行设置表
class TravelSettings(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'TravelSettings'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    destination = db.Column(db.String(200), nullable=True)
    days = db.Column(db.Integer, nullable=True)
    preference = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())


# 聊天会话表
class ChatSession(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'ChatSession'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())


# 聊天话题表
class ChatTopics(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'ChatTopics'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=True, index=True)
    session_id = db.Column(db.String(100), nullable=True, index=True)
    destination = db.Column(db.String(100), nullable=True, index=True)
    topic = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=True)


# 聊天消息表
class ChatMessages(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'ChatMessages'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    speaker_id = db.Column(db.String(100), nullable=False)
    speaker_type = db.Column(db.Enum('user', 'avatar', 'partner'), nullable=False)
    message_id = db.Column(db.String(100), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())
    
    # 添加复合索引，允许多条消息但防止完全重复
    __table_args__ = (
        db.Index('idx_user_session_speaker_message', 'user_id', 'session_id', 'speaker_type', 'message'),
    )


