"""Unit tests for Ok[T] implementation.

Tests verify Ok variant behavior for all Result ABC methods including:
- Type checking and comparisons
- Value extraction and transformation
- Method chaining with and_then
- Error handling
"""

import pytest

from results import Err, Ok, Result


class TestOkCreation:
    """Test Ok construction and basic properties."""

    def test_ok_creation_with_int(self) -> None:
        """Test creating Ok with integer value."""
        result: Result[int, str] = Ok(42)
        assert result.is_ok()
        assert not result.is_err()

    def test_ok_creation_with_string(self) -> None:
        """Test creating Ok with string value."""
        result: Result[str, int] = Ok("hello")
        assert result.is_ok()

    def test_ok_creation_with_none(self) -> None:
        """Test creating Ok with None value."""
        result: Result[None, str] = Ok(None)
        assert result.is_ok()
        assert result.ok() is None

    def test_ok_with_complex_type(self) -> None:
        """Test Ok with complex nested type."""
        data = {"key": [1, 2, 3]}
        result: Result[dict, str] = Ok(data)
        assert result.is_ok()
        assert result.ok() == data


class TestOkValueExtraction:
    """Test value extraction methods."""

    def test_ok_method_returns_value(self) -> None:
        """Test ok() returns the contained value."""
        result: Result[int, str] = Ok(42)
        assert result.ok() == 42

    def test_err_method_returns_none(self) -> None:
        """Test err() returns None for Ok variant."""
        result: Result[int, str] = Ok(42)
        assert result.err() is None

    def test_unwrap_returns_value(self) -> None:
        """Test unwrap() returns value without raising."""
        result: Result[int, str] = Ok(42)
        assert result.unwrap() == 42

    def test_unwrap_with_string(self) -> None:
        """Test unwrap() with string value."""
        result: Result[str, int] = Ok("hello")
        assert result.unwrap() == "hello"


class TestOkMap:
    """Test map() method for value transformation."""

    def test_map_with_identity(self) -> None:
        """Test map with identity function."""
        result: Result[int, str] = Ok(42)
        mapped = result.map(lambda x: x)
        assert mapped.ok() == 42

    def test_map_with_transformation(self) -> None:
        """Test map applies transformation function."""
        result: Result[int, str] = Ok(5)
        doubled = result.map(lambda x: x * 2)
        assert doubled.ok() == 10

    def test_map_with_type_change(self) -> None:
        """Test map can change value type."""
        result: Result[str, int] = Ok("hello")
        mapped = result.map(len)
        assert mapped.ok() == 5

    def test_map_chains_operations(self) -> None:
        """Test map can be chained."""
        result: Result[int, str] = Ok(5)
        chained = result.map(lambda x: x * 2).map(lambda x: x + 1)
        assert chained.ok() == 11

    def test_map_propagates_exception(self) -> None:
        """Test map propagates exceptions from function."""
        result: Result[int, str] = Ok(5)
        with pytest.raises(ZeroDivisionError):
            result.map(lambda x: 1 / (x - 5))

    def test_map_preserves_error_type(self) -> None:
        """Test map preserves the error type parameter."""
        result: Result[int, ValueError] = Ok(42)
        mapped: Result[int, ValueError] = result.map(lambda x: x * 2)
        assert mapped.ok() == 84


class TestOkMapErr:
    """Test map_err() method for error transformation."""

    def test_map_err_not_applied_to_ok(self) -> None:
        """Test map_err does not transform Ok values."""
        result: Result[int, str] = Ok(42)
        mapped = result.map_err(lambda e: f"Error: {e}")
        assert mapped.ok() == 42

    def test_map_err_chains_with_map(self) -> None:
        """Test map_err can chain with map operations."""
        result: Result[int, ValueError] = Ok(42)
        chained = result.map(lambda x: x * 2).map_err(RuntimeError)
        assert chained.ok() == 84

    def test_map_err_type_changes(self) -> None:
        """Test map_err changes error type."""
        result: Result[int, str] = Ok(42)
        # Type changes from str to RuntimeError
        mapped: Result[int, RuntimeError] = result.map_err(RuntimeError)
        assert mapped.ok() == 42


