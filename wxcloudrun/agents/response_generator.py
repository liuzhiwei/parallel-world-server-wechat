"""
回复生成器
负责生成各种AI回复
"""

import logging
from wxcloudrun.ai_service import DeepSeekV3Service

# 初始化日志
logger = logging.getLogger('log')


class ResponseGenerator:
    """回复生成器"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
    def generate_partner_response(self, avatar_message, conversation_history, avatar_info, partner_info):
        """生成伙伴回复（基于分身消息）"""
        try:
            # 创建系统提示词
            from .prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder(avatar_info, partner_info)
            system_prompt = prompt_builder.create_partner_prompt()
            
            # 构建消息列表
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加对话历史
            for msg in conversation_history[-10:]:  # 只保留最近10条消息
                if msg['speaker_type'] == 'user' or msg['speaker_type'] == 'avatar':
                    avatar_name = avatar_info.name
                    message_content = msg['message']
                    messages.append({"role": "user", "content": f"{avatar_name}: {message_content}"})
                elif msg['speaker_type'] == 'partner':
                    messages.append({"role": "assistant", "content": msg['message']})
            
            # 添加当前分身消息
            messages.append({"role": "user", "content": f"{avatar_info.name}: {avatar_message}"})
            
            # 调用AI服务
            logger.info(f"[RESPONSE_GENERATOR] 开始生成伙伴回复")
            logger.info(f"[RESPONSE_GENERATOR] 消息数量: {len(messages)}")
            logger.info(f"[RESPONSE_GENERATOR] 分身消息: {avatar_message[:50]}...")
            
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )
            
            response_text = self.ai_service.get_response_text(api_response)
            logger.info(f"[RESPONSE_GENERATOR] 伙伴回复生成完成，长度: {len(response_text)}字符")
            return response_text
            
        except Exception as e:
            logger.error(f"生成伙伴回复失败: {str(e)}")
            return f"抱歉，我现在有点忙，稍后再回复你。"
    
    def generate_avatar_message_by_plan(self, message_info, conversation_history, avatar_info, partner_info):
        """根据计划生成分身消息"""
        try:
            # 构建基于计划的提示词
            from .prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder(avatar_info, partner_info)
            plan_prompt = prompt_builder.create_avatar_plan_prompt(message_info)

            # 构建消息列表
            messages = [{"role": "system", "content": plan_prompt}]
            
            # 添加对话历史
            for msg in conversation_history[-5:]:  # 只保留最近5条消息
                if msg['speaker_type'] == 'user' or msg['speaker_type'] == 'avatar':
                    messages.append({"role": "assistant", "content": msg['message']})
                elif msg['speaker_type'] == 'partner':
                    partner_name = partner_info.partner_name
                    message_content = msg["message"]
                    messages.append({"role": "user", "content": f"{partner_name}: {message_content}"})
            
            # 调用AI服务
            logger.info(f"[RESPONSE_GENERATOR] 开始生成分身消息（基于计划）")
            logger.info(f"[RESPONSE_GENERATOR] 消息数量: {len(messages)}")
            logger.info(f"[RESPONSE_GENERATOR] 计划目的: {message_info.get('purpose', 'N/A')}")
            
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=300
            )
            
            result = self.ai_service.get_response_text(api_response)
            logger.info(f"[RESPONSE_GENERATOR] 分身消息生成完成，长度: {len(result)}字符")
            return result
            
        except Exception as e:
            logger.error(f"根据计划生成分身消息失败: {str(e)}")
            return "我觉得这个想法不错，我们继续讨论吧。"
    
    def generate_partner_message_by_plan(self, message_info, conversation_history, avatar_info, partner_info):
        """根据计划生成伙伴消息"""
        try:
            # 构建基于计划的提示词
            from .prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder(avatar_info, partner_info)
            plan_prompt = prompt_builder.create_partner_plan_prompt(message_info)

            # 构建消息列表
            messages = [{"role": "system", "content": plan_prompt}]
            
            # 添加对话历史
            for msg in conversation_history[-5:]:  # 只保留最近5条消息
                if msg['speaker_type'] == 'user' or msg['speaker_type'] == 'avatar':
                    avatar_name = avatar_info.name
                    message_content = msg["message"]
                    messages.append({"role": "user", "content": f"{avatar_name}: {message_content}"})
                elif msg['speaker_type'] == 'partner':
                    messages.append({"role": "assistant", "content": msg['message']})
            
            # 调用AI服务
            logger.info(f"[RESPONSE_GENERATOR] 开始生成伙伴消息（基于计划）")
            logger.info(f"[RESPONSE_GENERATOR] 消息数量: {len(messages)}")
            logger.info(f"[RESPONSE_GENERATOR] 计划目的: {message_info.get('purpose', 'N/A')}")
            
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=300
            )
            
            result = self.ai_service.get_response_text(api_response)
            logger.info(f"[RESPONSE_GENERATOR] 伙伴消息生成完成，长度: {len(result)}字符")
            return result
            
        except Exception as e:
            logger.error(f"根据计划生成伙伴消息失败: {str(e)}")
            return "我同意你的想法，让我们继续讨论吧。"
