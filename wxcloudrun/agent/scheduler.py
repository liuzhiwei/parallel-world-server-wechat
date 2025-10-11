import json
import logging
from typing import Any
from flask import current_app


logger = logging.getLogger(__name__)


def start_dispatch(stop_event: Any) -> None:
    """Consume events from the global WebSocket queue and dispatch work.

    Simplified dispatcher: ignores event type entirely.
    For any dict event containing a "user_id", it will:
      1) call DialogueController.step(user_id)
      2) if a "ws" is present on the event, send the reply to that ws
    """
    from .dialogue_controller import DialogueController

    controller = DialogueController()

    while not getattr(stop_event, "is_set", lambda: False)():
        # 获取轮询队列
        alive_chat_users = current_app.extensions["alive_chat_users"]
        user_id, ws = alive_chat_users.next()   # 空则阻塞
        if not user_id or not ws:
            logger.warning("[DISPATCH] event without user_id: %s, ws: %s", user_id, ws)
            continue

        # 生成回复
        try:
            reply = controller.step(user_id)
        except Exception as e:
            logger.error("[DISPATCH] error generating reply for user %s: %s", user_id, e)
            # 生成回复失败时移除用户，避免无限重试
            alive_chat_users.remove(user_id)
            continue

        # 发送回复
        if reply is not None:
            try:
                ws.send(json.dumps(reply, ensure_ascii=False))
            except Exception as send_err:
                logger.error("[DISPATCH] send failed for user %s: %s", user_id, send_err)
                # 移除失效的连接，等待前端重连
                alive_chat_users.remove(user_id)
