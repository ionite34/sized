from __future__ import annotations

import typing as t
from collections.abc import Generator
from functools import wraps
from types import TracebackType
from typing import overload

T_yield = t.TypeVar("T_yield")
T_send = t.TypeVar("T_send")
T_return = t.TypeVar("T_return")
T_call = t.TypeVar("T_call", bound=t.Callable[..., Generator])

SizeLike = t.Union[int, t.Sized]
ArgDict = t.Dict[str, t.Any]
SizedCallable = t.Callable[[ArgDict], SizeLike]
SupportsSize = t.Union[SizeLike, SizedCallable]


def _get_size(size: SizeLike) -> int:
    """Get an int size from int | Sized"""
    if isinstance(size, int):
        return size
    elif isinstance(size, t.Sized):
        return len(size)
    raise TypeError(f"{size} should be int or Sized, not {type(size)}")


def _size_call(func: SizedCallable, fn_dict: ArgDict) -> int:
    """Get int size from SizedCallable"""
    size_like = func(fn_dict)
    return _get_size(size_like)


class SizedGenerator(Generator[T_yield, T_send, T_return]):
    """Extended Generator with __len__"""

    def __init__(self, gen: Generator[T_yield, T_send, T_return], size_like: SizeLike):
        """
        Generator with fixed size.

        Args:
            gen: Base Generator
            size_like: Length of iterator as int | Sized
        """
        super().__init__()
        if not isinstance(gen, Generator):
            raise TypeError(f"Expected Generator, got {type(gen)}")
        self._gen = gen
        self._length = _get_size(size_like)
        self._index = 0

    def send(self, __value: T_send) -> T_yield:
        """Send the next value or raise StopIteration."""
        if self._index > self._length:
            raise StopIteration
        self._index += 1
        return self._gen.send(__value)

    @overload
    def throw(
        self,
        __typ: t.Type[BaseException],
        __val: object = ...,
        __tb: TracebackType | None = ...,
    ) -> T_yield:
        """Raise an exception in the generator."""
        ...

    @overload
    def throw(
        self,
        __typ: BaseException,
        __val: None = ...,
        __tb: TracebackType | None = ...,
    ) -> T_yield:
        """Raise an exception in the generator."""
        ...

    def throw(
        self,
        __typ: t.Type[BaseException] | BaseException,
        __val: BaseException | object | None = None,
        __tb: TracebackType | None = None,
    ) -> T_yield:
        """Raise an exception in the generator."""
        return self._gen.throw(__typ, __val, __tb)  # type: ignore

    def __len__(self) -> int:
        """Return the current length of the iterator, or max - iterated."""
        return self._length - self._index


def sized(
    size: SupportsSize,
) -> t.Callable[[T_call], t.Callable[..., SizedGenerator[T_yield, T_send, T_return]]]:
    """
    Decorator to make a generator with fixed size.

    Args:
        size: Length of iterator as int, or a callable that accepts
            a dict of {[int: index] | *args, [str: name] | *kwargs} and returns an int.

    Returns: Decorator

    Example:
        Provide int size_like::

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

    def decorator(
        func: T_call,
    ) -> t.Callable[..., SizedGenerator[T_yield, T_send, T_return]]:
        """Decorator"""

        @wraps(func)
        def wrapper(*args: t.Any, **kwargs: t.Any) -> SizedGenerator:
            """Wrapper"""
            if isinstance(size, (int, t.Sized)):
                resolved = _get_size(size)
            elif callable(size):
                # fn_dict is a union dict of kwargs with args added with index keys
                fn_dict = kwargs.copy()
                fn_dict.update(dict(*enumerate(args)))
                resolved = _size_call(size, fn_dict)
            else:
                raise TypeError(f"Expected int or Callable, got {type(size)}")

            return SizedGenerator(func(*args, **kwargs), size_like=resolved)

        return wrapper

    return decorator
