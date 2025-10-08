# wxcloudrun/views/websocket.py
from flask_sock import Sock
import json, logging
from flask import current_app
from gevent import spawn, sleep

logger = logging.getLogger(__name__)

def _close_ws_safely(ws):
    try:
        ws.close()
    except Exception:
        pass

def register_websocket_routes(app, sock: Sock):
    """注册 WebSocket 路由"""

    @sock.route("/ws/chat")
    def ws_chat(ws):
        logger.info("[WS] client connected")
        user_id = ""

        # 1) 首包握手（客户端应立即发送 {"user_id": "..."}）
        try:
            client_data = ws.receive(timeout=15)  # Flask-Sock API 支持超时
            data = json.loads(client_data or "{}")
            user_id = str(data.get("user_id", "")).strip()
            if not user_id:
                raise ValueError("empty user_id")

            user_socket_registry = current_app.extensions["user_socket_registry"]
            user_socket_registry.upsert(user_id, ws)
            logger.info(f"[WS] saved published for user={user_id}")
        except Exception as e:
            logger.error(f"[WS] handshake failed: {e}")
            _close_ws_safely(ws)
            return

        # 2) 接收协程：处理心跳与业务指令
        running = {"v": True}

        def recv_loop():
            while running["v"] and not getattr(ws, "closed", False):
                try:
                    # 客户端建议每 20~30s 发 {"type":"ping"}
                    msg = ws.receive(timeout=35)  # 超时→继续轮询
                    if not msg:
                        continue
                    obj = json.loads(msg)
                    typ = obj.get("type")
                    if typ == "ping":
                        try:
                            ws.send(json.dumps({"type": "pong"}))
                        except Exception:
                            break
                    elif typ == "stop":
                        break
                    elif typ == "input":
                        # TODO: 这里接入你的业务
                        pass
                except Exception:
                    break

        g = spawn(recv_loop)

        # 3) 轻量保活循环（不要阻塞 CPU；sleep 可让出执行权）
        try:
            while not getattr(ws, "closed", False):
                # 需要的话，也可以服务端定期发送 ping
                # ws.send(json.dumps({"type": "ping"}))
                sleep(30)
        finally:
            running["v"] = False
            try: g.kill()
            except Exception: pass
            if user_id:
                try:
                    user_socket_registry = current_app.extensions["user_socket_registry"]
                    user_socket_registry.remove(user_id, ws)
                except Exception:
                    pass
            logger.info(f"[WS] client disconnected user_id={user_id}")
