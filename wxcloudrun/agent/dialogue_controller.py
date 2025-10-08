from typing import Dict
import time
import logging

from wxcloudrun.agent.thought import Thought
from .dialogue_context import DialogueContext
from .digital_avatar import DigitalAvatar
from .digital_partner import DigitalPartner
from .agent_data import TurnAction
from ..idgeneration.id_gen import new_message_id

logger = logging.getLogger(__name__)


class DialogueController:
    def __init__(self):
        self.user_context: Dict[str, DialogueContext] = {}


    def step(self, user_id: str, session_id: str):
        
        # 构建完整的用户上下文
        self.build_user_context(user_id, session_id)
        
        # 思考
        thought_result = self.thought(user_id)
        
        if thought_result is None:
            logger.error(f"Thought failed for user {user_id}")
            return None

        # 调用工具
        speak_result = None
        try:
            speak_result = self.act(user_id, thought_result)
            
            if not speak_result or "text" not in speak_result:
                logger.error(f"Act failed for user {user_id}")
                return None
        except Exception as e:
            logger.error(f"Act method failed for user {user_id}: {e}, speak_result: {speak_result}")
            return None

        # 反思
        self.reflect(user_id)

        # 更新用户上下文
        self.update_user_context(user_id, thought_result, speak_result)

        # 构建回复消息
        reply = {
            "user_id": user_id,
            "agent_info": {
                "agent_id": speak_result["speaker_id"],
                "agent_type": speak_result["speaker_type"],
                "agent_name": speak_result["agent_name"],
                "agent_photo_url": speak_result["agent_photo_url"]
            },
            "contents": [{
                "message_id": f"msg_{user_id}_{int(time.time())}",
                "type": "text",
                "mime": "text/plain; charset=utf-8",
                "text": speak_result["text"],
                "lang": "zh-CN"
            }]
        }

        return reply

    def build_user_context(self, user_id: str, session_id: str):
        """从字典中获取context实例，如果没有则创建一个"""
        if user_id not in self.user_context:
            self.user_context[user_id] = DialogueContext(user_id, session_id)
            self.user_context[user_id].build()
        
        return self.user_context[user_id]

    def update_user_context(self, user_id: str, thought_result, speak_result):
        # 更新用户上下文
        self.user_context[user_id].update(thought_result, speak_result)

    def thought(self, user_id: str):
        context = self.user_context[user_id]
        thought = Thought(context)
        return thought.thought()

    def act(self, user_id: str, thought_result):
        speak_result = {}

        if thought_result.turn_action == TurnAction.SPEAK_USER_DIGITAL_AVATAR:
            avatar = DigitalAvatar()
            speak_text = avatar.speak(self.user_context[user_id], thought_result)
            speak_result = {"text": speak_text}
            
            # 检查digital_avatar是否存在
            if not self.user_context[user_id].digital_avatar:
                logger.error(f"Digital avatar not found for user {user_id}")
                raise ValueError(f"Digital avatar not found for user {user_id}")
            
            speak_result["speaker_id"] = self.user_context[user_id].digital_avatar.avatar_id
            speak_result["agent_name"] = self.user_context[user_id].digital_avatar.name
            speak_result["agent_photo_url"] = self.user_context[user_id].digital_avatar.avatar_url
            speak_result["speaker_type"] = "avatar"
            
        elif thought_result.turn_action == TurnAction.SPEAK_TRAVEL_PARTNER:
            partner = DigitalPartner()
            speak_text = partner.speak(self.user_context[user_id], thought_result)
            speak_result = {"text": speak_text}
            
            # 检查travel_partner是否存在
            if not self.user_context[user_id].travel_partner:
                logger.error(f"Travel partner not found for user {user_id}")
                raise ValueError(f"Travel partner not found for user {user_id}")
            
            speak_result["speaker_id"] = self.user_context[user_id].travel_partner.partner_id
            speak_result["agent_name"] = self.user_context[user_id].travel_partner.partner_name
            speak_result["agent_photo_url"] = self.user_context[user_id].travel_partner.partner_avatar_url
            speak_result["speaker_type"] = "partner"

        speak_result["message_id"] = new_message_id()
        return speak_result

    def reflect(self, user_id: str):
        pass