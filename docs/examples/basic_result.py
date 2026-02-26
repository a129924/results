#!/usr/bin/env python3
"""
Basic Result Operations

Demonstrates fundamental Result[T, E] usage patterns.

Run: python basic_result.py
"""

from results import Err, Ok, Result

# ============================================================================
# 1. Creating Results
# ============================================================================


def divide(x: int, y: int) -> Result[int, str]:
    """Return success or error."""
    if y == 0:
        return Err("division by zero")
    return Ok(x // y)


# ============================================================================
# 2. Checking Variants
# ============================================================================


def example_variant_checking():
    result = divide(10, 2)

    if result.is_ok():
        print(f"✓ Success: {result.ok()}")
    else:
        print(f"✗ Error: {result.err()}")


# ============================================================================
# 3. Transformations with map()
# ============================================================================


def example_transformations():
    print("\n--- Transformations ---")

    # Map transforms success value
    result = divide(20, 2).map(lambda x: x * 2)
    print(f"divide(20, 2).map(x*2) = {result.unwrap()}")  # Ok(20)

    # Errors pass through unchanged
    result = divide(10, 0).map(lambda x: x * 2)
    print(f"divide(10, 0).map(x*2) = {result.err()}")  # Err("division by zero")

    # Map errors
    result = Err[str, str]("error").map_err(str.upper)
    print(f"Err('error').map_err(upper) = {result.err()}")  # Err("ERROR")


# ============================================================================
# 4. Chaining Operations with and_then()
# ============================================================================


def example_chaining():
    print("\n--- Chaining (and_then) ---")

    result = (
        divide(20, 2)  # Ok(10)
        .and_then(lambda x: divide(x, 2))  # Ok(5)
        .and_then(lambda x: divide(x, 0))  # Err("division by zero")
    )

    if result.is_err():
        print(f"Chain failed: {result.err()}")


# ============================================================================
# 5. Error Recovery with or_else()
# ============================================================================


def example_recovery():
    print("\n--- Error Recovery ---")

    # Basic recovery
    result = divide(10, 0).or_else(lambda e: Ok(0))
    print(f"Error recovered with 0: {result.unwrap()}")  # Ok(0)

    # Conditional recovery
    result = divide(10, 0).or_else(lambda e: Ok(0) if "zero" in e else Err(e))
    print(f"Conditional recovery: {result.unwrap()}")  # Ok(0)


# ============================================================================
# 6. Extraction with unwrap_or()
# ============================================================================


def example_extraction():
    print("\n--- Extraction ---")

    success = divide(20, 2).unwrap_or(0)
    print(f"Success extracted: {success}")  # 10

    failure = divide(10, 0).unwrap_or(0)
    print(f"Error as default: {failure}")  # 0

    # With computed default
    failure = divide(10, 0).unwrap_or_else(lambda e: len(e))
    print(f"Error length: {failure}")  # 18


# ============================================================================
# 7. Side Effects with inspect()
# ============================================================================


def example_inspection():
    print("\n--- Inspection (for debugging) ---")

    result = (
        divide(20, 2)
        .inspect(lambda x: print(f"  Intermediate value: {x}"))
        .map(lambda x: x * 2)
        .inspect(lambda x: print(f"  After doubling: {x}"))
    )

    result.unwrap()


# ============================================================================
# 8. Context Chains for Debugging
# ============================================================================


def example_context():
    print("\n--- Context Chains ---")

    def fetch_order(order_id: int) -> Result[str, str]:
        # Simulated: order not found
        result = Err[str, str]("order not found in database")
        return result.context(f"fetching order {order_id}")

    def process_order(order_id: int) -> Result[str, str]:
        return fetch_order(order_id).context(f"processing order {order_id}")

    result = process_order(123)

    # Context shows when unwrapping
    try:
        result.unwrap()
    except Exception as e:
        print(f"Error with context:\n{e}")


# ============================================================================
# 9. Pattern Matching (Python 3.10+)
# ============================================================================


def example_pattern_matching():
    print("\n--- Pattern Matching ---")

    result = divide(20, 4)

    match result:
        case Ok(value) if value > 0:
            print(f"Positive result: {value}")
        case Ok(value):
            print(f"Non-positive result: {value}")
        case Err(error):
            print(f"Error: {error}")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 10. Composing Multiple Results
# ============================================================================


def example_composition():
    print("\n--- Composition ---")

    def safe_divide_pipeline(x: int, divisors: list[int]) -> Result[int, str]:
        """Apply multiple divisions safely."""
        result = Ok[int, str](x)
        for divisor in divisors:
            result = result.and_then(lambda v: divide(v, divisor))
        return result

    # Success path
    result = safe_divide_pipeline(120, [2, 3, 2])
    print(f"Pipeline result: {result.unwrap()}")  # 10

    # Failure path (stops at first error)
    result = safe_divide_pipeline(120, [2, 0, 2])
    print(f"Pipeline with error: {result.err()}")  # division by zero


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Basic Result Operations")
    print("=" * 70)

    example_variant_checking()
    example_transformations()
    example_chaining()
    example_recovery()
    example_extraction()
    example_inspection()
    example_context()
    example_pattern_matching()
    example_composition()

    print("\n✓ All examples completed!")
