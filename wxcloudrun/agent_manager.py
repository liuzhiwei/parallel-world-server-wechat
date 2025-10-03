import logging
from datetime import datetime
from wxcloudrun.dao import get_digital_avatar_by_user_id, get_travel_partner_by_user_id, get_travel_settings_by_user_id
from wxcloudrun.ai_service import DeepSeekV3Service

# 初始化日志
logger = logging.getLogger('log')


class AgentManager:
    """智能体管理器"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.avatar_info = None
        self.partner_info = None
        self.travel_settings = None
        self.ai_service = DeepSeekV3Service()
        
    def load_user_data(self):
        """加载用户数据"""
        try:
            # 加载分身信息
            self.avatar_info = get_digital_avatar_by_user_id(self.user_id)
            # 加载伙伴信息
            self.partner_info = get_travel_partner_by_user_id(self.user_id)
            # 加载旅行设置
            self.travel_settings = get_travel_settings_by_user_id(self.user_id)
            
            if not self.avatar_info or not self.partner_info:
                raise Exception("用户数据不完整，请先完成个人信息设置")
                
        except Exception as e:
            logger.error(f"加载用户数据失败: {str(e)}")
            raise e
    
    def create_avatar_prompt(self):
        """创建分身提示词"""
        if not self.avatar_info:
            raise Exception("分身信息不存在")
            
        prompt = f"""你是{self.avatar_info.name}的数字分身，性格特点是：{self.avatar_info.description}。

你正在和你的旅行伙伴{self.partner_info.partner_name}一起规划旅行。

你的说话风格：
- 根据你的性格特点，用自然、个性化的方式表达
- 分享你对旅行的期待和想法
- 与伙伴进行友好的讨论

你的目标：帮助规划理想的旅行，分享旅行想法和期待。

请用第一人称"我"来回答，就像真正的{self.avatar_info.name}一样。"""
        
        return prompt
    
    def create_partner_prompt(self):
        """创建伙伴提示词"""
        if not self.partner_info:
            raise Exception("伙伴信息不存在")
            
        prompt = f"""你是{self.partner_info.partner_name}，性格特点是：{self.partner_info.partner_description}。

你正在和{self.avatar_info.name}一起规划旅行。

你的说话风格：
- 根据你的性格特点，用自然、个性化的方式表达
- 提供不同的旅行视角和建议
- 与{self.avatar_info.name}进行友好的讨论

你的目标：作为旅行伙伴，提供不同的旅行视角和建议，让旅行更有趣。

请用第一人称"我"来回答，就像真正的{self.partner_info.partner_name}一样。"""
        
        return prompt
    
    def generate_avatar_response(self, partner_message, conversation_history):
        """生成分身回复（基于伙伴消息）"""
        try:
            # 创建系统提示词
            system_prompt = self.create_avatar_prompt()
            
            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加对话历史
            for msg in conversation_history[-10:]:  # 只保留最近10条消息
                if msg['speaker_type'] == 'avatar':
                    messages.append({"role": "assistant", "content": msg['message']})
                elif msg['speaker_type'] == 'partner':
                    messages.append({"role": "user", "content": f"{self.partner_info.partner_name}: {msg['message']}"})
            
            # 添加当前伙伴消息
            messages.append({"role": "user", "content": f"{self.partner_info.partner_name}: {partner_message}"})
            
            # 调用AI服务
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
            
            response_text = self.ai_service.get_response_text(api_response)
            return response_text
            
        except Exception as e:
            logger.error(f"生成分身回复失败: {str(e)}")
            return f"抱歉，我现在有点忙，稍后再回复你。"
    
    def generate_partner_response(self, avatar_message, conversation_history):
        """生成伙伴回复（基于分身消息）"""
        try:
            # 创建系统提示词
            system_prompt = self.create_partner_prompt()
            
            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加对话历史
            for msg in conversation_history[-10:]:  # 只保留最近10条消息
                if msg['speaker_type'] == 'avatar':
                    messages.append({"role": "user", "content": f"{self.avatar_info.name}: {msg['message']}"})
                elif msg['speaker_type'] == 'partner':
                    messages.append({"role": "assistant", "content": msg['message']})
            
            # 添加当前分身消息
            messages.append({"role": "user", "content": f"{self.avatar_info.name}: {avatar_message}"})
            
            # 调用AI服务
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
            
            response_text = self.ai_service.get_response_text(api_response)
            return response_text
            
        except Exception as e:
            logger.error(f"生成伙伴回复失败: {str(e)}")
            return f"抱歉，我现在有点忙，稍后再回复你。"
    
    def generate_auto_conversation(self, conversation_history):
        """生成自动对话（分身和伙伴自动聊天）"""
        try:
            # 加载用户数据
            self.load_user_data()
            
            # 如果对话历史为空，生成初始对话
            if not conversation_history:
                # 分身先说话
                avatar_message = "我们这次去哪里旅行呢？"
                # 伙伴回复
                partner_response = self.generate_partner_response(avatar_message, [])
                # 分身继续回复
                avatar_response = self.generate_avatar_response(partner_response, [
                    {'speaker_type': 'avatar', 'message': avatar_message},
                    {'speaker_type': 'partner', 'message': partner_response}
                ])
                
                return {
                    'avatar_message': avatar_message,
                    'partner_response': partner_response,
                    'avatar_response': avatar_response
                }
            else:
                # 基于最后一条消息生成回复
                last_message = conversation_history[-1]
                if last_message['speaker_type'] == 'partner':
                    # 最后是伙伴说话，分身回复
                    avatar_response = self.generate_avatar_response(last_message['message'], conversation_history)
                    return {
                        'avatar_response': avatar_response
                    }
                elif last_message['speaker_type'] == 'avatar':
                    # 最后是分身说话，伙伴回复
                    partner_response = self.generate_partner_response(last_message['message'], conversation_history)
                    return {
                        'partner_response': partner_response
                    }
            
        except Exception as e:
            logger.error(f"生成自动对话失败: {str(e)}")
            raise e
    
    def generate_responses(self, user_message, conversation_history):
        """生成回复（用户替分身说话）"""
        try:
            # 加载用户数据
            self.load_user_data()
            
            # 用户消息等同于分身说话
            avatar_message = user_message
            
            # 生成伙伴回复
            partner_response = self.generate_partner_response(avatar_message, conversation_history)
            
            # 生成分身继续回复
            avatar_response = self.generate_avatar_response(partner_response, conversation_history + [
                {'speaker_type': 'avatar', 'message': avatar_message},
                {'speaker_type': 'partner', 'message': partner_response}
            ])
            
            return {
                'avatar_message': avatar_message,
                'partner_response': partner_response,
                'avatar_response': avatar_response
            }
            
        except Exception as e:
            logger.error(f"生成智能体回复失败: {str(e)}")
            raise e