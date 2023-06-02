import asyncio
from typing import Mapping

import pytest
from liquid import Environment
from liquid import StrictUndefined
from liquid.exceptions import FilterArgumentError
from liquid.exceptions import UndefinedError

from liquid_jsonpath import Default
from liquid_jsonpath import Find


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


def test_find_filter(data: Mapping[str, object]) -> None:
    env = Environment()
    env.add_filter("find", Find())
    template = env.from_string("{{ data | find: '$.users.*.name' | join: ' ' }}")
    assert template.render(data=data) == "Sue John Sally Jane"


def test_find_filter_async(data: Mapping[str, object]) -> None:
    env = Environment()
    env.add_filter("find", Find())
    template = env.from_string("{{ data | find: '$.users.*.name' | join: ' ' }}")

    async def coro() -> str:
        return await template.render_async(data=data)

    assert asyncio.run(coro()) == "Sue John Sally Jane"


def test_string_left_undefined_default() -> None:
    env = Environment(undefined=StrictUndefined)
    env.add_filter("find", Find(default=Default.UNDEFINED))
    template = env.from_string("{{ 'foo' | find: '$.users.*.name' | join: ' ' }}")

    with pytest.raises(UndefinedError):
        template.render(data=data)

    async def coro() -> str:
        return await template.render_async(data=data)

    with pytest.raises(UndefinedError):
        asyncio.run(coro())


def test_int_left_undefined_default() -> None:
    env = Environment(undefined=StrictUndefined)
    env.add_filter("find", Find(default=Default.UNDEFINED))
    template = env.from_string("{{ 1 | find: '$.users.*.name' | join: ' ' }}")

    with pytest.raises(UndefinedError):
        template.render(data=data)

    async def coro() -> str:
        return await template.render_async(data=data)

    with pytest.raises(UndefinedError):
        asyncio.run(coro())


def test_invalid_path_undefined_default(data: Mapping[str, object]) -> None:
    env = Environment(undefined=StrictUndefined)
    env.add_filter("find", Find(default=Default.UNDEFINED))
    template = env.from_string("{{ data | find: '.@' | join: ' ' }}")

    with pytest.raises(UndefinedError):
        template.render(data=data)

    async def coro() -> str:
        return await template.render_async(data=data)

    with pytest.raises(UndefinedError):
        asyncio.run(coro())


def test_string_left_raise_default() -> None:
    env = Environment()
    env.add_filter("find", Find(default=Default.RAISE))
    template = env.from_string("{{ 'foo' | find: '$.users.*.name' | join: ' ' }}")

    with pytest.raises(FilterArgumentError):
        template.render(data=data)

    async def coro() -> str:
        return await template.render_async(data=data)

    with pytest.raises(FilterArgumentError):
        asyncio.run(coro())


def test_int_left_raise_default() -> None:
    env = Environment()
    env.add_filter("find", Find(default=Default.RAISE))
    template = env.from_string("{{ 1 | find: '$.users.*.name' | join: ' ' }}")

    with pytest.raises(FilterArgumentError):
        template.render(data=data)

    async def coro() -> str:
        return await template.render_async(data=data)

    with pytest.raises(FilterArgumentError):
        asyncio.run(coro())


def test_invalid_path_raise_default(data: Mapping[str, object]) -> None:
    env = Environment()
    env.add_filter("find", Find(default=Default.RAISE))
    template = env.from_string("{{ data | find: '.@' | join: ' ' }}")

    with pytest.raises(FilterArgumentError):
        template.render(data=data)

    async def coro() -> str:
        return await template.render_async(data=data)

    with pytest.raises(FilterArgumentError):
        asyncio.run(coro())


def test_string_left_empty_default() -> None:
    env = Environment()
    env.add_filter("find", Find(default=Default.EMPTY))
    template = env.from_string("{{ 'foo' | find: '$.users.*.name' | join: ' ' }}")

    async def coro() -> str:
        return await template.render_async(data=data)

    assert template.render(data=data) == ""  # noqa: PLC1901
    assert asyncio.run(coro()) == ""  # noqa: PLC1901


def test_int_left_empty_default() -> None:
    env = Environment()
    env.add_filter("find", Find(default=Default.EMPTY))
    template = env.from_string("{{ 1 | find: '$.users.*.name' | join: ' ' }}")

    async def coro() -> str:
        return await template.render_async(data=data)

    assert template.render(data=data) == ""  # noqa: PLC1901
    assert asyncio.run(coro()) == ""  # noqa: PLC1901


def test_invalid_path_empty_default(data: Mapping[str, object]) -> None:
    env = Environment()
    env.add_filter("find", Find(default=Default.EMPTY))
    template = env.from_string("{{ data | find: '.@' | join: ' ' }}")

    async def coro() -> str:
        return await template.render_async(data=data)

    assert template.render(data=data) == ""  # noqa: PLC1901
    assert asyncio.run(coro()) == ""  # noqa: PLC1901


def test_extra_find_filter_context(data: Mapping[str, object]) -> None:
    env = Environment()
    env.add_filter("find", Find())
    template = env.from_string(
        "{{ data | find: '$.users[?@.name in _.names].name' | join: ' ' }}",
        globals={"names": ["Sue", "Sally"]},
    )

    async def coro() -> str:
        return await template.render_async(data=data)

    assert template.render(data=data) == "Sue Sally"
    assert asyncio.run(coro()) == "Sue Sally"
