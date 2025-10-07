from ..llm.ai_service import DeepSeekV3Service
from string import Template
from .agent_data import ThoughtResult
import logging

logger = logging.getLogger(__name__)


class Thought:

    def __init__(self, context):
        self.context = context
        self.ai_service = DeepSeekV3Service()

    def thought(self):
        messages = [{"role": "user", "content": self.my_prompt()}]
        api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
        response_text = self.ai_service.extract_response_text(api_response)
        result, err = ThoughtResult.try_from_dict(response_text)
        if err:
            logger.error(f"LLM's ThoughtResult validation failed: {err}")
            return None
        return result

    def my_prompt(self):
        prompt = Template("""你是旅行对话系统的“Thought 决策器”。你的任务：
(1) 决定下一位发言者（数字分身 $user_digital_avatar_name 或 旅行伙伴 $partner_name），必要时让其连续多条自然表达（1–3 条）。
(2) 关于话题（topic）：
   - 若当前话题为空（首次），请生成第一个话题；
   - 若不为空，依据历史与当前对话，判断继续当前话题或收尾并生成新话题。

【上下文】
- 数字分身：$user_digital_avatar_name
  描述：$user_digital_avatar_description
  （说明：description 可包含性格、口吻、习惯、家乡、职业/公司、兴趣偏好、预算倾向、出行习惯等。仅用于理解，不要复述。）
- 旅行伙伴：$partner_name
  描述：$partner_description
   （说明：description 可包含性格、口吻、习惯、家乡、职业/公司、兴趣偏好、预算倾向、出行习惯等。仅用于理解，不要复述。）
- 目的地：$destination
- 历史话题（按目的地分组，供避免重复）：
$topic_history
- 当前话题：$current_topic  // 可能为 null
- 最近对话（升序，最多 $history_window 条）：
$history$

【决策准则（自然表达优先）】
A. 自然完成度：若某人正“展开完整意思/列举选项/补充细节/自我纠正”，允许同一人连续发言（1–3 条），直到段落自然结束。
B. 交接信号：出现“向对方提问/请其确认或选择/请求承诺”时再交给对方。
C. 分歧处理：出现分歧或误解，优先让另一方先复述对齐并给折中。
D. 信息完整性：谁能补齐未回答的关键点，就让谁继续说。
E. 话题充分度：
   - 若已达成共识/信息饱和/重复度高/存在自然过渡点 → END_AND_GENERATE，并生成一个紧接需求、可执行的新话题（例：“首日路线与到达时间”“住宿与预算取舍”“摄影与人少路线”“晚餐与夜景路线”）。
   - 否则 → CONTINUE_TOPIC。
F. 首次无话题：
   - 选择最自然的切入点作为首个话题（如"为什么去 $destination（动机/期待）""首日路线与到达时间"），避免与 $topic_history 重复。
   - 题名简短明确、行动导向。

【生成要求】
- 仅输出合法 JSON（见下方 schema），不得附加多余文本或思维过程。
- guidance_list：长度 1–3；每条是接下来发言人的小目标，示例：“每条1–25字（含标点）”、“推进主题”、“高质量的回复”。不要限定内容，更多是提示或建议。
- 若生成新话题：new_topic.title 清晰具体；rationale ≤40字说明“为何现在切换”。

【输出格式】
{
  "turn_action": "SPEAK_USER_DIGITAL_AVATAR | SPEAK_TRAVEL_PARTNER",
  "guidance_list": ["...", "..."],
  "topic_action": "INIT_AND_GENERATE | CONTINUE_TOPIC | END_AND_GENERATE",
  "topic_args": { "topic": "... or null", "new_topic": { "title": "...", "rationale": "...", "confidence": 0.0 } or null },
  "confidence": 0.0,
  "rationale": "string|null"
}
""")
        return prompt.substitute(
            user_digital_avatar_name=self.context.get_avatar_name(),
            user_digital_avatar_description=self.context.get_avatar_description(),
            partner_name=self.context.get_partner_name(),
            partner_description=self.context.get_partner_description(),
            destination=self.context.get_travel_destination(),
            current_topic=self.context.get_current_topic_text(),
            topic_history=self.context.get_topic_history_summary(),
            history_window=5,
            history=str(self.context.get_recent_history(5)))
        