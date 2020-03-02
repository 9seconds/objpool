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

    def __init__(
        self,
        maker: t.Union[
            types.SyncElementMaker[types.Element],
            types.AsyncElementMaker[types.Element],
        ],
    ) -> None:
        self._pool = collections.deque()
        if not asyncio.iscoroutinefunction(maker):
            self._maker = t.cast(  # type: ignore[assignment]
                t.Callable[[], t.Awaitable[types.Element]],
                async_decorator(maker),
            )
        else:
            self._maker = maker  # type: ignore[assignment]

    def __len__(self) -> int:
        return len(self._pool)

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}(size={len(self)})>"

    async def release(self, item: types.Element) -> None:
        self._pool.append(item)

    async def get(self) -> types.Element:
        try:
            return self._pool.popleft()
        except IndexError:
            return await self._maker()


class LimitedObjectPool(ObjectPool[types.Element]):
    _maxsize: int
    _created: int
    _cond: asyncio.Condition

    def __init__(
        self,
        maker: t.Union[
            types.SyncElementMaker[types.Element],
            types.AsyncElementMaker[types.Element],
        ],
        maxsize: int,
    ) -> None:
        if maxsize < 1:
            raise ValueError("Maxsize has to be >= 0")

        super().__init__(maker)
        self._maxsize = maxsize
        self._created = 0
        self._cond = asyncio.Condition()

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
            if self._created < self._maxsize:
                value = await self._maker()
                self._created += 1
                return value
            await self._cond.wait()
            return self._pool.popleft()
