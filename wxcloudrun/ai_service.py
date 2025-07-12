import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from wxcloudrun import socketio


class DeepSeekV3Service:
    """DeepSeek V3 API服务类"""
    
    def __init__(self):
        self.api_key = "sk-9109dab67ad949048268d64c72486bb7"
        self.base_url = "https://api.deepseek.com"
        self.model = "deepseek-chat"
        
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")
    
    def chat_completion(self, 
                       messages: List[Dict[str, str]], 
                       temperature: float = 0.7,
                       max_tokens: int = 1000,
                       stream: bool = False) -> Dict:
        """
        调用DeepSeek V3聊天完成API
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "消息内容"}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数
            stream: 是否流式响应
            
        Returns:
            API响应字典
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"DeepSeek API调用失败: {str(e)}")
    
    def get_response_text(self, api_response: Dict) -> str:
        """
        从API响应中提取文本内容
        
        Args:
            api_response: API响应字典
            
        Returns:
            响应文本
        """
        try:
            return api_response['choices'][0]['message']['content']
        except (KeyError, IndexError) as e:
            raise Exception(f"无法解析API响应: {str(e)}")
    
    def get_usage_info(self, api_response: Dict) -> Dict:
        """
        从API响应中提取使用信息
        
        Args:
            api_response: API响应字典
            
        Returns:
            使用信息字典
        """
        try:
            return api_response.get('usage', {})
        except KeyError:
            return {}
    
    def create_conversation_context(self, 
                                  user_id: str, 
                                  session_id: str,
                                  history: List) -> List[Dict[str, str]]:
        """
        创建对话上下文
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            history: 历史对话记录
            
        Returns:
            格式化的消息列表
        """
        messages = []
        
        # 添加系统消息
        system_message = {
            "role": "system",
            "content": "你是一个有用的AI助手，请用中文回答用户的问题。"
        }
        messages.append(system_message)
        
        # 添加历史对话
        for record in reversed(history):  # 反转顺序，从旧到新
            messages.append({
                "role": "user",
                "content": record.user_message
            })
            messages.append({
                "role": "assistant", 
                "content": record.ai_response
            })
        
        return messages
    
    def chat_completion_stream(self, 
                              messages: List[Dict[str, str]], 
                              temperature: float = 0.7,
                              max_tokens: int = 1000,
                              room: Optional[str] = None) -> str:
        """
        流式聊天完成API调用
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            room: WebSocket房间名称
            
        Returns:
            完整的AI响应文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
                stream=True
            )
            response.raise_for_status()
            
            full_response = ""
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    full_response += content
                                    
                                    if room:
                                        socketio.emit('chat_stream', {
                                            'code': 0,
                                            'data': {
                                                'content': content,
                                                'is_complete': False
                                            }
                                        }, to=room)
                        except json.JSONDecodeError:
                            continue
            
            return full_response
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"DeepSeek流式API调用失败: {str(e)}")     