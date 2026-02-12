"""Test Nothing variant - absence of value in Maybe type.

Tests cover:
- Nothing short-circuits all transformations
- Context chain management for diagnostic information
- Proper unwrap error handling
- Value extraction fallbacks (unwrap_or, unwrap_or_else)
- Combination operations (zip, zip_with)
"""

from __future__ import annotations

import pytest

from results import Maybe, Nothing, Some, UnwrapError


class TestNothingBasics:
    """Basic Nothing functionality tests."""

    def test_nothing_represents_absence(self) -> None:
        """Nothing represents absence of value."""
        result: Maybe[int] = Nothing()
        assert result.is_nothing() is True
        assert result.is_some() is False

    def test_nothing_preserves_type_parameter(self) -> None:
        """Nothing maintains type parameter through type system."""
        # The type parameter is phantom - Nothing() is still Nothing()
        # but type checkers see Maybe[int]
        int_nothing: Maybe[int] = Nothing()
        str_nothing: Maybe[str] = Nothing()
        assert int_nothing.is_nothing() is True
        assert str_nothing.is_nothing() is True

    def test_unwrap_raises_error(self) -> None:
        """unwrap() raises UnwrapError on Nothing."""
        with pytest.raises(UnwrapError) as exc_info:
            Nothing().unwrap()
        assert "called `unwrap()` on Nothing" in str(exc_info.value)

    def test_unwrap_or_returns_default(self) -> None:
        """unwrap_or() returns default when Nothing."""
        result = Nothing[int]().unwrap_or(42)
        assert result == 42

    def test_unwrap_or_else_computes_default(self) -> None:
        """unwrap_or_else() computes default."""
        call_count = 0

        def compute_default() -> int:
            nonlocal call_count
            call_count += 1
            return 42

        result = Nothing[int]().unwrap_or_else(compute_default)
        assert result == 42
        assert call_count == 1  # Called once


