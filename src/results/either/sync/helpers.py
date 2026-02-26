"""Helper functions for Either monad operations.

This module provides utility functions that operate on Either values,
implementing common patterns and transformations.

Functions:
    - flatten: Flatten Either[L, Either[L, R]] to Either[L, R]
    - swap: Swap Left and Right branches
    - from_ok_err: Convert Result[T, E] to Either[E, T]
    - partition: Partition sequence of Either values by variant
    - traverse: Apply async operation to sequence, collecting Either results
    - sequence: Collect sequence of Either values into Either[L, List[R]]
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from results.common.protocols import ErrMixin, OkMixin
from results.core.either_base import Either

from .left import Left
from .right import Right

__all__ = [
    "flatten",
    "swap",
    "from_ok_err",
    "partition",
    "sequence",
]

L = TypeVar("L")
R = TypeVar("R")
E = TypeVar("E")
T = TypeVar("T")
V = TypeVar("V")


def flatten(either: Either[L, Either[L, R]]) -> Either[L, R]:
    """Flatten nested Either[L, Either[L, R]] to Either[L, R].

    Extracts the inner Either from Right, or returns the outer Left.
    Useful after operations that return Either of Either.

    Parameters:
        either: Either[L, Either[L, R]] to flatten

    Returns:
        Either[L, R]: Flattened Either

    Example:
        >>> nested = Right(Right(42))
        >>> flatten(nested).unwrap_right()
        42

        >>> nested = Right(Left("error"))
        >>> flatten(nested).unwrap_left()
        "error"

        >>> nested = Left("outer error")
        >>> flatten(nested).unwrap_left()
        "outer error"
    """
    if either.is_right():
        inner = either.right()
        if inner is not None:
            return inner
        # Shouldn't happen with normal Either usage
        return Left("inner None")  # type: ignore[return-value]  # 異常路徑返回緊急值，型別無從推導
    # Left: return outer error
    return either.map_left(lambda _: _)  # type: ignore[arg-type]  # 身份函數型別推導不完備


def swap(either: Either[L, R]) -> Either[R, L]:
    """Swap Left and Right variants (exchange outcomes).

    Transforms Left[E] to Right[E] and Right[T] to Left[T].
    Useful when you want to invert the success/failure semantics.

    Parameters:
        either: Either[L, R] to swap

    Returns:
        Either[R, L]: Swapped Either

    Example:
        >>> right = Right(42)
        >>> swapped = swap(right)
        >>> swapped.unwrap_left()
        42

        >>> left = Left("error")
        >>> swapped = swap(left)
        >>> swapped.unwrap_right()
        "error"
    """
    if either.is_right():
        return Left(either.right())  # type: ignore[return-value]  # Left[R, ?] 無法推導為 Either[R, L]
    else:
        return Right(either.left())  # type: ignore[return-value]  # Right[?, L] 無法推導為 Either[R, L]


def from_ok_err(result: OkMixin[T, E] | ErrMixin[T, E]) -> Either[E, T]:
    """Convert Result[T, E] to Either[E, T].

    Flips error and value positions to create an Either from a Result.
    Useful when you want error on the Left and value on the Right.

    Parameters:
        result: Result[T, E] to convert

    Returns:
        Either[E, T]: Left contains error, Right contains value

    Example:
        >>> from results import Ok, Err
        >>> either_ok = from_ok_err(Ok(42))
        >>> either_ok.unwrap_right()
        42

        >>> either_err = from_ok_err(Err("error"))
        >>> either_err.unwrap_left()
        "error"
    """
    if result.is_ok():  # type: ignore[truthy-bool]  # Union 型別無法被 is_ok() 細化
        return Right(result.ok())  # type: ignore[union-attr]  # Union 型別缺乏 ok() 方法推導
    else:
        return Left(result.err())  # type: ignore[union-attr]  # Union 型別缺乏 err() 方法推導


def partition(
    eithers: Sequence[Either[L, R]],
) -> tuple[list[L], list[R]]:
    """Partition sequence of Either values by variant.

    Collects all Left values in one list and all Right values in another.
    Useful for processing heterogeneous Either collections.

    Parameters:
        eithers: Sequence of Either values to partition

    Returns:
        Tuple (lefts, rights) containing separated values

    Example:
        >>> eithers = [Right(1), Left("a"), Right(2), Left("b")]
        >>> lefts, rights = partition(eithers)
        >>> rights
        [1, 2]
        >>> lefts
        ["a", "b"]

        >>> eithers = [Right(x) for x in range(3)]
        >>> lefts, rights = partition(eithers)
        >>> len(lefts)
        0
        >>> len(rights)
        3
    """
    lefts: list[L] = []
    rights: list[R] = []

    for either in eithers:
        if either.is_left():
            left_val = either.left()
            if left_val is not None:
                lefts.append(left_val)
        else:
            right_val = either.right()
            if right_val is not None:
                rights.append(right_val)

    return lefts, rights


def sequence(eithers: Sequence[Either[L, R]]) -> Either[L, list[R]]:
    """Collect sequence of Either values into Either[L, List[R]].

    Returns Left containing the first error found, or Right with all values.
    Short-circuits on the first Left encountered.

    Parameters:
        eithers: Sequence of Either values

    Returns:
        Either[L, list[R]]: Left if any Either is Left, Right with collected values

    Example:
        >>> eithers = [Right(1), Right(2), Right(3)]
        >>> sequence(eithers).unwrap_right()
        [1, 2, 3]

        >>> eithers = [Right(1), Left("error"), Right(3)]
        >>> sequence(eithers).unwrap_left()
        "error"

        >>> eithers: list[Either[str, int]] = []
        >>> sequence(eithers).unwrap_right()
        []
    """
    results: list[R] = []

    for either in eithers:
        if either.is_left():
            left_val = either.left()
            if left_val is not None:
                return Left(left_val)
            return Left("inner None encountered")  # type: ignore[return-value]  # 緊急值型別無法推導至 Either[L, list[R]]
        else:
            right_val = either.right()
            if right_val is not None:
                results.append(right_val)

    return Right(results)
