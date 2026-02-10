"""Context chain management for error tracking and diagnostics.

This module provides unified context chain handling across all monad types
(Result, Maybe, Either), implementing the LIFO (Last-In-First-Out) stack
pattern for tracking error context.

Enables consistent error messages with context information across the entire
monad ecosystem.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing_extensions import Never


@dataclass(frozen=True)
class ContextChain:
    """Immutable LIFO (Last-In-First-Out) context stack for error tracking.

    Provides a functional way to build and manage error context information
    without mutation. Each operation returns a new ContextChain instance.

    Example:
        >>> chain = ContextChain()
        >>> chain_with_ctx = chain.push("validating user age")
        >>> chain_with_ctx = chain_with_ctx.push("processing user data")
        >>> chain_with_ctx.messages
        ('processing user data', 'validating user age')  # LIFO order
    """

    messages: tuple[str, ...] = ()

    def push(self, msg: str) -> ContextChain:
        """Add message to head of stack (LIFO).

        Args:
            msg: Context message to add

        Returns:
            New ContextChain with message prepended

        Example:
            >>> chain = ContextChain().push("step 1").push("step 2")
            >>> chain.messages
            ('step 2', 'step 1')
        """
        return ContextChain((msg, *self.messages))

    def push_lazy(self, f: Callable[[], str]) -> ContextChain:
        """Add lazily-evaluated message to stack.

        Message is only computed when push_lazy is called, not when
        returned. Useful for expensive context calculations.

        Args:
            f: Callable that returns context message

        Returns:
            New ContextChain with computed message prepended

        Example:
            >>> chain = ContextChain()
            >>> chain = chain.push_lazy(lambda: f"timestamp: {time.time()}")
        """
        return self.push(f())

    def format_lifo(self) -> str:
        """Format messages in LIFO order for display.

        Returns:
            Formatted string with messages, one per line with indentation.
            Empty string if no messages.

        Example:
            >>> chain = ContextChain().push("step 1").push("step 2")
            >>> print(chain.format_lifo())
              step 2
              step 1
        """
        return "\n".join(f"  {msg}" for msg in self.messages)

    def is_empty(self) -> bool:
        """Check if context chain is empty.

        Returns:
            True if no messages, False otherwise

        Example:
            >>> ContextChain().is_empty()
            True
            >>> ContextChain().push("msg").is_empty()
            False
        """
        return len(self.messages) == 0

    def __len__(self) -> int:
        """Get number of messages in context chain.

        Returns:
            Count of messages

        Example:
            >>> len(ContextChain().push("a").push("b"))
            2
        """
        return len(self.messages)


def unwrap_with_context(error: Any, context_chain: ContextChain) -> Never:
    """Unified unwrap logic for all monad types.

    Raises exception with context chain for error tracking. Handles both
    Exception types (re-raised) and non-Exception types (wrapped in UnwrapError).

    Args:
        error: The error value to unwrap
        context_chain: ContextChain for context information

    Raises:
        Never: Always raises (return type annotation only)

    Raises (Implementation):
        UnwrapError: For non-Exception error types with context
        Exception: Re-raised Exception types with context

    Example:
        >>> try:
        ...     unwrap_with_context(ValueError("bad"), ContextChain().push("validating"))
        ... except UnwrapError as e:
        ...     print(e)  # Shows context and error
    """
    # Import here to avoid circular dependency
    from results.exceptions import UnwrapError

    # Format context chain
    context_msg = ""
    if not context_chain.is_empty():
        context_msg = context_chain.format_lifo()

    # Handle Exception types: re-raise with context
    if isinstance(error, Exception):
        if context_msg:
            # Re-raise with context information
            msg = f"{context_msg}\n{str(error)}"
            raise UnwrapError(msg, original_error=error) from error
        else:
            raise error

    # Handle non-Exception types: wrap in UnwrapError
    if context_msg:
        msg = f"{context_msg}\n{str(error)}"
    else:
        msg = str(error)
    raise UnwrapError(msg, original_error=error) from None
