#!/usr/bin/env python3
"""
Integration with Pydantic

Shows how to use Results with Pydantic for validation.

Run: python with_pydantic.py

Note: Requires pydantic: pip install pydantic
"""

from pydantic import BaseModel, ValidationError, field_validator

from results import Err, Ok, Result

# ============================================================================
# 1. Wrapping Pydantic Validation
# ============================================================================


class User(BaseModel):
    """User model with validation."""

    id: int
    name: str
    email: str
    age: int

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()

    @field_validator("age")
    @classmethod
    def age_valid(cls, v):
        if v < 0 or v > 150:
            raise ValueError("Age must be between 0 and 150")
        return v


def parse_user(data: dict) -> Result[User, list[str]]:
    """Parse user data with Result wrapping."""
    try:
        user = User(**data)
        return Ok(user)
    except ValidationError as e:
        errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        return Err(errors)


def example_basic_validation():
    print("--- Basic Validation ---")

    # Valid data
    result = parse_user(
        {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30}
    )
    match result:
        case Ok(user):
            print(f"✓ Valid user: {user.name}")
        case Err(errors):
            print(f"✗ Validation errors: {errors}")

    # Invalid data
    result = parse_user({"id": 1, "name": "", "email": "bad", "age": 200})
    match result:
        case Ok(user):
            print(f"✓ Valid user: {user.name}")
        case Err(errors):
            for error in errors:
                print(f"  ✗ {error}")


# ============================================================================
# 2. Bulk Validation
# ============================================================================


def parse_users(data_list: list[dict]) -> Result[list[User], dict]:
    """Parse multiple users, returning first error or all users."""
    users = []
    for i, data in enumerate(data_list):
        result = parse_user(data)
        if result.is_err():
            return Err({"index": i, "errors": result.err(), "data": data})
        users.append(result.ok())
    return Ok(users)


def example_bulk_validation():
    print("\n--- Bulk Validation ---")

    data = [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "age": 30},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "age": 25},
        {"id": 3, "name": "Charlie", "email": "bad-email", "age": 35},
    ]

    result = parse_users(data)
    match result:
        case Ok(users):
            print(f"✓ All users valid: {len(users)}")
            for user in users:
                print(f"  - {user.name}")
        case Err(error):
            print(f"✗ Validation failed at index {error['index']}")
            print(f"  Data: {error['data']}")
            for err in error["errors"]:
                print(f"  Error: {err}")


# ============================================================================
# 3. Transform and Validate
# ============================================================================


class UserProfile(BaseModel):
    """Transformed user data."""

    username: str
    email: str
    years_old: int


def transform_to_profile(user: User) -> UserProfile:
    """Transform User to UserProfile."""
    return UserProfile(username=user.name.lower(), email=user.email, years_old=user.age)


def example_transform_validate():
    print("\n--- Transform and Validate ---")

    result = parse_user(
        {"id": 1, "name": "Alice Smith", "email": "alice@example.com", "age": 30}
    ).map(transform_to_profile)

    match result:
        case Ok(profile):
            print(f"✓ Profile created: {profile.username}")
        case Err(errors):
            print(f"✗ Errors: {errors}")


# ============================================================================
# 4. Conditional Validation
# ============================================================================


def validate_admin_user(user: User) -> Result[User, str]:
    """Additional validation for admin users."""
    if user.email.endswith("@admin.com"):
        return Ok(user)
    else:
        return Err("Admin email required for admin users")


def example_conditional():
    print("\n--- Conditional Validation ---")

    user_data = {"id": 1, "name": "Admin", "email": "admin@admin.com", "age": 40}

    result = parse_user(user_data).and_then(validate_admin_user)

    match result:
        case Ok(user):
            print(f"✓ Admin user valid: {user.name}")
        case Err(error):
            print(f"✗ {error}")


# ============================================================================
# 5. Real-World: API Payload Handler
# ============================================================================


class CreateUserRequest(BaseModel):
    """API request to create user."""

    name: str
    email: str
    age: int


def create_user_handler(request_data: dict) -> Result[dict, dict]:
    """Handle user creation request."""
    # 1. Parse request body
    try:
        request = CreateUserRequest(**request_data)
    except ValidationError as e:
        return Err(
            {
                "status": "validation_error",
                "errors": [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()],
            }
        )

    # 2. Create full User object
    user_data = {
        "id": 1,  # Would be generated
        "name": request.name,
        "email": request.email,
        "age": request.age,
    }

    result = parse_user(user_data)

    # 3. Process result
    match result:
        case Ok(user):
            return Ok(
                {
                    "status": "created",
                    "user": {"id": user.id, "name": user.name, "email": user.email},
                }
            )
        case Err(errors):
            return Err({"status": "invalid_user", "errors": errors})


def example_api_handler():
    print("\n--- API Handler ---")

    # Valid request
    request = {"name": "Alice", "email": "alice@example.com", "age": 30}
    result = create_user_handler(request)

    match result:
        case Ok(response):
            print(f"✓ {response['status']}: {response['user']['name']}")
        case Err(error):
            print(f"✗ {error['status']}: {error}")

    # Invalid request
    request = {"name": "", "email": "bad", "age": "not a number"}
    result = create_user_handler(request)

    match result:
        case Ok(response):
            print(f"✓ {response}")
        case Err(error):
            print(f"✗ {error['status']}")
            for err in error["errors"]:
                print(f"  - {err}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Integration with Pydantic")
    print("=" * 70)
    print()

    try:
        example_basic_validation()
        example_bulk_validation()
        example_transform_validate()
        example_conditional()
        example_api_handler()

        print("\n" + "=" * 70)
        print("Key Patterns:")
        print("  1. Wrap Pydantic ValidationError in Result")
        print("  2. Chain validations with and_then()")
        print("  3. Transform validated data with map()")
        print("  4. Use pattern matching for clear handler logic")
        print("=" * 70)

    except ImportError:
        print("⚠ Pydantic not installed. Install with: pip install pydantic")
