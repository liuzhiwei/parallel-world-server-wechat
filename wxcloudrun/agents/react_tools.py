"""
React模式对话系统的工具实现
"""

import logging
from typing import Dict, Any
from abc import ABC, abstractmethod
from .react_conversation import ActionResult
from .prompt_builder import PromptBuilder
from .response_generator import ResponseGenerator
from .conversation_planner import ConversationPlanner

# 初始化日志
logger = logging.getLogger('log')


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, params: Dict[str, Any], context: Any) -> ActionResult:
        """执行工具"""
        pass


class PlanGeneratorTool(BaseTool):
    """计划生成工具"""
    
    def __init__(self, conversation_planner: ConversationPlanner):
        super().__init__("plan_generator")
        self.conversation_planner = conversation_planner
    
    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        """生成对话计划"""
        try:
            min_rounds = params.get('min_rounds', 3)
            max_rounds = params.get('max_rounds', 6)
            
            plan = self.conversation_planner.generate_conversation_plan(
                context.avatar_info,
                context.partner_info,
                context.travel_settings,
                min_rounds,
                max_rounds
            )
            
            return ActionResult(
                success=True,
                data=plan,
                message="对话计划生成成功",
                metadata={'tool': self.name, 'rounds': len(plan.get('rounds', []))}
            )
            
        except Exception as e:
            logger.error(f"计划生成工具执行失败: {str(e)}")
            return ActionResult(
                success=False,
                data=None,
                message=f"计划生成失败: {str(e)}",
                metadata={'tool': self.name}
            )


class PlanUpdaterTool(BaseTool):
    """计划更新工具"""
    
    def __init__(self, conversation_planner: ConversationPlanner):
        super().__init__("plan_updater")
        self.conversation_planner = conversation_planner
    
    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        """更新对话计划"""
        try:
            # 根据当前对话进展更新计划
            current_round = context.session_state.get('current_round', 0)
            conversation_phase = context.session_state.get('conversation_phase', 'start')
            
            # 如果当前没有计划，生成新计划
            if not context.current_plan:
                return PlanGeneratorTool(self.conversation_planner).execute(params, context)
            
            # 根据对话进展调整计划
            updated_plan = context.current_plan.copy()
            
            # 可以根据实际需要调整计划内容
            if conversation_phase == 'middle' and current_round > 3:
                # 中期调整：增加深入讨论
                updated_plan['description'] += " (已调整：增加深入讨论)"
            
            return ActionResult(
                success=True,
                data=updated_plan,
                message="对话计划更新成功",
                metadata={'tool': self.name, 'current_round': current_round}
            )
            
        except Exception as e:
            logger.error(f"计划更新工具执行失败: {str(e)}")
            return ActionResult(
                success=False,
                data=None,
                message=f"计划更新失败: {str(e)}",
                metadata={'tool': self.name}
            )


class AvatarSpeakerTool(BaseTool):
    """分身发言工具"""
    
    def __init__(self, response_generator: ResponseGenerator):
        super().__init__("avatar_speaker")
        self.response_generator = response_generator
    
    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        """让分身发言"""
        try:
            # 构建消息信息
            message_info = {
                'purpose': params.get('purpose', '表达想法'),
                'topic': params.get('topic', '旅行讨论'),
                'tone': params.get('tone', '自然交流')
            }
            
            # 生成分身消息
            message = self.response_generator.generate_avatar_message_by_plan(
                message_info,
                context.history,
                context.avatar_info,
                context.partner_info
            )
            
            # 更新上下文
            context.add_message('avatar', message, {'tool': self.name})
            context.session_state['speaker_turn'] = 'partner'
            context.session_state['current_round'] += 1
            
            return ActionResult(
                success=True,
                data={'message': message, 'speaker': 'avatar'},
                message="分身发言成功",
                metadata={'tool': self.name, 'round': context.session_state['current_round']}
            )
            
        except Exception as e:
            logger.error(f"分身发言工具执行失败: {str(e)}")
            return ActionResult(
                success=False,
                data=None,
                message=f"分身发言失败: {str(e)}",
                metadata={'tool': self.name}
            )


