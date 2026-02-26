# Pattern Matching Guide

Using Python 3.10+ `match/case` syntax with Results, Maybe, and Either.

## Why Pattern Matching?

Pattern matching provides exhaustive, type-safe handling of monad variants:

```python
# ❌ Traditional if/else (verbose)
if result.is_ok():
    value = result.ok()
    process(value)
else:
    error = result.err()
    handle_error(error)

# ✅ Pattern matching (clear intent)
match result:
    case Ok(value):
        process(value)
    case Err(error):
        handle_error(error)
```

---

## Basic Patterns

### Result[T, E]

```python
from results import Ok, Err

result = Ok(42)

match result:
    case Ok(value):
        print(f"Success: {value}")
    case Err(error):
        print(f"Error: {error}")
```

### Maybe[T]

```python
from results import Some, Nothing

maybe = Some(10)

match maybe:
    case Some(x):
        print(f"Value: {x}")
    case Nothing():
        print("No value")
```

### Either[L, R]

```python
from results import Left, Right

either = Left("left value")

match either:
    case Left(value):
        print(f"Left: {value}")
    case Right(value):
        print(f"Right: {value}")
```

---

## Guard Clauses

Add conditions to patterns:

```python
result = Ok(100)

match result:
    case Ok(value) if value > 50:
        print(f"Large value: {value}")
    case Ok(value):
        print(f"Small value: {value}")
    case Err(error):
        print(f"Error: {error}")
```

---

## Nested Patterns

Pattern match across multiple values:

```python
result1 = Ok(10)
result2 = Ok(20)

match (result1, result2):
    case (Ok(x), Ok(y)):
        print(f"Both succeeded: {x}, {y}")
    case (Ok(x), Err(e)):
        print(f"Second failed: {e}")
    case (Err(e), _):
        print(f"First failed: {e}")
```

---

## Extracting and Transforming

```python
from results import Ok, Err

results = [Ok(1), Ok(2), Err("x"), Ok(3)]

for result in results:
    match result:
        case Ok(value):
            print(f"Processing: {value * 2}")
        case Err(error):
            print(f"Skipping error: {error}")
```

---

## Real-World: API Response Handler

```python
from results import Ok, Err
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

def handle_user_response(result) -> str:
    match result:
        # Success with specific user
        case Ok(User(id=123, name=name)):
            return f"Admin user: {name}"
        
        # Success with any user
        case Ok(User(name=name, email=email)):
            return f"User {name} ({email})"
        
        # Specific errors
        case Err(error) if "not found" in error:
            return "User doesn't exist"
        case Err(error) if "timeout" in error:
            return "Request timed out"
        
        # Generic error
        case Err(error):
            return f"Error: {error}"

# Usage
user = Ok(User(id=1, name="Alice", email="alice@example.com"))
print(handle_user_response(user))  # "User Alice (alice@example.com)"
```

---

## Pattern Matching in Pipelines

```python
from results import Ok, Err

def validate_and_process(data: dict):
    result = validate(data)
    
    # Can use pattern match instead of .map()/.or_else()
    match result:
        case Ok(valid_data):
            return process(valid_data)
        case Err(error):
            return {"error": error, "code": 400}
```

---

## Advanced: Structural Patterns

```python
from results import Ok, Err
from typing import Union

data: Union[Ok[dict], Err[str]] = Ok({"user": {"id": 1, "name": "Alice"}})

match data:
    # Nested structure matching
    case Ok({"user": {"id": user_id, "name": name}}):
        print(f"User {user_id}: {name}")
    
    # With sequence patterns
    case Ok({"items": [first, second, *rest]}):
        print(f"First: {first}, Second: {second}, Rest: {len(rest)}")
    
    case _:
        print("No match")
```

---

## Comparison: Traditional vs Pattern Matching

### Traditional Approach

```python
def process(result):
    if result.is_ok():
        value = result.ok()
        if isinstance(value, dict):
            if "error" in value:
                print(f"Nested error: {value['error']}")
            else:
                print(f"Success: {value}")
        else:
            print(f"Other type: {value}")
    else:
        error = result.err()
        if "timeout" in error:
            print("Timeout")
        else:
            print(f"Error: {error}")
```

### Pattern Matching Approach

```python
def process(result):
    match result:
        case Ok({"error": msg}):
            print(f"Nested error: {msg}")
        case Ok({"status": "ok"}):
            print(f"Success")
        case Ok(value):
            print(f"Other type: {value}")
        case Err(error) if "timeout" in error:
            print("Timeout")
        case Err(error):
            print(f"Error: {error}")
```

---

## Testing with Pattern Matching

```python
import pytest
from results import Ok, Err, Some, Nothing

class TestPatternMatching:
    def test_ok_value(self):
        result = Ok(42)
        match result:
            case Ok(value):
                assert value == 42
            case _:
                pytest.fail("Expected Ok")
    
    def test_maybe_nothing(self):
        maybe = Nothing()
        match maybe:
            case Some(_):
                pytest.fail("Expected Nothing")
            case Nothing():
                pass  # Success

    def test_error_with_guard(self):
        result = Err("timeout error")
        handled = False
        
        match result:
            case Err(msg) if "timeout" in msg:
                handled = True
        
        assert handled
```

---

## Best Practices

1. **Use patterns for control flow** — More readable than `.map()` chains when extracting values
2. **Use guards for conditions** — Better than nested matches
3. **Use `_` for wildcards** — When you don't care about value
4. **Exhaust all branches** — Compiler warns if missing cases
5. **Keep patterns simple** — Deep nesting becomes hard to read

---

## When to Use Each Approach

| Situation | Use |
|-----------|-----|
| Sequential transformations | `.map()` / `.and_then()` |
| Conditional branching | `match/case` |
| Side effects per branch | `match/case` |
| Complex nested structures | `match/case` |
| Chaining errors | `.map()` / `.and_then()` |

---

**Examples**: See [with_pydantic.py](../examples/with_pydantic.py) and [with_fastapi.py](../examples/with_fastapi.py) for real-world patterns.
