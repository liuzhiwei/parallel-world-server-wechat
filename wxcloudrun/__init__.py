from flask import Flask
from flask_sock import Sock
import json, logging

app = Flask(__name__)
sock = Sock(app)
logger = logging.getLogger("log")

@app.get("/ping")
def ping():
    return "pong"

@sock.route("/ws/stream")
def ws_stream(ws):
    logger.info("[WS] client connected")
    ws.send(json.dumps({"type": "connection", "message": "WebSocket连接成功"}, ensure_ascii=False))
    for msg in ["你好", "我是你的旅行分身", "很高兴为你规划旅行！"]:
        ws.send(json.dumps({"type": "message", "message": msg}, ensure_ascii=False))
