"""Tests for v0.2.0 debug utilities (inspect and inspect_err).

This module tests the inspect() and inspect_err() debug tools added in v0.2.0.
These methods allow inspection of intermediate values in a Result chain without
modifying the Result itself.

All tests verify:
- Callable is executed with correct value
- Result is returned unchanged
- Exceptions in callable propagate
- Chainability with other operations
"""

import pytest

from results import Err, Ok, Result


class TestInspect:
    """Test inspect() method for debugging Ok results."""

    def test_inspect_called_on_ok(self) -> None:
        """Test that inspect() executes the callable on Ok result."""
        called_with = None

        def inspector(value: int) -> None:
            nonlocal called_with
            called_with = value

        result = Ok(42).inspect(inspector)

        assert called_with == 42
        assert result.is_ok()
        assert result.ok() == 42

    def test_inspect_returns_ok_unchanged(self) -> None:
        """Test that inspect() returns the original Ok unchanged."""
        result = Ok(42).inspect(lambda _: None)

        assert result.is_ok()
        assert result.ok() == 42

    def test_inspect_not_called_on_err(self) -> None:
        """Test that inspect() is not called on Err result."""
        called = False

        def inspector(_: object) -> None:
            nonlocal called
            called = True

        result = Err("error").inspect(inspector)

        assert not called
        assert result.is_err()
        assert result.err() == "error"

    def test_inspect_exception_propagates(self) -> None:
        """Test that exceptions in inspect() propagate."""

        def bad_inspector(_: object) -> None:
            raise ValueError("inspection failed")

        result = Ok(42)
        with pytest.raises(ValueError, match="inspection failed"):
            result.inspect(bad_inspector)

    def test_inspect_chainable_with_map(self) -> None:
        """Test inspect() is chainable with map()."""
        inspected = None

        def inspector(value: int) -> None:
            nonlocal inspected
            inspected = value

        result = Ok(5).inspect(inspector).map(lambda x: x * 2)

        assert inspected == 5
        assert result.ok() == 10

    def test_inspect_multiple_calls(self) -> None:
        """Test multiple inspect() calls in sequence."""
        values = []

        result = (
            Ok(1)
            .inspect(lambda v: values.append(v))
            .map(lambda x: x + 1)
            .inspect(lambda v: values.append(v))
        )

        assert values == [1, 2]
        assert result.ok() == 2

    def test_inspect_with_complex_types(self) -> None:
        """Test inspect() with complex types."""
        inspected_dict = None

        def inspector(value: dict) -> None:
            nonlocal inspected_dict
            inspected_dict = value

        data = {"key": "value", "nested": {"count": 42}}
        result = Ok(data).inspect(inspector)

        assert inspected_dict is data
        assert result.ok() == data


class TestInspectErr:
    """Test inspect_err() method for debugging Err results."""

    def test_inspect_err_called_on_err(self) -> None:
        """Test that inspect_err() executes the callable on Err result."""
        called_with = None

        def inspector(error: str) -> None:
            nonlocal called_with
            called_with = error

        result = Err("test error").inspect_err(inspector)

        assert called_with == "test error"
        assert result.is_err()
        assert result.err() == "test error"

    def test_inspect_err_returns_err_unchanged(self) -> None:
        """Test that inspect_err() returns the original Err unchanged."""
        result = Err("error").inspect_err(lambda _: None)

        assert result.is_err()
        assert result.err() == "error"

    def test_inspect_err_not_called_on_ok(self) -> None:
        """Test that inspect_err() is not called on Ok result."""
        called = False

        def inspector(_: object) -> None:
            nonlocal called
            called = True

        result = Ok(42).inspect_err(inspector)

        assert not called
        assert result.is_ok()
        assert result.ok() == 42

    def test_inspect_err_exception_propagates(self) -> None:
        """Test that exceptions in inspect_err() propagate."""

        def bad_inspector(_: object) -> None:
            raise RuntimeError("error inspection failed")

        result = Err("error")
        with pytest.raises(RuntimeError, match="error inspection failed"):
            result.inspect_err(bad_inspector)

    def test_inspect_err_chainable_with_map_err(self) -> None:
        """Test inspect_err() is chainable with map_err()."""
        inspected = None

        def inspector(error: str) -> None:
            nonlocal inspected
            inspected = error

        result = (
            Err("original").inspect_err(inspector).map_err(lambda e: f"wrapped: {e}")
        )

        assert inspected == "original"
        assert result.err() == "wrapped: original"

    def test_inspect_err_multiple_calls(self) -> None:
        """Test multiple inspect_err() calls in sequence."""
        values = []

        result = (
            Err("a")
            .inspect_err(lambda v: values.append(v))
            .map_err(lambda e: f"{e}b")
            .inspect_err(lambda v: values.append(v))
        )

        assert values == ["a", "ab"]
        assert result.err() == "ab"

    def test_inspect_err_with_exception_type(self) -> None:
        """Test inspect_err() with exception objects."""
        inspected_error = None

        def inspector(error: Exception) -> None:
            nonlocal inspected_error
            inspected_error = error

        original_error = ValueError("something went wrong")
        result = Err(original_error).inspect_err(inspector)

        assert inspected_error is original_error
        assert result.err() is original_error


