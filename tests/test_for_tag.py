import asyncio
import operator
from typing import List
from typing import Mapping

import pytest
from jsonpath import JSONPathEnvironment
from jsonpath.exceptions import JSONPathTypeError
from liquid import DictLoader
from liquid import Environment
from liquid import Mode
from liquid import StrictUndefined
from liquid.exceptions import Error
from liquid.exceptions import LiquidSyntaxError
from liquid.exceptions import LiquidTypeError
from liquid.exceptions import UndefinedError
from liquid.future import Environment as FutureEnvironment
from liquid.golden.case import Case
from liquid.golden.for_tag import cases

from liquid_jsonpath import Default
from liquid_jsonpath import JSONPathForTag


@pytest.fixture()
def data() -> Mapping[str, object]:
    return {
        "users": [
            {
                "name": "Sue",
                "score": 100,
            },
            {
                "name": "John",
                "score": 86,
            },
            {
                "name": "Sally",
                "score": 84,
            },
            {
                "name": "Jane",
                "score": 55,
            },
        ]
    }


@pytest.mark.parametrize("case", cases, ids=operator.attrgetter("description"))
def test_golden(case: Case) -> None:
    """Test our _for_ tag is backwards compatible with the standard _for_ tag."""
    if not case.future:
        env = Environment(
            loader=DictLoader(case.partials),
            tolerance=Mode.STRICT,
        )
    else:
        env = FutureEnvironment(
            loader=DictLoader(case.partials),
            tolerance=Mode.STRICT,
        )

    env.add_tag(JSONPathForTag)

    if case.error:
        with pytest.raises(Error):
            env.from_string(case.template, globals=case.globals).render()
    else:
        result = env.from_string(case.template, globals=case.globals).render()
        assert result == case.expect


def test_jsonpath_in_for_loop(data: Mapping[str, object]) -> None:
    env = Environment()
    env.add_tag(JSONPathForTag)
    template = env.from_string(
        "{% for name in data | '$.users.*.name' %}{{ name }}, {% endfor %}"
    )

    assert template.render(data=data) == "Sue, John, Sally, Jane, "

    async def coro() -> str:
        return await template.render_async(data=data)

    assert asyncio.run(coro()) == "Sue, John, Sally, Jane, "


def test_target_string_undefined_default() -> None:
    class MyForTag(JSONPathForTag):
        default = Default.UNDEFINED

    env = Environment(undefined=StrictUndefined)
    env.add_tag(MyForTag)
    template = env.from_string(
        "{% for name in 'foo' | '$.users.*.name' %}{{ name }}, {% endfor %}"
    )

    with pytest.raises(UndefinedError):
        template.render()

    async def coro() -> str:
        return await template.render_async()

    with pytest.raises(UndefinedError):
        asyncio.run(coro())


def test_target_int_undefined_default() -> None:
    class MyForTag(JSONPathForTag):
        default = Default.UNDEFINED

    env = Environment(undefined=StrictUndefined, globals={"foo": 1})
    env.add_tag(MyForTag)
    template = env.from_string(
        "{% for name in foo | '$.users.*.name' %}{{ name }}, {% endfor %}"
    )

    with pytest.raises(UndefinedError):
        template.render()

    async def coro() -> str:
        return await template.render_async()

    with pytest.raises(UndefinedError):
        asyncio.run(coro())


def test_path_compilation_error() -> None:
    env = Environment(undefined=StrictUndefined, globals={"foo": 1})
    env.add_tag(JSONPathForTag)

    with pytest.raises(LiquidSyntaxError):
        env.from_string("{% for name in data | '$[1,2' %}{{ name }}, {% endfor %}")


def test_target_string_empty_default() -> None:
    class MyForTag(JSONPathForTag):
        default = Default.EMPTY

    env = Environment()
    env.add_tag(MyForTag)
    template = env.from_string(
        "{% for name in 'foo' | '$.users.*.name' %}{{ name }}, {% endfor %}"
    )

    assert template.render() == ""  # noqa: PLC1901

    async def coro() -> str:
        return await template.render_async()

    assert asyncio.run(coro()) == ""  # noqa: PLC1901


def test_target_string_raise_default() -> None:
    class MyForTag(JSONPathForTag):
        default = Default.RAISE

    env = Environment()
    env.add_tag(MyForTag)
    template = env.from_string(
        "{% for name in 'foo' | '$.users.*.name' %}{{ name }}, {% endfor %}"
    )

    with pytest.raises(LiquidTypeError):
        template.render()

    async def coro() -> str:
        return await template.render_async()

    with pytest.raises(LiquidTypeError):
        asyncio.run(coro())


def test_render_time_path_error(data: Mapping[str, object]) -> None:
    def mock_jsonpath_filter(_: object) -> List[str]:
        raise JSONPathTypeError(":(")  # noqa: EM101

    class MyJSONPathEnv(JSONPathEnvironment):
        def setup_function_extensions(self) -> None:
            super().setup_function_extensions()
            self.function_extensions["mock"] = mock_jsonpath_filter

    class MyForTag(JSONPathForTag):
        default = Default.RAISE
        jsonpath_class = MyJSONPathEnv

    env = Environment()
    env.add_tag(MyForTag)
    template = env.from_string(
        "{% for name in data | '$.users[?mock(@)]' %}{{ name }}, {% endfor %}"
    )

    with pytest.raises(LiquidTypeError):
        template.render(data=data)

    async def coro() -> str:
        return await template.render_async(data=data)

    with pytest.raises(LiquidTypeError):
        asyncio.run(coro())
