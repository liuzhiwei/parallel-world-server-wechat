from flask import Flask
from flask_sock import Sock
import threading

app = Flask(__name__)
sock = Sock(app)

# 导入并注册路由
from .views.api import register_api_routes
from .views.websocket import register_websocket_routes
from .views.user_views import user_bp
from .views.websocket import get_event_queue
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
