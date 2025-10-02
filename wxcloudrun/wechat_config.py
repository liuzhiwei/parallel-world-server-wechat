"""
微信云托管专用配置
"""
import os

class WeChatCloudConfig:
    """微信云托管配置类"""
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 微信云托管环境变量
    WX_CLOUD_ENV = os.getenv('WX_CLOUD_ENV', 'development')
    
    # 静态文件配置
    STATIC_URL_PATH = '/uploads'
    
    @staticmethod
    def get_upload_path():
        """获取上传路径"""
        if WeChatCloudConfig.WX_CLOUD_ENV == 'production':
            # 生产环境使用云存储
            return '7072-prod-6ggpgoum0c8c2ffd-1365416418user-avatar'
        else:
            # 开发环境使用本地存储
            return 'uploads'
    
    @staticmethod
    def get_file_url(filename):
        """获取文件访问URL"""
        return f"/uploads/{filename}"
    
    @staticmethod
    def is_allowed_file(filename):
        """检查文件类型是否允许"""
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in WeChatCloudConfig.ALLOWED_EXTENSIONS)
