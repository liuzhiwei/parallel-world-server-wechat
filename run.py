# 创建应用实例
import sys
from wxcloudrun import app

# 确保所有视图模块被导入
import wxcloudrun.views

# 启动Flask Web服务
if __name__ == '__main__':
    app.run(host=sys.argv[1], port=sys.argv[2])