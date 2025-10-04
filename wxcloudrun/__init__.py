from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
import logging
import sys
import json
import os



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

# 确保React蓝图被注册
try:
    from wxcloudrun.views.chat_views_react import react_chat_bp
    app.register_blueprint(react_chat_bp)
    print("React蓝图注册成功")
except Exception as e:
    print(f"React蓝图注册失败: {e}")

# 加载配置
app.config.from_object('config')

# 初始化 WebSocket
from flask_sock import Sock
sock = Sock(app)

# 确保 logger 可用
logger = logging.getLogger('log')

@sock.route("/ws/stream")
def stream(ws):
    logger.info("[WEBSOCKET] 客户端连接开始")
    ws.send(json.dumps({"type": "connection", "data": {"message": "WebSocket连接成功"}}, ensure_ascii=False))

    messages = [
        {"type": "message", "data": {"message": "你好！", "name": "旅行分身"}},
        {"type": "message", "data": {"message": "我是你的旅行分身", "name": "旅行分身"}},
        {"type": "message", "data": {"message": "很高兴为你规划这次旅行！", "name": "旅行分身"}},
        {"type": "complete", "data": {"total_messages": 3}}
    ]
    for msg in messages:
        ws.send(json.dumps(msg, ensure_ascii=False))

# 添加简单的健康检查
@app.route('/ping')
def ping():
    return "pong"

# 添加WebSocket测试接口
@app.route('/test/websocket')
def test_websocket():
    logger.info("[TEST] WebSocket测试接口被调用")
    return {"status": "ok", "message": "WebSocket服务正常", "websocket_route": "/ws/stream"}

# 微信云托管静态文件路由
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    from flask import send_from_directory, abort
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        abort(404)
