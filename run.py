# 创建应用实例
import logging
from wxcloudrun import app

# 确保所有视图模块被导入
import wxcloudrun.views

# 配置日志
logger = logging.getLogger('log')

# 打印所有注册的路由
with app.app_context():
    logger.info("========== Flask WebSocket应用初始化 ==========")
    logger.info("已注册的路由:")
    for rule in app.url_map.iter_rules():
        logger.info(f"  {rule.methods} {rule.rule}")