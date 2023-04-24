"""JSONPath filter and tag default actions."""
from enum import Enum


class Default(Enum):
    """JSONPath filter and tag default actions.

    Attributes:
        EMPTY: Always return an empty list when there's an error with the
            target object or the path.
        UNDEFINED: Always return an instance of the current Liquid
            environment's "undefined" type when there's an error with the
            target object or the path.
        RAISE: Raise a `FilterArgumentError` when there's a problem with the
            target object or the path.
    """

    EMPTY = 1
    UNDEFINED = 2
    RAISE = 3
