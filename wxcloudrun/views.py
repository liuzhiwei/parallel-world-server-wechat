from datetime import datetime
import os
import uuid
from flask import render_template, request
from werkzeug.utils import secure_filename
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid, insert_digital_avatar, get_digital_avatar_by_user_id, update_digital_avatar
from wxcloudrun.model import Counters, DigitalAvatar
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
from wxcloudrun.ai_service import DeepSeekV3Service
from wxcloudrun.wechat_config import WeChatCloudConfig


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


@app.route('/api/upload', methods=['POST'])
def upload_avatar():
    """
    头像上传接口
    :return: 上传后的文件URL
    """
    try:
        print(f"收到上传请求，Content-Type: {request.content_type}")
        print(f"请求文件: {list(request.files.keys())}")
        print(f"请求表单: {dict(request.form)}")
        
        # 检查是否有文件上传
        if 'file' not in request.files:
            print("错误：没有上传文件")
            return make_err_response('没有上传文件')
        
        file = request.files['file']
        if file.filename == '':
            print("错误：没有选择文件")
            return make_err_response('没有选择文件')
        
        print(f"文件名: {file.filename}")
        
        # 检查文件类型
        if not WeChatCloudConfig.is_allowed_file(file.filename):
            print(f"错误：不支持的文件格式: {file.filename}")
            return make_err_response('不支持的文件格式，请上传图片文件')
        
        # 检查上传类型
        upload_type = request.form.get('type', '')
        print(f"上传类型: {upload_type}")
        if upload_type != 'avatar':
            return make_err_response('上传类型错误')
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # 创建上传目录（微信云托管环境）
        upload_folder = os.path.join(WeChatCloudConfig.get_upload_path(), 'avatars')
        print(f"上传目录: {upload_folder}")
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            print(f"创建目录: {upload_folder}")
        
        # 保存文件
        file_path = os.path.join(upload_folder, unique_filename)
        print(f"保存路径: {file_path}")
        file.save(file_path)
        
        # 生成访问URL（微信云托管格式）
        avatar_url = WeChatCloudConfig.get_file_url(f"avatars/{unique_filename}")
        print(f"生成URL: {avatar_url}")
        
        return make_succ_response({'url': avatar_url})
        
    except Exception as e:
        print(f"上传异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return make_err_response(f'文件上传失败: {str(e)}')


@app.route('/api/upload-base64', methods=['POST'])
def upload_avatar_base64():
    """
    Base64 头像上传接口
    :return: 上传后的文件URL
    """
    try:
        print(f"收到 base64 上传请求，Content-Type: {request.content_type}")
        
        # 获取请求参数
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['file', 'type', 'filename']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        file_data = params['file']
        upload_type = params['type']
        filename = params['filename']
        
        print(f"上传类型: {upload_type}")
        print(f"文件名: {filename}")
        print(f"Base64 数据长度: {len(file_data)}")
        
        # 检查上传类型
        if upload_type != 'avatar':
            return make_err_response('上传类型错误')
        
        # 生成安全的文件名
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # 创建上传目录
        upload_folder = os.path.join(WeChatCloudConfig.get_upload_path(), 'avatars')
        print(f"上传目录: {upload_folder}")
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            print(f"创建目录: {upload_folder}")
        
        # 解码 base64 并保存文件
        import base64
        try:
            file_bytes = base64.b64decode(file_data)
            file_path = os.path.join(upload_folder, unique_filename)
            print(f"保存路径: {file_path}")
            
            with open(file_path, 'wb') as f:
                f.write(file_bytes)
            
            # 生成访问URL
            avatar_url = WeChatCloudConfig.get_file_url(f"avatars/{unique_filename}")
            print(f"生成URL: {avatar_url}")
            
            return make_succ_response({'url': avatar_url})
            
        except Exception as decode_error:
            print(f"Base64 解码失败: {str(decode_error)}")
            return make_err_response(f'Base64 解码失败: {str(decode_error)}')
        
    except Exception as e:
        print(f"Base64 上传异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return make_err_response(f'Base64 上传失败: {str(e)}')


@app.route('/api/files', methods=['GET'])
def list_uploaded_files():
    """
    列出已上传的文件
    :return: 文件列表
    """
    try:
        import os
        upload_folder = os.path.join(WeChatCloudConfig.get_upload_path(), 'avatars')
        
        if not os.path.exists(upload_folder):
            return make_succ_response({'files': [], 'count': 0})
        
        files = []
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                file_url = WeChatCloudConfig.get_file_url(f"avatars/{filename}")
                files.append({
                    'filename': filename,
                    'url': file_url,
                    'size': file_stat.st_size,
                    'created': file_stat.st_ctime
                })
        
        # 按创建时间排序
        files.sort(key=lambda x: x['created'], reverse=True)
        
        return make_succ_response({
            'files': files,
            'count': len(files),
            'upload_folder': upload_folder
        })
        
    except Exception as e:
        print(f"列出文件失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return make_err_response(f'列出文件失败: {str(e)}')


@app.route('/api/profile', methods=['POST'])
def create_profile():
    """
    创建数字分身接口
    :return: 创建结果
    """
    try:
        # 获取请求参数
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'name', 'description', 'avatar_url']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        name = params['name']
        description = params['description']
        avatar_url = params['avatar_url']
        
        # 验证参数
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        if not name.strip():
            return make_err_response('分身名称不能为空')
        if not description.strip():
            return make_err_response('性格描述不能为空')
        if not avatar_url.strip():
            return make_err_response('头像URL不能为空')
        
        # 检查是否已存在该用户的分身
        existing_avatar = get_digital_avatar_by_user_id(user_id)
        
        if existing_avatar:
            # 更新现有分身
            existing_avatar.name = name
            existing_avatar.description = description
            existing_avatar.avatar_url = avatar_url
            existing_avatar.updated_at = datetime.now()
            update_digital_avatar(existing_avatar)
            
            return make_succ_response({
                'ok': True,
                'message': '分身信息更新成功',
                'avatar': {
                    'id': existing_avatar.id,
                    'user_id': existing_avatar.user_id,
                    'name': existing_avatar.name,
                    'description': existing_avatar.description,
                    'avatar_url': existing_avatar.avatar_url,
                    'created_at': existing_avatar.created_at.isoformat(),
                    'updated_at': existing_avatar.updated_at.isoformat()
                }
            })
        else:
            # 创建新分身
            avatar = DigitalAvatar()
            avatar.user_id = user_id
            avatar.name = name
            avatar.description = description
            avatar.avatar_url = avatar_url
            avatar.created_at = datetime.now()
            avatar.updated_at = datetime.now()
            
            insert_digital_avatar(avatar)
            
            return make_succ_response({
                'ok': True,
                'message': '分身创建成功',
                'avatar': {
                    'id': avatar.id,
                    'user_id': avatar.user_id,
                    'name': avatar.name,
                    'description': avatar.description,
                    'avatar_url': avatar.avatar_url,
                    'created_at': avatar.created_at.isoformat(),
                    'updated_at': avatar.updated_at.isoformat()
                }
            })
        
    except Exception as e:
        return make_err_response(f'创建分身失败: {str(e)}')

