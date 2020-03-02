# vim: set et sw=4 ts=4:

import typing as t

from objpool import aio
from objpool import sync
from objpool import types


def make_async(
    maker: t.Union[
        types.SyncElementMaker[types.Element],
        types.AsyncElementMaker[types.Element],
    ],
    size: t.Optional[int] = None,
) -> t.Union[
    aio.ObjectPool[types.Element], aio.LimitedObjectPool[types.Element]
]:
    if size is None:
        return aio.ObjectPool(maker)
    if size < 0:
        raise ValueError("Pool must have a size >= 0")
    return aio.LimitedObjectPool(maker, size)


def make_sync(
    maker: types.SyncElementMaker[types.Element], size: t.Optional[int] = None
) -> t.Union[
    sync.ObjectPool[types.Element], sync.LimitedObjectPool[types.Element]
]:
    if size is None:
        return sync.ObjectPool(maker)
    if size < 0:
        raise ValueError("Pool must have a size >= 0")
    return sync.LimitedObjectPool(maker, size)
