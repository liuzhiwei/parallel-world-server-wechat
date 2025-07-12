from datetime import datetime

from wxcloudrun import db


# 计数表
class Counters(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'Counters'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=1)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
    updated_at = db.Column('updatedAt', db.TIMESTAMP, nullable=False, default=datetime.now())


# AI对话记录表
class AIConversation(db.Model):
    # 设置结构体表格名称
    __tablename__ = 'AIConversation'

    # 设定结构体对应表格的字段
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False, index=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(50), default='deepseek-v3')
    tokens_used = db.Column(db.Integer, default=0)
    created_at = db.Column('createdAt', db.TIMESTAMP, nullable=False, default=datetime.now())
