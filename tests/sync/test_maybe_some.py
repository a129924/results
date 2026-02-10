"""Test Some variant - presence of value in Maybe type.

Tests cover:
- Value preservation through transformations
- Method chaining (map, filter, and_then)
- Combination operations (zip, zip_with)
- Value extraction (unwrap, unwrap_or)
- Inspection without unwrapping
"""

from __future__ import annotations

import pytest

from results import Maybe, Nothing, Some


class TestSomeBasics:
    """Basic Some functionality tests."""

    def test_some_wraps_value(self) -> None:
        """Some wraps and preserves values."""
        result: Maybe[int] = Some(42)
        assert result.is_some() is True
        assert result.is_nothing() is False

    def test_some_preserves_any_type(self) -> None:
        """Some can wrap any type."""
        int_some: Maybe[int] = Some(42)
        str_some: Maybe[str] = Some("hello")
        list_some: Maybe[list[int]] = Some([1, 2, 3])

        assert int_some.unwrap() == 42
        assert str_some.unwrap() == "hello"
        assert list_some.unwrap() == [1, 2, 3]

    def test_unwrap_returns_value(self) -> None:
        """unwrap() extracts the wrapped value."""
        result = Some(42)
        assert result.unwrap() == 42

    def test_unwrap_or_returns_value(self) -> None:
        """unwrap_or() returns value when Some."""
        result = Some(42)
        assert result.unwrap_or(0) == 42

    def test_unwrap_or_else_returns_value(self) -> None:
        """unwrap_or_else() returns value without computing default."""
        call_count = 0

        def compute_default() -> int:
            nonlocal call_count
            call_count += 1
            return 0

        result = Some(42)
        assert result.unwrap_or_else(compute_default) == 42
        assert call_count == 0  # Never called


class TestSomeMap:
    """Map transformations on Some."""

    def test_map_transforms_value(self) -> None:
        """map() applies function to value."""
        result = Some(42).map(lambda x: x * 2)
        assert result.unwrap() == 84

    def test_map_chains_multiple(self) -> None:
        """map() can be chained multiple times."""
        result = Some(42).map(lambda x: x * 2).map(lambda x: x + 1).map(str)
        assert result.unwrap() == "85"

    def test_map_preserves_type(self) -> None:
        """map() returns Some with new type."""
        result: Maybe[str] = Some(42).map(str)
        assert isinstance(result, Some)
        assert result.unwrap() == "42"

    def test_map_with_exception_propagates(self) -> None:
        """map() lets exceptions propagate."""
        with pytest.raises(ValueError):
            Some(42).map(lambda x: (_ for _ in ()).throw(ValueError("test")))


class TestSomeFilter:
    """Filter operations on Some."""

    def test_filter_true_keeps_some(self) -> None:
        """filter() with true predicate returns Some."""
        result = Some(42).filter(lambda x: x > 0)
        assert result.is_some() is True
        assert result.unwrap() == 42

    def test_filter_false_returns_nothing(self) -> None:
        """filter() with false predicate returns Nothing."""
        result = Some(42).filter(lambda x: x > 100)
        assert result.is_nothing() is True

    def test_filter_chain_multiple(self) -> None:
        """filter() can be chained."""
        result = (
            Some(42)
            .filter(lambda x: x > 0)
            .filter(lambda x: x < 100)
            .filter(lambda x: x % 2 == 0)
        )
        assert result.is_some() is True

    def test_filter_chain_early_nothing(self) -> None:
        """filter() chain stops at first Nothing."""
        result = (
            Some(42)
            .filter(lambda x: x > 100)  # False, returns Nothing
            .filter(lambda x: x > 0)  # Skipped
        )
        assert result.is_nothing() is True


class TestSomeAndThen:
    """Monadic bind (and_then) operations."""

    def test_and_then_with_some(self) -> None:
        """and_then() flattens Some returning operation."""
        result = Some(42).and_then(lambda x: Some(x * 2))
        assert result.unwrap() == 84

    def test_and_then_with_nothing(self) -> None:
        """and_then() returns Nothing from operation."""
        result = Some(42).and_then(lambda x: Nothing())
        assert result.is_nothing() is True

    def test_and_then_chains(self) -> None:
        """and_then() can be chained."""
        result = (
            Some(42).and_then(lambda x: Some(x * 2)).and_then(lambda x: Some(x + 1))
        )
        assert result.unwrap() == 85

    def test_and_then_short_circuits(self) -> None:
        """and_then() short-circuits on Nothing."""
        call_count = 0

        def check_and_increment(x: int) -> Maybe[int]:
            nonlocal call_count
            call_count += 1
            if x >= 43:  # Second call: 43 >= 43, return Nothing
                return Nothing()
            return Some(x + 1)

        result = Some(42).and_then(check_and_increment).and_then(check_and_increment)
        assert result.is_nothing() is True
        assert call_count == 2  # First call returns Some(43), second returns Nothing


class TestSomeOrElse:
    """or_else() operations."""

    def test_or_else_ignores_alternative(self) -> None:
        """or_else() returns Some unchanged."""
        call_count = 0

        def get_alternative() -> Maybe[int]:
            nonlocal call_count
            call_count += 1
            return Some(0)

        result = Some(42).or_else(get_alternative)
        assert result.unwrap() == 42
        assert call_count == 0  # Never called


class TestSomeZip:
    """Zip operations combining two Maybes."""

    def test_zip_both_some(self) -> None:
        """zip() with two Some returns Some of tuple."""
        result = Some(1).zip(Some(2))
        assert result.is_some() is True
        assert result.unwrap() == (1, 2)

    def test_zip_with_nothing(self) -> None:
        """zip() with Nothing returns Nothing."""
        result = Some(1).zip(Nothing())
        assert result.is_nothing() is True

    def test_zip_different_types(self) -> None:
        """zip() works with different types."""
        result = Some(42).zip(Some("hello"))
        assert result.unwrap() == (42, "hello")


class TestSomeZipWith:
    """zip_with() operations with combining function."""

    def test_zip_with_both_some(self) -> None:
        """zip_with() combines values with function."""
        result = Some(40).zip_with(Some(2), lambda a, b: a + b)
        assert result.unwrap() == 42

    def test_zip_with_nothing(self) -> None:
        """zip_with() with Nothing returns Nothing."""
        result = Some(40).zip_with(Nothing(), lambda a, b: a + b)
        assert result.is_nothing() is True

    def test_zip_with_multiple_types(self) -> None:
        """zip_with() combines different types."""
        result = Some("Hello").zip_with(Some(" World"), lambda a, b: a + b)
        assert result.unwrap() == "Hello World"


class TestSomeInspect:
    """Inspect operations for debugging without unwrapping."""

    def test_inspect_calls_function(self) -> None:
        """inspect() calls function with value."""
        values: list[int] = []
        result = Some(42).inspect(lambda x: values.append(x))
        assert values == [42]
        assert result.unwrap() == 42  # Returns self

    def test_inspect_chains(self) -> None:
        """inspect() returns self for chaining."""
        values: list[int] = []
        result = (
            Some(42)
            .map(lambda x: x * 2)
            .inspect(lambda x: values.append(x))
            .map(lambda x: x + 1)
        )
        assert values == [84]
        assert result.unwrap() == 85


class TestSomeContext:
    """Context operations on Some (no-op)."""

    def test_context_no_op(self) -> None:
        """context() is no-op on Some."""
        result = Some(42).context("some message")
        assert result.unwrap() == 42

    def test_with_context_no_op(self) -> None:
        """with_context() is no-op on Some."""
        result = Some(42).with_context(lambda: "expensive computation")
        assert result.unwrap() == 42
