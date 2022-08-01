from __future__ import annotations

import typing as t
from abc import abstractmethod
from collections.abc import Generator, Sequence
from functools import wraps
from typing import Union

_T = t.TypeVar("_T")

SizeLike = t.Union[int, t.Sized]
SizedCallable = t.Callable[[dict[t.Union[str, int]]], SizeLike]
SupportsSize = t.Union[SizeLike, SizedCallable]


def _get_size(size: SizeLike) -> int:
    if isinstance(size, int):
        return size
    elif isinstance(size, t.Sized):
        return len(size)
    raise TypeError(f"{size} should be int or Sized, not {type(size)}")


def _size_call(size: SizedCallable) -> int:
    if callable(size):
        return size(dict())
    return size


class SizedGenerator(Generator[_T, None, None]):
    def __init__(self, gen: Generator[_T, None, None], length: int | t.Sized):
        """
        Generator with fixed size.

        Args:
            gen: Base Generator
            length: Length of iterator as int, or Sized object that implements __len__
        """
        super().__init__()
        if not isinstance(gen, Generator):
            raise TypeError(f"Expected Generator, got {type(gen)}")
        self._gen = gen
        self._length = Size(length)
        self._index: int = 0
        self._data: list = []

    def send(self, *args, **kwargs):
        if self._index > self._length.value:
            self.throw(
                IndexError(f"Iteration out of range: {self._index}/{self._length}")
            )
        self._index += 1
        # Update size if
        return self._gen.send(*args, **kwargs)

    def throw(self, *args, **kwargs):
        return self._gen.throw(*args, **kwargs)

    def __len__(self) -> int:
        return self._length.value - self._index


def sized(size: int | t.Callable[[dict[str | int]], int]):
    """
    Decorator to make a generator with fixed size.

    Args:
        size: Length of iterator as int, or a callable that accepts
            a dict of {[int: index] | *args, [str: name] | *kwargs} and returns an int.

    Returns: Decorator

    Example:
        Provide int length::

            >>> @sized(10)
            >>> def gen(): ...

        Size of Callable(dict[str | int]) -> int::

            >>> @sized(lambda x: len(x['data']))
            >>> def gen(data: list): ...

            >>> @sized(lambda x: len(x[0]))
            >>> def gen(data: list): ...

        Size of Callable(dict[str | int]) -> Sized::

            >>> @sized(lambda x: x['data'])
            >>> def gen(data: list): ...

            >>> @sized(lambda x: x[0])
            >>> def gen(data: list): ...

        | Same as above, return Sized types to use their len():
        | @sized(lambda x: x['data'])
        | def gen(data: list): ...
    """

    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs) -> SizedGenerator:
            # fn_dict is a union dict of kwargs with args added with index keys
            fn_dict = kwargs.copy()
            fn_dict.update(dict(enumerate(args)))

            return SizedGenerator(
                func(*args, **kwargs),
                length=size
            )

        return wrapper

    return deco
