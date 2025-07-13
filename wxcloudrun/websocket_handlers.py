from datetime import datetime
from flask import Response, request, stream_with_context
from wxcloudrun.ai_service import DeepSeekV3Service
import json
from run import app

def generate(user_message):

    yield f"data: {json.dumps({'type': 'start', 'message': '开始处理...'})}\n\n"
    
    service = DeepSeekV3Service()

    # 格式化消息为API所需的格式
    messages = [
        {
            "role": "user",
            "content": user_message
        }
    ]
    api_response = service.chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    
    ai_response = service.get_response_text(api_response)
    
    yield f"data: {json.dumps({'type': 'chunk', 'content': ai_response})}\n\n"

    # 发送完成信号
    yield f"data: {json.dumps({'type': 'complete', 'message': '处理完成'})}\n\n"
            

@app.route('/api/chat/stream', methods=['GET'])
def chat_stream():
    user_message = request.args.get('message', '')
    return Response(
        stream_with_context(generate(user_message)),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        })


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
