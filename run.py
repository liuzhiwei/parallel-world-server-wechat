# 创建应用实例
import sys
import logging
from wxcloudrun import app
from flask_sockets import Sockets

# 确保所有视图模块被导入
import wxcloudrun.views

# 初始化 WebSocket
sockets = Sockets(app)

# 配置日志
logger = logging.getLogger('log')

# 启动Flask WebSocket服务
if __name__ == '__main__':
    logger.info("========== Flask 简单WebSocket应用启动 ==========")
    logger.info(f"启动参数: host={sys.argv[1]}, port={sys.argv[2]}")
    
    # 打印所有注册的路由
    with app.app_context():
        logger.info("已注册的路由:")
        for rule in app.url_map.iter_rules():
            logger.info(f"  {rule.methods} {rule.rule}")
    
    # 使用 gevent 启动应用
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    server = pywsgi.WSGIServer((sys.argv[1], int(sys.argv[2])), app, handler_class=WebSocketHandler)
    logger.info("WebSocket服务器启动完成")
    server.serve_forever()