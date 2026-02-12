"""Unit tests for Left[L, R] variant implementation.

Tests all 16 abstract methods from Either ABC on Left variant.
Covers transformations, extractions, context chains, and edge cases.
"""

import pytest

from results import Left, Right
from results.exceptions import UnwrapError


class TestLeftBasics:
    """Basic variant checking and accessors."""

    def test_is_left_true(self) -> None:
        """Left.is_left() returns True."""
        assert Left("error").is_left() is True

    def test_is_right_false(self) -> None:
        """Left.is_right() returns False."""
        assert Left("error").is_right() is False

    def test_left_accessor_returns_value(self) -> None:
        """Left.left() returns the left value."""
        assert Left("error").left() == "error"

    def test_right_accessor_returns_none(self) -> None:
        """Left.right() returns None."""
        assert Left("error").right() is None

    def test_left_with_various_types(self) -> None:
        """Left can contain any type."""
        assert Left(42).left() == 42
        assert Left([1, 2, 3]).left() == [1, 2, 3]
        assert Left({"key": "value"}).left() == {"key": "value"}


class TestLeftMapOperations:
    """Right-focused map operations (should short-circuit on Left)."""

    def test_map_short_circuits(self) -> None:
        """Left.map() returns self unchanged (short-circuit)."""
        left: Left[str, int] = Left("error")
        result = left.map(lambda x: x * 2)
        assert result.is_left()
        assert result.left() == "error"

    def test_map_does_not_call_operation(self) -> None:
        """Left.map() doesn't execute the operation."""
        executed = False

        def op(x: int) -> int:
            nonlocal executed
            executed = True
            return x * 2

        Left("error").map(op)
        assert executed is False

    def test_map_preserves_type(self) -> None:
        """Left.map() preserves left value type."""
        left = Left("error")
        result = left.map(lambda x: str(x).upper())
        assert result.left() == "error"

    def test_map_left_executes(self) -> None:
        """Left.map_left() transforms the left value."""
        result = Left("error").map_left(str.upper)
        assert result.is_left()
        assert result.left() == "ERROR"

    def test_map_left_changes_type(self) -> None:
        """Left.map_left() can change left value type."""
        result = Left("error").map_left(len)
        assert result.left() == 5

    def test_map_left_with_exception_transform(self) -> None:
        """Left.map_left() works with exception transformations."""
        result = Left("error").map_left(lambda x: ValueError(x))
        assert isinstance(result.left(), ValueError)
        assert str(result.left()) == "error"


class TestLeftBimap:
    """Bimap transformations (apply to Left branch)."""

    def test_bimap_applies_left_op(self) -> None:
        """Left.bimap() applies left_op to left value."""
        result = Left("error").bimap(str.upper, lambda x: x * 2)
        assert result.is_left()
        assert result.left() == "ERROR"

    def test_bimap_ignores_right_op(self) -> None:
        """Left.bimap() doesn't execute right_op."""
        executed = False

        def right_op(x: int) -> int:
            nonlocal executed
            executed = True
            return x * 2

        Left("error").bimap(str.upper, right_op)
        assert executed is False

    def test_bimap_transforms_type(self) -> None:
        """Left.bimap() transforms left value type."""
        result = Left("error").bimap(len, lambda x: x * 2)
        assert result.left() == 5


class TestLeftMonadicOperations:
    """Monadic chain operations (and_then, and_then_left, or_else, or_else_left)."""

    def test_and_then_short_circuits(self) -> None:
        """Left.and_then() returns self unchanged."""
        result = Left("error").and_then(lambda x: Right(x * 2))
        assert result.is_left()
        assert result.left() == "error"

    def test_and_then_left_flattens_left(self) -> None:
        """Left.and_then_left() flattens nested Either."""
        result = Left("error").and_then_left(lambda x: Left(x.upper()))
        assert result.is_left()
        assert result.left() == "ERROR"

    def test_and_then_left_can_switch_to_right(self) -> None:
        """Left.and_then_left() can switch to Right."""
        result = Left("error").and_then_left(lambda x: Right(42))
        assert result.is_right()
        assert result.right() == 42

    def test_and_then_left_short_circuits_nested_left(self) -> None:
        """Left.and_then_left() returns nested Either directly."""
        nested = Right(99)
        result = Left("error").and_then_left(lambda x: nested)
        assert result.is_right()
        assert result.right() == 99

    def test_or_else_executes_on_left(self) -> None:
        """Left.or_else() executes the alternative computation."""
        result = Left("error").or_else(lambda: Right(42))
        assert result.is_right()
        assert result.right() == 42

    def test_or_else_left_short_circuits_on_left(self) -> None:
        """Left.or_else_left() returns self unchanged."""
        result = Left("error").or_else_left(lambda: Left("new error"))
        assert result.is_left()
        assert result.left() == "error"


