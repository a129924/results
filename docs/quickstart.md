# Quickstart (5 minutes)

Get up and running with Results in 5 minutes.

## Installation

```bash
pip install results
# or with uv
uv add results
```

## The Problem Results Solve

### Traditional Python (Error-prone)

```python
def get_user(user_id: int) -> dict:
    try:
        response = requests.get(f"/api/users/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return None  # ❌ What does None mean here?
        raise  # ❌ Inconsistent error handling

# Caller confusion:
user = get_user(123)
if user is None:
    # ❌ Is this "not found" or "error"?
    pass
```

### With Results (Type-safe)

```python
from results import Ok, Err, Result

def get_user(user_id: int) -> Result[dict, str]:
    try:
        response = requests.get(f"/api/users/{user_id}")
        response.raise_for_status()
        return Ok(response.json())
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return Err("user not found")
        return Err(f"server error: {e.status_code}")

# Type-safe handling:
user_result = get_user(123)
if user_result.is_ok():
    user = user_result.ok()
    print(f"Found: {user}")
else:
    error = user_result.err()
    print(f"Error: {error}")  # ✅ Clear intent
```

---

## Three Core Types

### 1. Result[T, E] — Success or Error

For operations that can fail:

```python
from results import Ok, Err

def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' is not a valid integer")

# Success case
parse_int("42").map(lambda x: x * 2).unwrap_or(0)  # 84

# Error case
parse_int("abc").map(lambda x: x * 2).unwrap_or(0)  # 0
```

### 2. Maybe[T] — Value or Absence

For optional values (like None, but type-safe):

```python
from results import Some, Nothing

def first_element(lst: list[int]) -> Maybe[int]:
    return Some(lst[0]) if lst else Nothing()

# Success case
first_element([1, 2, 3]).map(lambda x: x * 2).unwrap_or(0)  # 2

# Absence case
first_element([]).map(lambda x: x * 2).unwrap_or(0)  # 0
```

### 3. Either[L, R] — Two Symmetric Outcomes

For operations with two different non-error outcomes:

```python
from results import Left, Right

def validate_age(age: int) -> Either[str, int]:
    if age < 18:
        return Left("too young")
    elif age > 120:
        return Left("invalid age")
    else:
        return Right(age)

# Success
validate_age(25).map_right(lambda a: a + 1).unwrap_right()  # 26

# Failure
validate_age(10).map_left(lambda e: e.upper()).unwrap_left()  # "TOO YOUNG"
```

---

## Key Operations

### Transformations

```python
result = Ok(5)

# map: Transform success value
result.map(lambda x: x * 2)  # Ok(10)

# map_err: Transform error value (only on Err)
Err("error").map_err(str.upper)  # Err("ERROR")

# and_then: Chain operations (flatMap)
result.and_then(lambda x: Ok(x * 2) if x > 0 else Err("negative"))  # Ok(10)
```

### Extraction

```python
result = Ok(42)

# unwrap: Get value or raise
result.unwrap()  # 42

# unwrap_or: Get value or default
Err("error").unwrap_or(0)  # 0

# unwrap_or_else: Get value or compute default
Err("error").unwrap_or_else(lambda e: len(e))  # 5
```

### Inspection (for debugging)

```python
result = Ok(42)

# inspect: Observe success value without extracting
result.inspect(print)  # prints: 42

# inspect_err: Observe error value
Err("error").inspect_err(print)  # prints: error
```

---

## Async Operations

All types support async workflows:

```python
import asyncio
from results import AsyncResult, Ok, Err

async def fetch_user(user_id: int) -> AsyncResult[dict, str]:
    # Wraps an Awaitable[Result[dict, str]]
    async def resolver():
        try:
            response = await httpx.get(f"/api/users/{user_id}")
            response.raise_for_status()
            return Ok(response.json())
        except httpx.HTTPError:
            return Err("request failed")
    
    return AsyncResult.from_awaitable(resolver())

# Usage
async def main():
    result = await fetch_user(123).map_async(lambda u: u.get("name"))
    print(result.unwrap_or("Unknown"))

asyncio.run(main())
```

---

## Error Context (Debugging)

Track errors across operations:

```python
from results import Err

error = Err("database error")
error_with_context = (
    error
    .context("fetching product")
    .context("processing order #123")
)

# On unwrap, you get full context chain:
try:
    error_with_context.unwrap()
except Exception as e:
    print(e)
    # Shows:
    # DatabaseError: database error
    # Context:
    #   - processing order #123
    #   - fetching product
```

---

## Pattern Matching (Python 3.10+)

```python
from results import Ok, Err, Some, Nothing, Left, Right

result = Ok(42)

match result:
    case Ok(value):
        print(f"Success: {value}")
    case Err(error):
        print(f"Error: {error}")

maybe = Some(10)

match maybe:
    case Some(x):
        print(f"Value: {x}")
    case Nothing():
        print("No value")

either = Left("failed")

match either:
    case Left(error):
        print(f"Left: {error}")
    case Right(value):
        print(f"Right: {value}")
```

---

## Next Steps

- **[Full API Reference](./api-reference.md)** — All methods and types
- **[Error Handling Guide](./guides/error-handling.md)** — Best practices
- **[Async Workflows](./guides/async-workflows.md)** — Async patterns
- **[Examples](./examples/)** — Real-world use cases

---

## Common Patterns

### Option 1: Chain and Recover

```python
result = parse_int("42")
final = (
    result
    .map(lambda x: x * 2)
    .map(lambda x: x + 1)
    .or_else(lambda e: Ok(0))  # Default value on error
)
```

### Option 2: Map Multiple Values

```python
result1 = Ok(10)
result2 = Ok(20)

combined = (
    result1
    .and_then(lambda x: result2.map(lambda y: x + y))
)  # Ok(30)
```

### Option 3: Extract with Pattern Matching

```python
match result:
    case Ok(value) if value > 0:
        print(f"Positive: {value}")
    case Ok(value):
        print(f"Non-positive: {value}")
    case Err(error):
        print(f"Error: {error}")
```

---

## Ready?

Head to the [Full API Reference](./api-reference.md) or explore the [Examples](./examples/).

**Happy error handling! 🎉**
