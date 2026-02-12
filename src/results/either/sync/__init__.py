"""Sync implementations of Either type.

Exports:
    Left: Left variant implementation
    Right: Right variant implementation
"""

from .left import Left
from .right import Right

__all__ = ["Left", "Right"]
