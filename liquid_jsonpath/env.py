"""A JSONPath environment that uses Liquid `getitem` semantics."""
from operator import getitem
from typing import Any

from jsonpath import JSONPathEnvironment


class LiquidJSONPathEnvironment(JSONPathEnvironment):
    """A JSONPath environment that uses Liquid `getitem` semantics."""

    def getitem(self, obj: Any, key: Any) -> Any:
        """Sequence and mapping item getter."""
        if hasattr(key, "__liquid__"):
            key = key.__liquid__()
        return getitem(obj, key)

    async def getitem_async(self, obj: Any, key: object) -> Any:
        """Async sequence and mapping item getter."""

        async def _get_item(obj: Any, key: Any) -> object:
            if hasattr(obj, "__getitem_async__"):
                return await obj.__getitem_async__(key)
            return getitem(obj, key)

        if hasattr(key, "__liquid__"):
            key = key.__liquid__()
        return await _get_item(obj, key)
