# wxcloudrun/__init__.py
import logging, os, threading
import pymysql
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_sock import Sock

# ---- 全局扩展（与原来一致）----
db = SQLAlchemy()
sock = Sock()

# 你的进程内结构保持不变（单 worker 即可）
from .agent.users_set import RoundRobinSet
from .agent.ws_registry import WsRegistry
alive_chat_users = RoundRobinSet()
user_socket_registry = WsRegistry()

def create_app():
    # 1) 实例化 Flask
    app = Flask(__name__, instance_relative_config=True)

    # 2) 日志（只设置一次全局级别/格式）
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    # 3) 数据库：用 PyMySQL 作为 MySQLdb
    pymysql.install_as_MySQLdb()

    db_username = os.environ.get("MYSQL_USERNAME", "root")
    db_password = os.environ.get("MYSQL_PASSWORD", "root")
    db_address  = os.environ.get("MYSQL_ADDRESS",  "127.0.0.1:3306")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+pymysql://{db_username}:{db_password}@{db_address}/flask_demo?charset=utf8mb4"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,
        "max_overflow": 5,
        "pool_timeout": 10,
        # 官方推荐：预 ping 处理断连
        "pool_pre_ping": True,                 # ← 关键点（官方文档推荐）
        "pool_recycle": 180,
        "connect_args": {
            "charset": "utf8mb4",
            "connect_timeout": 5,
            "read_timeout": 15,
            "write_timeout": 15,
        },
        "pool_reset_on_return": "rollback",
    }

    # 4) 初始化扩展
    db.init_app(app)
    sock.init_app(app)
    app.extensions["alive_chat_users"]     = alive_chat_users
    app.extensions["user_socket_registry"] = user_socket_registry

    # 4.1) teardown：断连时释放连接池；其他情况仅记录日志（不要再抛异常）
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """
        - MySQL 断连（2006/2013/2055）：记录并 dispose()，下次自动重建
        - 其他异常：记录日志但不在 teardown 再抛，避免影响 worker 稳定性
        """
        import pymysql.err
        from sqlalchemy.exc import OperationalError, DBAPIError

        try:
            db.session.remove()
        except (OperationalError, DBAPIError) as e:
            orig_exc = getattr(e, "orig", None)
            if isinstance(orig_exc, pymysql.err.OperationalError):
                errno = orig_exc.args[0] if orig_exc.args else None
                if errno in (2006, 2013, 2055):
                    logging.getLogger(__name__).warning(
                        f"MySQL disconnect (errno={errno}); disposing pool"
                    )
                    try:
                        db.engine.dispose()
                    except Exception:
                        pass
                    return
            # 其他错误：仅记录，避免 teardown 阶段再抛异常导致 worker 器械性中断
            logging.getLogger(__name__).error(
                f"Unexpected error during teardown: {e}", exc_info=True
            )

    # 5) 路由与蓝图
    from .views.api import register_api_routes
    from .views.websocket import register_websocket_routes
    from .views.user_views import user_bp
    from .views.test_views import test_bp
    from .agent.scheduler import start_dispatch

    register_api_routes(app)
    register_websocket_routes(app, sock)
    app.register_blueprint(user_bp)
    app.register_blueprint(test_bp)

    # 6) 后台调度线程（轻量任务 OK；重任务建议放到队列）
    # gevent 已在 run.py 里 monkey.patch_all()，这里的 threading 会被协作化
    def _run_dispatch_in_ctx(stop_event):
        with app.app_context():
            start_dispatch(stop_event)

    app.dispatcher_stop = threading.Event()
    threading.Thread(
        target=_run_dispatch_in_ctx,
        args=(app.dispatcher_stop,),
        daemon=True
    ).start()

    return app