class TestOkAndThen:
    """Test and_then() for operation chaining."""

    def test_and_then_with_ok_result(self) -> None:
        """Test and_then chains with Ok-returning function."""

        def double_if_positive(x: int) -> Result[int, str]:
            if x > 0:
                return Ok(x * 2)
            return Err("not positive")

        result: Result[int, str] = Ok(5)
        chained = result.and_then(double_if_positive)
        assert chained.ok() == 10

    def test_and_then_with_err_result(self) -> None:
        """Test and_then chains to Err when function returns Err."""

        def divide(x: int) -> Result[int, str]:
            if x == 0:
                return Err("division by zero")
            return Ok(100 // x)

        result: Result[int, str] = Ok(0)
        chained = result.and_then(divide)
        assert chained.is_err()
        assert chained.err() == "division by zero"

    def test_and_then_accumulates_error_types(self) -> None:
        """Test and_then accumulates error types in union."""

        def op1(x: int) -> Result[int, ValueError]:
            return Ok(x * 2)

        def op2(x: int) -> Result[int, RuntimeError]:
            return Ok(x + 1)

        result: Result[int, str] = Ok(5)
        chained = result.and_then(op1).and_then(op2)
        # Type should be Result[int, RuntimeError | str] (or equivalent)
        assert chained.ok() == 11

    def test_and_then_short_circuits_on_error(self) -> None:
        """Test and_then returns Err result without further chaining."""

        def returns_error(x: int) -> Result[int, str]:
            return Err("first operation failed")

        result = Ok(5).and_then(returns_error)
        # Result is Err, subsequent and_then would short-circuit
        assert result.is_err()
        assert result.err() == "first operation failed"


class TestOkEquality:
    """Test equality comparison."""

    def test_ok_equals_same_value(self) -> None:
        """Test Ok with same value equals."""
        ok1: Result[int, str] = Ok(42)
        ok2: Result[int, str] = Ok(42)
        assert ok1 == ok2

    def test_ok_not_equals_different_value(self) -> None:
        """Test Ok with different value not equals."""
        ok1: Result[int, str] = Ok(42)
        ok2: Result[int, str] = Ok(43)
        assert ok1 != ok2

    def test_ok_not_equals_err(self) -> None:
        """Test Ok not equal to Err."""
        ok: Result[int, str] = Ok(42)
        err: Result[int, str] = Err("error")
        assert ok != err

    def test_ok_with_string_equals(self) -> None:
        """Test Ok equality with strings."""
        ok1: Result[str, int] = Ok("hello")
        ok2: Result[str, int] = Ok("hello")
        assert ok1 == ok2


class TestOkRepr:
    """Test string representation."""

    def test_ok_repr_with_int(self) -> None:
        """Test repr shows Ok with int value."""
        result: Result[int, str] = Ok(42)
        assert "Ok" in repr(result)
        assert "42" in repr(result)

    def test_ok_repr_with_string(self) -> None:
        """Test repr shows Ok with string value."""
        result: Result[str, int] = Ok("hello")
        repr_str = repr(result)
        assert "Ok" in repr_str
        assert "hello" in repr_str


class TestOkHash:
    """Test hashability."""

    def test_ok_is_hashable(self) -> None:
        """Test Ok values can be hashed."""
        result1: Result[int, str] = Ok(42)
        result2: Result[int, str] = Ok(42)
        # Should be hashable and equal hashes for equal values
        assert hash(result1) == hash(result2)

    def test_ok_in_set(self) -> None:
        """Test Ok can be used in sets."""
        ok1: Result[int, str] = Ok(42)
        ok2: Result[int, str] = Ok(42)
        ok3: Result[int, str] = Ok(43)
        s = {ok1, ok2, ok3}
        assert len(s) == 2  # ok1 and ok2 are duplicates

    def test_ok_as_dict_key(self) -> None:
        """Test Ok can be used as dict key."""
        ok1: Result[int, str] = Ok(42)
        ok2: Result[int, str] = Ok(42)
        d = {ok1: "first"}
        d[ok2] = "second"
        assert len(d) == 1
        assert d[ok1] == "second"


class TestOkImmutability:
    """Test that Ok is immutable."""

    def test_ok_is_frozen(self) -> None:
        """Test Ok attributes cannot be modified."""
        result: Result[int, str] = Ok(42)
        with pytest.raises((AttributeError, TypeError)):
            result._value = 100  # type: ignore


class TestOkTypeInference:
    """Test type inference with Ok."""

    def test_ok_type_preserved_in_map(self) -> None:
        """Test type is preserved through map operations."""
        # This test mainly verifies the type checking works at type-check time
        result: Result[int, str] = Ok(42)
        mapped: Result[str, str] = result.map(str)
        assert mapped.ok() == "42"

    def test_ok_complex_chain(self) -> None:
        """Test complex operation chain maintains types."""

        def parse(s: str) -> Result[int, ValueError]:
            try:
                return Ok(int(s))
            except ValueError as e:
                return Err(e)

        def validate(x: int) -> Result[int, RuntimeError]:
            if x >= 0:
                return Ok(x)
            return Err(RuntimeError("negative"))

        result = parse("42").and_then(validate).map(lambda x: x * 2)
        assert result.ok() == 84
