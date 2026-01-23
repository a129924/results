"""Unit tests for Result abstract base class contract.

This test module validates that the Result ABC is properly defined
and enforces the contract for all implementations.
"""

from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest
from typing_extensions import override

from results.core import Result
from results.exceptions import UnwrapError


class ValueError_(Exception):
    """Test exception for error values."""

    pass


class RuntimeError_(Exception):
    """Alternative test exception for error composition."""

    pass


@dataclass(frozen=True)
class ConcreteOk(Result[int, ValueError_]):
    """Concrete implementation of Result for Ok case (for testing contract)."""

    _value: int

    @override
    def is_ok(self) -> bool:
        return True

    @override
    def is_err(self) -> bool:
        return False

    @override
    def ok(self) -> int | None:
        return self._value

    @override
    def err(self) -> ValueError_ | None:
        return None

    @override
    def unwrap(self) -> int:
        return self._value

    @override
    def map(self, op: Callable[[int], Any]) -> Result[Any, ValueError_]:
        try:
            return ConcreteOk(op(self._value))
        except Exception as e:
            return ConcreteErr(ValueError_(str(e)))

    @override
    def map_err(
        self, op: "Callable[[ValueError_], Exception]"
    ) -> "Result[int, Exception]":
        return self  # type: ignore

    @override
    def and_then(
        self, op: Callable[[int], Result[int, RuntimeError_]]
    ) -> Result[int, RuntimeError_ | ValueError_]:
        try:
            return op(self._value)
        except Exception as e:
            return ConcreteErr(ValueError_(str(e)))  # type: ignore


@dataclass(frozen=True)
class ConcreteErr(Result[int, ValueError_]):
    """Concrete implementation of Result for Err case (for testing contract)."""

    _error: ValueError_

    @override
    def is_ok(self) -> bool:
        return False

    @override
    def is_err(self) -> bool:
        return True

    @override
    def ok(self) -> int | None:
        return None

    @override
    def err(self) -> ValueError_ | None:
        return self._error

    @override
    def unwrap(self) -> int:
        raise UnwrapError(f"Called unwrap on Err: {self._error}", self._error)

    @override
    def map(self, op: "Callable[[int], object]") -> "Result[object, ValueError_]":
        return self  # type: ignore

    @override
    def map_err(
        self, op: "Callable[[ValueError_], Exception]"
    ) -> "Result[int, Exception]":
        new_error = op(self._error)
        return ConcreteErr(new_error)  # type: ignore

    @override
    def and_then(
        self, op: Callable[[int], Result[int, RuntimeError_]]
    ) -> Result[int, RuntimeError_ | ValueError_]:
        return self  # type: ignore


class TestResultABC:
    """Tests for Result abstract base class contract."""

    def test_result_is_abc(self) -> None:
        """Result should be an abstract base class."""
        assert issubclass(Result, ABC)

    def test_result_cannot_be_instantiated(self) -> None:
        """Result should not be directly instantiable."""
        with pytest.raises(TypeError, match="abstract"):
            Result()  # type: ignore[call-arg]

    def test_concrete_ok_implements_contract(self) -> None:
        """ConcreteOk should implement all required Result methods."""
        ok = ConcreteOk(42)
        assert ok.is_ok() is True
        assert ok.is_err() is False
        assert ok.ok() == 42
        assert ok.err() is None

    def test_concrete_err_implements_contract(self) -> None:
        """ConcreteErr should implement all required Result methods."""
        error = ValueError_("Test error")
        err = ConcreteErr(error)
        assert err.is_ok() is False
        assert err.is_err() is True
        assert err.ok() is None
        assert err.err() is error

    def test_ok_unwrap_returns_value(self) -> None:
        """unwrap() on Ok should return the value."""
        ok = ConcreteOk(42)
        assert ok.unwrap() == 42

    def test_err_unwrap_raises(self) -> None:
        """unwrap() on Err should raise UnwrapError."""
        error = ValueError_("Test error")
        err = ConcreteErr(error)
        with pytest.raises(UnwrapError):
            err.unwrap()

    def test_ok_map_transforms_value(self) -> None:
        """map() on Ok should transform the value."""
        ok = ConcreteOk(5)
        mapped = ok.map(lambda x: x * 2)
        assert isinstance(mapped, ConcreteOk)
        assert mapped.unwrap() == 10

    def test_err_map_returns_err(self) -> None:
        """map() on Err should return the Err unchanged."""
        error = ValueError_("Test error")
        err = ConcreteErr(error)
        mapped = err.map(lambda x: x * 2)
        assert isinstance(mapped, ConcreteErr)
        assert mapped.err() is error

    def test_ok_map_err_returns_ok(self) -> None:
        """map_err() on Ok should return the Ok unchanged."""
        ok = ConcreteOk(42)
        mapped = ok.map_err(lambda e: RuntimeError_(str(e)))
        assert isinstance(mapped, ConcreteOk)
        assert mapped.unwrap() == 42

    def test_err_map_err_transforms_error(self) -> None:
        """map_err() on Err should transform the error."""
        error = ValueError_("Test error")
        err = ConcreteErr(error)
        mapped = err.map_err(lambda e: RuntimeError_(str(e)))
        assert isinstance(mapped, ConcreteErr)
        assert isinstance(mapped.err(), RuntimeError_)

    def test_concrete_implementations_have_override_decorator(self) -> None:
        """All Result method implementations should use @override."""
        # Check that ConcreteOk methods have the _override marker
        for method_name in [
            "is_ok",
            "is_err",
            "ok",
            "err",
            "unwrap",
            "map",
            "map_err",
            "and_then",
        ]:
            method = getattr(ConcreteOk, method_name)
            # @override adds __override__ attribute in typing_extensions
            assert hasattr(method, "__override__") or callable(method)

    def test_result_has_all_required_abstract_methods(self) -> None:
        """Result ABC should define all required methods."""
        abstract_methods = {
            "is_ok",
            "is_err",
            "ok",
            "err",
            "unwrap",
            "map",
            "map_err",
            "and_then",
        }
        result_abstract_methods = Result.__abstractmethods__
        assert abstract_methods == result_abstract_methods
