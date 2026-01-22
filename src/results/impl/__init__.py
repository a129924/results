"""Result type system concrete implementations.

This module contains the synchronous and asynchronous Result implementations.

Submodules:
    sync: Synchronous implementation (Ok, Err)
    async_: Asynchronous implementation (reserved for future use)
"""

from results.impl.sync import Err, Ok

__all__ = [
    "Ok",
    "Err",
]
