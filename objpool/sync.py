# vim: set et sw=4 ts=4:

import collections
import contextlib
import threading
import typing as t

from objpool import exceptions
from objpool import types


class ObjectPool(t.Generic[types.Element]):
    _pool: t.Deque[types.Element]
    _maker: t.Callable[[t.Any], types.Element]
    _maxsize: t.Optional[int]
    _created: int
    _cond: threading.Condition

    def __init__(
        self,
        maker: types.SyncElementMaker[types.Element],
        maxsize: t.Optional[int] = None,
    ) -> None:
        if maxsize is not None and maxsize < 1:
            raise ValueError("If maxsize is defined, it has to be >= 1")

        self._pool = collections.deque()
        self._maker = maker  # type: ignore[assignment]
        self._maxsize = maxsize
        self._created = 0
        self._cond = threading.Condition()

    def __len__(self) -> int:
        return len(self._pool)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}(size={len(self)}, maxsize={self._maxsize})>"

    __repr__ = __str__

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
            if self._maxsize is not None and self._created < self._maxsize:
                value = self._maker()
                self._created += 1
                return value
            if timeout == 0 or not self._cond.wait(timeout):
                raise exceptions.ObjectPoolEmptyError()
            return self._pool.popleft()

    @contextlib.contextmanager
    def acquired(
        self, timeout: types.Timeout = 0
    ) -> t.Iterator[types.Element]:
        item = self.get(timeout)
        try:
            yield item
        finally:
            self.release(item)
