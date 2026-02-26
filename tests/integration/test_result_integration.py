"""Integration tests for Result type system.

Tests verify end-to-end Result functionality including:
- Complex operation chains (multiple and_then calls)
- Error type accumulation in chains
- Private attribute enforcement
- Real-world usage patterns
"""

# pyright: reportOperatorIssue=false, reportPrivateUsage=false, reportUnusedFunction=false, reportMissingTypeArgument=false
import pytest

from results import Err, Ok, Result


class TestAndThenChaining:
    """Test multi-level and_then operations."""

    def test_successful_chain_three_levels(self) -> None:
        """Test successful operation chain with three and_then calls."""

        def parse_int(s: str) -> Result[int, ValueError]:
            try:
                return Ok(int(s))
            except ValueError as e:
                return Err(e)

        def validate_positive(x: int) -> Result[int, RuntimeError]:
            if x > 0:
                return Ok(x)
            return Err(RuntimeError("must be positive"))

        def square(x: int) -> Result[int, TypeError]:
            try:
                return Ok(x * x)
            except TypeError as e:
                return Err(e)

        result = parse_int("5").and_then(validate_positive).and_then(square)
        assert result.is_ok()
        assert result.ok() == 25

    def test_chain_fails_at_first_error(self) -> None:
        """Test chain stops at first error and doesn't call subsequent operations."""

        call_count = {"parse": 0, "validate": 0, "square": 0}

        def parse_int(s: str) -> Result[int, ValueError]:
            call_count["parse"] += 1
            try:
                return Ok(int(s))
            except ValueError as e:
                return Err(e)

        def validate_positive(x: int) -> Result[int, RuntimeError]:
            call_count["validate"] += 1
            if x > 0:
                return Ok(x)
            return Err(RuntimeError("must be positive"))

        def square(x: int) -> Result[int, TypeError]:
            call_count["square"] += 1
            return Ok(x * x)

        # First operation fails
        result = parse_int("invalid").and_then(validate_positive).and_then(square)
        assert result.is_err()
        assert isinstance(result.err(), ValueError)
        assert call_count["parse"] == 1
        assert call_count["validate"] == 0  # Not called
        assert call_count["square"] == 0  # Not called

    def test_chain_fails_at_middle_operation(self) -> None:
        """Test chain stops at middle operation."""

        def parse_int(s: str) -> Result[int, ValueError]:
            try:
                return Ok(int(s))
            except ValueError as e:
                return Err(e)

        def validate_positive(x: int) -> Result[int, RuntimeError]:
            if x > 0:
                return Ok(x)
            return Err(RuntimeError("must be positive"))

        def square(x: int) -> Result[int, TypeError]:
            return Ok(x * x)

        # Middle operation fails
        result = parse_int("-5").and_then(validate_positive).and_then(square)
        assert result.is_err()
        assert isinstance(result.err(), RuntimeError)
        assert str(result.err()) == "must be positive"

    def test_error_type_accumulation(self) -> None:
        """Test error types accumulate correctly through chain.

        While we can't directly check the accumulated type at runtime,
        we verify that chains complete and errors are preserved.
        """

        def op1(x: int) -> Result[int, ValueError]:
            return Ok(x * 2)

        def op2(x: int) -> Result[int, RuntimeError]:
            if x < 100:
                return Ok(x + 1)
            return Err(RuntimeError("too large"))

        def op3(x: int) -> Result[int, TypeError]:
            return Ok(x * 3)

        # Chain that succeeds
        result1 = Ok(10).and_then(op1).and_then(op2).and_then(op3)
        assert result1.is_ok()
        assert result1.ok() == 63  # ((10 * 2) + 1) * 3

        # Chain that fails at op2
        result2 = Ok(100).and_then(op1).and_then(op2).and_then(op3)
        assert result2.is_err()
        assert isinstance(result2.err(), RuntimeError)


class TestMapChaining:
    """Test multiple map operations."""

    def test_map_chain_transformations(self) -> None:
        """Test multiple map operations transform correctly."""
        result = Ok(5).map(lambda x: x * 2).map(lambda x: x + 3).map(str)
        assert result.ok() == "13"

    def test_map_with_and_then_mixing(self) -> None:
        """Test mixing map and and_then operations."""

        def double_if_positive(x: int) -> Result[int, str]:
            if x > 0:
                return Ok(x * 2)
            return Err("negative")

        result = Ok(5).map(lambda x: x + 3).and_then(double_if_positive).map(str)
        assert result.ok() == "16"

    def test_map_chain_error_preservation(self) -> None:
        """Test error is preserved through map chain."""
        result: Result[str, str] = Err("original error").map(lambda x: x * 2)
        mapped_again = result.map(str)
        assert mapped_again.is_err()
        assert mapped_again.err() == "original error"


