"""A _for_ tag that allows iterables to be piped through a JSONPath."""
from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Mapping
from typing import Optional
from typing import Sequence
from typing import Union

from jsonpath import CompoundJSONPath
from jsonpath import JSONPath
from jsonpath import JSONPathEnvironment
from jsonpath.exceptions import JSONPathError
from liquid.ast import BlockNode
from liquid.builtin.tags.for_tag import ENDFORBLOCK
from liquid.builtin.tags.for_tag import ENDFORELSEBLOCK
from liquid.builtin.tags.for_tag import TAG_ELSE
from liquid.builtin.tags.for_tag import TAG_ENDFOR
from liquid.builtin.tags.for_tag import ForNode
from liquid.builtin.tags.for_tag import ForTag
from liquid.exceptions import LiquidSyntaxError
from liquid.exceptions import LiquidTypeError
from liquid.expression import Expression
from liquid.expression import LoopExpression
from liquid.expression import LoopIterable
from liquid.expressions.common import parse_identifier
from liquid.expressions.common import parse_string_literal
from liquid.expressions.loop.lex import tokenize
from liquid.expressions.loop.parse import parse_loop_arguments
from liquid.expressions.loop.parse import parse_range
from liquid.expressions.stream import TokenStream as ExprTokenStream
from liquid.parse import expect
from liquid.parse import get_parser
from liquid.stream import TokenStream
from liquid.token import TOKEN_EXPRESSION
from liquid.token import TOKEN_IDENTIFIER
from liquid.token import TOKEN_IN
from liquid.token import TOKEN_LPAREN
from liquid.token import TOKEN_PIPE
from liquid.token import TOKEN_STRING
from liquid.token import TOKEN_TAG

from liquid_jsonpath import Default

if TYPE_CHECKING:
    from liquid import Context
    from liquid import Environment
    from liquid.ast import Node


class JSONPathExpression(Expression):
    """A Liquid expression that evaluates a JSONPath against an object."""

    __slots__ = ("expression", "path", "default")

    def __init__(
        self,
        expr: Expression,
        path: Union[CompoundJSONPath, JSONPath],
        default: Default = Default.UNDEFINED,
    ) -> None:
        self.expression = expr
        self.path = path
        self.default = default

    def evaluate(self, context: Context) -> object:  # noqa: D102
        obj = self.expression.evaluate(context)
        if isinstance(obj, str):
            return self._default(obj, context.env)
        if isinstance(obj, (Mapping, Sequence)):
            try:
                return self.path.findall(obj)
            except JSONPathError as err:
                return self._default(obj, context.env, err)
        return self._default(obj, context.env)

    async def evaluate_async(self, context: Context) -> object:  # noqa: D102
        obj = await self.expression.evaluate_async(context)
        if isinstance(obj, str):
            return self._default(obj, context.env)
        if isinstance(obj, (Mapping, Sequence)):
            try:
                return await self.path.findall_async(obj)
            except JSONPathError as err:
                return self._default(obj, context.env, err)
        return self._default(obj, context.env)

    def _default(
        self, obj: object, env: Environment, err: Optional[Exception] = None
    ) -> object:
        if self.default == Default.EMPTY:
            return []
        if self.default == Default.UNDEFINED:
            return env.undefined("<jsonpath>")
        if err:
            msg = f"jsonpath error: {err}"
            raise LiquidTypeError(msg) from err

        msg = f"expected a sequence or mapping, found {obj.__class__.__name__}"
        raise LiquidTypeError(msg)


class JSONPathForTag(ForTag):
    """A _for_ tag that allows iterables to be piped through a JSONPath."""

    default = Default.UNDEFINED
    jsonpath_class = JSONPathEnvironment

    def __init__(self, env: Environment):
        super().__init__(env)
        self.jsonpath = self.jsonpath_class()

    def parse(self, stream: TokenStream) -> Node:  # noqa: D102
        tok = stream.next_token()
        expect(stream, TOKEN_EXPRESSION)
        expr = self._parse_expression(stream.current.value)
        stream.next_token()

        parser = get_parser(self.env)
        block = parser.parse_block(stream, ENDFORBLOCK)
        default: Optional[BlockNode] = None

        if stream.current.istag(TAG_ELSE):
            stream.next_token()
            default = parser.parse_block(stream, ENDFORELSEBLOCK)

        expect(stream, TOKEN_TAG, value=TAG_ENDFOR)
        return ForNode(tok, expression=expr, block=block, default=default)

    def _parse_expression(self, expr: str, linenum: int = 1) -> LoopExpression:
        """Parse a loop expression, possibly filtered by a JSONPath."""
        stream = ExprTokenStream(tokenize(expr, linenum))
        stream.expect(TOKEN_IDENTIFIER)
        name = next(stream)[2]

        # Eat TOKEN_IN
        stream.expect(TOKEN_IN)
        next(stream)

        if stream.current[1] == TOKEN_IDENTIFIER:
            expression: LoopIterable = parse_identifier(stream)
            next(stream)
        elif stream.current[1] == TOKEN_STRING:
            expression = parse_string_literal(stream)
            next(stream)
        elif stream.current[1] == TOKEN_LPAREN:
            expression = parse_range(stream)
            next(stream)
        else:
            msg = "invalid loop expression"
            raise LiquidSyntaxError(msg, linenum=stream.current[0])

        if stream.current[1] == TOKEN_PIPE:
            next(stream)
            stream.expect(TOKEN_STRING)
            path = self._compile_path(parse_string_literal(stream).value)
            expression = JSONPathExpression(expression, path, default=self.default)
            next(stream)

        args, reversed_ = parse_loop_arguments(stream)
        return LoopExpression(
            name=name, iterable=expression, reversed_=reversed_, **args
        )

    def _compile_path(self, path: str) -> Union[CompoundJSONPath, JSONPath]:
        try:
            return self.jsonpath.compile(path)
        except JSONPathError as err:
            raise LiquidSyntaxError(str(err)) from err
