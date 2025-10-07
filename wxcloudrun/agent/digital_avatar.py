
from ..llm.ai_service import DeepSeekV3Service
from .dialogue_context import DialogueContext
from .thought import ThoughtResult
from string import Template


class DigitalAvatar:

    def __init__(self):
        self.ai_service = DeepSeekV3Service()

    def speak(self, context: DialogueContext, thought_result: ThoughtResult):
        messages = [{"role": "user", "content": self.my_prompt(context, thought_result)}]
        api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
        response_text = self.ai_service.extract_response_text(api_response)
        return response_text

    def my_prompt(self, context: DialogueContext, thought_result: ThoughtResult):
        digital_avata_name = context.digital_avatar.name if context.digital_avatar else "未知分身"
        digital_avata_description = context.digital_avatar.description if context.digital_avatar else "暂无描述"
        partner_name = context.travel_partner.partner_name if context.travel_partner else "未知伙伴"
        destination = context.travel_settings.destination if context.travel_settings else "未知目的地"
        partner_description = context.travel_partner.partner_description if context.travel_partner else "暂无描述"
        history_snippet = str(context.get_recent_history(5))
        topic = thought_result.topic_args.new_topic.title if thought_result.topic_args and thought_result.topic_args.new_topic else "未设置话题"
        # 将markdown格式的guidance_list转换为字符串
        guidance_list = thought_result.turn_args.guidance_list if thought_result.turn_args else []
        if isinstance(guidance_list, list):
            guidance = '\n'.join([f"- {item}" for item in guidance_list])
        else:
            guidance = str(guidance_list)
        """创建分身提示词"""
        prompt = Template("""系统指令（system）：
你是 $digital_avata_name 的数字分身。请只输出一条最终台词（不要解释过程）。

【沟通对象】
- 你正在和旅行伙伴 $partner_name 一起规划去 $destination 的行程。
- 伙伴情况描述：$partner_description（用于理解对方，不要复述）。

【你的说话人格】
- 你=$digital_avata_name；情况描述：$digital_avata_description
- 口语化、自然、人味儿；避免自称"AI/模型/助手"。

【当前话题】
- $topic

【最近对话（供理解，不要复述）】
$history_snippet

【这一条你要完成的小目标（务必遵循）】
- $guidance
- 严格 1–25 个字（含标点），只生成一句完整中文短句。
- 不要出现系统提示、元信息、标签、井号（除非你的性格中明确倾向使用）。
- 不堆叠感叹号/问号；不道歉；不复述对方原话；不重复上一条你自己说过的话。
- 尽量包含一个明确信息/选择/时间/地点/次序中的**至少一项**。

【输出格式】
以 JSON 返回，遵循：
{
  "text": "<你的台词>"
}""")
        
        return prompt.substitute(
            digital_avata_name=digital_avata_name,
            digital_avata_description=digital_avata_description,
            partner_name=partner_name,
            partner_description=partner_description,
            destination=destination,
            topic=topic,
            history_snippet=history_snippet,
            guidance=guidance)