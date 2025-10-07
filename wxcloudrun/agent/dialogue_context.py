from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
import logging
from ..dbops.model import ChatMessages, DigitalAvatar, TravelPartner, TravelSettings, ChatTopics
from ..dbops.dao import insert_chat_message, get_chat_messages_by_session, get_digital_avatar_by_user_id, get_travel_partner_by_user_id, get_travel_settings_by_user_id, get_user_sessions, insert_chat_topic, get_session_topics
from .agent_data import TopicAction

# 配置logging
logger = logging.getLogger(__name__)


@dataclass
class HistoryItem:
    speaker_id: str
    speaker_type: str
    message_id: str
    message_content: str


class DialogueContext:

    def __init__(self, user_id: str):
        self.user_id = user_id
        # 会话ID
        self.session_id: str = ""
        # 用户历史
        self.history: List[HistoryItem] = []
        # 用户数据属性
        self.digital_avatar: Optional[DigitalAvatar] = None
        self.travel_partner: Optional[TravelPartner] = None
        self.travel_settings: Optional[TravelSettings] = None
        # 话题相关
        self.current_topic: Optional[str] = None  # 当前目的地
        self.topic_history: Dict[str, List[str]] = {}  # 按destination分组的topics

    def build(self):
        """构建用户上下文：加载历史记录和用户数据"""

        # 获取用户最新的session_id
        self.load_latest_session_id()
        
        # 加载话题历史
        self.load_session_topics()
        
        if not self.history:  # 如果history为空
            self.load_history_from_db(limit=10)
        
        # 从数据库加载用户相关数据
        try:
            # 加载数字分身数据
            self.digital_avatar = get_digital_avatar_by_user_id(self.user_id)
            
            # 加载旅行伙伴数据
            self.travel_partner = get_travel_partner_by_user_id(self.user_id)
            
            # 加载旅行设置数据
            self.travel_settings = get_travel_settings_by_user_id(self.user_id)
        except Exception as e:
            logger.error(f"加载用户数据失败: {e}")
    
    def load_latest_session_id(self):
        """从数据库加载用户最新的session_id"""
        try:
            # 获取用户最近的session列表
            sessions = get_user_sessions(self.user_id, limit=1)
            if sessions and len(sessions) > 0:
                self.session_id = sessions[0].session_id
                logger.info(f"加载最新session_id: {self.session_id}")
            else:
                logger.warning(f"用户 {self.user_id} 没有找到任何session")
        except Exception as e:
            logger.error(f"加载最新session_id失败: {e}")
    
    def load_session_topics(self):
        """加载当前session的所有topics，按destination分组"""
        try:
            # 获取按destination分组的topics
            self.topic_history = get_session_topics(self.session_id)
            # 获取最新的topic作为当前topic
            if self.topic_history:
                # 获取最新的topic（第一个destination的第一个topic）
                latest_destination = list(self.topic_history.keys())[0] if self.topic_history else None
                if latest_destination and self.topic_history[latest_destination]:
                    self.current_topic = self.topic_history[latest_destination][0]  # 最新的topic内容
                    logger.info(f"加载session topics，共{len(self.topic_history)}个destination，当前topic: {self.current_topic}")
                else:
                    self.current_topic = None
                    logger.info(f"session {self.session_id} 没有找到任何topic内容")
            else:
                self.current_topic = None
                logger.info(f"session {self.session_id} 没有找到任何topics")
        except Exception as e:
            logger.error(f"加载session topics失败: {e}")
    
    def create_new_topic(self, topic_text: str, destination: str = None):
        """创建新的topic"""
        try:
            new_topic = ChatTopics(
                user_id=self.user_id,
                session_id=self.session_id,
                destination=destination,
                topic=topic_text,
            )
            
            insert_chat_topic(new_topic)
            
            # 更新内存中的topic_history
            if destination:
                if destination not in self.topic_history:
                    self.topic_history[destination] = []
                # 将新topic插入到该destination的列表开头
                self.topic_history[destination].insert(0, topic_text)
                self.current_topic = topic_text  # 设置当前topic为话题内容
            else:
                # 如果没有destination，创建一个默认分组
                default_dest = "未分类"
                if default_dest not in self.topic_history:
                    self.topic_history[default_dest] = []
                self.topic_history[default_dest].insert(0, topic_text)
                self.current_topic = topic_text  # 设置当前topic为话题内容
            
            logger.info(f"创建新topic成功: {topic_text}, destination: {destination}")
            return new_topic
        except Exception as e:
            logger.error(f"创建新topic失败: {e}")
            return None
    
    def get_topic_history_summary(self) -> str:
        """获取topics历史摘要，按destination分组，用于AI参考"""
        if not self.topic_history:
            return "暂无讨论话题"
        
        summary = "历史话题（按目的地分组，供避免重复）：\n"
        for destination, topics in self.topic_history.items():
            summary += f"【{destination}】:\n"
            for i, topic in enumerate(topics, 1):  # 显示所有topic
                summary += f"  {i}. {topic}\n"
        
        return summary
    
    def get_current_topic_text(self) -> str:
        """获取当前话题文本"""
        return self.current_topic if self.current_topic else "未设置话题"
    
    def update(self, thought_result, speak_result):
        # 处理topic变更
        if thought_result.topic_action == TopicAction.END_AND_GENERATE:
            if thought_result.topic_args and thought_result.topic_args.new_topic:
                new_topic_info = thought_result.topic_args.new_topic
                # 获取destination，优先使用travel_settings中的destination
                destination = self.travel_settings.destination if self.travel_settings else "未分类"
                self.create_new_topic(new_topic_info.title, destination)

        # 添加一条历史记录：先插入数据库，再更新内存
        try:
            # 从输入对象提取数据
            session_id = self.session_id
            speaker_id = speak_result["speaker_id"]
            speaker_type = speak_result["speaker_type"]
            message_id = speak_result.get("message_id")
            message_content = speak_result.get("text")
            
            # 检查必要字段
            if not session_id:
                raise ValueError("session_id is required")
            if not speaker_id:
                raise ValueError("speaker_id is required")
            if not speaker_type:
                raise ValueError("speaker_type is required")
            if not message_id:
                raise ValueError("message_id is required")
            if not message_content:
                raise ValueError("message_content is required")

            # 创建数据库记录
            chat_message = ChatMessages(
                user_id=self.user_id,
                session_id=session_id,
                speaker_id=speaker_id,
                speaker_type=speaker_type,
                message_id=message_id,
                message=message_content,
            )
            
            # 插入数据库
            insert_chat_message(chat_message)
            
            # 创建内存历史记录
            history_item = HistoryItem(
                speaker_id=speaker_id,
                speaker_type=speaker_type,
                message_id=message_id,
                message_content=message_content,
            )
            
            # 更新内存中的history
            self.history.append(history_item)
            
        except Exception as e:
            # 如果数据库插入失败，仍然保存到内存
            logger.error(f"数据库插入失败，仅保存到内存: {e}")
            history_item = HistoryItem(
                speaker_id=speaker_id,
                speaker_type=speaker_type,
                message_id=message_id,
                message_content=message_content,
            )
            self.history.append(history_item)
        
    
    def get_recent_history(self, count: int = 5) -> List[HistoryItem]:
        """获取最近的几条历史记录"""
        return self.history[-count:] if count > 0 else self.history
    
    def load_history_from_db(self, session_id: str = "", limit: int = 50):
        """从数据库加载历史记录到内存（仅在history为空时加载）"""
        try:
            # 从数据库获取消息
            db_messages = get_chat_messages_by_session(self.user_id, session_id, limit)
            
            # 将数据库记录转换为HistoryItem并添加到内存
            for msg in db_messages:
                history_item = HistoryItem(
                    speaker_id=msg.speaker_id,
                    speaker_type=msg.speaker_type,
                    message_id=msg.message_id,
                    message_content=msg.message,
                )
                self.history.append(history_item)
                
        except Exception as e:
            logger.error(f"从数据库加载历史记录失败: {e}")
    
    def get_avatar_name(self) -> str:
        """获取数字分身名称"""
        return self.digital_avatar.name if self.digital_avatar else "未知分身"
    
    def get_avatar_description(self) -> str:
        """获取数字分身描述"""
        return self.digital_avatar.description if self.digital_avatar else "暂无描述"
    
    def get_partner_name(self) -> str:
        """获取旅行伙伴名称"""
        return self.travel_partner.partner_name if self.travel_partner else "未知伙伴"
    
    def get_partner_description(self) -> str:
        """获取旅行伙伴描述"""
        return self.travel_partner.partner_description if self.travel_partner else "暂无描述"
    
    def get_travel_destination(self) -> str:
        """获取旅行目的地"""
        return self.travel_settings.destination if self.travel_settings else "未设置目的地"
    
    def get_travel_days(self) -> int:
        """获取旅行天数"""
        return self.travel_settings.days if self.travel_settings and self.travel_settings.days else 0
    
    def get_travel_preference(self) -> str:
        """获取旅行偏好"""
        return self.travel_settings.preference if self.travel_settings else "暂无偏好"
    
    def has_complete_profile(self) -> bool:
        """检查用户是否有完整的个人资料"""
        return (
            self.digital_avatar is not None and 
            self.travel_partner is not None and 
            self.travel_settings is not None
        )
    
    def get_current_session_id(self) -> str:
        """获取当前会话ID"""
        return self.session_id
