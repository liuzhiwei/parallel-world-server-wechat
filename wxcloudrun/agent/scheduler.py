import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def start_dispatch(event_q: Any, stop_event: Any) -> None:
    """Consume events from the global WebSocket queue and dispatch work.

    Simplified dispatcher: ignores event type entirely.
    For any dict event containing a "user_id", it will:
      1) call DialogueController.step(user_id)
      2) if a "ws" is present on the event, send the reply to that ws
    """
    from .dialogue_controller import DialogueController
    from ..views.websocket import _close_ws_safely  # reuse safe close helper

    controller = DialogueController()

    while not getattr(stop_event, "is_set", lambda: False)():
        try:
            evt = event_q.get(timeout=1)
        except Exception:
            # idle wait; allow stop_event checks
            continue

        if not isinstance(evt, dict):
            # ignore non-dict events
            continue

        user_id = str(evt.get("user_id", "")).strip()
        if not user_id:
            logger.warning("[DISPATCH] event without user_id: %s", evt)
            continue

        try:
            reply = controller.step(user_id)
            ws = evt.get("ws")
            if ws and reply is not None:
                try:
                    ws.send(json.dumps(reply, ensure_ascii=False))
                except Exception as send_err:
                    logger.error("[DISPATCH] send failed: %s", send_err)
                    _close_ws_safely(ws)

        except Exception as e:
            logger.error("[DISPATCH] error handling event for user %s: %s", user_id, e)


