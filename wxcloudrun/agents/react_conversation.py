"""
React模式对话系统
实现思考-行动-反思循环的智能对话
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from wxcloudrun.ai_service import DeepSeekV3Service

# 初始化日志
logger = logging.getLogger('log')


class ActionType(Enum):
    """行动类型枚举"""
    PLAN_GENERATE = "plan_generate"
    PLAN_UPDATE = "plan_update"
    AVATAR_SPEAK = "avatar_speak"
    PARTNER_SPEAK = "partner_speak"
    CONTEXT_UPDATE = "context_update"
    CONVERSATION_END = "conversation_end"


@dataclass
class Action:
    """行动定义"""
    type: ActionType
    params: Dict[str, Any]
    reason: str = ""


@dataclass
class ActionResult:
    """行动结果"""
    success: bool
    data: Any
    message: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class Reflection:
    """反思结果"""
    action_evaluation: str
    strategy_adjustment: str
    next_action_hint: str
    confidence: float


class ConversationContext:
    """对话上下文"""
    
    def __init__(self, avatar_info, partner_info, travel_settings):
        self.avatar_info = avatar_info
        self.partner_info = partner_info
        self.travel_settings = travel_settings
        
        # 动态状态
        self.history: List[Dict[str, Any]] = []
        self.current_plan: Optional[Dict[str, Any]] = None
        self.session_state: Dict[str, Any] = {
            'current_round': 0,
            'current_topic': '',
            'conversation_phase': 'start',
            'speaker_turn': 'avatar'
        }
        self.reflection_log: List[Reflection] = []
        self.action_history: List[Tuple[Action, ActionResult]] = []
    
    def add_message(self, speaker_type: str, message: str, metadata: Dict[str, Any] = None):
        """添加消息到历史"""
        self.history.append({
            'speaker_type': speaker_type,
            'message': message,
            'timestamp': metadata.get('timestamp') if metadata else None,
            'metadata': metadata or {}
        })
    
    def update_plan(self, plan: Dict[str, Any]):
        """更新对话计划"""
        self.current_plan = plan
    
    def update_session_state(self, updates: Dict[str, Any]):
        """更新会话状态"""
        self.session_state.update(updates)
    
    def add_reflection(self, reflection: Reflection):
        """添加反思记录"""
        self.reflection_log.append(reflection)
    
    def add_action_result(self, action: Action, result: ActionResult):
        """添加行动结果"""
        self.action_history.append((action, result))
    
    def get_context_for_thinking(self) -> str:
        """为思考模型提供上下文"""
        context_parts = []
        
        # 基本信息
        context_parts.append(f"分身: {self.avatar_info.name} ({self.avatar_info.description})")
        context_parts.append(f"伙伴: {self.partner_info.partner_name} ({self.partner_info.partner_description})")
        
        if self.travel_settings:
            context_parts.append(f"目的地: {self.travel_settings.destination}")
        
        # 当前状态
        context_parts.append(f"当前轮次: {self.session_state['current_round']}")
        context_parts.append(f"当前话题: {self.session_state['current_topic']}")
        context_parts.append(f"对话阶段: {self.session_state['conversation_phase']}")
        context_parts.append(f"轮到发言: {self.session_state['speaker_turn']}")
        
        # 对话历史
        if self.history:
            context_parts.append("对话历史:")
            for msg in self.history[-10:]:  # 最近10条
                context_parts.append(f"  {msg['speaker_type']}: {msg['message']}")
        
        # 当前计划
        if self.current_plan:
            context_parts.append(f"当前计划: {self.current_plan.get('description', '无描述')}")
        
        # 最近的反思
        if self.reflection_log:
            latest_reflection = self.reflection_log[-1]
            context_parts.append(f"最近反思: {latest_reflection.action_evaluation}")
        
        return "\n".join(context_parts)
    
    def should_end_conversation(self) -> bool:
        """判断是否应该结束对话"""
        # 可以根据多种条件判断
        if self.session_state['current_round'] >= 10:  # 最大轮次
            return True
        
        if self.session_state['conversation_phase'] == 'end':
            return True
        
        # 可以根据计划完成度判断
        if self.current_plan and self.session_state['current_round'] >= len(self.current_plan.get('rounds', [])):
            return True
        
        return False


class ThinkingModel:
    """思考模型"""
    
    def __init__(self, ai_service: DeepSeekV3Service):
        self.ai_service = ai_service
    
    def think(self, context: ConversationContext) -> Action:
        """分析当前状态，决定下一步行动"""
        try:
            # 构建思考提示词
            thinking_prompt = f"""你是一个智能对话协调器，负责分析当前对话状态并决定下一步行动。

当前上下文:
{context.get_context_for_thinking()}

可用的行动类型:
1. plan_generate - 生成新的对话计划
2. plan_update - 更新现有对话计划
3. avatar_speak - 让分身发言
4. partner_speak - 让伙伴发言
5. context_update - 更新上下文信息
6. conversation_end - 结束对话

