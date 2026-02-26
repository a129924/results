#!/usr/bin/env python3
"""
Either for Validation and Branching

Demonstrates Either[L, R] for non-error branching logic.

Run: python either_validation.py
"""

from enum import Enum
from typing import Literal, TypedDict

from typing_extensions import NotRequired, Required

from results import Either, Left, Right


class EvaluateStatus(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class PaymentInfo(TypedDict, total=True):
    status: Required[Literal["success", "error"]]
    message: NotRequired[str]
    amount: NotRequired[int]


# ============================================================================
# 1. When to Use Either (vs Result)
# ============================================================================


def example_either_use_case():
    print("--- Either for Non-Error Branching ---")
    print("""
Result[T, E]: One success (T), one error (E)
  Used for: File operations, API calls, parsing
  Think: success/failure

Either[L, R]: Two equally valid outcomes (L, R)
  Used for: Business logic with two paths
  Think: this outcome OR that outcome
  Examples:
    - Admin user OR regular user
    - Local cache OR remote fetch
    - User action OR system action
    - Approved OR Rejected OR Manual Review
""")


# ============================================================================
# 2. Basic Either Operations
# ============================================================================


def categorize_user(age: int) -> Either[str, str]:
    """Categorize user by age."""
    if age < 18:
        return Left("minor")
    else:
        return Right("adult")


def example_basic():
    print("\n--- Basic Operations ---")

    user = categorize_user(25)

    # Variant checking
    if user.is_right():
        category = user.right()
        print(f"✓ User is: {category}")
    else:
        category = user.left()
        print(f"→ User is: {category}")


# ============================================================================
# 3. Transformations
# ============================================================================


def example_transformations():
    print("\n--- Transformations ---")

    # Transform right (like map)
    user = categorize_user(25).map(str.upper)
    print(f"Transformed right: {user.right()}")  # ADULT

    # Transform left (like map_err but symmetric)
    user = categorize_user(15).map_left(str.upper)
    print(f"Transformed left: {user.left()}")  # MINOR

    # Transform both branches
    user = categorize_user(20).bimap(
        lambda x: f"Too young: {x}", lambda x: f"Qualified: {x}"
    )
    print(f"Bimap: {user.right()}")  # Qualified: adult


# ============================================================================
# 4. Chaining Operations
# ============================================================================


def apply_to_adult(category: str) -> Either[str, str]:
    """Apply logic only for adults."""
    if category == "adult":
        return Right("Approved for credit card")
    else:
        return Left("Not eligible")


def example_chaining():
    print("\n--- Chaining ---")

    result = categorize_user(25).and_then(apply_to_adult)

    match result:
        case Right(msg):
            print(f"✓ {msg}")
        case Left(msg):
            print(f"→ {msg}")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 5. Real-World: Request Routing
# ============================================================================


def example_request_routing():
    print("\n--- Request Routing Example ---")

    def route_request(source: str) -> Either[str, str]:
        """Route to cache or database based on source."""
        match source:
            case "cache":
                return Left("fetching from cache")
            case "db":
                return Right("querying database")
            case _:
                return Left("unknown source")

    # Process routing decision
    routing = route_request("cache")

    match routing:
        case Left(action):
            print(f"→ Fallback: {action}")
            # Execute cache fetch
        case Right(action):
            print(f"✓ Primary: {action}")
            # Execute DB query
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 6. Real-World: Approval Workflow
# ============================================================================


def example_approval():
    print("\n--- Approval Workflow ---")

    def evaluate_application(score: int) -> Either[str, str]:
        """Evaluate loan application."""
        if score < 600:
            return Left("rejected")
        elif score >= 750:
            return Right("approved")
        else:
            return Right("manual_review")

    def send_notification(status: str) -> str:
        """Send approval/rejection notification."""
        return f"Sent {status} notification"

    def process_application(credit_score: int) -> str:
        result = evaluate_application(credit_score)

        match result:
            case Left(reason):
                print(f"❌ Application rejected: {reason}")
                return send_notification("rejection")
            case Right(status):
                print(f"✅ Application {status}")
                return send_notification(status)
            case unexpected:
                print(f"Unexpected: {unexpected}")
                return send_notification("error")

    print(process_application(550))  # Rejected
    print(process_application(700))  # Manual review
    print(process_application(780))  # Approved


# ============================================================================
# 7. Either as Decision Tree
# ============================================================================


def example_decision_tree():
    print("\n--- Decision Tree ---")

    def check_payment(amount: int, balance: int) -> Either[str, str]:
        """Check payment eligibility."""
        if amount <= 0:
            return Left("invalid_amount")
        elif balance < amount:
            return Left("insufficient_funds")
        else:
            return Right("approved")

    def process_payment(amount: int, balance: int) -> PaymentInfo:
        """Process payment with clear branching."""
        result = check_payment(amount, balance)

        match result:
            case Left("invalid_amount"):
                return {"status": "error", "message": "Amount must be positive"}
            case Left("insufficient_funds"):
                return {"status": "error", "message": f"Need ${amount - balance} more"}
            case Right("approved"):
                return {"status": "success", "amount": amount}
            case unexpected:
                return {"status": "error", "message": f"Unexpected: {unexpected}"}

    print("Payment 1:", process_payment(50, 100))  # Approved
    print("Payment 2:", process_payment(-10, 100))  # Invalid
    print("Payment 3:", process_payment(150, 100))  # Insufficient


# ============================================================================
# 8. Combining Either with Result
# ============================================================================


def example_either_with_result():
    print("\n--- Either with Result ---")

    from results import Err, Ok, Result

    def get_user(user_id: int) -> Result[dict[str, str | int], str]:
        """Get user or error."""
        if user_id > 0:
            return Ok({"id": user_id, "role": "admin"})
        else:
            return Err("Invalid user ID")

    def check_permission(user: dict[str, str | int]) -> Either[str, str]:
        """Check if user is admin."""
        if user.get("role") == "admin":
            return Right("Access granted")
        else:
            return Left("Access denied")

    # Chain Result and Either
    user_id = 1
    result = get_user(user_id)

    match result:
        case Ok(user):
            permission = check_permission(user)
            match permission:
                case Right(msg):
                    print(f"✓ {msg}")
                case Left(msg):
                    print(f"→ {msg}")
                case unexpected:
                    print(f"Unexpected: {unexpected}")
        case Err(error):
            print(f"✗ {error}")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 9. Pattern Matching with Either
# ============================================================================


def example_pattern_matching():
    print("\n--- Pattern Matching ---")

    result = categorize_user(30)

    match result:
        case Left(category) if "minor" in category:
            print(f"Young {category}")
        case Left(category):
            print(f"Other: {category}")
        case Right(category):
            print(f"Adult: {category}")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Either for Validation and Branching")
    print("=" * 70)

    example_either_use_case()
    example_basic()
    example_transformations()
    example_chaining()
    example_request_routing()
    example_approval()
    example_decision_tree()
    example_either_with_result()
    example_pattern_matching()

    print("\n" + "=" * 70)
    print("Key Takeaway:")
    print("  Result[T, E]: Success or Error")
    print("  Either[L, R]: Primary path (R) or Fallback (L)")
    print("  Either is symmetric - both branches are equally valid!")
    print("=" * 70)
