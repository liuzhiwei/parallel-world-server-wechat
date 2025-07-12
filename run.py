# 创建应用实例
import sys

from wxcloudrun import app, socketio

# 启动Flask Web服务
if __name__ == '__main__':
    socketio.run(app, 
                 host=sys.argv[1], 
                 port=int(sys.argv[2]), 
                 debug=True)