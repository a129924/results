"""Helper functions for synchronous Maybe workflows."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast, overload

from ...core.maybe_base import Maybe
from ...core.types import T, U
from .nothing import Nothing
from .some import Some


def flatten(maybe: Maybe[Maybe[T]]) -> Maybe[T]:
    """Flatten nested Maybe structure.

    Args:
        maybe: Maybe[Maybe[T]]

    Returns:
        Flattened Maybe[T]

    Examples:
        >>> flatten(Some(Some(42)))
        Some(42)

        >>> flatten(Some(Nothing()))
        Nothing()

        >>> flatten(Nothing())
        Nothing()
    """
    if isinstance(maybe, Some):
        some: Some[Maybe[T]] = maybe
        return some.value

    if isinstance(maybe, Nothing):
        return cast(Maybe[T], maybe)
    raise TypeError(f"Unexpected Maybe variant: {maybe!r}")


def transpose(maybe: Maybe[list[T]]) -> list[Maybe[T]]:
    """Convert Maybe[list[T]] to list[Maybe[T]].

    Args:
        maybe: Maybe[list[T]]

    Returns:
        list[Maybe[T]], where Some wraps each element

    Examples:
        >>> transpose(Some([1, 2, 3]))
        [Some(1), Some(2), Some(3)]

        >>> transpose(Nothing())
        []
    """
    if isinstance(maybe, Some):
        return [Some(item) for item in maybe.value]
    if isinstance(maybe, Nothing):
        return []
    raise TypeError(f"Unexpected Maybe variant: {maybe!r}")


@overload
def map_or(maybe: Some[T], default: U, fn: Callable[[T], U]) -> U: ...
@overload
def map_or(maybe: Nothing[None], default: U, fn: Callable[[Any], U]) -> U: ...
def map_or(maybe: Maybe[T], default: U, fn: Callable[[T], U]) -> U:
    """Map with default value.

    Args:
        maybe: Maybe[T]
        default: Default value if Nothing
        fn: Transformation function

    Returns:
        Transformed value or default

    Examples:
        >>> map_or(Some(5), 0, lambda x: x * 2)
        10

        >>> map_or(Nothing(), 0, lambda x: x * 2)
        0
    """
    if isinstance(maybe, Some):
        return fn(maybe.value)
    if isinstance(maybe, Nothing):
        return default
    raise TypeError(f"Unexpected Maybe variant: {maybe!r}")


def get_or_insert(maybe: Maybe[T], default: T) -> Maybe[T]:
    """Get Some or insert default, returning modified version.

    Args:
        maybe: Maybe[T]
        default: Value to insert if Nothing

    Returns:
        Some with original or default value

    Examples:
        >>> get_or_insert(Some(42), 0)
        Some(42)

        >>> get_or_insert(Nothing(), 99)
        Some(99)
    """
    if isinstance(maybe, Some):
        return maybe
    if isinstance(maybe, Nothing):
        return Some(default)
    raise TypeError(f"Unexpected Maybe variant: {maybe!r}")
