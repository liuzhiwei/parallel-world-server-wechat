import requests
import logging
from datetime import datetime
from typing import List, Dict, Optional

# 初始化日志
logger = logging.getLogger('log')


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
                        max_tokens: int = 1000) -> Dict:
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
            "stream": False
        }
        
        try:
            logger.info(f"[AI_SERVICE] 开始调用DeepSeek API")
            logger.info(f"[AI_SERVICE] 请求参数: model={self.model}, temperature={temperature}, max_tokens={max_tokens}")
            logger.info(f"[AI_SERVICE] 消息数量: {len(messages)}")
            logger.info(f"[AI_SERVICE] 请求URL: {self.base_url}/chat/completions")
            
            start_time = datetime.now()
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=300
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"[AI_SERVICE] API调用完成，耗时: {duration:.2f}秒")
            logger.info(f"[AI_SERVICE] 响应状态码: {response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"[AI_SERVICE] 响应内容长度: {len(str(result))}")
            if 'choices' in result and len(result['choices']) > 0:
                content_length = len(result['choices'][0].get('message', {}).get('content', ''))
                logger.info(f"[AI_SERVICE] 生成内容长度: {content_length}字符")
            
            return result
        except requests.exceptions.Timeout as e:
            logger.error(f"[AI_SERVICE] API调用超时: {str(e)}")
            raise Exception(f"DeepSeek API调用超时: {str(e)}")
        except requests.exceptions.RequestException as e:
            logger.error(f"[AI_SERVICE] API调用失败: {str(e)}")
            raise Exception(f"DeepSeek API调用失败: {str(e)}")
        except Exception as e:
            logger.error(f"[AI_SERVICE] 未知错误: {str(e)}")
            raise Exception(f"DeepSeek API调用异常: {str(e)}")
    
    def get_response_text(self, api_response: Dict) -> str:
        """
        从API响应中提取文本内容
        
        Args:
            api_response: API响应字典
            
        Returns:
            响应文本
        """
        try:
            logger.info(f"[AI_SERVICE] 开始解析API响应")
            content = api_response['choices'][0]['message']['content']
            logger.info(f"[AI_SERVICE] 解析成功，内容长度: {len(content)}字符")
            logger.info(f"[AI_SERVICE] 内容预览: {content[:100]}...")
            return content
        except (KeyError, IndexError) as e:
            logger.error(f"[AI_SERVICE] 解析API响应失败: {str(e)}")
            logger.error(f"[AI_SERVICE] 响应结构: {api_response}")
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