"""Result 類型系統的同步實現。

此模組提供了同步版本的 Ok 和 Err 實現。
"""

from .ok import Ok
from .err import Err

__all__ = [
    "Ok",
    "Err",
]
