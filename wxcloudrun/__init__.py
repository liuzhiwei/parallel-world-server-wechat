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
    # 数据库连接池配置
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        # 小池子，避免容器+线程把连接占满
        'pool_size': 5,
        'max_overflow': 5,
        'pool_timeout': 10,
        # 关键：连接使用前先 ping；回收时间 < 服务端空闲超时
        'pool_pre_ping': True,
        'pool_recycle': 180,
        # 尽量别把 autocommit 打开，交给 SQLAlchemy 接管事务
        'connect_args': {
            'charset': 'utf8mb4',
            'connect_timeout': 5,
            'read_timeout': 15,
            'write_timeout': 15,
            # 'autocommit': True,   # ← 删除这行
        },
        # 连接归还时做回滚，避免脏状态回池
        'pool_reset_on_return': 'rollback',
    }

    # 4) 初始化扩展
    db.init_app(app)
    sock.init_app(app)

    # 4.1) 处理断连错误并重建连接池
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        """
        按 SQLAlchemy 推荐处理断连：
        1. 检测已知的断连错误码（2006/2013/2055等）
        2. 记录详细日志并 dispose() 连接池
        3. 其他错误正常抛出
        """
        import pymysql.err
        from sqlalchemy.exc import OperationalError, DBAPIError
        
        logger = logging.getLogger(__name__)
        
        try:
            db.session.remove()
        except (OperationalError, DBAPIError) as e:
            # 检查是否是已知的 MySQL 断连错误码
            orig_exc = getattr(e, 'orig', None)
            if isinstance(orig_exc, pymysql.err.OperationalError):
                errno = orig_exc.args[0] if orig_exc.args else None
                # MySQL 断连错误码：2006/2013/2055
                if errno in (2006, 2013, 2055):
                    logger.warning(
                        f"MySQL disconnect detected (errno={errno}) during teardown: {orig_exc.args[1] if len(orig_exc.args) > 1 else ''}"
                        f" - disposing connection pool"
                    )
                    # 丢弃整个连接池，下次请求会自动重建
                    db.engine.dispose()
                    return
            
            # 非断连错误，正常抛出
            logger.error(f"Unexpected error during session teardown: {e}", exc_info=True)
            raise

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
