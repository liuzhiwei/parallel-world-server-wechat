from flask import Flask
from flask_sock import Sock
import json

app = Flask(__name__)
sock = Sock(app)

@app.route("/ping")
def ping():
    return "pong"

@sock.route("/ws/stream")
def ws_stream(ws):
    ws.send(json.dumps({"message": "WebSocket连接成功"}))
    for msg in ["你好", "我是你的旅行分身", "很高兴为你规划旅行！"]:
        ws.send(json.dumps({"message": msg}))
