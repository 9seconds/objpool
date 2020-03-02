# vim: set et sw=4 ts=4:


class ObjectPoolError(Exception):
    """A base error for this module."""


class ObjectPoolFullError(ObjectPoolError, ValueError):
    """An error which should be raised if we try to release an
    element for full pool."""


class ObjectPoolEmptyError(ObjectPoolError, IndexError):
    """An error which means that object pool is empty."""
