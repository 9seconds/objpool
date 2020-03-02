# vim: set et sw=4 ts=4:

import asyncio
import collections
import functools
import typing as t

from objpool import exceptions
from objpool import types


def async_decorator(func):
    @functools.wraps(func)
    async def decorator(self):
        return func()

    return decorator


class ObjectPool(t.Generic[types.Element]):
    _pool: t.Deque[types.Element]
    _maker: t.Callable[[t.Any], t.Awaitable[types.Element]]
    _maxsize: t.Optional[int]
    _created: int
    _cond: asyncio.Condition

    def __init__(
        self,
        maker: t.Union[
            types.SyncElementMaker[types.Element],
            types.AsyncElementMaker[types.Element],
        ],
        maxsize: t.Optional[int] = None,
    ) -> None:
        if maxsize is not None and maxsize < 1:
            raise ValueError("If maxsize is defined, it has to be >= 1")

        self._pool = collections.deque()
        if not asyncio.iscoroutinefunction(maker):
            self._maker = t.cast(  # type: ignore[assignment]
                t.Callable[[], t.Awaitable[types.Element]],
                async_decorator(maker),
            )
        else:
            self._maker = maker  # type: ignore[assignment]
        self._maxsize = maxsize
        self._created = 0
        self._cond = asyncio.Condition()

    def __len__(self) -> int:
        return len(self._pool)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}(size={len(self)}, maxsize={self._maxsize})>"

    async def release(self, item: types.Element) -> None:
        async with self._cond:
            if len(self) == self._maxsize:
                raise exceptions.ObjectPoolFullError()
            self._pool.append(item)
            self._cond.notify()

    async def get(self) -> types.Element:
        async with self._cond:
            if len(self) > 0:
                return self._pool.popleft()
            if self._maxsize is not None and self._created < self._maxsize:
                value = await self._maker()
                self._created += 1
                return value
            await self._cond.wait()
            return self._pool.popleft()
