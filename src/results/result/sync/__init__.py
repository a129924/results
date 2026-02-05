"""Result sync implementation - Ok and Err variants.

This module implements the synchronous Result type and its variants.

Exported:
    Ok: Success variant
    Err: Failure variant
"""

from results.result.sync.err import Err
from results.result.sync.ok import Ok

__all__ = ["Ok", "Err"]
