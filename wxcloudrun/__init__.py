from flask import Flask
from flask_sock import Sock
from flask_sqlalchemy import SQLAlchemy
import os
import threading

app = Flask(__name__)

# 数据库配置（默认SQLite，可通过环境覆盖）
app.config.setdefault('SQLALCHEMY_DATABASE_URI', os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///data.db'))
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

# 初始化数据库与 WebSocket
db = SQLAlchemy(app)
sock = Sock(app)

# 延后导入，避免循环引用，确保 db 已定义
from .views.api import register_api_routes
from .views.websocket import register_websocket_routes, get_event_queue
from .views.user_views import user_bp
from .agent.scheduler import start_dispatch

# 注册所有路由
register_api_routes(app)
register_websocket_routes(app, sock)

# 注册用户相关蓝图
app.register_blueprint(user_bp)

# 启动全局调度线程，消费 WebSocket 事件
_dispatcher_stop = threading.Event()
threading.Thread(
    target=start_dispatch,
    args=(get_event_queue(), _dispatcher_stop),
    daemon=True
).start()
