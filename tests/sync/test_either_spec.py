"""Cross-variant Either specification tests.

Tests that verify behavior across Left and Right variants.
Covers spec compliance, type conversions, and combined scenarios.
"""

from typing import Any

import pytest
from typing_extensions import Never

from results import Left, Right
from results.core.either_base import Either


class TestEitherVariantEquivalence:
    """Tests that verify correct either-or semantics."""

    def test_left_right_distinct(self) -> None:
        """Left and Right are distinct variants."""
        left = Left[str, str]("error")
        right = Right[str, str]("success")
        assert left.is_left()
        assert not left.is_right()
        assert right.is_right()
        assert not right.is_left()

    def test_left_and_right_with_same_value_type(self) -> None:
        """Left and Right can both contain same type."""
        left = Left[str, str]("value")
        right = Right[str, str]("value")
        assert left.left() == right.right()
        assert left.unwrap_left() == right.unwrap_right()

    def test_accessor_symmetry_when_opposite_none(self) -> None:
        """Each variant returns None for opposite accessor."""
        left = Left[str, int]("error")
        right = Right[str, int](42)
        assert left.right() is None
        assert right.left() is None


class TestEitherSwapSymmetry:
    """Swap operation creates Left/Right pairs."""

    def test_swap_creates_inverse_pair(self) -> None:
        """Left.swap() creates equivalent Right and vice versa."""
        original_left = Left[str, str]("error")
        swapped = original_left.swap()
        assert swapped.is_right()
        assert swapped.right() == "error"

        original_right = Right[str, int](42)
        swapped2 = original_right.swap()
        assert swapped2.is_left()
        assert swapped2.left() == 42

    def test_double_swap_involution(self) -> None:
        """Double swap returns to original variant."""
        left = Left[str, str]("error")
        right = Right[str, int](42)
        assert left.swap().swap().is_left()
        assert right.swap().swap().is_right()
        assert left.swap().swap().left() == left.left()
        assert right.swap().swap().right() == right.right()


class TestEitherBimap:
    """Bimap applies appropriate function to each variant."""

    def test_bimap_dispatches_correctly(self) -> None:
        """Bimap applies left_op to Left, right_op to Right."""
        left = Left[str, str]("error").bimap(str.upper, lambda x: x * 2)
        right = Right[str, int](42).bimap(str.upper, lambda x: x * 2)
        assert left.left() == "ERROR"
        assert right.right() == 84

    def test_bimap_type_flexibility(self) -> None:
        """Bimap can transform into completely different types."""
        left = Left[list[int], str]([1, 2, 3]).bimap(len, str)
        right = Right[str, list[int]]([1, 2, 3]).bimap(len, str)
        assert left.left() == 3
        assert right.right() == "[1, 2, 3]"

    def test_bimap_with_exceptions(self) -> None:
        """Bimap can transform to/from exceptions."""
        left = Left[str, str]("error").bimap(lambda x: ValueError(x), int)
        assert isinstance(left.left(), ValueError)
        assert "error" in str(left.left())


class TestEitherFold:
    """Fold reduces Either to unified type."""

    def test_fold_both_variants(self) -> None:
        """Fold produces same type from both Left and Right."""
        left = Left[str, str]("error")
        right = Right[str, int](42)
        left_str = left.fold(str.upper, lambda x: str(x))
        right_str = right.fold(str.upper, lambda x: str(x))
        assert isinstance(left_str, str)
        assert isinstance(right_str, str)

    def test_fold_with_custom_logic(self) -> None:
        """Fold applies custom transformation logic to each branch."""
        left = Left[dict[str, str], dict[str, list[int]]](
            {"code": "E001", "msg": "error"}
        )
        right = Right[dict[str, list[int]], dict[str, list[int]]]({"data": [1, 2, 3]})
        left_result = left.fold(
            lambda x: f"Error: {x['msg']}", lambda x: f"Success: {len(x)}"
        )
        right_result = right.fold(
            lambda x: f"Error: {x['msg']}", lambda x: f"Success: {len(x)}"
        )
        assert left_result == "Error: error"
        assert right_result == "Success: 1"

    def test_fold_unifies_error_and_success(self) -> None:
        """Fold can unify error and success into single type."""

        def either_to_message(
            either: Either[str, dict[str, int]],
        ) -> str:
            return either.fold(lambda e: f"Failed: {e}", lambda v: f"Success: {v}")

        assert (
            either_to_message(Left("connection timeout"))
            == "Failed: connection timeout"
        )
        assert either_to_message(Right({"id": 123})) == "Success: {'id': 123}"


