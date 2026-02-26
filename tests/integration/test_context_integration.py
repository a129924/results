"""Integration tests for v0.2.0 context chain and debug tools.

This module tests real-world scenarios combining context chain and debug tools.
These tests verify that new v0.2.0 features work correctly in realistic
applications.

All tests follow v0.1.0 backward compatibility requirements.
"""

# pyright: reportPrivateUsage=false, reportReturnType=false, reportArgumentType=false, reportOperatorIssue=false, reportMissingTypeArgument=false
from typing import TypedDict

from results import Err, Ok, Result


class User(TypedDict):
    """Example user data structure."""

    email: str
    password: str


class TestContextIntegration:
    """Integration tests for context chain in real-world scenarios."""

    def test_user_registration_flow(self) -> None:
        """Test context chain through a user registration flow."""
        debug_log: list[str] = []

        def validate_email(email: str) -> Result[str, str]:
            if "@" not in email:
                return Err("invalid email format").context("email validation")
            return Ok(email)

        def validate_password(password: str) -> Result[str, str]:
            if len(password) < 8:
                return Err("password too short").context("password validation")
            return Ok(password)

        def register_user(email: str, password: str) -> Result[User, str]:
            return (
                validate_email(email)
                .inspect(lambda e: debug_log.append(f"email validated: {e}"))
                .and_then(
                    lambda e: validate_password(password)
                    .inspect(lambda p: debug_log.append(f"password validated: {p}"))
                    .map(lambda p: User(email=e, password=p))
                )
            )

        # Successful case
        result = register_user("user@example.com", "securepass123")
        assert result.is_ok()

        user = result.ok()
        assert user is not None
        assert user["email"] == "user@example.com"

        # Failed email case
        result = register_user("invalid-email", "securepass123")
        assert result.is_err()
        register_err = result.err()
        assert register_err is not None
        assert "invalid email format" in register_err
        assert isinstance(result, Err) and result._context_chain.messages == (
            "email validation",
        )

    def test_data_pipeline_with_context(self) -> None:
        """Test context chain through a data processing pipeline."""

        def parse_int(s: str) -> Result[int, str]:
            try:
                return Ok(int(s))
            except ValueError:
                return Err(f"not a number: {s}").context("parsing")

        def validate_range(num: int) -> Result[int, str]:
            if not 0 <= num <= 100:
                return Err(f"out of range: {num}").context("validation")
            return Ok(num)

        def process_pipeline(
            inputs: list[str],
        ) -> Result[list[int], str]:
            results: list[int] = []
            for input_val in inputs:
                result = parse_int(input_val).and_then(validate_range)
                if result.is_err():
                    return result
                results.append(result.ok())
            return Ok(results)

        # Successful case
        result = process_pipeline(["1", "50", "100"])
        assert result.ok() == [1, 50, 100]

        # Failed case with context
        result = process_pipeline(["1", "invalid", "100"])
        assert result.is_err()
        assert "not a number" in result.err()
        assert result._context_chain.messages == ("parsing",)

    def test_nested_and_then_with_context(self) -> None:
        """Test deeply nested and_then operations with context."""

        def step1() -> Result[int, str]:
            return Ok(1)

        def step2(x: int) -> Result[int, str]:
            if x < 0:
                return Err("negative").context("step2")
            return Ok(x + 1)

        def step3(x: int) -> Result[int, str]:
            if x > 10:
                return Err("too large").context("step3")
            return Ok(x * 2)

        result = step1().and_then(step2).and_then(step3)
        assert result.ok() == 4

    def test_context_chain_display(self) -> None:
        """Test that context chain is properly displayed in errors."""
        result = (
            Err(ValueError("database connection failed"))
            .context("User.save()")
            .context("UserService.register()")
            .context("POST /api/users")
        )

        try:
            result.unwrap()
        except ValueError as e:
            error_msg = str(e)
            assert "database connection failed" in error_msg
            assert "User.save()" in error_msg
            assert "UserService.register()" in error_msg
            assert "POST /api/users" in error_msg

    def test_multiple_error_paths_with_different_contexts(self) -> None:
        """Test different error paths producing different context chains."""

        def load_config(path: str) -> Result[dict, str]:
            if not path:
                return Err("empty path").context("load_config")
            if not path.endswith(".json"):
                return Err("not json").context("load_config").context("format check")
            return Ok({})

        # Path 1: empty path
        result1 = load_config("")
        assert result1._context_chain.messages == ("load_config",)

        # Path 2: wrong format
        result2 = load_config("config.txt")
        assert result2._context_chain.messages == ("format check", "load_config")

    def test_inspect_with_context_chain(self) -> None:
        """Test inspect methods work correctly with context chain."""
        inspected_errors = []

        def error_logger(err: str) -> None:
            inspected_errors.append(err)

        result = (
            Err("original error")
            .context("step 1")
            .inspect_err(error_logger)
            .context("step 2")
            .inspect_err(error_logger)
        )

        assert inspected_errors == ["original error", "original error"]
        assert result._context_chain.messages == ("step 2", "step 1")

    def test_map_err_preserves_context(self) -> None:
        """Test that map_err preserves context chain."""
        result = (
            Err("low level error")
            .context("database layer")
            .map_err(lambda e: ValueError(f"Wrapped: {e}"))
        )

        assert isinstance(result.err(), ValueError)
        assert result._context_chain.messages == ("database layer",)

    def test_or_else_with_new_context(self) -> None:
        """Test map_err with new context."""
        result = (
            Err("primary failed")
            .context("primary operation")
            .map_err(lambda _: "recovery failed")
            .context("recovery operation")
        )

        assert result.is_err()
        assert result.err() == "recovery failed"
        assert result._context_chain.messages == (
            "recovery operation",
            "primary operation",
        )

    def test_complex_mixed_operations(self) -> None:
        """Test complex mix of map, and_then, inspect, and context."""
        operations = []

        def op1(x: int) -> Result[int, str]:
            operations.append("op1")
            return Ok(x + 1) if x >= 0 else Err("negative").context("op1")

        def op2(x: int) -> Result[int, str]:
            operations.append("op2")
            return Ok(x * 2) if x < 100 else Err("overflow").context("op2")

        result = (
            Ok(5)
            .and_then(op1)
            .inspect(lambda x: operations.append(f"inspected: {x}"))
            .and_then(op2)
            .inspect(lambda x: operations.append(f"final: {x}"))
        )

        assert result.ok() == 12
        assert operations == ["op1", "inspected: 6", "op2", "final: 12"]

    def test_backward_compatibility_with_v0_1(self) -> None:
        """Test that v0.1.0 code patterns still work with v0.2.0 features."""

        # This is purely v0.1.0 style code
        def process(x: int) -> Result[int, str]:
            if x < 0:
                return Err("negative")
            return Ok(x * 2)

        result = Ok(5).and_then(process).map(lambda x: x + 1).map(lambda x: x * 2)

        assert result.ok() == 22
        # Ok results don't have context chain (only Err has _context_chain)
        assert result.is_ok()
        assert not result.is_err()
