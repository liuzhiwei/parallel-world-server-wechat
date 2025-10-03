"""
对话计划器
负责生成对话计划
"""

import logging
import json
import re
from wxcloudrun.ai_service import DeepSeekV3Service

# 初始化日志
logger = logging.getLogger('log')


class ConversationPlanner:
    """对话计划器"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
    def generate_conversation_plan(self, avatar_info, partner_info, travel_settings, min_rounds, max_rounds):
        """生成对话计划"""
        try:
            # 构建计划提示词
            from .prompt_builder import PromptBuilder
            prompt_builder = PromptBuilder(avatar_info, partner_info)
            plan_prompt = prompt_builder.create_conversation_plan_prompt(travel_settings, min_rounds, max_rounds)

            messages = [{"role": "user", "content": plan_prompt}]
            
            logger.info(f"[CONVERSATION_PLANNER] 开始生成对话计划")
            logger.info(f"[CONVERSATION_PLANNER] 计划提示词长度: {len(plan_prompt)}字符")
            logger.info(f"[CONVERSATION_PLANNER] 轮次范围: {min_rounds}-{max_rounds}")
            
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=2000
            )
            
            plan_text = self.ai_service.get_response_text(api_response)
            logger.info(f"[CONVERSATION_PLANNER] 计划生成完成，响应长度: {len(plan_text)}字符")
            
            # 解析JSON计划
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan_json = json.loads(json_match.group())
                return plan_json
            else:
                # 如果解析失败，直接抛出异常
                raise Exception("AI生成的对话计划格式错误，无法解析JSON")
                
        except Exception as e:
            logger.error(f"生成对话计划失败: {str(e)}")
            raise e
    
    def get_default_plan(self, min_rounds, max_rounds):
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
                    {"speaker": "avatar" if i % 2 == 0 else "partner", "purpose": "讨论具体安排", "topic": "行程规划", "tone": "认真讨论"}
                ]
            elif i < total_rounds * 2 // 3:
                purpose = "分享旅行经验和建议"
                messages = [
                    {"speaker": "avatar" if i % 2 == 0 else "partner", "purpose": "分享经验", "topic": "旅行建议", "tone": "分享交流"}
                ]
            else:
                purpose = "总结和确认旅行计划"
                messages = [
                    {"speaker": "avatar" if i % 2 == 0 else "partner", "purpose": "总结讨论", "topic": "计划确认", "tone": "总结确认"}
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