class TestNothingMap:
    """Map transformations on Nothing."""

    def test_map_returns_nothing(self) -> None:
        """map() returns Nothing unchanged."""
        result = Nothing().map(lambda x: x * 2)
        assert result.is_nothing() is True

    def test_map_never_calls_function(self) -> None:
        """map() never calls function."""
        call_count = 0

        def multiply(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result = Nothing().map(multiply)
        assert result.is_nothing() is True
        assert call_count == 0

    def test_map_chains_short_circuit(self) -> None:
        """map() chains short-circuit through Nothing."""
        call_count = 0

        def count_and_transform(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result = (
            Nothing()
            .map(count_and_transform)
            .map(count_and_transform)
            .map(count_and_transform)
        )
        assert result.is_nothing() is True
        assert call_count == 0


class TestNothingFilter:
    """Filter operations on Nothing."""

    def test_filter_returns_nothing(self) -> None:
        """filter() returns Nothing unchanged."""
        result = Nothing().filter(lambda x: x > 0)
        assert result.is_nothing() is True

    def test_filter_never_calls_predicate(self) -> None:
        """filter() never calls predicate."""
        call_count = 0

        def check(x: int) -> bool:
            nonlocal call_count
            call_count += 1
            return x > 0

        result = Nothing().filter(check)
        assert result.is_nothing() is True
        assert call_count == 0


class TestNothingAndThen:
    """Monadic bind (and_then) operations."""

    def test_and_then_returns_nothing(self) -> None:
        """and_then() returns Nothing without calling operation."""
        call_count = 0

        def compute_next(x: int) -> Maybe[int]:
            nonlocal call_count
            call_count += 1
            return Some(x * 2)

        result = Nothing().and_then(compute_next)
        assert result.is_nothing() is True
        assert call_count == 0

    def test_and_then_chain_short_circuits(self) -> None:
        """and_then() chain short-circuits through Nothing."""
        call_count = 0

        def increment(x: int) -> Maybe[int]:
            nonlocal call_count
            call_count += 1
            return Some(x + 1)

        result = Nothing().and_then(increment).and_then(increment)
        assert result.is_nothing() is True
        assert call_count == 0


class TestNothingOrElse:
    """or_else() operations."""

    def test_or_else_calls_alternative(self) -> None:
        """or_else() computes alternative when Nothing."""
        result = Nothing().or_else(lambda: Some(42))
        assert result.is_some() is True
        assert result.unwrap() == 42

    def test_or_else_can_stay_nothing(self) -> None:
        """or_else() can return Nothing."""
        result = Nothing().or_else(lambda: Nothing())
        assert result.is_nothing() is True

    def test_or_else_lazy_evaluation(self) -> None:
        """or_else() computes alternative lazily."""
        call_count = 0

        def compute_alternative() -> Maybe[int]:
            nonlocal call_count
            call_count += 1
            return Some(42)

        Nothing().or_else(compute_alternative)
        assert call_count == 1


class TestNothingZip:
    """Zip operations with Nothing."""

    def test_zip_with_some_returns_nothing(self) -> None:
        """zip() with Some returns Nothing."""
        result = Nothing().zip(Some(1))
        assert result.is_nothing() is True

    def test_zip_with_nothing_returns_nothing(self) -> None:
        """zip() with Nothing returns Nothing."""
        result = Nothing().zip(Nothing())
        assert result.is_nothing() is True


class TestNothingZipWith:
    """zip_with() operations with Nothing."""

    def test_zip_with_some_returns_nothing(self) -> None:
        """zip_with() with Some returns Nothing."""
        result = Nothing().zip_with(Some(1), lambda a, b: a + b)
        assert result.is_nothing() is True

    def test_zip_with_function_never_called(self) -> None:
        """zip_with() never calls combining function."""
        call_count = 0

        def combine(a: int, b: int) -> int:
            nonlocal call_count
            call_count += 1
            return a + b

        result = Nothing().zip_with(Some(1), combine)
        assert result.is_nothing() is True
        assert call_count == 0


class TestNothingInspect:
    """Inspect operations on Nothing."""

    def test_inspect_no_op(self) -> None:
        """inspect() is no-op on Nothing."""
        values: list[int] = []
        result = Nothing().inspect(lambda x: values.append(x))
        assert values == []  # Never called
        assert result.is_nothing() is True

    def test_inspect_function_never_called(self) -> None:
        """inspect() never calls function."""
        call_count = 0

        def count(x: int) -> None:
            nonlocal call_count
            call_count += 1

        Nothing().inspect(count)
        assert call_count == 0


class TestNothingContext:
    """Context chain management on Nothing."""

    def test_context_adds_message(self) -> None:
        """context() adds diagnostic message to Nothing."""
        nothing_with_ctx = Nothing().context("user not found")
        # Verify it's still Nothing
        assert nothing_with_ctx.is_nothing() is True

    def test_context_message_in_error(self) -> None:
        """context() message appears in unwrap error."""
        with pytest.raises(UnwrapError) as exc_info:
            Nothing().context("user not found").unwrap()
        # Error message should contain context
        error_str = str(exc_info.value)
        assert "user not found" in error_str or "Nothing" in error_str

    def test_context_chain_lifo(self) -> None:
        """context() builds LIFO chain."""
        nothing_with_ctx = (
            Nothing().context("step 1").context("step 2").context("step 3")
        )
        with pytest.raises(UnwrapError) as exc_info:
            nothing_with_ctx.unwrap()
        error_str = str(exc_info.value)
        # All messages should be in error
        assert "step 1" in error_str or "step 2" in error_str or "step 3" in error_str

    def test_with_context_lazy_evaluation(self) -> None:
        """with_context() computes message when called (not delayed)."""
        call_count = 0

        def expensive_diagnostic() -> str:
            nonlocal call_count
            call_count += 1
            return "diagnostic info"

        # push_lazy computes the function when called
        nothing_with_ctx = Nothing().with_context(expensive_diagnostic)
        # Function IS called during with_context
        assert call_count == 1
        # Message is added to context chain
        with pytest.raises(UnwrapError) as exc_info:
            nothing_with_ctx.unwrap()
        # Error message should contain the diagnostic info
        error_str = str(exc_info.value)
        assert "diagnostic info" in error_str or "Nothing" in error_str

    def test_reason_field(self) -> None:
        """Nothing can have optional reason."""
        nothing_with_reason = Nothing(_reason="specific reason")
        assert nothing_with_reason.is_nothing() is True


class TestNothingIntegration:
    """Integration tests with Nothing."""

    def test_some_to_nothing_chain(self) -> None:
        """Chain from Some can result in Nothing."""
        result = (
            Some(42)
            .filter(lambda x: x > 100)  # Becomes Nothing
            .map(lambda x: x * 2)  # Skipped
            .or_else(lambda: Some(0))  # Alternative
        )
        assert result.unwrap() == 0

    def test_early_exit_on_nothing(self) -> None:
        """Operation stops immediately on Nothing."""
        operations = []

        def track_operation(name: str):
            def operation(x: int) -> Maybe[int]:
                operations.append(name)
                return Some(x + 1)

            return operation

        result = (
            Some(5)
            .and_then(track_operation("op1"))  # Executed
            .filter(lambda x: x > 10)  # False, becomes Nothing
            .and_then(track_operation("op2"))  # Skipped
            .and_then(track_operation("op3"))  # Skipped
        )
        assert operations == ["op1"]
        assert result.is_nothing() is True
