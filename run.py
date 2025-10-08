# run.py —— 入口尽早打猴子补丁
from gevent import monkey
monkey.patch_all()

from wxcloudrun import create_app

app = create_app()

if __name__ == "__main__":
    # 本地调试可用
    app.run(host="0.0.0.0", port=80, debug=True)