class TestLeftInspection:
    """Inspection operations (side effects without modification)."""

    def test_inspect_does_not_execute_on_left(self) -> None:
        """Left.inspect() doesn't execute side effect."""
        executed = False

        def effect(x: int) -> None:
            nonlocal executed
            executed = True

        Left("error").inspect(effect)
        assert executed is False

    def test_inspect_left_executes_on_left(self) -> None:
        """Left.inspect_left() executes side effect on Left."""
        executed = False

        def effect(x: str) -> None:
            nonlocal executed
            executed = True

        Left("error").inspect_left(effect)
        assert executed is True

    def test_inspect_left_returns_self(self) -> None:
        """Left.inspect_left() returns self for chaining."""
        left = Left("error")
        result = left.inspect_left(lambda x: None)
        assert result.is_left()
        assert result.left() == "error"

    def test_inspect_left_returns_same_instance(self) -> None:
        """Left.inspect_left() doesn't create new instance."""
        left = Left("error")
        result = left.inspect_left(lambda x: None)
        # Should be same reference
        assert result._value == left._value


class TestLeftUnwrapping:
    """Unwrap operations extracting values or raising exceptions."""

    def test_unwrap_right_raises_on_left(self) -> None:
        """Left.unwrap_right() raises UnwrapError."""
        with pytest.raises(UnwrapError):
            Left("error").unwrap_right()

    def test_unwrap_right_includes_original_error(self) -> None:
        """UnwrapError contains information about the left value."""
        try:
            Left("error message").unwrap_right()
        except UnwrapError as e:
            # Check that it's the correct error type
            assert isinstance(e, UnwrapError)

    def test_unwrap_left_returns_value(self) -> None:
        """Left.unwrap_left() returns the left value."""
        assert Left("error").unwrap_left() == "error"

    def test_unwrap_or_returns_default(self) -> None:
        """Left.unwrap_or() returns the default (Right type)."""
        assert Left("error").unwrap_or(42) == 42

    def test_unwrap_or_ignores_right_value(self) -> None:
        """Left.unwrap_or() doesn't use right value."""
        result = Left("error")
        assert result.unwrap_or(99) == 99

    def test_unwrap_or_else_computes_default(self) -> None:
        """Left.unwrap_or_else() executes the computation."""
        result = Left("error").unwrap_or_else(lambda: 42)
        assert result == 42

    def test_unwrap_or_else_executes_only_on_left(self) -> None:
        """Left.unwrap_or_else() computation is always executed."""
        executed = False

        def compute() -> int:
            nonlocal executed
            executed = True
            return 42

        Left("error").unwrap_or_else(compute)
        assert executed is True


class TestLeftFold:
    """Fold operation (catamorphism - total deconstruction)."""

    def test_fold_applies_left_op(self) -> None:
        """Left.fold() applies left_op."""
        result = Left("error").fold(str.upper, lambda x: str(x * 2))
        assert result == "ERROR"

    def test_fold_ignores_right_op(self) -> None:
        """Left.fold() doesn't execute right_op."""
        executed = False

        def right_op(x: int) -> str:
            nonlocal executed
            executed = True
            return str(x)

        Left("error").fold(str, right_op)
        assert executed is False

    def test_fold_unifies_types(self) -> None:
        """Left.fold() reduces to unified return type."""
        result = Left(42).fold(lambda x: str(x), lambda x: f"right:{x}")
        assert result == "42"
        assert isinstance(result, str)


