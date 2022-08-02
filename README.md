# sized

[![Build](https://github.com/ionite34/sized/actions/workflows/build.yml/badge.svg)](https://github.com/ionite34/sized/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/ionite34/sized/branch/main/graph/badge.svg)](https://codecov.io/gh/ionite34/sized)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![FOSSA Status](https://app.fossa.com/api/projects/custom%2B31224%2Fgithub.com%2Fionite34%2Fsized.svg?type=shield)](https://app.fossa.com/projects/custom%2B31224%2Fgithub.com%2Fionite34%2Fsized?ref=badge_shield)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ionite34/sized/main.svg)](https://results.pre-commit.ci/latest/github/ionite34/sized/main)
[![DeepSource](https://deepsource.io/gh/ionite34/sized.svg/?label=active+issues&show_trend=true&token=F69_eHULQKuPhzJHAa6XvCcH)](https://deepsource.io/gh/ionite34/sized/?ref=repository-badge)

[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sized)](https://pypi.org/project/sized/)
[![PyPI version](https://badge.fury.io/py/sized.svg)](https://pypi.org/project/sized/)

### Sized Generators with Decorators

## Why?
- The `SizedGenerator` type provides a simple and robust way to keep track of iterations and max sizes for
generators and iterators.
- An issue with using normal Generators with long-running / multithread processes has been reporting
progress.
- Here is an example of a standard `Generator` being wrapped with `tqdm`:

```python
from tqdm import tqdm

def gen():
    n = 2
    for _ in range(100):
        n += (5 * 1 / n)
        yield n

for x in tqdm(gen()):
    pass

# Output has no progress bar:
> 100it [00:00, 1.00it/s]
```

- A solution would be to keep track of the total progress, but this gets messy if an iteration is
interrupted by user actions and the progress bar needs to continue.
- Now with the `sized` decorator:

```python
from sized import sized

@sized(100)
def s_gen():
    n = 2
    for _ in range(100):
        n += (5 * 1 / n)
        yield n

for x in tqdm(s_gen()):
    pass

# Now with a progress bar!
> 100%|██████████| 100/100 [00:00<00:00, 1.00it/s]
```

- `SizedGenerator` will also track iterations called and reflect remaining length

```python
gen_instance = s_gen()

len(gen_instance) -> 100

next(gen_instance)
next(gen_instance)

len(gen_instance) -> 98
```

## Getting started

### There are 2 main ways to create a `SizedGenerator`

### 1. `@sized` decorator
```python
from sized import sized

@sized(5)
def gen():
    yield ...
```


### 2. `SizedGenerator` constructor
```python
from sized import SizedGenerator

gen = SizedGenerator((x ** 2 for x in range(10)), 10)
```

## Additional Info

- The `size` argument can be either an `int`, `Sized` object, or a callable accepting a dictionary of
arguments and keyword-arguments, returning an `int` or `Sized` object.

```python
@sized(15) # int
def gen():
    for i in range(15):
        yield i ** 2
```
```python
ls = [1, 4, 5]

@sized(ls) # `Sized` objects will have len(obj) called automatically
def gen():
    for i in ls:
        yield i ** 2
```
```python
@sized(lambda x: x['some_arg']) # Callable using keyword argument, returning `Sized`
def gen(arg = None):
    for i in arg:
        yield i ** 2
```
```python
@sized(lambda x: 2 * len(x['1'])) # Callable using positional argument, returning `int`
def gen(arg_0, arg_1):
    for _ in range(2):
        for i in arg_1:
            yield i ** 2 + arg_0
```

## License
The code in this project is released under the [MIT License](LICENSE).

[![FOSSA Status](https://app.fossa.com/api/projects/custom%2B31224%2Fgithub.com%2Fionite34%2Fsized.svg?type=large)](https://app.fossa.com/projects/custom%2B31224%2Fgithub.com%2Fionite34%2Fsized?ref=badge_large)