class TestInspectIntegration:
    """Test inspect/inspect_err integration scenarios."""

    def test_inspect_and_inspect_err_together(self) -> None:
        """Test using inspect() and inspect_err() together."""
        ok_inspected = None
        err_inspected = None

        def ok_inspector(value: int) -> None:
            nonlocal ok_inspected
            ok_inspected = value

        def err_inspector(error: str) -> None:
            nonlocal err_inspected
            err_inspected = error

        Ok(42).inspect(ok_inspector).inspect_err(err_inspector)
        assert ok_inspected == 42
        assert err_inspected is None

        Err("error").inspect(ok_inspector).inspect_err(err_inspector)
        assert ok_inspected == 42  # Not changed
        assert err_inspected == "error"

    def test_inspect_in_pipeline(self) -> None:
        """Test inspect() in a complex pipeline."""
        logged = []

        def process(x: int) -> Result[str, str]:
            if x < 0:
                return Err("negative")
            return Ok(str(x))

        result = (
            Ok(5)
            .inspect(lambda x: logged.append(f"input: {x}"))
            .and_then(process)
            .inspect(lambda x: logged.append(f"output: {x}"))
        )

        assert result.ok() == "5"
        assert logged == ["input: 5", "output: 5"]

    def test_inspect_err_in_error_pipeline(self) -> None:
        """Test inspect_err() in error transformation pipeline."""
        errors_seen = []

        (
            Err("initial")
            .inspect_err(lambda e: errors_seen.append(e))
            .map_err(lambda e: f"recovered from: {e}")
            .inspect_err(lambda e: errors_seen.append(e))
        )

        assert len(errors_seen) == 2
        assert errors_seen[0] == "initial"
        assert errors_seen[1] == "recovered from: initial"

    def test_inspect_after_context(self) -> None:
        """Test inspect() with context chain."""
        inspected = None

        def inspector(error: str) -> None:
            nonlocal inspected
            inspected = error

        result = Err("base").context("step 1").context("step 2").inspect_err(inspector)

        assert inspected == "base"
        assert result._context_chain.messages == ("step 2", "step 1")

    def test_inspect_with_side_effects(self) -> None:
        """Test inspect() with side effects (file writes, etc.)."""
        side_effects = []

        def record_effect(value: int) -> None:
            side_effects.append(("seen", value))

        result = (
            Ok(10).inspect(record_effect).map(lambda x: x * 2).inspect(record_effect)
        )

        assert result.ok() == 20
        assert side_effects == [("seen", 10), ("seen", 20)]

    def test_inspect_chainable_results(self) -> None:
        """Test that inspect()/inspect_err() maintain chainability."""
        result = (
            Ok(5)
            .inspect(lambda _: None)
            .map(lambda x: x + 1)
            .inspect(lambda _: None)
            .and_then(lambda x: Ok(x * 2) if x > 0 else Err("invalid"))
            .inspect(lambda _: None)
        )

        assert result.ok() == 12
