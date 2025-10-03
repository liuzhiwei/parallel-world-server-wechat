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


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=datetime.now())


# 数字分身表
class DigitalAvatar(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'DigitalAvatar'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
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


# # AI对话记录表
# class AIConversation(db.Model):
#     # 设置结构体表格名称
#     __tablename__ = 'AIConversation'

#     # 设定结构体对应表格的字段
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.String(100), nullable=False, index=True)
#     session_id = db.Column(db.String(100), nullable=True)
#     user_message = db.Column(db.Text, nullable=True)
#     ai_response = db.Column(db.Text, nullable=True)
#     created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
