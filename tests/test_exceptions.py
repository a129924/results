"""Unit tests for exception hierarchy.

This test module validates that the exception classes are correctly defined
and usable for error handling in the Result framework.
"""

from dataclasses import FrozenInstanceError, dataclass, is_dataclass

import pytest

from results.exceptions import BaseError, ResultError, UnwrapError


@dataclass(frozen=True)
class CustomError(BaseError):
    """Custom error implementation for testing BaseError."""

    error_code: int
    error_message: str

    def __str__(self) -> str:
        return f"CustomError({self.error_code}): {self.error_message}"


class TestResultError:
    """Tests for ResultError base exception."""

    def test_result_error_is_exception(self) -> None:
        """ResultError should inherit from Exception."""
        assert issubclass(ResultError, Exception)

    def test_result_error_can_be_raised(self) -> None:
        """ResultError should be raisable."""
        with pytest.raises(ResultError):
            raise ResultError("Test error")

    def test_result_error_message(self) -> None:
        """ResultError should preserve error message."""
        msg = "Test error message"
        with pytest.raises(ResultError, match=msg):
            raise ResultError(msg)


class TestUnwrapError:
    """Tests for UnwrapError exception."""

    def test_unwrap_error_is_result_error(self) -> None:
        """UnwrapError should inherit from ResultError."""
        assert issubclass(UnwrapError, ResultError)

    def test_unwrap_error_requires_original_error(self) -> None:
        """UnwrapError should require original_error argument."""
        error = ValueError("original")
        unwrap_err = UnwrapError("Called unwrap on Err", error)
        assert unwrap_err.message == "Called unwrap on Err"
        assert unwrap_err.original_error is error

    def test_unwrap_error_can_be_raised(self) -> None:
        """UnwrapError should be raisable."""
        original = ValueError("original")
        with pytest.raises(UnwrapError):
            raise UnwrapError("Called unwrap on Err", original)

    def test_unwrap_error_stores_context(self) -> None:
        """UnwrapError should preserve both message and original error."""
        original = RuntimeError("root cause")
        msg = "Called unwrap on Err"
        unwrap_err = UnwrapError(msg, original)
        assert str(unwrap_err) == msg
        assert unwrap_err.original_error is original


class TestBaseError:
    """Tests for BaseError optional template."""

    def test_base_error_is_exception(self) -> None:
        """BaseError should inherit from Exception."""
        assert issubclass(BaseError, Exception)

    def test_base_error_is_dataclass(self) -> None:
        """BaseError should be a frozen dataclass."""
        assert is_dataclass(BaseError)

    def test_base_error_is_frozen(self) -> None:
        """BaseError instances should be frozen."""
        error = CustomError(error_code=123, error_message="test")
        with pytest.raises(FrozenInstanceError):  # FrozenInstanceError
            error.error_code = 456  # type: ignore

    def test_base_error_requires_str_implementation(self) -> None:
        """BaseError subclasses must implement __str__."""

        # Create a subclass without __str__ - should not be directly instantiable
        # because __str__ is abstract
        class IncompleteError(BaseError):
            value: int

        # This will fail because __str__ is abstract and not implemented
        with pytest.raises(TypeError):
            IncompleteError(value=42)  # type: ignore

    def test_custom_error_implements_str(self) -> None:
        """Custom error implementation should implement __str__."""
        error = CustomError(error_code=123, error_message="test")
        assert str(error) == "CustomError(123): test"

    def test_base_error_initializes_exception_args(self) -> None:
        """BaseError.__post_init__ should initialize Exception.args."""
        error = CustomError(error_code=123, error_message="test")
        # Exception.args should be set for logging compatibility
        # BaseError uses astuple to init args
        assert len(error.args) > 0

    def test_base_error_can_be_raised(self) -> None:
        """Custom error should be raisable."""
        with pytest.raises(CustomError):
            raise CustomError(error_code=123, error_message="test")

    def test_base_error_preserves_error_info(self) -> None:
        """Custom error should preserve all fields."""
        error = CustomError(error_code=456, error_message="critical")
        assert error.error_code == 456
        assert error.error_message == "critical"

    def test_multiple_base_error_implementations(self) -> None:
        """Multiple BaseError implementations should work independently."""

        @dataclass(frozen=True)
        class ErrorTypeA(BaseError):
            code: str

            def __str__(self) -> str:
                return f"TypeA[{self.code}]"

        @dataclass(frozen=True)
        class ErrorTypeB(BaseError):
            count: int

            def __str__(self) -> str:
                return f"TypeB[{self.count}]"

        err_a = ErrorTypeA(code="A001")
        err_b = ErrorTypeB(count=42)

        assert str(err_a) == "TypeA[A001]"
        assert str(err_b) == "TypeB[42]"
        assert isinstance(err_a, BaseError)
        assert isinstance(err_b, BaseError)

    def test_base_error_is_abc_with_abstract_method(self) -> None:
        """BaseError should be an ABC with abstract __str__."""
        # Check that BaseError.__str__ is abstract
        assert hasattr(BaseError.__str__, "__isabstractmethod__")
        assert BaseError.__str__.__isabstractmethod__ is True
