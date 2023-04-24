"""A Liquid filter bringing JSONPath syntax to Liquid templates."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Mapping
from typing import Optional
from typing import Sequence

from jsonpath import JSONPathEnvironment
from jsonpath import JSONPathError
from liquid.exceptions import FilterArgumentError

from liquid_jsonpath import Default

if TYPE_CHECKING:
    from liquid import Environment


class Find:
    """A Liquid filter bringing JSONPath syntax to Liquid templates.

    Args:
        default: The default action to take when either the filter left
            value or the JSONPath are invalid.

    Attributes:
        jsonpath_class: The `JSONPathEnvironment` to use. Override this with
            as custom `JSONPathEnvironment` subclass to configure JSONPath.
    """

    jsonpath_class = JSONPathEnvironment
    with_environment = True

    def __init__(self, default: Default = Default.UNDEFINED) -> None:
        self.default = default
        self.jsonpath = self.jsonpath_class()

    def __call__(self, obj: object, path: str, environment: Environment) -> object:
        """Find all objects in _obj_ matching the JSONPath _path_.

        If _obj_ is not a mapping or sequence - like a list or dictionary - a
        default value is returned or an exceptions is raised, depending on the
        value of _self.default_.
        """
        if isinstance(obj, str):
            return self._default(obj, environment)

        if isinstance(obj, (Mapping, Sequence)):
            try:
                return self.jsonpath.findall(path, obj)
            except JSONPathError as err:
                return self._default(obj, environment, err)

        return self._default(obj, environment)

    async def filter_async(
        self, obj: object, path: str, environment: Environment
    ) -> object:
        """Find all objects in _obj_ matching the JSONPath _path_.

        Where _obj_ and its children implement `__getitem_async__`, it will
        be awaited instead of calling `getitem()`.

        If _obj_ is not a mapping or sequence - like a list or dictionary - a
        default value is returned or an exceptions is raised, depending on the
        value of _self.default_.
        """
        if isinstance(obj, str):
            return self._default(obj, environment)

        if isinstance(obj, (Mapping, Sequence)):
            try:
                return await self.jsonpath.findall_async(path, obj)
            except JSONPathError as err:
                return self._default(obj, environment, err)

        return self._default(obj, environment)

    def _default(
        self, obj: object, env: Environment, err: Optional[Exception] = None
    ) -> object:
        if self.default == Default.EMPTY:
            return []
        if self.default == Default.UNDEFINED:
            return env.undefined("<jsonpath>")
        if err:
            msg = f"jsonpath error: {err}"
            raise FilterArgumentError(msg) from err

        msg = f"expected a sequence or mapping, found {obj.__class__.__name__}"
        raise FilterArgumentError(msg)
