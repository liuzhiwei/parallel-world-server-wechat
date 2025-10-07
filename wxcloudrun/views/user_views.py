from datetime import datetime
import os
import uuid
import logging
import json
from flask import request, Blueprint, Response
from werkzeug.utils import secure_filename
from ..dbops.dao import insert_digital_avatar, insert_travel_partner, insert_travel_settings, ensure_user_exists, insert_chat_session
from ..dbops.model import DigitalAvatar, TravelPartner, TravelSettings, ChatSession
from ..wechat_config import WeChatCloudConfig
from ..idgeneration import id_gen

# 初始化日志
logger = logging.getLogger('log')

# 创建蓝图
user_bp = Blueprint('user', __name__, url_prefix='/api')

def make_succ_empty_response():
    data = json.dumps({'code': 0, 'data': {}})
    return Response(data, mimetype='application/json')


def make_succ_response(data):
    data = json.dumps({'code': 0, 'data': data})
    return Response(data, mimetype='application/json')


def make_err_response(err_msg):
    data = json.dumps({'code': -1, 'errorMsg': err_msg})
    return Response(data, mimetype='application/json')


@user_bp.route('/user', methods=['POST'])
def create_user():
    """
    创建/更新用户记录
    :return: 创建结果
    """
    try:
        params = request.get_json()
        
        if not params or 'user_id' not in params:
            return make_err_response('缺少用户ID')
        
        user_id = params['user_id']
        
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 确保用户存在
        user = ensure_user_exists(user_id)
        
        return make_succ_response({
            'message': '用户记录创建成功',
            'user_id': user_id,
            'user_db_id': user.id
        })
        
    except Exception as e:
        logger.error(f"创建用户记录失败: {str(e)}")
        return make_err_response(f'创建用户记录失败: {str(e)}')


@user_bp.route('/save-all', methods=['POST'])
def save_all_data():
    """
    一次性保存所有数据（分身+伙伴+设置）
    :return: 保存结果
    """
    try:
        params = request.get_json()
        
        if not params:
            return make_err_response('请求体不能为空')
        
        # 必需参数检查
        required_fields = ['user_id', 'avatar', 'partner', 'settings']
        for field in required_fields:
            if field not in params:
                return make_err_response(f'缺少必需参数: {field}')
        
        user_id = params['user_id']
        avatar_data = params['avatar']
        partner_data = params['partner']
        settings_data = params['settings']
        
        # 验证用户ID
        if not user_id.strip():
            return make_err_response('用户ID不能为空')
        
        # 确保用户存在
        ensure_user_exists(user_id)
        time = datetime.now().isoformat(),

        # 保存分身信息
        avatar = DigitalAvatar(
            user_id=user_id,
            avatar_id=id_gen.new_name_id(avatar_data['name']),
            name=avatar_data['name'],
            description=avatar_data['description'],
            avatar_url=avatar_data['avatar_url'],
            created_at=time,
            updated_at=time
        )
        insert_digital_avatar(avatar)
        
        # 保存旅行伙伴信息
        partner = TravelPartner(
            user_id=user_id,
            partner_id=id_gen.new_name_id(partner_data['partner_name']),
            partner_name=partner_data['partner_name'],
            partner_description=partner_data['partner_description'],
            partner_avatar_url=partner_data['partner_avatar_url'],
            created_at=time,
            updated_at=time
        )
        insert_travel_partner(partner)
        
        # 保存旅行设置信息
        settings = TravelSettings(
            user_id=user_id,
            destination=settings_data['destination'],
            days=settings_data['days'],
            preference=settings_data['preference'],
            created_at=time,
            updated_at=time
        )
        insert_travel_settings(settings)
        
        return make_succ_response({
            'message': '所有数据保存成功',
            'data': {
                'avatar_id': avatar.id,
                'partner_id': partner.id,
                'settings_id': settings.id
            }
        })
        
    except Exception as e:
        logger.error(f'保存所有数据失败: {str(e)}')
        return make_err_response(f'保存所有数据失败: {str(e)}')


@user_bp.route('/upload', methods=['POST'])
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


@user_bp.route('/create-session', methods=['POST'])
def create_session():
    """创建新的聊天会话"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return make_err_response('user_id is required')
        
        # 生成新的session_id
        session_id = id_gen.new_session_id()

        # 创建session记录
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            created_at=datetime.now().isoformat()
        )
        
        # 插入数据库
        insert_chat_session(session)
        
        return make_succ_response({
            'session_id': session_id,
            'created_at': session.created_at.isoformat()
        })
        
    except Exception as e:
        return make_err_response(f'创建会话失败: {str(e)}')

# 移除与 WebSocket 直连相关的辅助接口（已改为队列驱动）

