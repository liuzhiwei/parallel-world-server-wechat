from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 输出到控制台
        logging.FileHandler('app.log')      # 输出到文件
    ]
)

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)

# 微信云托管静态文件配置
import os
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保上传目录存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 设定数据库链接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/flask_demo'.format(config.username, 
                                                                             config.password,
                                                                             config.db_address)

# 禁用SQLAlchemy修改跟踪（减少开销）
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 数据库连接池配置
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,  # 1小时回收连接
    'pool_pre_ping': True,  # 连接前检查
    'pool_timeout': 30,
    'max_overflow': 20,
    'connect_args': {
        'charset': 'utf8mb4',
        'autocommit': True,
        'connect_timeout': 30,
        'read_timeout': 30,
        'write_timeout': 30
    }
}

# 初始化DB操作对象
db = SQLAlchemy(app)

# 加载控制器
from wxcloudrun import views
from wxcloudrun import websocket_handlers

# 确保React蓝图被注册
try:
    from wxcloudrun.views.chat_views_react import react_chat_bp
    app.register_blueprint(react_chat_bp)
    print("React蓝图注册成功")
except Exception as e:
    print(f"React蓝图注册失败: {e}")

# 加载配置
app.config.from_object('config')

# 微信云托管静态文件路由
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    from flask import send_from_directory, abort
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        abort(404)
