import logging
from datetime import datetime
from wxcloudrun.dao import get_digital_avatar_by_user_id, get_travel_partner_by_user_id, get_travel_settings_by_user_id
from wxcloudrun.ai_service import DeepSeekV3Service
from .prompt_builder import PromptBuilder
from .response_generator import ResponseGenerator
from .conversation_planner import ConversationPlanner
from .message_processor import MessageProcessor
from .react_controller import ReactConversationController

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
        
        # 初始化组件
        self.response_generator = ResponseGenerator(self.ai_service)
        self.conversation_planner = ConversationPlanner(self.ai_service)
        self.message_processor = MessageProcessor()
        
        # 初始化React对话控制器
        self.react_controller = ReactConversationController(user_id, self.ai_service)
        
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
            
            # 初始化React控制器的上下文
            self.react_controller.initialize_context(
                self.avatar_info, 
                self.partner_info, 
                self.travel_settings
            )
                
        except Exception as e:
            logger.error(f"加载用户数据失败: {str(e)}")
            raise e
    
    
    def create_avatar_prompt(self):
        """创建分身提示词"""
        prompt_builder = PromptBuilder(self.avatar_info, self.partner_info)
        return prompt_builder.create_avatar_prompt()
    
    def create_partner_prompt(self):
        """创建伙伴提示词"""
        prompt_builder = PromptBuilder(self.avatar_info, self.partner_info)
        return prompt_builder.create_partner_prompt()
    
    
    def generate_partner_response(self, avatar_message, conversation_history):
        """生成伙伴回复（基于分身消息）"""
        return self.response_generator.generate_partner_response(
            avatar_message, conversation_history, self.avatar_info, self.partner_info
        )
    
    
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
        """生成多轮对话流(基于AI计划的智能对话)"""
        try:
            # 确保用户数据已加载
            self.load_user_data()
            
            conversation_history = []
            total_messages = 0
            
            # 生成对话计划
            plan = self.generate_conversation_plan(min_rounds, max_rounds)
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
        return self.conversation_planner.generate_conversation_plan(
            self.avatar_info, self.partner_info, self.travel_settings, min_rounds, max_rounds
        )
    
    def _generate_avatar_message_by_plan(self, message_info, conversation_history):
        """根据计划生成分身消息"""
        return self.response_generator.generate_avatar_message_by_plan(
            message_info, conversation_history, self.avatar_info, self.partner_info
        )
    
    def _generate_partner_message_by_plan(self, message_info, conversation_history):
        """根据计划生成伙伴消息"""
        return self.response_generator.generate_partner_message_by_plan(
            message_info, conversation_history, self.avatar_info, self.partner_info
        )
    
    def _push_message(self, speaker_type, message, conversation_history, message_index):
        """推送消息到历史记录并yield"""
        result = self.message_processor.push_message(speaker_type, message, conversation_history, message_index)
        yield result
    
    def generate_react_conversation_stream(self, min_rounds=3, max_rounds=6):
        """生成React模式对话流"""
        try:
            # 确保用户数据已加载
            self.load_user_data()
            
            # 配置React控制器
            self.react_controller.update_config(
                min_rounds=min_rounds,
                max_rounds=max_rounds,
                enable_reflection=True,
                debug_mode=False
            )
            
            # 运行React对话循环
            for message in self.react_controller.run_conversation():
                yield {
                    'speaker_type': message['speaker_type'],
                    'message': message['message'],
                    'metadata': message.get('metadata', {})
                }
            
        except Exception as e:
            logger.error(f"生成React对话流失败: {str(e)}")
            raise e
    
    def generate_react_conversation_sync(self, min_rounds=3, max_rounds=6):
        """同步生成React模式对话"""
        try:
            # 确保用户数据已加载
            self.load_user_data()
            
            # 配置React控制器
            self.react_controller.update_config(
                min_rounds=min_rounds,
                max_rounds=max_rounds,
                enable_reflection=True,
                debug_mode=False
            )
            
            # 运行React对话循环
            messages = self.react_controller.run_conversation_sync()
            
            return {
                'messages': messages,
                'summary': self.react_controller.get_conversation_summary(),
                'total_messages': len(messages)
            }
            
        except Exception as e:
            logger.error(f"生成React对话失败: {str(e)}")
            raise e
    
    def get_react_conversation_debug(self):
        """获取React对话调试信息"""
        if not self._data_loaded:
            self.load_user_data()
        
        return self.react_controller.get_debug_info()
    
    def reset_react_conversation(self):
        """重置React对话"""
        if not self._data_loaded:
            self.load_user_data()
        
        self.react_controller.reset_conversation()