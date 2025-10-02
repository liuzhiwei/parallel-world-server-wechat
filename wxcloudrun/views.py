from datetime import datetime
import os
import uuid
from flask import render_template, request
from werkzeug.utils import secure_filename
from run import app
from wxcloudrun.dao import insert_digital_avatar, get_digital_avatar_by_user_id, update_digital_avatar
from wxcloudrun.model import DigitalAvatar
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.wechat_config import WeChatCloudConfig


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/init-db', methods=['POST'])
def init_database():
    """
    初始化数据库表
    :return: 初始化结果
    """
    try:
        from wxcloudrun import db
        db.create_all()
        return make_succ_response({'message': '数据库表创建成功'})
    except Exception as e:
        return make_err_response(f'数据库初始化失败: {str(e)}')


@app.route('/api/upload', methods=['POST'])
def upload_avatar():
    """
    头像上传接口
    :return: 上传后的文件URL
    """
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return make_err_response('没有上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return make_err_response('没有选择文件')
        
        # 检查文件类型
        if not WeChatCloudConfig.is_allowed_file(file.filename):
            return make_err_response('不支持的文件格式，请上传图片文件')
        
        # 检查上传类型
        upload_type = request.form.get('type', '')
        if upload_type != 'avatar':
            return make_err_response('上传类型错误')
        
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # 创建上传目录（微信云托管环境）
        upload_folder = os.path.join(WeChatCloudConfig.get_upload_path(), 'avatars')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # 生成访问URL（微信云托管格式）
        avatar_url = WeChatCloudConfig.get_file_url(f"avatars/{unique_filename}")
        
        return make_succ_response({'url': avatar_url})
        
    except Exception as e:
        return make_err_response(f'文件上传失败: {str(e)}')






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