class TestMapErrChaining:
    """Test error transformation chains."""

    def test_map_err_chain_transformations(self) -> None:
        """Test multiple map_err operations."""
        result = (
            Err("initial")
            .map_err(lambda e: f"Error: {e}")
            .map_err(RuntimeError)
            .map_err(lambda e: str(e))
        )
        assert result.is_err()
        assert "Error: initial" in result.err()

    def test_map_err_preserves_success(self) -> None:
        """Test map_err chain preserves successful result."""
        result = Ok(42).map_err(lambda e: str(e)).map_err(RuntimeError)
        assert result.ok() == 42


class TestPrivateAttributeEnforcement:
    """Test that private attributes cannot be directly accessed."""

    def test_ok_value_is_private(self) -> None:
        """Test Ok._value raises AttributeError when accessed."""
        result = Ok(42)
        with pytest.raises((AttributeError, TypeError)):
            result._value = 100

    def test_err_error_is_private(self) -> None:
        """Test Err._error raises AttributeError when accessed."""
        result = Err("error")
        with pytest.raises((AttributeError, TypeError)):
            result._error = "new error"

    def test_cannot_modify_ok_attributes(self) -> None:
        """Test all Ok attributes are frozen."""
        result = Ok(42)
        with pytest.raises((AttributeError, TypeError)):
            result.new_attr = "value"

    def test_cannot_modify_err_attributes(self) -> None:
        """Test all Err attributes are frozen."""
        result = Err("error")
        with pytest.raises((AttributeError, TypeError)):
            result.new_attr = "value"


class TestRealWorldPatterns:
    """Test real-world usage patterns."""

    def test_user_registration_flow(self) -> None:
        """Test a realistic user registration flow with multiple validations."""

        def parse_email(email_str: str) -> Result[str, ValueError]:
            if "@" not in email_str:
                return Err(ValueError("Invalid email format"))
            return Ok(email_str)

        def validate_password(password: str) -> Result[str, RuntimeError]:
            if len(password) < 8:
                return Err(RuntimeError("Password too short"))
            return Ok(password)

        def check_email_unique(email: str) -> Result[str, RuntimeError]:
            # Simulate database check
            blocked_emails = {"admin@example.com", "root@example.com"}
            if email in blocked_emails:
                return Err(RuntimeError("Email already registered"))
            return Ok(email)

        def register_user(
            email: str, password: str
        ) -> Result[dict, ValueError | RuntimeError]:
            """Simulate user registration."""
            result = parse_email(email).and_then(
                lambda e: check_email_unique(e).map(lambda _: email)
            )

            return result.map(lambda e: {"email": e, "password": password})

        # Test success case
        success = register_user("user@example.com", "password123")
        assert success.is_ok()
        assert success.ok() == {"email": "user@example.com", "password": "password123"}

        # Test email format failure
        format_fail = register_user("invalid-email", "password123")
        assert format_fail.is_err()
        assert isinstance(format_fail.err(), ValueError)

        # Test email exists failure
        exists_fail = register_user("admin@example.com", "password123")
        assert exists_fail.is_err()
        assert isinstance(exists_fail.err(), RuntimeError)

    def test_json_parsing_pipeline(self) -> None:
        """Test realistic JSON parsing with error handling."""

        def parse_json(json_str: str) -> Result[dict, ValueError]:
            import json

            try:
                return Ok(json.loads(json_str))
            except ValueError as e:
                return Err(e)

        def validate_required_fields(data: dict) -> Result[dict, RuntimeError]:
            required = {"name", "age"}
            if not required.issubset(data.keys()):
                return Err(
                    RuntimeError(f"Missing fields: {required - set(data.keys())}")
                )
            return Ok(data)

        def validate_age(data: dict) -> Result[dict, TypeError]:
            try:
                age = int(data["age"])
                if age < 0:
                    return Err(TypeError("Age cannot be negative"))
                return Ok(data)
            except (ValueError, TypeError) as e:
                return Err(TypeError(f"Age must be integer: {e}"))

        # Test success
        valid_json = '{"name": "Alice", "age": "30"}'
        result = (
            parse_json(valid_json)
            .and_then(validate_required_fields)
            .and_then(validate_age)
        )
        assert result.is_ok()
        assert result.ok() == {"name": "Alice", "age": "30"}

        # Test parsing failure
        invalid_json = "not valid json"
        result = (
            parse_json(invalid_json)
            .and_then(validate_required_fields)
            .and_then(validate_age)
        )
        assert result.is_err()
        assert isinstance(result.err(), ValueError)

        # Test missing fields
        incomplete_json = '{"name": "Bob"}'
        result = (
            parse_json(incomplete_json)
            .and_then(validate_required_fields)
            .and_then(validate_age)
        )
        assert result.is_err()
        assert isinstance(result.err(), RuntimeError)
