"""Single AsyncResult awaitable wrapper for Result[T, E].

This module implements AsyncResult as a unified awaitable container
that wraps Awaitable[Result[T, E]] and provides a complete async/await API:
- map_async, map_err_async, and_then_async
- inspect_async, inspect_err_async
- unwrap_async, resolve
- context management (LIFO)

Implementation uses an operation queue pattern to accumulate transformations
and evaluate them atomically on await/resolve, reducing branching complexity.
"""

__all__ = ["AsyncResult"]
