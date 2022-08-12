from collections.abc import Sized
from typing import Generator

import pytest
from tqdm import tqdm

from sized.gen import SizedGenerator, sized


@pytest.fixture(scope="function")
def make_gen():
    size = 25

    @sized(size=25)
    def _make_gen(size_in: int) -> Generator[int, None, None]:
        yield from range(size_in)

    return _make_gen(size)


@pytest.mark.parametrize(
    "value, expected",
    [
        (1, True),  # int
        ([1, 2, 3], True),  # list
        (1.0, False),  # float
        ((x for x in range(3)), False),  # Generator
    ],
)
def test_length_like(value: tuple, expected: bool) -> None:
    assert isinstance(value, (int, Sized)) == expected


def test_length_like_ex() -> None:
    # Make a generator
    gen = (i for i in range(3))
    # Try size
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        len(gen)  # type: ignore
    # Generator should not be Sized
    assert not isinstance(gen, Sized)


def test_decorator(make_gen) -> None:
    # Check keyword arguments
    @sized(lambda x: x["size_in"])
    def _make_gen_k(size_in: int) -> Generator[int, None, None]:
        yield from range(size_in)

    # Check positional argument usage
    @sized(lambda x: x["0"])
    def _make_gen_p(size_in: int) -> Generator[int, None, None]:
        yield from range(size_in)

    gen_p = _make_gen_p(25)
    gen_k = _make_gen_k(20)

    assert len(gen_p) == 25
    assert len(gen_k) == 20
    assert list(gen_p) == list(range(25))
    assert list(gen_k) == list(range(20))

    # Check out of range
    with pytest.raises(StopIteration):
        next(gen_p)

    # Check throw
    with pytest.raises(RuntimeError):
        gen_p.throw(RuntimeError)


def test_decorator_ext() -> None:
    # Extended decorator test with Sized and dict
    source = [1, 2, 3]

    @sized(size=source)
    def _make_gen(size_in: list[int]) -> Generator[int, None, None]:
        yield from size_in

    @sized(size=lambda x: x["size_in"])
    def _make_gen_dict(size_in: list[int]) -> Generator[int, None, None]:
        yield from size_in

    # Check functions
    assert list(_make_gen(source)) == source
    assert list(_make_gen_dict(source)) == source


def test_decorator_ex() -> None:
    # Check invalid decorator use
    with pytest.raises(TypeError):

        @sized(5)
        def _make_gen(n: int):
            return 1 + n

        _make_gen(2)


def test_sized_gen() -> None:
    # Create a generator
    gen = (i for i in range(10))

    # Wrap it using with_len
    f_gen = SizedGenerator(gen, 10)

    # Check that it has __len__
    assert len(f_gen) == 10

    # Check that it works as a generator
    assert isinstance(f_gen, Generator)
    results = []
    for i in f_gen:
        results.append(i)
    assert results == list(range(10))


def test_sized_gen_ex() -> None:
    # Test wrong LengthLike type
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        SizedGenerator((i for i in range(5)), 1.0)  # type: ignore


def test_fixed_gen_tqdm(capsys) -> None:
    # Create a generator and wrap it with FixedGenerator
    gen = (i for i in range(128))
    # Use list as LengthLike source
    f_gen = SizedGenerator(gen, list(range(128)))
    assert len(f_gen) == 128

    # Check that it works with tqdm
    counter = 0
    for i in tqdm(f_gen):
        counter += 1
    assert counter == 128
    captured = capsys.readouterr()
    assert "128/128" in captured.err
