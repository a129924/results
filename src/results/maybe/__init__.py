"""Maybe monad - type-safe handling of optional values.

The Maybe type represents an optional value:
- Some[T]: Present value of type T
- Nothing: Absent value (expected case, not an error)

Unlike Result[T, E] which distinguishes success from failure,
Maybe only tracks presence/absence.

Example:
    >>> from results import Some, Nothing
    >>> result: Maybe[int] = Some(42)
    >>> result.map(lambda x: x * 2).unwrap_or(0)
    84

    >>> nothing: Maybe[str] = Nothing()
    >>> nothing.map(lambda x: x.upper()).unwrap_or("default")
    "default"
"""

from __future__ import annotations

from .sync.maybe import Nothing, Some

__all__ = [
    "Some",
    "Nothing",
]
