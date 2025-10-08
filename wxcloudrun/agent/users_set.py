import threading
from collections import OrderedDict
from typing import Hashable, Optional, List

class RoundRobinSet:
    """线程安全：可增删用户，空时阻塞等待，公平轮询（不移除元素）"""
    def __init__(self):
        self._cv = threading.Condition()
        self._users = OrderedDict()   # {user_id: True}

    def add(self, user: Hashable) -> None:
        """加入用户；若此前为空，会唤醒一个等待者"""
        with self._cv:
            was_empty = not self._users
            if user not in self._users:
                self._users[user] = True
            else:
                # 已存在则刷新到队尾（可选）
                self._users.move_to_end(user, last=True)
            if was_empty:
                self._cv.notify()      # 空->非空 时叫醒一个等待者

    def remove(self, user: Hashable) -> None:
        """删除用户；不存在则忽略"""
        with self._cv:
            self._users.pop(user, None)

    def clear(self) -> None:
        """清空集合"""
        with self._cv:
            self._users.clear()

    def next(self, timeout: Optional[float] = None):
        """
        轮询返回下一位用户；若当前为空则阻塞直至有用户或超时。
        返回后会把该用户放回队尾；超时返回 None。
        """
        with self._cv:
            ok = self._cv.wait_for(lambda: bool(self._users), timeout=timeout)
            if not ok:
                return None
            user, _ = self._users.popitem(last=False)  # 取队头（最久未轮到）
            self._users[user] = True                   # 放回队尾
            return user

    # === 新增：查看与统计 ===
    def get_all(self) -> List[Hashable]:
        """返回当前集合用户的快照（列表拷贝）"""
        with self._cv:
            return list(self._users.keys())  # 拷贝，避免外部影响内部结构

    def count(self) -> int:
        """返回当前集合用户数量"""
        with self._cv:
            return len(self._users)

    def __len__(self) -> int:
        with self._cv:
            return len(self._users)
