from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sock import Sock
import os, threading, logging

db = SQLAlchemy()
sock = Sock()

def create_app():

    app = Flask(__name__)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app.config.setdefault('SQLALCHEMY_DATABASE_URI',
                          os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///data.db'))
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    db.init_app(app)
    sock.init_app(app)

    from .views.api import register_api_routes
    from .views.websocket import register_websocket_routes, get_event_queue
    from .views.user_views import user_bp
    from .views.test_views import test_bp
    from .agent.scheduler import start_dispatch

    register_api_routes(app)
    register_websocket_routes(app, sock)
    app.register_blueprint(user_bp)
    app.register_blueprint(test_bp)

    # 自动创建数据库表
    with app.app_context():
        from .dbops import model  # 导入所有模型
        db.create_all()

    # 在应用上下文里启动后台线程（关键！）
    def _run_dispatch_in_ctx(q, stop_event):
        with app.app_context():
            start_dispatch(q, stop_event)

    app.dispatcher_stop = threading.Event()
    threading.Thread(
        target=_run_dispatch_in_ctx,
        args=(get_event_queue(), app.dispatcher_stop),
        daemon=True
    ).start()

    return app
