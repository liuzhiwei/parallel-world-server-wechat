from datetime import datetime
from flask import render_template, request
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.ai_service import DeepSeekV3Service


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/chat')
def chat_page():
    """
    :return: 返回聊天页面
    """
    return render_template('chat.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    DeepSeek V3聊天API
    :return: AI回复
    """
    try:
        # 获取请求参数
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['message', 'user_id']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_message = params['message']
        user_id = params['user_id']
        temperature = params.get('temperature', 0.7)
        max_tokens = params.get('max_tokens', 1000)
        
        # 验证参数
        if not user_message.strip():
            return make_err_response('消息内容不能为空')
        
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 初始化DeepSeek服务
        try:
            ai_service = DeepSeekV3Service()
        except ValueError as e:
            return make_err_response(f'AI服务初始化失败: {str(e)}')
        
        # 创建对话上下文
        messages = []
        
        # 添加系统消息
        system_message = {
            "role": "system",
            "content": "你是一个有用的AI助手，请用中文回答用户的问题。"
        }
        messages.append(system_message)
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # 调用DeepSeek API
        api_response = ai_service.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # 提取AI回复
        ai_response = ai_service.get_response_text(api_response)
        usage_info = ai_service.get_usage_info(api_response)
        
        # 返回响应
        response_data = {
            'response': ai_response,
            'model': 'deepseek-v3',
            'usage': usage_info
        }
        
        return make_succ_response(response_data)
        
    except Exception as e:
        return make_err_response(f'聊天服务错误: {str(e)}')



