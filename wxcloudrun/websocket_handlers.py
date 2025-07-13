from flask import Response, request, stream_with_context
from wxcloudrun.ai_service import DeepSeekV3Service
import json
import urllib.parse
from run import app

def create_response(generator):
    """创建统一的响应"""
    return Response(
        stream_with_context(generator),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Access-Control-Allow-Origin': '*'}
    )

def yield_data(data_type, **data):
    """生成事件数据"""
    yield f"data: {json.dumps({'type': data_type, **data})}\n\n"

def generate_error(message):
    """生成错误响应"""
    yield from yield_data('error', message=message)

def generate(messages):
    """生成AI响应"""
    try:
        messages = [{"role": "user", "content": messages}]
        
        service = DeepSeekV3Service()
        
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                api_response = service.chat_completion(messages=messages, temperature=0.7, max_tokens=1000)
                ai_response = service.get_response_text(api_response)
                yield from yield_data('chunk', content=ai_response)
                return  # 成功则退出
            except Exception as e:
                print(f"第{attempt + 1}次尝试失败: {str(e)}")
                if attempt == max_retries - 1:  # 最后一次尝试
                    raise e
                import time
                time.sleep(1)  # 等待1秒后重试
        
    except Exception as e:
        print(f"AI服务调用失败: {str(e)}")
        error_msg = str(e)
        if "SSL" in error_msg or "EOF" in error_msg:
            error_msg = "网络连接失败，请稍后重试"
        yield from yield_data('error', message=f'处理失败: {error_msg}')

def get_messages_from_request():
    """从请求中获取消息数据"""
    encoded_data = request.args.get('data', '')
    if not encoded_data:
        raise ValueError("缺少data参数")
    
    decoded_data = urllib.parse.unquote(encoded_data)
    print(f"解码后的数据: {decoded_data}")
    
    data = json.loads(decoded_data)
    print(f"解析后的JSON数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    messages = data.get('messages', [])
    print(f"提取的messages: {json.dumps(messages, ensure_ascii=False, indent=2)}")
    
    if not messages:
        raise ValueError("缺少messages数据")
    
    return messages

@app.route('/api/chat/stream', methods=['GET'])
def chat_stream():
    """聊天流式接口"""
    try:
        messages = get_messages_from_request()
        return create_response(generate(messages))
    except (ValueError, json.JSONDecodeError) as e:
        return create_response(generate_error(str(e)))
    except Exception as e:
        return create_response(generate_error(f"处理失败: {str(e)}"))


# @socketio.on('chat_message')
# def handle_chat_message(data):
#     """处理实时聊天消息"""
#     try:
#         user_id = data.get('user_id')
#         session_id = data.get('session_id')
#         message = data.get('message')
#         temperature = data.get('temperature', 0.7)
#         max_tokens = data.get('max_tokens', 1000)
        
#         if not user_id or not session_id or not message:
#             emit('error', {'code': -1, 'errorMsg': '缺少必需参数: user_id, session_id, message'})
#             return
        
#         if not message.strip():
#             emit('error', {'code': -1, 'errorMsg': '消息内容不能为空'})
#             return
        
#         room = f"{user_id}_{session_id}"
        
#         try:
#             ai_service = DeepSeekV3Service()
#         except ValueError as e:
#             emit('error', {'code': -1, 'errorMsg': f'AI服务初始化失败: {str(e)}'})
#             return
        
#         history = get_conversation_history(user_id, session_id, limit=5)
#         messages = ai_service.create_conversation_context(user_id, session_id, history)
        
#         messages.append({
#             "role": "user",
#             "content": message
#         })
        
#         try:
#             api_response = ai_service.chat_completion(
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=max_tokens
#             )
            
#             ai_response = ai_service.get_response_text(api_response)
#             usage_info = ai_service.get_usage_info(api_response)
            
#             conversation = AIConversation()
#             conversation.user_id = user_id
#             conversation.session_id = session_id
#             conversation.user_message = message
#             conversation.ai_response = ai_response
#             conversation.created_at = datetime.now()
            
#             insert_ai_conversation(conversation)
            
#             socketio.emit('chat_response', {
#                 'code': 0,
#                 'data': {
#                     'user_message': message,
#                     'ai_response': ai_response,
#                     'model': 'deepseek-v3',
#                     'usage': usage_info
#                 }
#             }, to=room)
            
#         except Exception as e:
#             emit('error', {'code': -1, 'errorMsg': f'聊天失败: {str(e)}'})
                
#     except Exception as e:
#         emit('error', {'code': -1, 'errorMsg': f'处理聊天消息失败: {str(e)}'})


# @socketio.on('get_history')
# def handle_get_history(data):
#     """获取聊天历史"""
#     try:
#         user_id = data.get('user_id')
#         session_id = data.get('session_id')
#         limit = data.get('limit', 10)
        
#         if not user_id or not session_id:
#             emit('error', {'code': -1, 'errorMsg': '缺少user_id或session_id参数'})
#             return
        
#         history = get_conversation_history(user_id, session_id, limit)
        
#         history_data = []
#         for record in reversed(history):
#             history_data.append({
#                 'id': record.id,
#                 'user_message': record.user_message,
#                 'ai_response': record.ai_response,
#                 'created_at': record.created_at.isoformat()
#             })
        
#         emit('history_response', {
#             'code': 0,
#             'data': {
#                 'history': history_data,
#                 'count': len(history_data)
#             }
#         })
        
#     except Exception as e:
#         emit('error', {'code': -1, 'errorMsg': f'获取历史记录失败: {str(e)}'})
