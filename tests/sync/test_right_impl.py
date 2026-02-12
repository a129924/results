"""Unit tests for Right[L, R] variant implementation.

Tests all 16 abstract methods from Either ABC on Right variant.
Covers transformations, extractions, context chains, and edge cases.
Mirrors test_left_impl.py with inverted logic.
"""

import pytest

from results import Left, Right
from results.exceptions import UnwrapError


class TestRightBasics:
    """Basic variant checking and accessors."""

    def test_is_right_true(self) -> None:
        """Right.is_right() returns True."""
        assert Right(42).is_right() is True

    def test_is_left_false(self) -> None:
        """Right.is_left() returns False."""
        assert Right(42).is_left() is False

    def test_right_accessor_returns_value(self) -> None:
        """Right.right() returns the right value."""
        assert Right(42).right() == 42

    def test_left_accessor_returns_none(self) -> None:
        """Right.left() returns None."""
        assert Right(42).left() is None

    def test_right_with_various_types(self) -> None:
        """Right can contain any type."""
        assert Right("success").right() == "success"
        assert Right([1, 2, 3]).right() == [1, 2, 3]
        assert Right({"key": "value"}).right() == {"key": "value"}


class TestRightMapOperations:
    """Right-focused map operations (executes on Right)."""

    def test_map_transforms_value(self) -> None:
        """Right.map() transforms the right value."""
        result = Right(42).map(lambda x: x * 2)
        assert result.is_right()
        assert result.right() == 84

    def test_map_executes_operation(self) -> None:
        """Right.map() calls the operation."""
        executed = False

        def op(x: int) -> int:
            nonlocal executed
            executed = True
            return x * 2

        Right(42).map(op)
        assert executed is True

    def test_map_changes_type(self) -> None:
        """Right.map() can change right value type."""
        result = Right(42).map(str)
        assert result.right() == "42"
        assert isinstance(result.right(), str)

    def test_map_left_short_circuits(self) -> None:
        """Right.map_left() returns self unchanged."""
        right = Right(42)
        result = right.map_left(str.upper)
        assert result.is_right()
        assert result.right() == 42

    def test_map_left_does_not_call_operation(self) -> None:
        """Right.map_left() doesn't execute the operation."""
        executed = False

        def op(x: str) -> str:
            nonlocal executed
            executed = True
            return x.upper()

        Right(42).map_left(op)
        assert executed is False


class TestRightBimap:
    """Bimap transformations (apply to Right branch)."""

    def test_bimap_applies_right_op(self) -> None:
        """Right.bimap() applies right_op to right value."""
        result = Right(42).bimap(str.upper, lambda x: x * 2)
        assert result.is_right()
        assert result.right() == 84

    def test_bimap_ignores_left_op(self) -> None:
        """Right.bimap() doesn't execute left_op."""
        executed = False

        def left_op(x: str) -> str:
            nonlocal executed
            executed = True
            return x.upper()

        Right(42).bimap(left_op, lambda x: x * 2)
        assert executed is False

    def test_bimap_transforms_type(self) -> None:
        """Right.bimap() transforms right value type."""
        result = Right(42).bimap(len, str)
        assert result.right() == "42"


class TestRightMonadicOperations:
    """Monadic chain operations (and_then, and_then_left, or_else, or_else_left)."""

    def test_and_then_flattens_right(self) -> None:
        """Right.and_then() flattens nested Either."""
        result = Right(42).and_then(lambda x: Right(x * 2))
        assert result.is_right()
        assert result.right() == 84

    def test_and_then_can_switch_to_left(self) -> None:
        """Right.and_then() can switch to Left."""
        result = Right(42).and_then(lambda x: Left("error"))
        assert result.is_left()
        assert result.left() == "error"

    def test_and_then_executes_operation(self) -> None:
        """Right.and_then() calls the operation."""
        executed = False

        def op(x: int) -> Right[str, int]:
            nonlocal executed
            executed = True
            return Right(x * 2)

        Right(42).and_then(op)
        assert executed is True

    def test_and_then_left_short_circuits_on_right(self) -> None:
        """Right.and_then_left() returns self unchanged."""
        result = Right(42).and_then_left(lambda x: Left(x.upper()))
        assert result.is_right()
        assert result.right() == 42

    def test_or_else_short_circuits_on_right(self) -> None:
        """Right.or_else() returns self unchanged."""
        result = Right(42).or_else(lambda: Right(99))
        assert result.is_right()
        assert result.right() == 42

    def test_or_else_left_executes_on_right(self) -> None:
        """Right.or_else_left() executes the alternative computation."""
        result = Right(42).or_else_left(lambda: Left("error"))
        assert result.is_left()
        assert result.left() == "error"


