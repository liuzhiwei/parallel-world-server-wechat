import requests
import logging
from flask import Blueprint, request, jsonify
from ..wechat_config import WECHAT_CONFIG
from ..dbops.dao import ensure_user_exists

logger = logging.getLogger(__name__)

# 创建微信相关的蓝图
wechat_bp = Blueprint('wechat', __name__, url_prefix='/api')

def make_succ_response(data=None):
    """成功响应"""
    return jsonify({
        'code': 0,
        'message': 'success',
        'data': data
    })

def make_err_response(message, code=-1):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': None
    })

@wechat_bp.route('/wechat-login', methods=['POST'])
def wechat_login():
    """微信登录，通过code获取openid"""
    try:
        data = request.get_json()
        code = data.get('code')
        
        if not code:
            return make_err_response('缺少code参数')
        
        # 调用微信接口获取openid
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': WECHAT_CONFIG['app_id'],
            'secret': WECHAT_CONFIG['app_secret'],
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
        except requests.exceptions.SSLError as e:
            logger.warning(f'SSL证书验证失败，尝试不验证证书: {e}')
            # 备用方案：不验证SSL证书
            response = requests.get(url, params=params, verify=False)
            result = response.json()
        
        if 'openid' in result:
            openid = result['openid']
            logger.info(f'微信登录成功，openid: {openid}')
            
            # 直接创建用户记录
            try:
                user = ensure_user_exists(openid)
                logger.info(f'用户记录创建成功，user_id: {openid}, db_id: {user.id}')
            except Exception as e:
                logger.error(f'创建用户记录失败: {e}')
                return make_err_response(f'创建用户记录失败: {str(e)}')
            
            return make_succ_response({
                'openid': openid
            })
        else:
            logger.error(f'微信登录失败: {result}')
            return make_err_response(f'微信登录失败: {result.get("errmsg", "未知错误")}')
            
    except Exception as e:
        logger.error(f'微信登录异常: {e}')
        return make_err_response(f'登录异常: {str(e)}')

@wechat_bp.route('/get-user-info', methods=['POST'])
def get_user_info():
    """获取用户信息（需要用户授权）"""
    try:
        data = request.get_json()
        encrypted_data = data.get('encryptedData')
        iv = data.get('iv')
        session_key = data.get('sessionKey')
        
        if not all([encrypted_data, iv, session_key]):
            return make_err_response('缺少必要参数')
        
        # 这里需要实现解密逻辑
        # 由于微信小程序用户信息获取需要解密，这里先返回基本信息
        logger.info('获取用户信息请求')
        
        return make_succ_response({
            'message': '用户信息获取功能待实现'
        })
        
    except Exception as e:
        logger.error(f'获取用户信息异常: {e}')
        return make_err_response(f'获取用户信息异常: {str(e)}')