请分析当前情况，选择最合适的行动，并说明理由。

返回格式:
ACTION: [行动类型]
REASON: [选择理由]
PARAMS: [行动参数，JSON格式]

例如:
ACTION: avatar_speak
REASON: 当前轮到分身发言，需要根据计划推进对话
PARAMS: {{"topic": "目的地选择", "tone": "兴奋期待"}}"""

            messages = [{"role": "user", "content": thinking_prompt}]
            
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            response_text = self.ai_service.get_response_text(api_response)
            
            # 解析响应
            action_type, reason, params = self._parse_thinking_response(response_text)
            
            return Action(
                type=ActionType(action_type),
                params=params,
                reason=reason
            )
            
        except Exception as e:
            logger.error(f"思考模型执行失败: {str(e)}")
            # 默认行动
            return Action(
                type=ActionType.AVATAR_SPEAK if context.session_state['speaker_turn'] == 'avatar' else ActionType.PARTNER_SPEAK,
                params={},
                reason="思考模型异常，使用默认行动"
            )
    
    def _parse_thinking_response(self, response_text: str) -> Tuple[str, str, Dict[str, Any]]:
        """解析思考模型的响应"""
        import re
        import json
        
        # 提取ACTION
        action_match = re.search(r'ACTION:\s*(\w+)', response_text)
        action_type = action_match.group(1) if action_match else "avatar_speak"
        
        # 提取REASON
        reason_match = re.search(r'REASON:\s*([^\n]+)', response_text)
        reason = reason_match.group(1).strip() if reason_match else "未提供理由"
        
        # 提取PARAMS
        params_match = re.search(r'PARAMS:\s*(\{.*\})', response_text, re.DOTALL)
        if params_match:
            try:
                params = json.loads(params_match.group(1))
            except:
                params = {}
        else:
            params = {}
        
        return action_type, reason, params


class ReflectionModel:
    """反思模型"""
    
    def __init__(self, ai_service: DeepSeekV3Service):
        self.ai_service = ai_service
    
    def reflect(self, context: ConversationContext, action: Action, result: ActionResult) -> Reflection:
        """反思行动结果，调整策略"""
        try:
            # 构建反思提示词
            reflection_prompt = f"""你是一个对话反思器，负责评估行动效果并调整策略。

最近行动:
- 行动类型: {action.type.value}
- 行动理由: {action.reason}
- 行动参数: {action.params}
- 执行结果: {result.success}
- 结果消息: {result.message}

当前上下文:
{context.get_context_for_thinking()}

请评估这次行动的效果，并提出策略调整建议。

返回格式:
EVALUATION: [行动效果评估]
ADJUSTMENT: [策略调整建议]
NEXT_HINT: [下一步行动提示]
CONFIDENCE: [信心度 0-1]

例如:
EVALUATION: 分身发言成功，话题推进顺利
ADJUSTMENT: 继续保持当前节奏，注意话题深度
NEXT_HINT: 让伙伴回应分身的想法
CONFIDENCE: 0.8"""

            messages = [{"role": "user", "content": reflection_prompt}]
            
            api_response = self.ai_service.chat_completion(
                messages=messages,
                temperature=0.6,
                max_tokens=400
            )
            
            response_text = self.ai_service.get_response_text(api_response)
            
            # 解析响应
            evaluation, adjustment, next_hint, confidence = self._parse_reflection_response(response_text)
            
            return Reflection(
                action_evaluation=evaluation,
                strategy_adjustment=adjustment,
                next_action_hint=next_hint,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"反思模型执行失败: {str(e)}")
            # 默认反思
            return Reflection(
                action_evaluation="反思模型异常",
                strategy_adjustment="保持当前策略",
                next_action_hint="继续对话",
                confidence=0.5
            )
    
    def _parse_reflection_response(self, response_text: str) -> Tuple[str, str, str, float]:
        """解析反思模型的响应"""
        import re
        
        # 提取EVALUATION
        eval_match = re.search(r'EVALUATION:\s*([^\n]+)', response_text)
        evaluation = eval_match.group(1).strip() if eval_match else "未提供评估"
        
        # 提取ADJUSTMENT
        adj_match = re.search(r'ADJUSTMENT:\s*([^\n]+)', response_text)
        adjustment = adj_match.group(1).strip() if adj_match else "无调整建议"
        
        # 提取NEXT_HINT
        hint_match = re.search(r'NEXT_HINT:\s*([^\n]+)', response_text)
        next_hint = hint_match.group(1).strip() if hint_match else "无提示"
        
        # 提取CONFIDENCE
        conf_match = re.search(r'CONFIDENCE:\s*([0-9.]+)', response_text)
        try:
            confidence = float(conf_match.group(1)) if conf_match else 0.5
        except:
            confidence = 0.5
        
        return evaluation, adjustment, next_hint, confidence
