"""
提示词构建器
负责构建各种AI提示词
"""


class PromptBuilder:
    """提示词构建器"""
    
    def __init__(self, avatar_info, partner_info):
        self.avatar_info = avatar_info
        self.partner_info = partner_info
    
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
    
    def create_conversation_plan_prompt(self, travel_settings, min_rounds, max_rounds):
        """创建对话计划提示词"""
        if not self.avatar_info or not self.partner_info:
            raise Exception("分身或伙伴信息不存在")
            
        plan_prompt = f"""作为对话规划师，请为{self.avatar_info.name}和{self.partner_info.partner_name}制定一个旅行对话计划。

用户信息：
- 分身：{self.avatar_info.name}，性格：{self.avatar_info.description}
- 伙伴：{self.partner_info.partner_name}，性格：{self.partner_info.partner_description}"""

        if not travel_settings or not travel_settings.destination:
            raise Exception("旅行目的地未设置，请先完成旅行设置")
        
        plan_prompt += f"\n- 目的地：{travel_settings.destination}"
        if hasattr(travel_settings, 'duration') and travel_settings.duration:
            plan_prompt += f"\n- 旅行时长：{travel_settings.duration}"

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

        return plan_prompt
    
    def create_avatar_plan_prompt(self, message_info):
        """创建基于计划的分身提示词"""
        plan_prompt = f"""你是{self.avatar_info.name}，性格特点是：{self.avatar_info.description}。

当前对话目的：{message_info['purpose']}
讨论话题：{message_info['topic']}
语气风格：{message_info['tone']}

你正在和{self.partner_info.partner_name}讨论旅行。请根据以上信息，自然地表达你的想法。

请用第一人称"我"来回答，就像真正的{self.avatar_info.name}一样。"""

        return plan_prompt
    
    def create_partner_plan_prompt(self, message_info):
        """创建基于计划的伙伴提示词"""
        plan_prompt = f"""你是{self.partner_info.partner_name}，性格特点是：{self.partner_info.partner_description}。

当前对话目的：{message_info['purpose']}
讨论话题：{message_info['topic']}
语气风格：{message_info['tone']}

你正在和{self.avatar_info.name}讨论旅行。请根据以上信息，自然地表达你的想法。

请用第一人称"我"来回答，就像真正的{self.partner_info.partner_name}一样。"""

        return plan_prompt
