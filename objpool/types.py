# vim: set et sw=4 ts=4:

import typing as t


Element = t.TypeVar("Element")
SyncElementMaker = t.Callable[[], Element]
AsyncElementMaker = t.Callable[[], t.Awaitable[Element]]
Timeout = t.Union[int, float]
