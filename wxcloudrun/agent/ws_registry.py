import threading
from typing import Any, Hashable, Optional, Dict, Tuple


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

    def upsert(self, user_id, ws):
        old_ws = None
        with self._lock:
            if user_id in self._map:
                old_ws, ver = self._map[user_id]
                ver += 1
            else:
                ver = 1
            self._map[user_id] = (ws, ver)
        # 锁外关闭旧连接（若与新不同）
        if old_ws is not None and old_ws is not ws:
            try:
                old_ws.close()   # 直接关闭即可
            except Exception:
                pass
        return ver

    def get(self, user: Hashable) -> Optional[Any]:
        with self._lock:
            tup = self._map.get(user)
            return tup[0] if tup else None

    def get_info(self, user: Hashable) -> Optional[Tuple[Any, float, int]]:
        """需要时间戳/版本时使用"""
        with self._lock:
            return self._map.get(user)

    def remove(self, user: Hashable, ws: Any = None) -> None:
        """若传 ws，则仅当注册表里还是这条 ws 时才删除（防止老连接误删新连接）"""
        with self._lock:
            cur = self._map.get(user)
            if not cur:
                return
            cur_ws, _, _ = cur
            if (ws is None) or (ws is cur_ws):
                self._map.pop(user, None)
                ws.close()

    def snapshot(self) -> Dict[Hashable, Any]:
        """返回 {user: ws} 的浅拷贝（仅用于观察/调试/UI）"""
        with self._lock:
            return {u: info[0] for u, info in self._map.items()}

    def __len__(self) -> int:
        with self._lock:
            return len(self._map)