# Error Handling Guide

Best practices for using Result types effectively in enterprise applications.

## Understanding Result[T, E]

Result represents an operation that can either succeed with value `T` or fail with error `E`.

```python
from results import Ok, Err, Result

def divide(x: int, y: int) -> Result[int, str]:
    """Integer division that returns Result."""
    if y == 0:
        return Err("division by zero")
    return Ok(x // y)
```

### Why Result over Exceptions?

| Aspect | Exceptions | Result |
|--------|-----------|--------|
| **Visibility** | Hidden in code ❌ | Explicit in return type ✅ |
| **Type Safety** | Unchecked ❌ | Type-checked ✅ |
| **Control Flow** | Long-distance jumps ❌ | Local composition ✅ |
| **Testing** | Hard to mock ❌ | Easy to test ✅ |
| **Performance** | Stack unwinding overhead | Direct return |

---

## Pattern 1: Unwrap with Defaults

For cases where you have a sensible default:

```python
from results import Ok, Err

# Basic unwrap_or
result = divide(10, 0)
quotient = result.unwrap_or(0)  # Returns 0 on error

# Computed default with unwrap_or_else
quotient = result.unwrap_or_else(lambda error: {
    "division by zero": -1,
    "invalid input": -2,
}.get(error, -99))
```

**When to use**: Non-critical operations where defaults exist.

---

## Pattern 2: Map and Chain Operations

Transform success without touching errors:

```python
# Single transformation
result = divide(20, 5).map(lambda x: x * 2)  # Ok(8)

# Multiple transformations (chaining)
result = (
    divide(20, 5)
    .map(lambda x: x * 10)
    .map(lambda x: x + 5)
    .map(lambda x: max(x, 100))
)

# Chain dependent operations
result = (
    divide(20, 5)
    .and_then(lambda x: 
        divide(100, x)  # Takes result of previous operation
    )
)
```

**Benefits**:
- Error propagates automatically
- No repetitive `if result.is_ok()` checks
- Cleaner, more functional code

---

## Pattern 3: Error Recovery

Recover from specific errors:

```python
# Simple recovery: use any other Result
divide(10, 0).or_else(lambda err: Ok(0))  # Ok(0)

# Smart recovery: examine error
divide(10, 0).or_else(lambda err: 
    Ok(0) if "division" in err else Err(err)
)

# Fallback chain
def divide_safe(x: int, y: int) -> Result[int, str]:
    return (
        divide(x, y)
        .or_else(lambda e1: divide(x, 1))  # Fallback to divide by 1
        .or_else(lambda e2: Ok(x))          # Final fallback
    )

divide_safe(10, 0)  # Ok(10)
```

**When to use**: When operation has fallback strategies.

---

## Pattern 4: Combining Multiple Results

Merge results from multiple operations:

```python
from results import Ok, Err

def combine_two(r1: Result[int, str], r2: Result[int, str]) -> Result[int, str]:
    """Return sum of both or first error."""
    return r1.and_then(lambda x:
        r2.map(lambda y: x + y)
    )

# Usage
result = combine_two(divide(20, 2), divide(30, 3))  # Ok(17)
result = combine_two(divide(20, 2), divide(30, 0))  # Err("division by zero")
```

**Pattern**: Use nested `and_then` → `map` for clean composition.

---

## Pattern 5: Conditional Mapping

Validate during transformation:

```python
# Reject invalid values during transformation
result = (
    divide(20, 5)
    .and_then(lambda x: 
        Ok(x) if x > 0 else Err("result must be positive")
    )
)

# With Maybe (for optional values)
from results import Some, Nothing

def validate_positive(x: int) -> Maybe[int]:
    return Some(x) if x > 0 else Nothing()

divide(20, 5).map(validate_positive)  # Ok(Some(4))
```

---

## Pattern 6: Error Context for Debugging

Add diagnostic information:

```python
def fetch_user(user_id: int) -> Result[dict, str]:
    # Simulated database call
    result = Err("database timeout")
    
    return result.context(f"fetching user {user_id}")

def process_user(user_id: int) -> Result[dict, str]:
    return (
        fetch_user(user_id)
        .map(lambda u: u.get("name"))
        .context(f"processing user {user_id}")
        .context("in payment processor")
    )

# On error, unwrap shows full chain:
try:
    process_user(123).unwrap()
except Exception as e:
    print(e)
    # Shows:
    # database timeout
    # Context:
    #   - in payment processor
    #   - processing user 123
    #   - fetching user 123
```

**Benefits**: Full traceability without logging boilerplate.

---

## Pattern 7: Function Composition

Build reusable pipeline functions:

```python
from typing import Callable

def result_compose(*funcs: Callable[[int], Result[int, str]]) -> Callable[[int], Result[int, str]]:
    """Compose functions that return Result."""
    def composed(x: int) -> Result[int, str]:
        result = Ok(x)
        for func in funcs:
            result = result.and_then(func)
        return result
    return composed

# Define clean operations
def add_five(x: int) -> Result[int, str]:
    return Ok(x + 5)

def divide_by_two(x: int) -> Result[int, str]:
    return divide(x, 2)

# Compose them
pipeline = result_compose(
    add_five,
    divide_by_two,
    add_five,
)

pipeline(10)  # Ok(15)
```