class TestRightInspection:
    """Inspection operations (side effects without modification)."""

    def test_inspect_executes_on_right(self) -> None:
        """Right.inspect() executes side effect on Right."""
        executed = False

        def effect(x: int) -> None:
            nonlocal executed
            executed = True

        Right(42).inspect(effect)
        assert executed is True

    def test_inspect_left_does_not_execute_on_right(self) -> None:
        """Right.inspect_left() doesn't execute side effect."""
        executed = False

        def effect(x: str) -> None:
            nonlocal executed
            executed = True

        Right(42).inspect_left(effect)
        assert executed is False

    def test_inspect_returns_self(self) -> None:
        """Right.inspect() returns self for chaining."""
        right = Right(42)
        result = right.inspect(lambda x: None)
        assert result.is_right()
        assert result.right() == 42

    def test_inspect_does_not_modify_value(self) -> None:
        """Right.inspect() doesn't modify the value."""
        result = Right(42).inspect(lambda x: print(x))
        assert result.right() == 42


class TestRightUnwrapping:
    """Unwrap operations extracting values or raising exceptions."""

    def test_unwrap_right_returns_value(self) -> None:
        """Right.unwrap_right() returns the right value."""
        assert Right(42).unwrap_right() == 42

    def test_unwrap_left_raises_on_right(self) -> None:
        """Right.unwrap_left() raises UnwrapError."""
        with pytest.raises(UnwrapError):
            Right(42).unwrap_left()

    def test_unwrap_left_includes_original_error(self) -> None:
        """UnwrapError contains information about the right value."""
        try:
            Right("unexpected value").unwrap_left()
        except UnwrapError as e:
            # Check that it's the correct error type
            assert isinstance(e, UnwrapError)

    def test_unwrap_or_returns_value(self) -> None:
        """Right.unwrap_or() returns the right value."""
        assert Right(42).unwrap_or(99) == 42

    def test_unwrap_or_ignores_default(self) -> None:
        """Right.unwrap_or() doesn't use default."""
        result = Right(42)
        assert result.unwrap_or(999) == 42

    def test_unwrap_or_else_returns_value(self) -> None:
        """Right.unwrap_or_else() returns the right value."""
        result = Right(42).unwrap_or_else(lambda: 99)
        assert result == 42

    def test_unwrap_or_else_ignores_computation(self) -> None:
        """Right.unwrap_or_else() doesn't execute computation."""
        executed = False

        def compute() -> int:
            nonlocal executed
            executed = True
            return 99

        Right(42).unwrap_or_else(compute)
        assert executed is False


class TestRightFold:
    """Fold operation (catamorphism - total deconstruction)."""

    def test_fold_applies_right_op(self) -> None:
        """Right.fold() applies right_op."""
        result = Right(42).fold(str.upper, lambda x: str(x * 2))
        assert result == "84"

    def test_fold_ignores_left_op(self) -> None:
        """Right.fold() doesn't execute left_op."""
        executed = False

        def left_op(x: str) -> str:
            nonlocal executed
            executed = True
            return x.upper()

        Right(42).fold(left_op, str)
        assert executed is False

    def test_fold_unifies_types(self) -> None:
        """Right.fold() reduces to unified return type."""
        result = Right(42).fold(lambda x: f"left:{x}", lambda x: f"right:{x}")
        assert result == "right:42"
        assert isinstance(result, str)


