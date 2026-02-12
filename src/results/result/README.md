# Result Type — Success or Failure

The `Result[T, E]` type represents either a success (`Ok[T]`) or a failure (`Err[E]`). It enables type-safe error handling without relying on exceptions or None checks.

**Quick links:** See [root README](../../README.md) for complete documentation and tutorials.

---

## Overview

Result forces explicit handling of error cases through the type system. Instead of uncaught exceptions or silent None returns, all operations must be composed through Result's API.

```python
from results import Ok, Err, Result

def divide(x: int, y: int) -> Result[int, str]:
    return Err("Cannot divide by zero") if y == 0 else Ok(x // y)

result = divide(10, 2).map(lambda x: x * 2)  # Ok(10)
```

---

## Directory Structure

```
result/
├── __init__.py          # Public API exports (Ok, Err, AsyncResult)
├── sync/
│   ├── ok.py           # Ok[T] implementation
│   └── err.py          # Err[E] implementation
└── asyncio/
    └── result.py       # AsyncResult[T, E] implementation
```

- **sync/** — Synchronous operations (blocking)
- **asyncio/** — Asynchronous operations (non-blocking)

---

## Quick API Reference

### Ok[T] — Success Variant

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_ok()` | `() -> bool` | Check if Ok |
| `is_err()` | `() -> bool` | Always False |
| `ok()` | `() -> T` | Extract success value |
| `err()` | `() -> None` | Always None |
| `map(op)` | `(T -> U) -> Ok[U]` | Transform success, preserve error |
| `map_err(op)` | `(E -> F) -> Ok[T]` | Transform error (ignored for Ok) |
| `and_then(op)` | `(T -> Result[U, F]) -> Result[U, F \| E]` | Chain operations |
| `inspect(f)` | `(T -> None) -> Ok[T]` | Debug: call side-effect, return unchanged |
| `inspect_err(f)` | `(E -> None) -> Ok[T]` | Debug: no-op for Ok |
| `context(msg)` | `(str) -> Ok[T]` | Add context (no-op for Ok) |
| `with_context(f)` | `(Callable[[], str]) -> Ok[T]` | Add lazy context (no-op for Ok) |
| `unwrap()` | `() -> T` | Extract value or raise UnwrapError |

### Err[E] — Error Variant

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_ok()` | `() -> bool` | Always False |
| `is_err()` | `() -> bool` | Check if Err |
| `ok()` | `() -> None` | Always None |
| `err()` | `() -> E` | Extract error value |
| `map(op)` | `(T -> U) -> Err[E]` | No-op (short-circuit) |
| `map_err(op)` | `(E -> F) -> Err[F]` | Transform error |
| `and_then(op)` | `(T -> Result[U, F]) -> Err[E]` | Short-circuit (ignored) |
| `inspect(f)` | `(T -> None) -> Err[E]` | Debug: no-op for Err |
| `inspect_err(f)` | `(E -> None) -> Err[E]` | Debug: call side-effect, return unchanged |
| `context(msg)` | `(str) -> Err[E]` | Push context (LIFO stack) |
| `with_context(f)` | `(Callable[[], str]) -> Err[E]` | Push lazy context (evaluated on demand) |
| `unwrap()` | `() -> Never` | Always raises UnwrapError with context chain |

### AsyncResult[T, E]

| Method | Signature | Description |
|--------|-----------|-------------|
| `map_async(fn)` | `(T -> Awaitable[U]) -> AsyncResult[U, E]` | Async transformation |
| `map_err_async(fn)` | `(E -> Awaitable[F]) -> AsyncResult[T, F]` | Async error transform |
| `and_then_async(op)` | `(T -> Awaitable[Result[U, F]]) -> AsyncResult[U, E \| F]` | Async chain |
| `inspect_async(f)` | `(T -> Awaitable[None]) -> AsyncResult[T, E]` | Async debug |
| `inspect_err_async(f)` | `(E -> Awaitable[None]) -> AsyncResult[T, E]` | Async debug error |
| `context(msg)` | `(str) -> AsyncResult[T, E]` | Add context |
| `with_context(f)` | `(Callable[[], str]) -> AsyncResult[T, E]` | Add lazy context |
| `unwrap_async()` | `async () -> T` | Async unwrap with context chain |
| `resolve()` | `async () -> Result[T, E]` | Resolve to sync Result |

---

## Quick Examples

### Basic Usage

```python
from results import Ok, Err

# Create
ok_value = Ok(42)
err_value = Err("Something failed")

# Check
assert ok_value.is_ok()
assert err_value.is_err()

# Extract
assert ok_value.ok() == 42
assert err_value.err() == "Something failed"
```

### Functional Chain

```python
result = (
    Ok(5)
    .map(lambda x: x * 2)
    .map(lambda x: x + 1)
)
assert result.ok() == 11
```

### Error Handling with `and_then()`

```python
def validate_positive(x: int) -> Result[int, str]:
    return Err("Must be positive") if x <= 0 else Ok(x)

result = (
    Ok(10)
    .and_then(validate_positive)
    .map(lambda x: x * 2)
)
assert result.ok() == 20
```

### Context Chain (Debugging)

```python
from results import Err

result = (
    Err(ValueError("Invalid format"))
    .context("Parsing JSON")
    .context("Loading config")
)

try:
    result.unwrap()
except ValueError as e:
    # Output shows full context (LIFO):
    # Loading config
    # Parsing JSON
    # Invalid format
    print(str(e))
```

### Async Example

```python
from results import AsyncResult, Ok, Err

async def fetch_data(url: str) -> AsyncResult[str, Exception]:
    async def fetch():
        # Simulated async operation
        return Ok("data") if url else Err(ValueError("Empty URL"))
    return AsyncResult.from_awaitable(fetch())

async def main():
    result = (
        fetch_data("https://example.com")
        .context("Fetching from API")
        .and_then_async(lambda data: AsyncResult.from_awaitable(...))
    )
    data = await result.unwrap_async()
```

---

## Pattern Matching (Python 3.10+)

```python
from results import Ok, Err

result = Ok(42)
match result:
    case Ok(value):
        print(f"Success: {value}")
    case Err(error):
        print(f"Error: {error}")
```

---

## Common Patterns

### Early Exit with `map_err()`

```python
result = (
    parse_config()
    .map_err(lambda e: RuntimeError(f"Config error: {e}"))
)
```

### Conditional Chaining

```python
result = (
    Ok(user_id)
    .and_then(lambda id: fetch_user(id))  # Returns Result
    .and_then(lambda user: validate_age(user))
    .map(lambda user: enrich_data(user))
)
```

### Mixing Functional and Imperative

```python
result = validate_input(data)

if result.is_err():
    logger.error(result.err())
    return Err("Validation failed")

value = result.ok()
# Process value...
```

---

## See Also

- **Root README** — [Complete tutorial and API reference](../../README.md)
- **Maybe Type** — [Optional values without error semantics](../maybe/README.md)
- **Core Contracts** — [Abstract base classes](../core/)