---

## Pattern 8: Match/Case Pattern (Python 3.10+)

Explicit handling of success/error:

```python
from results import Ok, Err

result = divide(20, 5)

match result:
    case Ok(value):
        print(f"Success: {value}")
    case Err(error):
        print(f"Error: {error}")
        # Handle error specifically
        if "division" in error:
            print("Division error detected")
```

**Benefits**: Exhaustive checking, more readable than conditionals.

---

## Pattern 9: Bulk Operations

Handle collections of Results:

```python
from results import Ok, Err

results = [
    divide(20, 2),   # Ok(10)
    divide(30, 3),   # Ok(10)
    divide(10, 0),   # Err("division by zero")
]

# Collect successes and errors
successes = [r.unwrap_or(0) for r in results]  # [10, 10, 0]
errors = [r.err() for r in results if r.is_err()]  # ["division by zero"]

# Map over all, collect first error
def all_double(items: list[Result[int, str]]) -> Result[list[int], str]:
    result = Ok([])
    for item in items:
        result = result.and_then(lambda acc:
            item.map(lambda x: acc + [x * 2])
        )
    return result

all_double(results)  # Err("division by zero")
```

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Unwrap Without Context

```python
# BAD: No error info if it fails
value = result.unwrap()

# GOOD: Provide default or context
value = result.unwrap_or(0)
# or
value = result.context("processing order").unwrap_or_else(lambda e: {
    print(f"Failed: {e}")
    return 0
})
```

### ❌ Anti-Pattern 2: Ignoring Results

```python
# BAD: Silently ignoring errors
process_payment(order_id)

# GOOD: Explicitly handle error
process_payment(order_id).context("processing payment").or_else(lambda e: {
    log_error(e)
    return Err(e)
})
```

### ❌ Anti-Pattern 3: Raising Inside Maps

```python
# BAD: Mixing Result with exceptions
result.map(lambda x: risky_operation(x))  # Exception breaks the flow

# GOOD: Return Result from map
result.and_then(lambda x: 
    try_risky_operation(x)  # Returns Result
)
```

### ❌ Anti-Pattern 4: Mixing Exception Handling

```python
# BAD: Inconsistent error handling
try:
    value = fetch_user(123).unwrap()
except Exception as e:
    # Only catches unwrap failures, not business logic
    pass

# GOOD: Consistent Result handling
fetch_user(123).or_else(lambda e: {
    log_error(e)
    return Ok(default_user())
}).map(lambda u: u.name)
```

---

## Real-World Example: API Handler

```python
from results import Ok, Err, Result
import json

def validate_json(data: str) -> Result[dict, str]:
    try:
        return Ok(json.loads(data))
    except json.JSONDecodeError as e:
        return Err(f"invalid json: {e}")

def validate_email(data: dict) -> Result[str, str]:
    email = data.get("email")
    if not email:
        return Err("email missing")
    if "@" not in email:
        return Err("invalid email format")
    return Ok(email)

def validate_age(data: dict) -> Result[int, str]:
    age = data.get("age")
    if not isinstance(age, int):
        return Err("age must be integer")
    if age < 18 or age > 120:
        return Err("age outside valid range")
    return Ok(age)

def process_request(json_body: str) -> Result[dict, str]:
    """Pipeline: parse → validate → save."""
    return (
        validate_json(json_body)
        .context("parsing request body")
        .and_then(lambda data: 
            validate_email(data)
            .and_then(lambda email:
                validate_age(data)
                .map(lambda age: {"email": email, "age": age})
            )
        )
        .context("validating user data")
    )

# Usage in FastAPI
@app.post("/users")
def create_user(body: str):
    return (
        process_request(body)
        .map(lambda data: save_user(data))
        .unwrap_or_else(lambda error: {
            "status": "error",
            "message": error,
        })
    )
```

---

## Testing with Results

```python
from results import Ok, Err

def test_divide_success():
    result = divide(20, 4)
    assert result.is_ok()
    assert result.ok() == 5

def test_divide_by_zero():
    result = divide(20, 0)
    assert result.is_err()
    assert "division" in result.err()

def test_error_context():
    result = divide(20, 0).context("dividing numbers")
    error_str = result.context("in pipeline").unwrap_or_else(lambda e: e)
    # Can verify context chain in tests
```

---

## Key Takeaways

1. **Prefer chaining over conditionals** — Use `.map()` and `.and_then()` for cleaner code
2. **Add context early** — Use `.context()` to build diagnostic chains
3. **Use pattern matching** — Python 3.10+ match/case for explicit handling
4. **Compose small functions** — Build pipelines from simple, testable parts
5. **Choose Result type carefully** — Result for errors, Maybe for absence, Either for two outcomes

**Next**: Check [Async Workflows](./async-workflows.md) for async patterns.
