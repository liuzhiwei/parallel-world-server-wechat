"""
React模式对话系统的主控制器
实现思考-行动-反思循环
"""

import logging
from typing import Dict, Any, List, Generator
from .react_conversation import (
    ConversationContext, ThinkingModel, ReflectionModel, 
    ActionType, Action, ActionResult, Reflection
)
from .react_tools import ToolRegistry
from wxcloudrun.ai_service import DeepSeekV3Service

# 初始化日志
logger = logging.getLogger('log')


class ReactConversationController:
    """React模式对话控制器"""
    
    def __init__(self, user_id: str, ai_service: DeepSeekV3Service = None):
        self.user_id = user_id
        self.ai_service = ai_service or DeepSeekV3Service()
        
        # 初始化组件
        self.thinking_model = ThinkingModel(self.ai_service)
        self.reflection_model = ReflectionModel(self.ai_service)
        self.tool_registry = ToolRegistry(self.ai_service)
        
        # 对话上下文
        self.context: ConversationContext = None
        
        # 配置参数
        self.max_rounds = 10
        self.min_rounds = 3
        self.enable_reflection = True
        self.debug_mode = False
    
    def initialize_context(self, avatar_info, partner_info, travel_settings):
        """初始化对话上下文"""
        self.context = ConversationContext(avatar_info, partner_info, travel_settings)
        
        # 设置初始状态
        self.context.session_state.update({
            'current_round': 0,
            'current_topic': '旅行规划',
            'conversation_phase': 'start',
            'speaker_turn': 'avatar'
        })
        
        logger.info(f"对话上下文初始化完成: {self.user_id}")
    
    def run_conversation(self, max_rounds: int = None) -> Generator[Dict[str, Any], None, None]:
        """运行对话循环"""
        if not self.context:
            raise Exception("对话上下文未初始化")
        
        if max_rounds:
            self.max_rounds = max_rounds
        
        logger.info(f"[REACT_CONTROLLER] 开始React对话循环: {self.user_id}, 最大轮次: {self.max_rounds}")
        
        try:
            # 初始行动：生成对话计划
            initial_action = Action(
                type=ActionType.PLAN_GENERATE,
                params={'min_rounds': self.min_rounds, 'max_rounds': self.max_rounds},
                reason="初始化对话计划"
            )
            
            logger.info(f"[REACT_CONTROLLER] 执行初始行动: {initial_action.type.value}")
            # 执行初始行动
            result = self.tool_registry.execute(initial_action.type.value, initial_action.params, self.context)
            self.context.add_action_result(initial_action, result)
            logger.info(f"[REACT_CONTROLLER] 初始行动完成: {result.success}")
            
            if result.success:
                self.context.update_plan(result.data)
                yield self._format_message('system', f"对话计划生成: {result.data.get('description', '')}")
            
            # 主对话循环
            for round_num in range(1, self.max_rounds + 1):
                logger.info(f"[REACT_CONTROLLER] 对话轮次 {round_num}/{self.max_rounds}")
                
                # 检查是否应该结束
                if self.context.should_end_conversation():
                    logger.info("[REACT_CONTROLLER] 对话达到结束条件")
                    break
                
                # 思考阶段
                logger.info(f"[REACT_CONTROLLER] 开始思考阶段")
                action = self.thinking_model.think(self.context)
                logger.info(f"[REACT_CONTROLLER] 思考结果: {action.type.value} - {action.reason}")
                
                # 执行阶段
                logger.info(f"[REACT_CONTROLLER] 开始执行阶段")
                result = self.tool_registry.execute(action.type.value, action.params, self.context)
                self.context.add_action_result(action, result)
                logger.info(f"[REACT_CONTROLLER] 执行结果: {result.success} - {result.message}")
                
                # 反思阶段
                if self.enable_reflection:
                    logger.info(f"[REACT_CONTROLLER] 开始反思阶段")
                    reflection = self.reflection_model.reflect(self.context, action, result)
                    self.context.add_reflection(reflection)
                    logger.info(f"[REACT_CONTROLLER] 反思结果: {reflection.action_evaluation}")
                
                # 产出消息
                if result.success and result.data:
                    if 'message' in result.data:
                        # 发言类工具
                        yield self._format_message(
                            result.data['speaker'], 
                            result.data['message'],
                            metadata={
                                'round': round_num,
                                'action': action.type.value,
                                'tool': result.metadata.get('tool', 'unknown')
                            }
                        )
                    elif 'end_message' in result.data:
                        # 结束对话
                        yield self._format_message('system', result.data['end_message'])
                        break
                
                # 检查对话结束
                if action.type == ActionType.CONVERSATION_END:
                    logger.info("对话正常结束")
                    break
            
            # 对话结束
            if not self.context.should_end_conversation():
                # 强制结束
                end_action = Action(
                    type=ActionType.CONVERSATION_END,
                    params={'end_message': '对话达到最大轮次，自动结束'},
                    reason="达到最大轮次限制"
                )
                result = self.tool_registry.execute(end_action.type.value, end_action.params, self.context)
                self.context.add_action_result(end_action, result)
                
                if result.success:
                    yield self._format_message('system', result.data['end_message'])
            
            logger.info(f"React对话循环结束: {self.user_id}, 总轮次: {self.context.session_state['current_round']}")
            
        except Exception as e:
            logger.error(f"React对话循环异常: {str(e)}")
            yield self._format_message('system', f"对话异常: {str(e)}")
            raise e
    
    def run_conversation_sync(self, max_rounds: int = None) -> List[Dict[str, Any]]:
        """同步运行对话循环，返回所有消息"""
        messages = []
        for message in self.run_conversation(max_rounds):
            messages.append(message)
        return messages
    
    def _format_message(self, speaker_type: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """格式化消息输出"""
        return {
            'speaker_type': speaker_type,
            'message': message,
            'metadata': metadata or {}
        }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要"""
        if not self.context:
            return {}
        
        return {
            'total_rounds': self.context.session_state['current_round'],
            'total_messages': len(self.context.history),
            'conversation_phase': self.context.session_state['conversation_phase'],
            'current_topic': self.context.session_state['current_topic'],
            'reflections_count': len(self.context.reflection_log),
            'actions_count': len(self.context.action_history),
            'plan_description': self.context.current_plan.get('description', '') if self.context.current_plan else '',
            'recent_messages': self.context.history[-5:] if self.context.history else []
        }
    
    def get_debug_info(self) -> Dict[str, Any]:
        """获取调试信息"""
        if not self.context:
            return {}
        
        return {
            'context': {
                'session_state': self.context.session_state,
                'current_plan': self.context.current_plan,
                'history_length': len(self.context.history)
            },
            'reflections': [
                {
                    'evaluation': r.action_evaluation,
                    'adjustment': r.strategy_adjustment,
                    'confidence': r.confidence
                } for r in self.context.reflection_log[-3:]  # 最近3次反思
            ],
            'recent_actions': [
                {
                    'type': action.type.value,
                    'reason': action.reason,
                    'success': result.success,
                    'message': result.message
                } for action, result in self.context.action_history[-5:]  # 最近5次行动
            ]
        }
    
    def update_config(self, **kwargs):
        """更新配置"""
        if 'max_rounds' in kwargs:
            self.max_rounds = kwargs['max_rounds']
        if 'min_rounds' in kwargs:
            self.min_rounds = kwargs['min_rounds']
        if 'enable_reflection' in kwargs:
            self.enable_reflection = kwargs['enable_reflection']
        if 'debug_mode' in kwargs:
            self.debug_mode = kwargs['debug_mode']
        
        logger.info(f"配置更新: {kwargs}")
    
    def reset_conversation(self):
        """重置对话"""
        if self.context:
            self.context.history.clear()
            self.context.reflection_log.clear()
            self.context.action_history.clear()
            self.context.current_plan = None
            self.context.session_state.update({
                'current_round': 0,
                'current_topic': '旅行规划',
                'conversation_phase': 'start',
                'speaker_turn': 'avatar'
            })
        
        logger.info("对话已重置")
