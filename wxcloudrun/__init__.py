from flask import Flask
from flask_sock import Sock
import json, logging, uuid

app = Flask(__name__)
sock = Sock(app)
logger = logging.getLogger("log")

@app.get("/ping")
def ping():
    return "pong"

@sock.route("/ws/chat")
def ws_stream(ws):
    logger.info("[WS] client connected")
    
    # 发送连接确认消息
    connection_response = {
        "user_id": "",
        "session_id": "",
        "agent_info": {
            "agent_id": "travel_guide_ai",
            "agent_type": "ai",
            "agent_name": "旅行向导AI",
            "agent_photo_url": "/images/avatar.png"
        },
        "contents": [{
            "message_id": str(uuid.uuid4()),
            "type": "text",
            "mime": "text/plain; charset=utf-8",
            "text": "WebSocket连接成功！我是你的旅行向导AI，很高兴为你服务！",
            "lang": "zh-CN"
        }]
    }
    
    ws.send(json.dumps(connection_response, ensure_ascii=False))
    
    # 发送欢迎消息
    welcome_messages = [
        "你好！我是你的旅行分身",
        "很高兴为你规划旅行！",
        "请告诉我你想去哪里旅行？"
    ]
    
    for msg_text in welcome_messages:
        welcome_response = {
            "user_id": "",
            "session_id": "",
            "agent_info": {
                "agent_id": "travel_guide_ai",
                "agent_type": "ai",
                "agent_name": "旅行向导AI",
                "agent_photo_url": "/images/avatar.png"
            },
            "contents": [{
                "message_id": str(uuid.uuid4()),
                "type": "text",
                "mime": "text/plain; charset=utf-8",
                "text": msg_text,
                "lang": "zh-CN"
            }]
        }
        ws.send(json.dumps(welcome_response, ensure_ascii=False))
    
    # 单向通信：只推送消息，不监听客户端消息
    try:
        while True:
            # 这里可以添加定时推送或其他逻辑
            import time
            time.sleep(1)  # 保持连接活跃
    except Exception as e:
        logger.error(f"[WS] Connection error: {e}")
    
    logger.info("[WS] client disconnected")
