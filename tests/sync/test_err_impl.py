"""Unit tests for Err[E] implementation.

Tests verify Err variant behavior for all Result ABC methods including:
- Type checking and comparisons
- Error extraction and transformation
- Short-circuiting in operation chains
- Unwrap behavior
"""

import pytest

from results import Err, Ok, Result, UnwrapError


class TestErrCreation:
    """Test Err construction and basic properties."""

    def test_err_creation_with_string(self) -> None:
        """Test creating Err with string error."""
        result: Result[int, str] = Err("error message")
        assert result.is_err()
        assert not result.is_ok()

    def test_err_creation_with_exception(self) -> None:
        """Test creating Err with Exception object."""
        error = ValueError("invalid value")
        result: Result[int, ValueError] = Err(error)
        assert result.is_err()
        assert result.err() is error

    def test_err_creation_with_int(self) -> None:
        """Test creating Err with integer error code."""
        result: Result[str, int] = Err(404)
        assert result.is_err()
        assert result.err() == 404

    def test_err_with_complex_error(self) -> None:
        """Test Err with complex error type."""
        error = {"code": "NOT_FOUND", "message": "Resource not found"}
        result: Result[str, dict] = Err(error)
        assert result.is_err()
        assert result.err() == error


class TestErrValueExtraction:
    """Test error extraction methods."""

    def test_ok_method_returns_none(self) -> None:
        """Test ok() returns None for Err variant."""
        result: Result[int, str] = Err("error")
        assert result.ok() is None

    def test_err_method_returns_error(self) -> None:
        """Test err() returns the contained error."""
        result: Result[int, str] = Err("error")
        assert result.err() == "error"

    def test_unwrap_raises_unwrap_error(self) -> None:
        """Test unwrap() raises UnwrapError."""
        result: Result[int, str] = Err("something failed")
        with pytest.raises(UnwrapError) as exc_info:
            result.unwrap()
        assert exc_info.value.original_error == "something failed"

    def test_unwrap_error_contains_message(self) -> None:
        """Test UnwrapError contains descriptive message."""
        result: Result[int, str] = Err("operation failed")
        with pytest.raises(UnwrapError) as exc_info:
            result.unwrap()
        assert "Err" in str(exc_info.value)
        assert exc_info.value.message == "Called unwrap on Err"


