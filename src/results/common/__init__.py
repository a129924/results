"""Shared utilities and protocols for the monad ecosystem.

This module provides common types and protocols used across all monad
implementations (Result, Maybe, Either, etc.).

Exports:
    - ContextAware: Protocol for types supporting context stacking
    - Unwrappable: Protocol for types supporting unwrap operations
    - Inspectable: Protocol for types supporting inspection
    - Mappable: Protocol for types supporting transformations
    - Chainable: Protocol for types supporting monadic chaining
    - AsyncMappable: Protocol for async map operations
"""

from .protocols import (
    AsyncMappable,
    Chainable,
    ContextAware,
    Inspectable,
    Mappable,
    Unwrappable,
)

__all__ = [
    "ContextAware",
    "Unwrappable",
    "Inspectable",
    "Mappable",
    "Chainable",
    "AsyncMappable",
]
