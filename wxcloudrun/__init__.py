from flask import Flask
from flask_sock import Sock
import json
import logging
import sys

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("log")

# Flask app
app = Flask(__name__)

# 初始化 Sock
sock = Sock(app)

@sock.route("/ws/stream")
def ws_stream(ws):
    logger.info("[WEBSOCKET] 客户端连接开始")
    ws.send(json.dumps({"type": "connection", "data": {"message": "WebSocket连接成功"}}))
    for msg in [
        {"type": "message", "data": {"message": "你好！", "name": "旅行分身"}},
        {"type": "message", "data": {"message": "我是你的旅行分身", "name": "旅行分身"}},
        {"type": "message", "data": {"message": "很高兴为你规划这次旅行！", "name": "旅行分身"}},
        {"type": "complete", "data": {"total_messages": 3}}
    ]:
        ws.send(json.dumps(msg, ensure_ascii=False))

@app.route("/ping")
def ping():
    return "pong"

@app.route("/hello")
def hello():
    return {"msg": "hello, world!"}
