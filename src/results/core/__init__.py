"""Result 類型系統的核心契約層。

此模組定義了 Result 類型的抽象基類（ABC）和型別變數。
所有具體實現都必須遵循此層定義的契約。
"""

from .base import Result
from .types import E, T

__all__ = [
    "Result",
    "T",
    "E",
]
