from dataclasses import dataclass
from typing import List, Optional, Dict
import logging
from ..dbops.model import DigitalAvatar, TravelPartner, TravelSettings, ChatTopics, ChatMessages
from ..dbops.dao import get_digital_avatar_by_user_id, get_travel_partner_by_user_id, get_travel_settings_by_user_id, insert_chat_topic
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
        
        # 从数据库加载最近的10条对话历史
        self.load_recent_history_from_db(limit=10)
        
        # 从数据库加载最近的10个话题
        self.load_recent_topics_from_db(limit=10)
        
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
    
    def load_recent_history_from_db(self, limit: int = 10):
        """从ChatMessages表加载最近的对话历史"""
        try:
            # 查询最近的消息
            recent_messages = ChatMessages.query.filter(
                ChatMessages.user_id == self.user_id
            ).order_by(ChatMessages.created_at.desc()).limit(limit).all()
            
            # 反转顺序（从旧到新）
            recent_messages.reverse()
            
            # 转换为HistoryItem并添加到内存
            for msg in recent_messages:
                history_item = HistoryItem(
                    speaker_id=msg.speaker_id,
                    speaker_type=msg.speaker_type,
                    message_id=msg.message_id,
                    message_content=msg.message
                )
                self.history.append(history_item)
            
            logger.info(f"从数据库加载了 {len(recent_messages)} 条对话历史")
        except Exception as e:
            logger.error(f"从数据库加载对话历史失败: {e}")
    
    def load_recent_topics_from_db(self, limit: int = 10):
        """从ChatTopics表加载最近的话题"""
        try:
            # 查询最近的话题
            recent_topics = ChatTopics.query.filter(
                ChatTopics.user_id == self.user_id
            ).order_by(ChatTopics.created_at.desc()).limit(limit).all()
            
            if not recent_topics:
                logger.info("未找到任何话题记录")
                return
            
            # 最新的作为current_topic
            latest_topic = recent_topics[0]
            self.current_topic = latest_topic.topic
            
            # 其余的按destination分组到topic_history
            for topic_record in recent_topics:
                destination = topic_record.destination or "未分类"
                if destination not in self.topic_history:
                    self.topic_history[destination] = []
                # 避免重复添加
                if topic_record.topic not in self.topic_history[destination]:
                    self.topic_history[destination].append(topic_record.topic)
            
            logger.info(f"从数据库加载了 {len(recent_topics)} 个话题，当前话题: {self.current_topic}")
        except Exception as e:
            logger.error(f"从数据库加载话题失败: {e}")
    
    def create_new_topic(self, topic_text: str, destination: str = None):
        """创建新的topic"""
        try:
            new_topic = ChatTopics(
                user_id=self.user_id,
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

        # 添加一条历史记录：仅保存到内存
        try:
            # 从输入对象提取数据
            speaker_id = speak_result["speaker_id"]
            speaker_type = speak_result["speaker_type"]
            message_id = speak_result.get("message_id")
            message_content = speak_result.get("text")
            
            # 检查必要字段
            if not speaker_id:
                raise ValueError("speaker_id is required")
            if not speaker_type:
                raise ValueError("speaker_type is required")
            if not message_id:
                raise ValueError("message_id is required")
            if not message_content:
                raise ValueError("message_content is required")

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
            logger.error(f"添加历史记录失败: {e}")
        
    
    def get_recent_history(self, count: int = 5) -> List[HistoryItem]:
        """获取最近的几条历史记录"""
        return self.history[-count:] if count > 0 else self.history
    
    
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
    
