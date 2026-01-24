"""Tests for v0.2.0 context chain functionality (LIFO stack).

This module tests the context chain feature added in v0.2.0, including:
- context() method for eager context push
- with_context() method for lazy context push
- _context_chain field (LIFO stack)
- Immutability of context chain
- Integration with unwrap() display

All tests follow v0.1.0 backward compatibility requirements.
"""

import pytest

from results import Err, Ok
from results.exceptions import UnwrapError


class TestContextChain:
    """Test context chain LIFO stack implementation."""

    def test_single_context(self) -> None:
        """Test adding a single context message to an Err result."""
        result = Err("error")
        result = result.context("step A")

        assert result.is_err()
        assert result._context_chain == ("step A",)
        assert result.err() == "error"

    def test_multiple_context_lifo(self) -> None:
        """Test LIFO (Last In, First Out) stacking of context messages.

        When A -> B -> C are called in order, the chain should be
        (C, B, A) with newest (C) at index 0.
        """
        result = Err("error")
        result = result.context("A")
        assert result._context_chain == ("A",)

        result = result.context("B")
        assert result._context_chain == ("B", "A")

        result = result.context("C")
        assert result._context_chain == ("C", "B", "A")

    def test_context_preserves_error(self) -> None:
        """Test that context() preserves the original error value."""
        error = ValueError("original error")
        result = Err(error)
        result = result.context("processing step")

        assert result.err() is error
        assert str(result.err()) == "original error"

    def test_context_immutable(self) -> None:
        """Test that context() returns new Err, doesn't mutate original."""
        r1 = Err("error").context("A")
        assert r1._context_chain == ("A",)

        r2 = r1.context("B")
        assert r2._context_chain == ("B", "A")

        # r1 should not be modified
        assert r1._context_chain == ("A",)

    def test_with_context_returns_result_unchanged(self) -> None:
        """Test that with_context() returns the result unchanged."""
        result = Err("error").with_context(lambda: "new context")

        # with_context() pushes context to chain
        assert result.is_err()
        assert result.err() == "error"
        assert result._context_chain == ("new context",)

    def test_with_context_lazy_evaluation(self) -> None:
        """Test that with_context() evaluates the callable.

        The context callable is evaluated and the context message is added
        to the error chain.
        """
        call_count = 0

        def context_provider() -> str:
            nonlocal call_count
            call_count += 1
            return f"evaluated {call_count} times"

        result = Err("test error").with_context(context_provider)

        # Context callable should have been called once
        assert call_count == 1
        assert result._context_chain == ("evaluated 1 times",)

        # Calling again should evaluate again
        result2 = result.with_context(context_provider)
        assert call_count == 2
        assert result2._context_chain == ("evaluated 2 times", "evaluated 1 times")

    def test_context_with_none_value(self) -> None:
        """Test context() works with None as error value."""
        result = Err(None)
        result = result.context("step")

        assert result.is_err()
        assert result.err() is None
        assert result._context_chain == ("step",)

    def test_unwrap_shows_context_chain(self) -> None:
        """Test that unwrap() displays context chain with Exception types."""
        result = (
            Err(ValueError("initial error"))
            .context("step 1")
            .context("step 2")
            .context("step 3")
        )

        try:
            result.unwrap()
        except ValueError as e:
            msg = str(e)
            # Should contain all contexts in LIFO order (3, 2, 1)
            assert "step 3" in msg
            assert "step 2" in msg
            assert "step 1" in msg
            # Most recent should appear first
            assert msg.index("step 3") < msg.index("step 2")
            assert msg.index("step 2") < msg.index("step 1")

    def test_empty_context_chain_on_new_err(self) -> None:
        """Test that new Err results have empty context chain."""
        result = Err("error")
        assert result._context_chain == ()

    def test_context_chain_through_map_err(self) -> None:
        """Test that context chain is preserved through map_err()."""
        result = (
            Err("original error")
            .context("step 1")
            .map_err(lambda e: ValueError(f"wrapped: {e}"))
        )

        assert result.is_err()
        assert isinstance(result.err(), ValueError)
        assert result._context_chain == ("step 1",)

    def test_context_chain_preserved_through_and_then_error(self) -> None:
        """Test context preserved when and_then short-circuits on error."""
        result = (
            Err("error").context("step A").and_then(lambda _: Ok("should not happen"))
        )

        assert result.is_err()
        assert result.err() == "error"
        assert result._context_chain == ("step A",)

    def test_context_on_ok_returns_ok_unchanged(self) -> None:
        """Test that context() on Ok result is a no-op (passthrough)."""
        result = Ok(42)
        result_with_context = result.context("this should be ignored")

        assert result_with_context.is_ok()
        assert result_with_context.ok() == 42

    def test_with_context_on_ok_returns_ok_unchanged(self) -> None:
        """Test that with_context() on Ok result is a no-op (passthrough)."""
        result = Ok(42)
        result_with_context = result.with_context(lambda: "this should be ignored")

        assert result_with_context.is_ok()
        assert result_with_context.ok() == 42

    def test_multiple_contexts_immutability(self) -> None:
        """Test immutability when building context chain."""
        chain = []

        r1 = Err("e1")
        chain.append(r1._context_chain)

        r2 = r1.context("A")
        chain.append(r2._context_chain)

        r3 = r2.context("B")
        chain.append(r3._context_chain)

        # Each should be independent
        assert chain[0] == ()
        assert chain[1] == ("A",)
        assert chain[2] == ("B", "A")

    def test_context_chain_with_chained_operations(self) -> None:
        """Test context chain through complex chained operations."""
        result = (
            Err("base error")
            .context("operation")
            .map_err(lambda e: f"transformed: {e}")
        )

        assert result.is_err()
        assert "transformed:" in result.err()
        assert result._context_chain == ("operation",)

    def test_context_with_special_characters(self) -> None:
        """Test context() with special characters in message."""
        msg = "Failed at line 42\n\tFile: /path/to/file.py\n\tError: <type Error>"
        result = Err("error").context(msg)

        assert result._context_chain == (msg,)
        assert result.err() == "error"

    def test_backward_compatibility_v0_1_operations(self) -> None:
        """Test that v0.1.0 operations work unchanged with context."""
        err = Err("error").context("debug info")

        # v0.1.0 operations should still work
        assert err.is_err()
        assert err.is_ok() is False
        assert err.err() == "error"
        assert err.ok() is None

        with pytest.raises(UnwrapError):
            err.unwrap()

    def test_context_empty_string(self) -> None:
        """Test context() with empty string."""
        result = Err("error").context("")
        assert result._context_chain == ("",)

    def test_large_context_chain(self) -> None:
        """Test with a large number of context messages (stress test)."""
        result = Err("error")
        for i in range(100):
            result = result.context(f"context-{i}")

        # Should maintain LIFO order
        assert result._context_chain[0] == "context-99"  # Most recent
        assert result._context_chain[1] == "context-98"
        assert result._context_chain[-1] == "context-0"  # Oldest
        assert len(result._context_chain) == 100
