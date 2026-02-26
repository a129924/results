#!/usr/bin/env python3
"""
Maybe vs Optional Comparison

Demonstrates why Maybe[T] is safer than Optional[T].

Run: python maybe_optional.py
"""

from typing_extensions import TypedDict

from results import Maybe, Nothing, Some


class User(TypedDict):
    id: int
    name: str
    company_id: int  # Could be None if user has no company


# ============================================================================
# 1. The Problem with Optional
# ============================================================================


def get_user_optional(user_id: int) -> User | None:
    """Traditional approach with Optional."""
    if user_id < 0:
        return None  # What does this mean? Error? Not found?
    return {"id": user_id, "name": "Alice", "company_id": 1}


def example_optional_ambiguity():
    print("--- Optional Ambiguity ---")

    result = get_user_optional(-1)

    if result is None:
        print("❓ What does None mean here?")
        print("   - User not found?")
        print("   - Request error?")
        print("   - Timeout?")
        print("   - User hasn't set their profile?")


# ============================================================================
# 2. Better with Maybe
# ============================================================================


def get_user_maybe(user_id: int) -> Maybe[User]:
    """Explicit intent with Maybe."""
    if user_id < 0:
        return Nothing()  # Clear: no user found
    return Some({"id": user_id, "name": "Alice", "company_id": 1})


def example_maybe_clarity():
    print("\n--- Maybe Clarity ---")

    result = get_user_maybe(-1)

    match result:
        case Some(user):
            print(f"✓ Found user: {user['name']}")
        case Nothing():
            print("✓ No user found (explicit intent)")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 3. Transformations: Optional vs Maybe
# ============================================================================


def example_transformations():
    print("\n--- Transformations ---")

    # With Optional (error-prone)
    user_opt = get_user_optional(1)
    if user_opt is not None:
        name = user_opt.get("name", "Unknown")
    else:
        name = "Unknown"
    print(f"Optional result: {name}")

    # With Maybe (type-safe)
    user_maybe = get_user_maybe(1)
    name = user_maybe.map(lambda u: u.get("name")).unwrap_or("Unknown")
    print(f"Maybe result: {name}")


# ============================================================================
# 4. Chaining: Optional vs Maybe
# ============================================================================


def get_company(company_id: int) -> Maybe[User]:
    """Get company for given ID."""
    if company_id < 0:
        return Nothing()
    return Some({"id": company_id, "name": "Acme Corp", "company_id": 1})


def example_chaining():
    print("\n--- Chaining Operations ---")

    # With Optional (nested ifs)
    user_opt = get_user_optional(1)
    if user_opt is not None:
        company_id = user_opt.get("company_id", -1)
        if company_id >= 0:
            company_opt = get_company(company_id)
            company_name = company_opt.unwrap_or(
                User(id=0, name="Unknown", company_id=0)
            )["name"]
        else:
            company_name = "Unknown"
    else:
        company_name = "Unknown"
    print(f"Optional (nested): {company_name}")

    # With Maybe (clean)
    company_name = (
        get_user_maybe(1)
        .and_then(lambda u: get_company(u.get("company_id", -1)))
        .map(lambda c: c.get("name"))
        .unwrap_or("Unknown")
    )
    print(f"Maybe (flat): {company_name}")


# ============================================================================
# 5. Filtering: Optional vs Maybe
# ============================================================================


def example_filtering():
    print("\n--- Filtering ---")

    # Optional: Check value after extracting
    user_opt = get_user_optional(1)
    if user_opt is not None and user_opt.get("id", 0) > 0:
        print(f"Optional: Valid user {user_opt['id']}")

    # Maybe: Chain naturally
    is_valid = get_user_maybe(1).filter(lambda u: u.get("id", 0) > 0)

    match is_valid:
        case Some(user):
            print(f"Maybe: Valid user {user['id']}")
        case Nothing():
            print("Maybe: User doesn't match filter")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 6. Type Safety Comparison
# ============================================================================


def example_type_safety():
    print("\n--- Type Safety ---")
    print("""
Optional[T] issues:
  ❌ Can't distinguish between None values (is it absence or error?)
  ❌ Type checker can't enforce non-None checks (Optional[int] could be None)
  ❌ mypy can't catch all None dereferences

Maybe[T] benefits:
  ✓ Explicit Some(value) or Nothing()
  ✓ Type checking enforces pattern matching
  ✓ mypy --strict catches all branching
""")


# ============================================================================
# 7. Real-World Example: Database Query
# ============================================================================


class LoginUser(TypedDict):
    id: int
    email: str
    verified: bool


def get_user_from_db(user_id: int) -> Maybe[LoginUser]:
    """Query database and return user."""
    # Simulated
    if user_id == 1:
        return Some({"id": 1, "email": "alice@example.com", "verified": True})
    elif user_id == 2:
        return Some({"id": 2, "email": "bob@example.com", "verified": False})
    else:
        return Nothing()


def example_database_query():
    print("\n--- Database Query Example ---")

    # Get user and check if verified
    verified_email = (
        get_user_from_db(1)
        .filter(lambda u: u.get("verified", False))
        .map(lambda u: u.get("email"))
        .unwrap_or("User not verified")
    )
    print(f"Verified email: {verified_email}")

    # Get unverified user's email with clear handling
    user_opt = get_user_from_db(2)
    match user_opt:
        case Some(user) if not user.get("verified"):
            print(f"Unverified user: {user['email']}")
        case Some(user):
            print(f"Verified user: {user['email']}")
        case Nothing():
            print("User not found")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 8. Converting Between Optional and Maybe
# ============================================================================


def example_conversions():
    print("\n--- Conversions ---")

    # Optional to Maybe (using helper)
    optional_value: int | None = 42
    maybe_value = Some(optional_value) if optional_value is not None else Nothing[int]()  # type: ignore
    print(f"Optional → Maybe: {maybe_value}")

    # Maybe to Optional
    maybe_value = Some(42)
    optional_value = maybe_value.unwrap()
    print(f"Maybe → Optional: {optional_value}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Maybe vs Optional Comparison")
    print("=" * 70)

    example_optional_ambiguity()
    example_maybe_clarity()
    example_transformations()
    example_chaining()
    example_filtering()
    example_type_safety()
    example_database_query()
    example_conversions()

    print("\n" + "=" * 70)
    print("Key Takeaway:")
    print("  Optional[T] is just None or a value")
    print("  Maybe[T] is explicitly Some(value) or Nothing()")
    print("  Maybe is more expressive and type-safe!")
    print("=" * 70)