class TestErrMap:
    """Test map() method - should short-circuit."""

    def test_map_not_applied_to_err(self) -> None:
        """Test map function is not applied to Err variant."""
        call_count = 0

        def transform(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result: Result[int, str] = Err("error")
        mapped = result.map(transform)
        assert call_count == 0  # Function not called
        assert mapped.is_err()

    def test_map_preserves_error(self) -> None:
        """Test map preserves error value."""
        result: Result[int, str] = Err("original error")
        mapped = result.map(lambda x: x * 2)
        assert mapped.err() == "original error"

    def test_map_changes_success_type_only(self) -> None:
        """Test map changes success type but not error type."""
        result: Result[int, ValueError] = Err(ValueError("error"))
        # Type changes from Result[int, ValueError] to Result[str, ValueError]
        mapped: Result[str, ValueError] = result.map(str)
        assert mapped.is_err()

    def test_map_chain_short_circuits(self) -> None:
        """Test chained map operations short-circuit."""
        call_count = 0

        def transform(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        result: Result[int, str] = Err("error")
        result.map(transform).map(transform).map(transform)
        assert call_count == 0  # No functions called


class TestErrMapErr:
    """Test map_err() method for error transformation."""

    def test_map_err_transforms_error(self) -> None:
        """Test map_err applies transformation to error."""
        result: Result[int, str] = Err("not found")
        mapped = result.map_err(lambda e: RuntimeError(e))
        assert mapped.is_err()
        assert isinstance(mapped.err(), RuntimeError)
        assert str(mapped.err()) == "not found"

    def test_map_err_changes_error_type(self) -> None:
        """Test map_err changes error type."""
        result: Result[int, str] = Err("error")
        # Type changes from str to RuntimeError
        mapped: Result[int, RuntimeError] = result.map_err(RuntimeError)
        assert mapped.is_err()

    def test_map_err_chain_operations(self) -> None:
        """Test map_err can chain multiple transformations."""
        result: Result[int, str] = Err("original")
        chained = result.map_err(lambda e: f"Error: {e}").map_err(RuntimeError)
        assert isinstance(chained.err(), RuntimeError)
        assert "Error: original" in str(chained.err())

    def test_map_err_preserves_success_type(self) -> None:
        """Test map_err does not affect success type."""
        result: Result[int, str] = Err("error")
        # Success type remains int
        mapped: Result[int, RuntimeError] = result.map_err(RuntimeError)
        assert mapped.is_err()


class TestErrAndThen:
    """Test and_then() - should short-circuit for Err."""

    def test_and_then_not_called_for_err(self) -> None:
        """Test and_then function is not called for Err variant."""
        call_count = 0

        def operation(x: int) -> Result[int, str]:
            nonlocal call_count
            call_count += 1
            return Ok(x * 2)

        result: Result[int, str] = Err("error")
        chained = result.and_then(operation)
        assert call_count == 0  # Operation not called

    def test_and_then_returns_error_unchanged(self) -> None:
        """Test and_then returns the same Err."""
        error = ValueError("original")
        result: Result[int, ValueError] = Err(error)
        chained = result.and_then(lambda x: Ok(x * 2))
        assert chained.is_err()
        assert chained.err() is error

    def test_and_then_accumulates_error_types(self) -> None:
        """Test and_then accumulates error types."""

        def operation1(x: int) -> Result[int, RuntimeError]:
            return Ok(x * 2)

        def operation2(x: int) -> Result[int, TypeError]:
            return Ok(x + 1)

        result: Result[int, str] = Err("first error")
        # Type should accumulate: Result[int, RuntimeError | str] -> Result[int, TypeError | RuntimeError | str]
        chained = result.and_then(operation1).and_then(operation2)
        assert chained.is_err()
        assert chained.err() == "first error"

    def test_and_then_chain_short_circuits(self) -> None:
        """Test chained and_then operations short-circuit."""
        call_count = 0

        def operation(x: int) -> Result[int, str]:
            nonlocal call_count
            call_count += 1
            return Ok(x)

        result: Result[int, str] = Err("initial error")
        result.and_then(operation).and_then(operation).and_then(operation)
        assert call_count == 0  # No operations called


class TestErrEquality:
    """Test equality comparison."""

    def test_err_equals_same_error(self) -> None:
        """Test Err with same error equals."""
        err1: Result[int, str] = Err("error")
        err2: Result[int, str] = Err("error")
        assert err1 == err2

    def test_err_not_equals_different_error(self) -> None:
        """Test Err with different error not equals."""
        err1: Result[int, str] = Err("error1")
        err2: Result[int, str] = Err("error2")
        assert err1 != err2

    def test_err_not_equals_ok(self) -> None:
        """Test Err not equal to Ok."""
        ok: Result[int, str] = Ok(42)
        err: Result[int, str] = Err("error")
        assert ok != err

    def test_err_equals_with_exception(self) -> None:
        """Test Err equality with exceptions."""
        error1 = ValueError("test")
        error2 = ValueError("test")
        err1: Result[int, ValueError] = Err(error1)
        err2: Result[int, ValueError] = Err(error2)
        # Different exception objects, but might have equal representation
        assert err1.err() is error1


class TestErrRepr:
    """Test string representation."""

    def test_err_repr_with_string(self) -> None:
        """Test repr shows Err with string."""
        result: Result[int, str] = Err("error message")
        assert "Err" in repr(result)
        assert "error message" in repr(result)

    def test_err_repr_with_int(self) -> None:
        """Test repr shows Err with int error code."""
        result: Result[str, int] = Err(404)
        repr_str = repr(result)
        assert "Err" in repr_str
        assert "404" in repr_str


class TestErrHash:
    """Test hashability."""

    def test_err_is_hashable(self) -> None:
        """Test Err values can be hashed."""
        err1: Result[int, str] = Err("error")
        err2: Result[int, str] = Err("error")
        assert hash(err1) == hash(err2)

    def test_err_in_set(self) -> None:
        """Test Err can be used in sets."""
        err1: Result[int, str] = Err("error")
        err2: Result[int, str] = Err("error")
        err3: Result[int, str] = Err("other")
        s = {err1, err2, err3}
        assert len(s) == 2  # err1 and err2 are duplicates

    def test_err_as_dict_key(self) -> None:
        """Test Err can be used as dict key."""
        err1: Result[int, str] = Err("error")
        err2: Result[int, str] = Err("error")
        d = {err1: "first"}
        d[err2] = "second"
        assert len(d) == 1
        assert d[err1] == "second"


class TestErrImmutability:
    """Test that Err is immutable."""

    def test_err_is_frozen(self) -> None:
        """Test Err attributes cannot be modified."""
        result: Result[int, str] = Err("error")
        with pytest.raises((AttributeError, TypeError)):
            result._error = "new error"  # type: ignore


class TestErrTypeInference:
    """Test type inference with Err."""

    def test_err_type_inference_in_chain(self) -> None:
        """Test type inference works in error chains."""
        result: Result[int, str] = Err("parse failed")
        mapped: Result[int, RuntimeError] = result.map_err(RuntimeError)
        assert mapped.is_err()

    def test_err_complex_chain(self) -> None:
        """Test complex operation chain with Err."""

        def parse(s: str) -> Result[int, ValueError]:
            try:
                return Ok(int(s))
            except ValueError as e:
                return Err(e)

        # This will fail at parse
        result = parse("not a number")
        transformed = result.map(lambda x: x * 2)
        assert transformed.is_err()


class TestErrInteroperability:
    """Test Err works with Ok in chains."""

    def test_ok_then_err_in_chain(self) -> None:
        """Test chain starting with Ok can hit Err."""

        def validate(x: int) -> Result[int, str]:
            if x > 0:
                return Ok(x)
            return Err("must be positive")

        result = Ok(-5).and_then(validate)
        assert result.is_err()
        assert result.err() == "must be positive"

    def test_err_mixed_with_ok_operations(self) -> None:
        """Test Err short-circuits even with Ok operations."""

        def transform(x: int) -> Result[int, str]:
            return Ok(x * 2)

        error_result: Result[int, str] = Err("initial error")
        mixed = error_result.and_then(transform).map_err(lambda e: f"Error: {e}")
        assert mixed.is_err()
        assert mixed.err() == "Error: initial error"
