import threading, time
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
            
            # 防御性代码：检查数据格式
            try:
                if len(cur) == 3:
                    cur_ws, _, _ = cur
                elif len(cur) == 2:
                    cur_ws, _ = cur
                else:
                    # 数据格式异常，直接删除
                    self._map.pop(user, None)
                    return
            except (ValueError, TypeError):
                # 解包失败，直接删除
                self._map.pop(user, None)
                return
                
            if (ws is None) or (ws is cur_ws):
                self._map.pop(user, None)
                # 由调用方决定是否 close(ws)

    def snapshot(self) -> Dict[Hashable, Any]:
        """返回 {user: ws} 的浅拷贝（仅用于观察/调试/UI）"""
        with self._lock:
            return {u: info[0] for u, info in self._map.items()}

    def __len__(self) -> int:
        with self._lock:
            return len(self._map)