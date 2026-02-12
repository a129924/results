"""Sync implementations of Either type.

Exports:
    Left: Left variant implementation
    Right: Right variant implementation
    flatten: Flatten nested Either
    swap: Swap Left and Right
    from_ok_err: Convert Result to Either
    partition: Partition sequence by variant
    sequence: Collect Either sequence
"""

from .helpers import flatten, from_ok_err, partition, sequence, swap
from .left import Left
from .right import Right

__all__ = [
    "Left",
    "Right",
    "flatten",
    "swap",
    "from_ok_err",
    "partition",
    "sequence",
]
