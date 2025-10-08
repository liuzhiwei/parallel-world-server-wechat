from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sock import Sock
import os, threading, logging
import pymysql

db = SQLAlchemy()
sock = Sock()

def create_app():

    # 1) 使用 instance_relative_config，启用实例目录（/app/instance）
    #    便于把 data.db 放到实例目录，且可加载实例级 config.py
    app = Flask(__name__, instance_relative_config=True)
    
    # 2) 日志：同时输出到控制台与文件（app.log）
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 3) 数据库
    # 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
    pymysql.install_as_MySQLdb()
    # 读取数据库环境变量
    db_username = os.environ.get("MYSQL_USERNAME", 'root')
    db_password = os.environ.get("MYSQL_PASSWORD", 'root')
    db_address = os.environ.get("MYSQL_ADDRESS", '127.0.0.1:3306')
    # 设定数据库链接
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_username}:{db_password}@{db_address}/flask_demo?charset=utf8mb4'
    # 禁用SQLAlchemy修改跟踪（减少开销）
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 4) 初始化扩展
    db.init_app(app)
    sock.init_app(app)

    # 5) 路由与蓝图
    from .views.api import register_api_routes
    from .views.websocket import register_websocket_routes, get_event_queue
    from .views.user_views import user_bp
    from .views.test_views import test_bp
    from .agent.scheduler import start_dispatch

    register_api_routes(app)
    register_websocket_routes(app, sock)
    app.register_blueprint(user_bp)
    app.register_blueprint(test_bp)

    # 6)在应用上下文里启动后台线程（关键！）
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
