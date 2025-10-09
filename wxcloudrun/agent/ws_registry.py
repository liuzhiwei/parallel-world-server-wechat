import threading
import logging
from typing import Hashable, Any, Optional

logger = logging.getLogger(__name__)

class WsRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._map: dict[Hashable, Any] = {}

    def add(self, user: Hashable, ws: Any) -> None:
        """设置/替换该 user 的当前活跃连接；若有旧连接，锁外关闭。"""
        old_ws: Optional[Any] = None
        with self._lock:
            old_ws = self._map.pop(user, None)
            self._map[user] = ws

        if old_ws and old_ws is not ws:
            try:
                old_ws.close()
            except Exception as e:
                # 检查是否是常见的连接关闭异常
                error_str = str(e).lower()
                if any(code in error_str for code in ['1005', '1006', 'connection closed', 'connection reset']):
                    logger.info(f"[WS] 旧连接已关闭 (user={user}): {e}")
                else:
                    logger.warning(f"[WS] close old failed (user={user}): {e}")

    def get(self, user: Hashable) -> Optional[Any]:
        with self._lock:
            return self._map.get(user)

    def remove(self, user: Hashable, ws: Optional[Any] = None) -> bool:
        """
        删除并关闭 user 的活跃连接。
        - ws 为 None：无条件删除该 user 的当前活跃连接（常用于 on_close 清理）
        - ws 非 None：仅当传入 ws 与当前活跃连接对象是同一个对象时才删除
        返回是否删除成功。
        """
        ws_to_close: Optional[Any] = None
        with self._lock:
            cur = self._map.get(user)
            if cur is None:
                logger.info(f"[WS] user {user} not found, skip remove")
                return False

            if ws is None or ws is cur:   # 注意用 `is` 比较对象身份
                self._map.pop(user, None)
                ws_to_close = cur
                logger.info(f"[WS] removed active ws (user={user})")
            else:
                logger.info(f"[WS] given ws is not active, skip (user={user})")
                return False

        if ws_to_close:
            try:
                ws_to_close.close()
            except Exception as e:
                # 检查是否是常见的连接关闭异常
                error_str = str(e).lower()
                if any(code in error_str for code in ['1005', '1006', 'connection closed', 'connection reset']):
                    logger.info(f"[WS] 连接已关闭 (user={user}): {e}")
                else:
                    logger.warning(f"[WS] close failed (user={user}): {e}")
        return True

    def snapshot(self) -> dict[Hashable, Any]:
        """返回 {user: ws} 的浅拷贝（仅用于观察/调试/UI）"""
        with self._lock:
            return self._map.copy()

    def __len__(self) -> int:
        with self._lock:
            return len(self._map)