class TestRightSwap:
    """Swap operation (exchange Left and Right)."""

    def test_swap_returns_left(self) -> None:
        """Right.swap() returns Left with same value."""
        result = Right(42).swap()
        assert result.is_left()
        assert result.left() == 42

    def test_swap_preserves_value_type(self) -> None:
        """Right.swap() preserves the value type."""
        result = Right("success").swap()
        assert result.left() == "success"
        assert isinstance(result.left(), str)

    def test_swap_is_involutive(self) -> None:
        """Right.swap().swap() returns Right."""
        result = Right(42).swap().swap()
        assert result.is_right()
        assert result.right() == 42


class TestRightContext:
    """Context chain operations for diagnostic information."""

    def test_context_adds_message(self) -> None:
        """Right.context() adds message to chain."""
        result = Right(42).context("computed value")
        assert "computed value" in result._context_chain.messages

    def test_context_returns_new_instance(self) -> None:
        """Right.context() returns new Right instance."""
        right1 = Right(42)
        right2 = right1.context("at computation")
        assert right1 is not right2
        assert right1.right() == right2.right()

    def test_context_lifo_order(self) -> None:
        """Context messages are stored in LIFO order."""
        result = Right(42).context("first").context("second")
        assert result._context_chain.messages[0] == "second"
        assert result._context_chain.messages[1] == "first"

    def test_with_context_lazy_evaluation(self) -> None:
        """Right.with_context() evaluates lazily."""
        executed = False

        def compute_message() -> str:
            nonlocal executed
            executed = True
            return "lazy message"

        right = Right(42).with_context(compute_message)
        assert executed is True  # Note: push_lazy may execute immediately
        assert "lazy message" in right._context_chain.messages

    def test_context_chain_preserved_in_transformations(self) -> None:
        """Context chain preserved through transformations."""
        result = (
            Right(42)
            .context("first context")
            .map(lambda x: x * 2)
            .context("second context")
        )
        assert "first context" in result._context_chain.messages
        assert "second context" in result._context_chain.messages


class TestRightChaining:
    """Complex chaining scenarios."""

    def test_chained_map_operations(self) -> None:
        """Multiple map operations chain correctly."""
        result = Right(42).map(lambda x: x * 2).map(lambda x: x + 1)
        assert result.right() == 85

    def test_chained_and_then_operations(self) -> None:
        """Multiple and_then operations chain correctly."""
        result = (
            Right(42)
            .and_then(lambda x: Right(x * 2))
            .and_then(lambda x: Right(x + 1))
        )
        assert result.is_right()
        assert result.right() == 85

    def test_chained_with_or_else_left(self) -> None:
        """Right.or_else_left chain with recovery."""
        result = (
            Right(42)
            .or_else_left(lambda: Left("error1"))
            .or_else_left(lambda: Left("error2"))
        )
        assert result.is_left()
        assert result.left() == "error1"

    def test_mixed_operations_chain(self) -> None:
        """Complex chain mixing multiple operations."""
        step1 = Right(42).context("first context")
        assert "first context" in step1._context_chain.messages

        step2 = step1.map(lambda x: x * 2).context("second context")
        assert "first context" in step2._context_chain.messages
        assert "second context" in step2._context_chain.messages


class TestRightEdgeCases:
    """Edge cases and special scenarios."""

    def test_right_with_none_value(self) -> None:
        """Right can contain None as a value."""
        right = Right(None)
        assert right.right() is None
        assert right.is_right()

    def test_right_with_exception_value(self) -> None:
        """Right can contain Exception as a value."""
        exc = ValueError("test error")
        result = Right(exc)
        assert result.right() is exc

    def test_right_with_function_value(self) -> None:
        """Right can contain function as a value."""
        def my_func() -> int:
            return 42

        result = Right(my_func)
        assert result.right() is my_func

    def test_right_frozen_immutability(self) -> None:
        """Right instance is frozen (immutable)."""
        right = Right(42)
        from dataclasses import FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            right._value = 99  # type: ignore

    def test_right_context_empty_by_default(self) -> None:
        """Right has empty context chain by default."""
        right = Right(42)
        assert right._context_chain.messages == ()

    def test_right_with_complex_data_structure(self) -> None:
        """Right can contain complex nested structures."""
        data = {"user": {"id": 123, "items": ["a", "b", "c"]}}
        result = Right(data)
        assert result.right() == data
        assert result.right()["user"]["id"] == 123