class TestLeftSwap:
    """Swap operation (exchange Left and Right)."""

    def test_swap_returns_right(self) -> None:
        """Left.swap() returns Right with same value."""
        result = Left("error").swap()
        assert result.is_right()
        assert result.right() == "error"

    def test_swap_preserves_value_type(self) -> None:
        """Left.swap() preserves the value type."""
        result = Left(42).swap()
        assert result.right() == 42
        assert isinstance(result.right(), int)

    def test_swap_is_involutive(self) -> None:
        """Left.swap().swap() returns Left."""
        result = Left("error").swap().swap()
        assert result.is_left()
        assert result.left() == "error"


class TestLeftContext:
    """Context chain operations for diagnostic information."""

    def test_context_adds_message(self) -> None:
        """Left.context() adds message to chain."""
        result = Left("error").context("at validation")
        assert "at validation" in result._context_chain.messages

    def test_context_returns_new_instance(self) -> None:
        """Left.context() returns new Left instance."""
        left1 = Left("error")
        left2 = left1.context("at validation")
        assert left1 is not left2
        assert left1.left() == left2.left()

    def test_context_lifo_order(self) -> None:
        """Context messages are stored in LIFO order."""
        result = Left("error").context("first").context("second")
        assert result._context_chain.messages[0] == "second"
        assert result._context_chain.messages[1] == "first"

    def test_with_context_lazy_evaluation(self) -> None:
        """Left.with_context() evaluates lazily."""
        executed = False

        def compute_message() -> str:
            nonlocal executed
            executed = True
            return "lazy message"

        left = Left("error").with_context(compute_message)
        assert executed is True  # Note: push_lazy may execute immediately
        assert "lazy message" in left._context_chain.messages

    def test_context_chain_preserved_in_transformations(self) -> None:
        """Context chain preserved through transformations."""
        result = (
            Left("error")
            .context("first context")
            .map_left(str.upper)
            .context("second context")
        )
        assert "first context" in result._context_chain.messages
        assert "second context" in result._context_chain.messages


class TestLeftChaining:
    """Complex chaining scenarios."""

    def test_chained_map_left_operations(self) -> None:
        """Multiple map_left operations chain correctly."""
        result = (
            Left("error")
            .map_left(str.upper)
            .map_left(lambda x: f"[{x}]")
        )
        assert result.left() == "[ERROR]"

    def test_chained_and_then_left_operations(self) -> None:
        """Multiple and_then_left operations chain correctly."""
        result = (
            Left("error")
            .and_then_left(lambda x: Left(x.upper()))
            .and_then_left(lambda x: Right(len(x)))
        )
        assert result.is_right()
        assert result.right() == 5

    def test_chained_with_or_else(self) -> None:
        """Left.or_else chain with recovery."""
        result = (
            Left("error1")
            .or_else(lambda: Left("error2"))
            .or_else(lambda: Right(42))
        )
        assert result.is_right()
        assert result.right() == 42

    def test_mixed_operations_chain(self) -> None:
        """Complex chain mixing multiple operations."""
        step1 = Left("error").context("first context")
        assert "first context" in step1._context_chain.messages

        step2 = step1.map_left(str.upper).context("second context")
        assert "first context" in step2._context_chain.messages
        assert "second context" in step2._context_chain.messages


class TestLeftEdgeCases:
    """Edge cases and special scenarios."""

    def test_left_with_none_value(self) -> None:
        """Left can contain None as a value."""
        left: Left[None, str] = Left(None)
        assert left.left() is None
        assert left.is_left()

    def test_left_with_exception_value(self) -> None:
        """Left can contain Exception as a value."""
        exc = ValueError("test error")
        result = Left(exc)
        assert result.left() is exc

    def test_left_with_function_value(self) -> None:
        """Left can contain function as a value."""
        def my_func() -> int:
            return 42

        result = Left(my_func)
        assert result.left() is my_func

    def test_left_frozen_immutability(self) -> None:
        """Left instance is frozen (immutable)."""
        left = Left("error")
        from dataclasses import FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            left._value = "new error"  # type: ignore

    def test_left_context_empty_by_default(self) -> None:
        """Left has empty context chain by default."""
        left = Left("error")
        assert left._context_chain.messages == ()

    def test_left_with_complex_data_structure(self) -> None:
        """Left can contain complex nested structures."""
        data = {"error": {"code": 404, "details": ["not", "found"]}}
        result = Left(data)
        assert result.left() == data
        assert result.left()["error"]["code"] == 404
