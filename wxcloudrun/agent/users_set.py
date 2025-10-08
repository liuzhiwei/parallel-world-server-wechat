import threading
from collections import OrderedDict
from typing import Hashable, Optional, List, Tuple

class RoundRobinSet:
    """线程安全：可增删用户，空时阻塞等待，公平轮询；每个用户仅一个 session_id"""
    def __init__(self):
        self._cv = threading.Condition()
        self._users: "OrderedDict[Hashable, Hashable]" = OrderedDict()  # {user_id: session_id}

    def add(self, user: Hashable, session_id: Hashable) -> None:
        """加入/更新用户的 session；若此前为空，会唤醒一个等待者"""
        with self._cv:
            was_empty = not self._users
            # 更新该用户的 session_id，并把它刷到队尾
            self._users[user] = session_id
            self._users.move_to_end(user, last=True)
            if was_empty:
                self._cv.notify()  # 空->非空 时叫醒一个等待者

    def remove(self, user: Hashable) -> None:
        """删除用户（及其唯一 session）；不存在则忽略"""
        with self._cv:
            self._users.pop(user, None)

    def clear(self) -> None:
        """清空集合"""
        with self._cv:
            self._users.clear()

    def next(self, timeout: Optional[float] = None) -> Optional[Tuple[Hashable, Hashable]]:
        """
        轮询返回 (user_id, session_id)；
        若当前为空则阻塞直至有用户或超时；返回后把该用户放回队尾；超时返回 None。
        """
        with self._cv:
            ok = self._cv.wait_for(lambda: bool(self._users), timeout=timeout)
            if not ok:
                return None
            user, session_id = self._users.popitem(last=False)  # 取队头
            self._users[user] = session_id                      # 放回队尾
            return user, session_id

    # === 查看与统计 ===
    def get_all(self) -> List[Hashable]:
        """返回当前用户列表快照"""
        with self._cv:
            return list(self._users.keys())

    def get_session(self, user: Hashable) -> Optional[Hashable]:
        """获取某用户当前的 session_id"""
        with self._cv:
            return self._users.get(user)

    def count(self) -> int:
        with self._cv:
            return len(self._users)

    def __len__(self) -> int:
        with self._cv:
            return len(self._users)
