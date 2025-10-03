"""
消息处理器
负责处理消息的推送和历史记录
"""


class MessageProcessor:
    """消息处理器"""
    
    def __init__(self):
        pass
    
    def push_message(self, speaker_type, message, conversation_history, message_index):
        """推送消息到历史记录并yield"""
        conversation_history.append({'speaker_type': speaker_type, 'message': message})
        return {
            'speaker_type': speaker_type,
            'message': message,
            'message_index': message_index + 1
        }
