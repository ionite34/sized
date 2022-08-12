from __future__ import annotations

import inspect
import typing as t
from collections.abc import Generator
from functools import wraps
from types import TracebackType
from typing import Any, Callable, Dict, Sized, Union, cast, overload

from typing_extensions import ParamSpec

__all__ = ["SizedGenerator", "sized"]

T_yield = t.TypeVar("T_yield")
T_send = t.TypeVar("T_send")
T_return = t.TypeVar("T_return")
T_call = t.TypeVar("T_call", bound=t.Callable[..., Generator])
P = ParamSpec("P")

SizeLike = Union[int, Sized]
ArgDict = Dict[str, Any]
SizedCallable = Callable[[ArgDict], SizeLike]
SupportsSize = Union[SizeLike, SizedCallable]

null = object()  # Sentinel for missing defaults


def _get_size(size: SizeLike) -> int:
    """Get an int size from int | Sized"""
    if isinstance(size, int):
        return size
    elif isinstance(size, Sized):
        return len(size)
    raise TypeError(f"{size} should be int or Sized, not {type(size)}")


def _size_call(func: SizedCallable, fn_dict: ArgDict) -> int:
    """Get int size from SizedCallable"""
    size_like = func(fn_dict)
    # Use _get_size to resolve (int | Sized) into int
    return _get_size(size_like)


def _get_keywords(func: Callable, kwargs: dict) -> ArgDict:
    """Return a dict of (reversed) keyword arguments from a function."""
    spec = inspect.getfullargspec(func)
    # Make dict with args first
    args_size, defaults_size = len(spec.args), len(spec.defaults or [])
    args = spec.args
    defaults = spec.defaults or ()
    # Pad with null sentinels to match length of args
    values = [null] * (args_size - defaults_size)
    values.extend(defaults)
    # Create dict
    arg_dict = {k: (v if k not in kwargs else kwargs[k]) for k, v in zip(args, values)}
    return arg_dict


def _resolve_args(func: Callable, args: tuple, kwargs: dict) -> ArgDict:
    """Resolve args and kwargs to a dict of {str: Any}"""
    # Get ArgDict
    arg_dict = _get_keywords(func, kwargs)
    # Update with positional args
    arg_dict.update({str(idx): arg for idx, arg in enumerate(args)})
    print(arg_dict)
    # For null sentinels, replace with args
    for i, (k, v) in enumerate(arg_dict.items()):
        if v is null:
            try:
                arg_dict[k] = args[i]
            except IndexError as exc:
                raise TypeError(
                    f"{func.__name__}() missing a required positional argument: '{k}'"
                ) from exc
    return arg_dict


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
) -> Callable[
    [Callable[P, Generator[T_yield, T_send, T_return]]],
    Callable[P, SizedGenerator[T_yield, T_send, T_return]],
]:
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
        func: Callable[P, Generator[T_yield, T_send, T_return]],
    ) -> Callable[P, SizedGenerator[T_yield, T_send, T_return]]:
        """Decorator"""

        @wraps(func)
        def wrapper(
            *args: P.args, **kwargs: P.kwargs
        ) -> SizedGenerator[T_yield, T_send, T_return]:
            """Wrapper"""
            if isinstance(size, (int, Sized)):
                resolved = _get_size(size)
            elif callable(size):
                # Get dict of all kwargs, with positionals mapped as well
                fn_dict = _resolve_args(func, args, kwargs)
                # Call the provided callable with the dict
                resolved = _size_call(size, fn_dict)
            else:
                raise TypeError(f"Expected int or Callable, got {type(size)}")

            return SizedGenerator(func(*args, **kwargs), size_like=resolved)

        return cast(Callable[P, SizedGenerator[T_yield, T_send, T_return]], wrapper)

    return decorator
