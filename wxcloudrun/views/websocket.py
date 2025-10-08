from flask_sock import Sock
import json, logging, time, threading
from flask import current_app

logger = logging.getLogger(__name__)


def _close_ws_safely(ws):
    try:
        ws.close()
    except Exception:
        pass

def register_websocket_routes(app, sock):
    """注册WebSocket路由"""
    
    @sock.route("/ws/chat")
    def ws_chat(ws):
        logger.info(f"[WS] client connected")
        user_id = ""
        
        # 1) 首包握手（带 user_id）
        try:
            client_data = ws.receive()
            data = json.loads(client_data or "{}")
            user_id = str(data.get("user_id", "")).strip()
            if not user_id:
                raise ValueError("empty user_id")

            # 存储可用的 ws，由业务线程决定如何处理（含替换逻辑）
            user_socket_registry = current_app.extensions["user_socket_registry"]
            user_socket_registry.upsert(user_id, ws)
            logger.info(f"[WS] saved published for user={user_id}")
        except Exception as e:
            logger.error(f"[WS] handshake failed: {e}")
            _close_ws_safely(ws)
            return

        # 2) 轻量接收线程：处理心跳/指令（不阻塞主线程）
        stop_flag = {"stop": False}

        def recv_loop():
            while not stop_flag["stop"]:
                try:
                    # 客户端可每 20~30s 发一条 {"type":"ping"}
                    msg = ws.receive(timeout=35)  # 超时就继续，以便检测替换/关闭
                    if not msg:
                        continue
                    obj = json.loads(msg)
                    typ = obj.get("type")
                    if typ == "ping":
                        # 立刻回 pong
                        ws.send(json.dumps({"type": "pong"}))
                    elif typ == "stop":
                        # 客户端要求停止
                        break
                    elif typ == "input":
                        # 你的业务指令，在这里处理
                        pass
                except Exception:
                    # 超时/对端断开/网络异常都会到这里 -> 退出接收线程
                    break

        threading.Thread(target=recv_loop, daemon=True).start()

        # 3) 驻留主循环：保持路由活着；轻量保活
        try:
            while True:
                time.sleep(30)  # 低频休眠即可，完全不忙等
                # 如需：也可检测底层状态（某些实现有 .closed）
                # if getattr(ws, "closed", False): break
        except Exception as e:
            logger.error(f"[WS] hold-loop error: {e}")
        finally:
            stop_flag["stop"] = True
            # 通知业务线程移除此 ws
            if user_id:
                user_socket_registry = current_app.extensions["user_socket_registry"]
                user_socket_registry.remove(user_id, ws)
            logger.info(f"[WS] client disconnected user_id={user_id}")
