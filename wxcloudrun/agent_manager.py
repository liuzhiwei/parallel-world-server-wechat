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
        self._data_loaded = False
        
    def load_user_data(self, force_reload=False):
        """加载用户数据"""
        # 如果数据已加载且不强制重新加载，则跳过
        if self._data_loaded and not force_reload:
            return
            
        try:
            # 加载分身信息
            self.avatar_info = get_digital_avatar_by_user_id(self.user_id)
            # 加载伙伴信息
            self.partner_info = get_travel_partner_by_user_id(self.user_id)
            # 加载旅行设置
            self.travel_settings = get_travel_settings_by_user_id(self.user_id)
            
            if not self.avatar_info or not self.partner_info:
                raise Exception("用户数据不完整，请先完成个人信息设置")
            
            self._data_loaded = True
                
        except Exception as e:
            logger.error(f"加载用户数据失败: {str(e)}")
            raise e
    
    def refresh_user_data(self):
        """强制刷新用户数据（当用户修改信息后调用）"""
        self.load_user_data(force_reload=True)
    
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
                if msg['speaker_type'] == 'user' or msg['speaker_type'] == 'avatar':
                    messages.append({"role": "assistant", "content": msg['message']})
                elif msg['speaker_type'] == 'partner':
                    partner_name = self.partner_info.partner_name
                    message_content = msg['message']
                    messages.append({"role": "user", "content": f"{partner_name}: {message_content}"})
            
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
                if msg['speaker_type'] == 'user' or msg['speaker_type'] == 'avatar':
                    avatar_name = self.avatar_info.name
                    message_content = msg['message']
                    messages.append({"role": "user", "content": f"{avatar_name}: {message_content}"})
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
    
    
    def generate_responses_by_user_input(self, user_message, conversation_history):
        """生成回复（用户替分身说话）"""
        try:
            # 确保用户数据已加载
            self.load_user_data()
            
            # 用户消息（替分身说话）
            user_message_content = user_message
            
            # 生成伙伴回复
            partner_response = self.generate_partner_response(user_message_content, conversation_history)
            
            return {
                'user_message': user_message_content,
                'partner_response': partner_response
            }
            
        except Exception as e:
            logger.error(f"生成智能体回复失败: {str(e)}")
            raise e
    
    def generate_multi_round_conversation_stream(self, min_rounds=10, max_rounds=20):
        """生成多轮对话流（基于AI计划的智能对话）"""
        try:
            # 确保用户数据已加载
            self.load_user_data()
            
            conversation_history = []
            total_messages = 0
            
            # 生成对话计划
            plan = self.generate_conversation_plan(min_rounds, max_rounds)
            yield from self._push_message('system', f"对话计划：{plan['description']}", conversation_history, total_messages)
            total_messages += 1
            
            # 根据计划生成对话
            for round_info in plan['rounds']:
                # 生成当前轮次的对话
                for message_info in round_info['messages']:
                    if message_info['speaker'] == 'avatar':
                        response = self._generate_avatar_message_by_plan(message_info, conversation_history)
                    else:
                        response = self._generate_partner_message_by_plan(message_info, conversation_history)
                    
                    yield from self._push_message(message_info['speaker'], response, conversation_history, total_messages)
                    total_messages += 1
            
        except Exception as e:
            logger.error(f"生成多轮对话流失败: {str(e)}")
            raise e
    
    def generate_conversation_plan(self, min_rounds, max_rounds):
        """生成对话计划"""
        try:
            # 构建计划提示词
            plan_prompt = f"""作为对话规划师，请为{self.avatar_info.name}和{self.partner_info.partner_name}制定一个旅行对话计划。

用户信息：
- 分身：{self.avatar_info.name}，性格：{self.avatar_info.description}
- 伙伴：{self.partner_info.partner_name}，性格：{self.partner_info.partner_description}"""

            if not self.travel_settings or not self.travel_settings.destination:
                raise Exception("旅行目的地未设置，请先完成旅行设置")
            
            plan_prompt += f"\n- 目的地：{self.travel_settings.destination}"
            if hasattr(self.travel_settings, 'duration') and self.travel_settings.duration:
                plan_prompt += f"\n- 旅行时长：{self.travel_settings.duration}"

            plan_prompt += f"""

请制定一个{min_rounds}-{max_rounds}轮的对话计划，让两个智能体自然地进行旅行讨论。

要求：
1. 对话要自然流畅，符合各自的性格特点
2. 每轮对话要有明确的目的和话题
3. 对话要围绕旅行主题展开
4. 要有互动和讨论，不是单方面的陈述

请以JSON格式返回计划，包含：
- description: 整体对话描述
- rounds: 轮次数组，每轮包含：
  - round: 轮次号
  - purpose: 本轮目的
  - messages: 消息数组，每条包含：
    - speaker: "avatar" 或 "partner"
    - purpose: 这条消息的目的
    - topic: 讨论话题
    - tone: 语气风格"""

            messages = [{"role": "user", "content": plan_prompt}]
            
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=2000
            )
            
            plan_text = self.ai_service.get_response_text(api_response)
            
            # 解析JSON计划
            import json
            import re
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan_json = json.loads(json_match.group())
                return plan_json
            else:
                # 如果解析失败，返回默认计划
                return self._get_default_plan(min_rounds, max_rounds)
                
        except Exception as e:
            logger.error(f"生成对话计划失败: {str(e)}")
            return self._get_default_plan(min_rounds, max_rounds)
    
    def _get_default_plan(self, min_rounds, max_rounds):
        """获取默认对话计划"""
        import random
        total_rounds = random.randint(min_rounds, max_rounds)
        
        rounds = []
        for i in range(total_rounds):
            if i == 0:
                purpose = "开始旅行讨论，确定目的地和基本想法"
                messages = [
                    {"speaker": "avatar", "purpose": "提出旅行想法", "topic": "目的地选择", "tone": "兴奋期待"},
                    {"speaker": "partner", "purpose": "回应并分享想法", "topic": "旅行期待", "tone": "友好讨论"}
                ]
            elif i < total_rounds // 3:
                purpose = "深入讨论旅行细节"
                messages = [
                    {"speaker": "avatar" if i % 2 == 1 else "partner", "purpose": "讨论具体安排", "topic": "行程规划", "tone": "认真讨论"}
                ]
            elif i < total_rounds * 2 // 3:
                purpose = "分享旅行经验和建议"
                messages = [
                    {"speaker": "avatar" if i % 2 == 1 else "partner", "purpose": "分享经验", "topic": "旅行建议", "tone": "分享交流"}
                ]
            else:
                purpose = "总结和确认旅行计划"
                messages = [
                    {"speaker": "avatar" if i % 2 == 1 else "partner", "purpose": "总结讨论", "topic": "计划确认", "tone": "总结确认"}
                ]
            
            rounds.append({
                "round": i + 1,
                "purpose": purpose,
                "messages": messages
            })
        
        return {
            "description": f"旅行讨论对话，共{total_rounds}轮",
            "rounds": rounds
        }
    
    def _generate_avatar_message_by_plan(self, message_info, conversation_history):
        """根据计划生成分身消息"""
        try:
            # 构建基于计划的提示词
            plan_prompt = f"""你是{self.avatar_info.name}，性格特点是：{self.avatar_info.description}。

当前对话目的：{message_info['purpose']}
讨论话题：{message_info['topic']}
语气风格：{message_info['tone']}

你正在和{self.partner_info.partner_name}讨论旅行。请根据以上信息，自然地表达你的想法。

请用第一人称"我"来回答，就像真正的{self.avatar_info.name}一样。"""

            # 构建消息列表
            messages = [{"role": "system", "content": plan_prompt}]
            
            # 添加对话历史
            for msg in conversation_history[-20:]:  # 只保留最近20条消息
                if msg['speaker_type'] == 'user' or msg['speaker_type'] == 'avatar':
                    messages.append({"role": "assistant", "content": msg['message']})
                elif msg['speaker_type'] == 'partner':
                    partner_name = self.partner_info.partner_name
                    message_content = msg["message"]
                    messages.append({"role": "user", "content": f"{partner_name}: {message_content}"})
            
            # 调用AI服务
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=300
            )
            
            return self.ai_service.get_response_text(api_response)
            
        except Exception as e:
            logger.error(f"根据计划生成分身消息失败: {str(e)}")
            return "我觉得这个想法不错，我们继续讨论吧。"
    
    def _generate_partner_message_by_plan(self, message_info, conversation_history):
        """根据计划生成伙伴消息"""
        try:
            # 构建基于计划的提示词
            plan_prompt = f"""你是{self.partner_info.partner_name}，性格特点是：{self.partner_info.partner_description}。

当前对话目的：{message_info['purpose']}
讨论话题：{message_info['topic']}
语气风格：{message_info['tone']}

你正在和{self.avatar_info.name}讨论旅行。请根据以上信息，自然地表达你的想法。

请用第一人称"我"来回答，就像真正的{self.partner_info.partner_name}一样。"""

            # 构建消息列表
            messages = [{"role": "system", "content": plan_prompt}]
            
            # 添加对话历史
            for msg in conversation_history[-5:]:  # 只保留最近5条消息
                if msg['speaker_type'] == 'user' or msg['speaker_type'] == 'avatar':
                    avatar_name = self.avatar_info.name
                    message_content = msg["message"]
                    messages.append({"role": "user", "content": f"{avatar_name}: {message_content}"})
                elif msg['speaker_type'] == 'partner':
                    messages.append({"role": "assistant", "content": msg['message']})
            
            # 调用AI服务
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=300
            )
            
            return self.ai_service.get_response_text(api_response)
            
        except Exception as e:
            logger.error(f"根据计划生成伙伴消息失败: {str(e)}")
            return "我同意你的想法，让我们继续讨论吧。"
    
    def _push_message(self, speaker_type, message, conversation_history, message_index):
        """推送消息到历史记录并yield"""
        conversation_history.append({'speaker_type': speaker_type, 'message': message})
        yield {
            'speaker_type': speaker_type,
            'message': message,
            'message_index': message_index + 1
        }
    
    def generate_auto_conversation_stream(self, conversation_history):
        """生成自动对话流（仅返回业务数据）"""
        try:
            # 确保用户数据已加载
            self.load_user_data()
            
            # 生成自动对话
            responses = self.generate_auto_conversation(conversation_history)
            
            # 按顺序返回消息
            message_order = []
            if 'avatar_message' in responses:
                message_order.append(('avatar', responses['avatar_message']))
            if 'partner_response' in responses:
                message_order.append(('partner', responses['partner_response']))
            if 'avatar_response' in responses:
                message_order.append(('avatar', responses['avatar_response']))
            
            # 逐条返回消息
            for speaker_type, message_content in message_order:
                yield {
                    'speaker_type': speaker_type,
                    'message': message_content
                }
            
        except Exception as e:
            logger.error(f"生成自动对话流失败: {str(e)}")
            raise e