import threading, time, logging
from typing import Any, Hashable, Optional, Dict, Tuple

logger = logging.getLogger(__name__)


class WsRegistry:
    """
    线程安全地维护 (user_id -> ws)。
    - upsert: 新连接替换旧连接，并可选关闭旧 ws
    - get:    通过 user_id 取当前 ws
    - remove: 删除（可带 ws 身份校验）
    """
    def __init__(self, close_old_ws: bool = True):
        self._lock = threading.Lock()
        self._map: Dict[Hashable, Tuple[Any, float, int]] = {}
        # value: (ws, updated_at, version)
        self._close_old_ws = close_old_ws

    def upsert(self, user: Hashable, ws: Any) -> int:
        """设置/替换用户连接，返回新的 version（递增）"""
        old_ws = None
        with self._lock:
            if user in self._map:
                old_ws, _, ver = self._map[user]
                ver += 1
            else:
                ver = 1
            self._map[user] = (ws, time.time(), ver)
        if self._close_old_ws and old_ws and old_ws is not ws:
            try:
                old_ws.close()
            except Exception as e:
                logger.warning(f"关闭旧WebSocket连接失败 (user={user}): {e}")
        return ver

    def get(self, user: Hashable) -> Optional[Any]:
        with self._lock:
            tup = self._map.get(user)
            return tup[0] if tup else None

    def get_info(self, user: Hashable) -> Optional[Tuple[Any, float, int]]:
        """需要时间戳/版本时使用"""
        with self._lock:
            return self._map.get(user)

    def remove(self, user: Hashable) -> None:
        """删除用户的所有WebSocket连接，并关闭连接"""
        ws_to_close = None
        with self._lock:
            tup = self._map.pop(user, None)
            if tup:
                ws_to_close = tup[0]  # 提取 ws
        
        # 在锁外关闭 WebSocket，避免阻塞
        if ws_to_close:
            try:
                ws_to_close.close()
            except Exception as e:
                logger.warning(f"关闭WebSocket连接失败 (user={user}): {e}")

    def snapshot(self) -> Dict[Hashable, Any]:
        """返回 {user: ws} 的浅拷贝（仅用于观察/调试/UI）"""
        with self._lock:
            return {u: info[0] for u, info in self._map.items()}

    def __len__(self) -> int:
        with self._lock:
            return len(self._map)