class TestEitherAsMonoid:
    """Either in monoid/applicative patterns."""

    def test_left_preserves_through_right_operations(self) -> None:
        """Left propagates unchanged through right-focused operations."""
        result = (
            Left[str, int]("error")
            .map(lambda x: x * 2)
            .and_then(lambda x: Right[str, int](x))
            # Note: or_else on Left executes the alternative, so this becomes Right
            .map(lambda x: x)  # Keep Left unchanged
        )
        assert result.is_left()
        assert result.left() == "error"

    def test_right_preserves_through_left_operations(self) -> None:
        """Right propagates unchanged through left-focused operations."""
        result = (
            Right[str, int](42)
            .map_left(str.upper)
            .and_then_left(lambda x: Left[str, int](x))
            # Note: or_else_left on Right executes the alternative, so this becomes Left
            .map(lambda x: x)  # Keep Right unchanged
        )
        assert result.is_right()
        assert result.right() == 42


class TestEitherConversions:
    """Converting between Either variants and other types."""

    def test_left_unwrap_patterns(self) -> None:
        """Pattern matching on Left variant."""
        either = Left[str, str]("error")
        if either.is_left():
            error = either.left()
            assert error == "error"
        else:
            pytest.fail("Expected Left")

    def test_right_unwrap_patterns(self) -> None:
        """Pattern matching on Right variant."""
        either = Right[str, int](42)
        if either.is_right():
            value = either.right()
            assert value == 42
        else:
            pytest.fail("Expected Right")

    def test_left_unwrap_with_defaults(self) -> None:
        """Safely extract with defaults."""
        left = Left[str, int]("error")
        safe_value = left.unwrap_or(0)
        assert safe_value == 0

    def test_right_unwrap_with_defaults(self) -> None:
        """Safely extract with defaults."""
        right = Right[str, int](42)
        safe_value = right.unwrap_or(0)
        assert safe_value == 42


class TestEitherChainRules:
    """Monadic laws and chain behaviors."""

    def test_left_identity_and_then(self) -> None:
        """Left short-circuits and_then regardless of operation."""
        left = Left[str, int]("error")
        result1 = left.and_then(lambda x: Right[str, int](x * 2))
        result2 = left.and_then(lambda x: Left[str, int]("new error"))
        assert result1.is_left()
        assert result2.is_left()

    def test_right_identity_and_then(self) -> None:
        """Right.and_then executes the operation."""
        right = Right[str, int](42)
        result = right.and_then(lambda x: Right[str, int](x * 2))
        assert result.is_right()
        assert result.right() == 84

    def test_or_else_recovery_chain(self) -> None:
        """or_else chains provide recovery path."""
        result = (
            Left[str, int]("error1")
            .or_else(lambda: Left[str, int]("error2"))
            .or_else(lambda: Right[str, int](42))
        )
        assert result.is_right()
        assert result.right() == 42

    def test_mixed_chain_behavior(self) -> None:
        """Complex chain with mixed operations."""
        result = (
            Right[str, int](10)
            .map(lambda x: x * 2)
            .and_then(
                lambda x: Right[str, int](x + 5)
                if x > 10
                else Left[str, int]("too small")
            )
            .map(lambda x: x * 10)
            .unwrap_or(0)
        )
        assert result == 250  # (10 * 2 + 5) * 10


class TestEitherErrorPropagation:
    """Error propagation patterns."""

    def test_left_stops_chain(self) -> None:
        """Left stops further right-focused operations."""
        result: Either[str, int] = (
            Left[str, int]("initial error")
            .map(lambda x: raise_error(x))
            .and_then(lambda x: raise_error(x))
        )
        assert result.is_left()

    def test_right_continues_chain(self) -> None:
        """Right allows operations to continue."""
        result = (
            Right[str, int](42)
            .map(lambda x: x * 2)
            .map(lambda x: x + 1)
            .map(lambda x: x * 10)
        )
        assert result.is_right()
        assert result.right() == 850

    def test_switch_branches_mid_chain(self) -> None:
        """Operations can switch between branches."""
        # Right to Left
        result1 = Right[str, int](42).and_then(
            lambda x: Left[str, int]("error") if x > 40 else Right[str, int](x)
        )
        assert result1.is_left()

        # Left to Right
        result2 = Left[str, int]("error").or_else(lambda: Right[str, int](42))
        assert result2.is_right()


def raise_error(x: Any) -> Never:
    """Helper function that always raises."""
    raise RuntimeError("Should not be called")
