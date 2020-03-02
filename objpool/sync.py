# vim: set et sw=4 ts=4:

import collections
import threading
import typing as t

from objpool import exceptions
from objpool import types


class ObjectPool(t.Generic[types.Element]):
    _pool: t.Deque[types.Element]
    _maker: t.Callable[[t.Any], types.Element]

    def __init__(self, maker: types.SyncElementMaker[types.Element]) -> None:
        self._pool = collections.deque()
        self._maker = maker  # type: ignore[assignment]

    def __len__(self) -> int:
        return len(self._pool)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}(size={len(self)})>"

    __repr__ = __str__

    def release(self, item: types.Element) -> None:
        self._pool.append(item)

    def get(self, timeout: types.Timeout = 0) -> types.Element:
        if timeout < 0:
            raise ValueError(f"Incorrect timeout value {timeout}")

        try:
            return self._pool.popleft()
        except IndexError:
            return self._maker()


class LimitedObjectPool(ObjectPool[types.Element]):
    _maxsize: int
    _created: int
    _cond: threading.Condition

    def __init__(self, maker: types.SyncElementMaker, maxsize: int) -> None:
        if maxsize < 1:
            raise ValueError("Maxsize has to be >= 0")

        super().__init__(maker)
        self._maxsize = maxsize
        self._created = 0
        self._cond = threading.Condition()

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}(size={len(self)}, maxsize={self._maxsize})>"

    def release(self, item: types.Element) -> None:
        with self._cond:
            if len(self) == self._maxsize:
                raise exceptions.ObjectPoolFullError()
            self._pool.append(item)
            self._cond.notify()

    def get(self, timeout: types.Timeout = 0) -> types.Element:
        if timeout < 0:
            raise ValueError(f"Incorrect timeout value {timeout}")

        with self._cond:
            if len(self) > 0:
                return self._pool.popleft()
            if self._created < self._maxsize:
                value = self._maker()
                self._created += 1
                return value
            if timeout > 0 and self._cond.wait(timeout):
                return self._pool.popleft()
            raise exceptions.ObjectPoolEmptyError()
