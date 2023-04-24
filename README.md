<h1 align="center">Liquid JSONPath</h1>

<p align="center">
<a href="https://github.com/jg-rp/python-jsonpath">JSONPath</a> selectors for <a href="https://jg-rp.github.io/liquid/">Python Liquid</a>.
</p>

<p align="center">
  <a href="https://github.com/jg-rp/liquid-jsonpath/blob/main/LICENSE">
    <img src="https://img.shields.io/pypi/l/liquid-jsonpath.svg?style=flat-square" alt="License">
  </a>
  <br>
  <a href="https://pypi.org/project/liquid-jsonpath/">
    <img src="https://img.shields.io/pypi/v/liquid-jsonpath.svg?style=flat-square" alt="PyPi - Version">
  </a>
  <a href="https://pypi.org/project/liquid-jsonpath/">
    <img src="https://img.shields.io/pypi/pyversions/liquid-jsonpath.svg?style=flat-square" alt="Python versions">
  </a>
  <br>
  <a href="https://github.com/jg-rp/liquid-jsonpath/actions/workflows/tests.yaml">
    <img src="https://img.shields.io/github/actions/workflow/status/jg-rp/liquid-jsonpath/tests.yaml?branch=main&label=tests&style=flat-square" alt="Tests">
  </a>
  <a href="https://github.com/jg-rp/liquid-jsonpath/actions/workflows/coverage.yaml">
    <img src="https://img.shields.io/github/actions/workflow/status/jg-rp/liquid-jsonpath/coverage.yaml?branch=main&label=coverage&style=flat-square" alt="Coverage">
  </a>
</p>

---

**Table of Contents**

- [Installation](#installation)
- [Links](#links)
- [Examples](#examples)
- [License](#license)

## Installation

Install JSONPath for Liquid using [pip](https://pip.pypa.io/en/stable/getting-started/):

```console
python -m pip install -U liquid-jsonpath
```

Or [pipenv](https://pipenv.pypa.io/en/latest/):

```console
pipenv install liquid-jsonpath
```

## Links

- Docs: https://jg-rp.github.io/liquid/jsonpath/introduction
- Change log: https://github.com/jg-rp/liquid-jsonpath/blob/main/CHANGES.md
- PyPi: https://pypi.org/project/liquid-jsonpath/
- Issue tracker: https://github.com/jg-rp/liquid-jsonpath/issues

## Examples

### Filter

This example adds the `find` filter to a Liquid environment. You can think of `find` as an advanced alternative to the standard `map` and `where` filters. It takes a JSONPath string argument and applies it to the filter's left value.

```python
from liquid import Environment
from liquid_jsonpath import Find

env = Environment()
env.add_filter("find", Find())

data = {
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

template = env.from_string("{{ data | find: '$.users.*.name' | join: ' ' }}")
print(template.render(data=data))  # Sue John Sally Jane
```

### Tag

This example replaces the standard `{% for %}` tag with one that supports piping an iterable through a JSONPath expression.

```python
from liquid import Environment
from liquid_jsonpath import JSONPathForTag

env = Environment()
env.add_tag(JSONPathForTag)

data = {
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

template = env.from_string(
    "{% for name in data | '$.users.*.name' %}"
    "{{ name }}, "
    "{% endfor %}"
)
print(template.render(data=data))  # Sue, John, Sally, Jane,
```

## License

`liquid-jsonpath` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