class PartnerSpeakerTool(BaseTool):
    """伙伴发言工具"""
    
    def __init__(self, response_generator: ResponseGenerator):
        super().__init__("partner_speaker")
        self.response_generator = response_generator
    
    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        """让伙伴发言"""
        try:
            # 构建消息信息
            message_info = {
                'purpose': params.get('purpose', '回应讨论'),
                'topic': params.get('topic', '旅行讨论'),
                'tone': params.get('tone', '友好回应')
            }
            
            # 生成伙伴消息
            message = self.response_generator.generate_partner_message_by_plan(
                message_info,
                context.history,
                context.avatar_info,
                context.partner_info
            )
            
            # 更新上下文
            context.add_message('partner', message, {'tool': self.name})
            context.session_state['speaker_turn'] = 'avatar'
            
            return ActionResult(
                success=True,
                data={'message': message, 'speaker': 'partner'},
                message="伙伴发言成功",
                metadata={'tool': self.name, 'round': context.session_state['current_round']}
            )
            
        except Exception as e:
            logger.error(f"伙伴发言工具执行失败: {str(e)}")
            return ActionResult(
                success=False,
                data=None,
                message=f"伙伴发言失败: {str(e)}",
                metadata={'tool': self.name}
            )


class ContextUpdateTool(BaseTool):
    """上下文更新工具"""
    
    def __init__(self):
        super().__init__("context_update")
    
    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        """更新上下文信息"""
        try:
            # 更新会话状态
            if 'session_state' in params:
                context.update_session_state(params['session_state'])
            
            # 更新话题
            if 'topic' in params:
                context.session_state['current_topic'] = params['topic']
            
            # 更新对话阶段
            if 'phase' in params:
                context.session_state['conversation_phase'] = params['phase']
            
            # 更新计划
            if 'plan' in params:
                context.update_plan(params['plan'])
            
            return ActionResult(
                success=True,
                data={'updated_state': context.session_state},
                message="上下文更新成功",
                metadata={'tool': self.name}
            )
            
        except Exception as e:
            logger.error(f"上下文更新工具执行失败: {str(e)}")
            return ActionResult(
                success=False,
                data=None,
                message=f"上下文更新失败: {str(e)}",
                metadata={'tool': self.name}
            )


class ConversationEndTool(BaseTool):
    """对话结束工具"""
    
    def __init__(self):
        super().__init__("conversation_end")
    
    def execute(self, params: Dict[str, Any], context) -> ActionResult:
        """结束对话"""
        try:
            # 更新对话阶段为结束
            context.session_state['conversation_phase'] = 'end'
            
            # 添加结束消息
            end_message = params.get('end_message', '对话结束，感谢讨论！')
            context.add_message('system', end_message, {'tool': self.name})
            
            return ActionResult(
                success=True,
                data={'end_message': end_message},
                message="对话结束成功",
                metadata={'tool': self.name, 'total_rounds': context.session_state['current_round']}
            )
            
        except Exception as e:
            logger.error(f"对话结束工具执行失败: {str(e)}")
            return ActionResult(
                success=False,
                data=None,
                message=f"对话结束失败: {str(e)}",
                metadata={'tool': self.name}
            )


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self, ai_service):
        # 初始化工具
        self.conversation_planner = ConversationPlanner(ai_service)
        self.response_generator = ResponseGenerator(ai_service)
        
        # 注册工具
        self.tools = {
            'plan_generate': PlanGeneratorTool(self.conversation_planner),
            'plan_update': PlanUpdaterTool(self.conversation_planner),
            'avatar_speak': AvatarSpeakerTool(self.response_generator),
            'partner_speak': PartnerSpeakerTool(self.response_generator),
            'context_update': ContextUpdateTool(),
            'conversation_end': ConversationEndTool()
        }
    
    def execute(self, tool_name: str, params: Dict[str, Any], context) -> ActionResult:
        """执行工具"""
        if tool_name not in self.tools:
            return ActionResult(
                success=False,
                data=None,
                message=f"未知工具: {tool_name}",
                metadata={'tool': tool_name}
            )
        
        try:
            return self.tools[tool_name].execute(params, context)
        except Exception as e:
            logger.error(f"工具执行异常: {tool_name}, {str(e)}")
            return ActionResult(
                success=False,
                data=None,
                message=f"工具执行异常: {str(e)}",
                metadata={'tool': tool_name}
            )
    
    def list_tools(self) -> list:
        """列出所有可用工具"""
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """获取工具信息"""
        if tool_name in self.tools:
            return {
                'name': self.tools[tool_name].name,
                'description': f"工具: {self.tools[tool_name].name}"
            }
        return None
