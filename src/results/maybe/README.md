# Maybe Type — Presence or Absence

The `Maybe[T]` type represents an optional value: either `Some[T]` (value present) or `Nothing` (value absent). Unlike `Result[T, E]` which distinguishes success from failure, **Maybe only tracks presence/absence—not errors**.

**Quick links:** See [root README](../../README.md) for complete documentation and tutorials.

---

## Overview

Maybe is for when a value **may or may not exist**, without error semantics:

```python
from results import Some, Nothing, Maybe

def find_user(user_id: int) -> Maybe[dict]:
    users = {1: {"name": "Alice"}}
    return Some(users[user_id]) if user_id in users else Nothing()

user = find_user(1).map(lambda u: u["name"])  # Some("Alice")
missing = find_user(999).map(lambda u: u["name"])  # Nothing
```

---

## Directory Structure

```
maybe/
├── __init__.py          # Public API exports
├── sync/
│   ├── some.py         # Some[T] implementation
│   ├── nothing.py      # Nothing implementation
│   └── helpers.py      # flatten, transpose, map_or, etc.
└── asyncio/
    └── maybe.py        # AsyncMaybe[T] implementation
```

- **sync/** — Synchronous operations (blocking)
- **asyncio/** — Asynchronous operations (non-blocking)

---

## Result vs Maybe

| Aspect | Result[T, E] | Maybe[T] |
|--------|--------------|----------|
| **Semantics** | Success or Failure | Presence or Absence |
| **Ok/Err** | `Ok(value)`, `Err(error)` | `Some(value)`, `Nothing` |
| **Absence** | Not used | Represents missing value |
| **Error Info** | Carries error details | No error semantics |
| **Use Case** | Operations that can fail | Optional lookups |

**Choose Result when:** operation can fail with meaningful error  
**Choose Maybe when:** value may simply not exist

---

## Quick API Reference

### Some[T] — Presence Variant

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_some()` | `() -> bool` | Check if Some |
| `is_nothing()` | `() -> bool` | Always False |
| `map(op)` | `(T -> U) -> Some[U]` | Transform value |
| `filter(pred)` | `(T -> bool) -> Maybe[T]` | Some if predicate true, else Nothing |
| `and_then(op)` | `(T -> Maybe[U]) -> Maybe[U]` | Chain Maybe operations |
| `or_else(op)` | `(Callable[[], Maybe[T]]) -> Some[T]` | No-op (return self) |
| `inspect(f)` | `(T -> None) -> Some[T]` | Debug: call side-effect, return unchanged |
| `unwrap()` | `() -> T` | Extract value or raise UnwrapError |
| `unwrap_or(default)` | `(T) -> T` | Extract value or return default |
| `unwrap_or_else(f)` | `(Callable[[], T]) -> T` | Extract value or compute default |
| `zip(other)` | `(Maybe[U]) -> Maybe[(T, U)]` | Combine two Maybes |
| `zip_with(other, f)` | `(Maybe[U], (T, U) -> V) -> Maybe[V]` | Combine and transform |
| `context(msg)` | `(str) -> Some[T]` | Add context (no-op for Some) |
| `with_context(f)` | `(Callable[[], str]) -> Some[T]` | Add lazy context (no-op for Some) |

### Nothing — Absence Variant

| Method | Signature | Description |
|--------|-----------|-------------|
| `is_some()` | `() -> bool` | Always False |
| `is_nothing()` | `() -> bool` | Check if Nothing |
| `map(op)` | `(T -> U) -> Nothing` | Short-circuit |
| `filter(pred)` | `(T -> bool) -> Nothing` | Return self |
| `and_then(op)` | `(T -> Maybe[U]) -> Nothing` | Short-circuit |
| `or_else(op)` | `(Callable[[], Maybe[T]]) -> Maybe[T]` | Execute alternative |
| `inspect(f)` | `(T -> None) -> Nothing` | No-op |
| `unwrap()` | `() -> Never` | Always raises UnwrapError |
| `unwrap_or(default)` | `(T) -> T` | Return default |
| `unwrap_or_else(f)` | `(Callable[[], T]) -> T` | Compute default |
| `zip(other)` | `(Maybe[U]) -> Nothing` | Short-circuit |
| `zip_with(other, f)` | `(Maybe[U], ...) -> Nothing` | Short-circuit |
| `context(msg)` | `(str) -> Nothing` | Push context (LIFO stack) |
| `with_context(f)` | `(Callable[[], str]) -> Nothing` | Push lazy context |

### Helper Functions

| Function | Signature | Description |
|----------|-----------|-------------|
| `flatten(m)` | `(Maybe[Maybe[T]]) -> Maybe[T]` | Flatten nested Maybe |
| `transpose(m)` | `(Maybe[list[T]]) -> list[Maybe[T]]` | Convert structure |
| `map_or(m, f, default)` | `(Maybe[T], T -> U, U) -> U` | Map with default |
| `get_or_insert(m, default)` | `(Maybe[T], T) -> T` | Get value or insert default |

### AsyncMaybe[T]

| Method | Signature | Description |
|--------|-----------|-------------|
| `map_async(fn)` | `(T -> Awaitable[U]) -> AsyncMaybe[U]` | Async transformation |
| `and_then_async(op)` | `(T -> Awaitable[Maybe[U]]) -> AsyncMaybe[U]` | Async chain |
| `or_else_async(op)` | `(Callable[[], Awaitable[Maybe[T]]]) -> AsyncMaybe[T]` | Async alternative |
| `inspect_async(f)` | `(T -> Awaitable[None]) -> AsyncMaybe[T]` | Async debug |
| `unwrap_async()` | `async () -> T` | Async unwrap |
| `unwrap_or_async(default)` | `async (T) -> T` | Async unwrap with default |
| `unwrap_or_else_async(f)` | `async (Callable[[], Awaitable[T]]) -> T` | Async compute default |
| `context(msg)` | `(str) -> AsyncMaybe[T]` | Add context |
| `with_context(f)` | `(Callable[[], str]) -> AsyncMaybe[T]` | Add lazy context |

---

## Quick Examples

### Basic Usage

```python
from results import Some, Nothing

# Create
value = Some(42)
empty = Nothing()

# Check
assert value.is_some()
assert empty.is_nothing()

# Extract
assert value.unwrap() == 42
assert empty.unwrap_or(0) == 0
```

### Functional Chain

```python
result = (
    Some(5)
    .map(lambda x: x * 2)
    .filter(lambda x: x > 5)
    .map(lambda x: x + 1)
)
assert result.unwrap() == 11
```

### Finding with Fallback

```python
def find_user(user_id: int) -> Maybe[str]:
    users = {1: "Alice", 2: "Bob"}
    return Some(users[user_id]) if user_id in users else Nothing()

# Fallback to default
name = find_user(999).unwrap_or("Anonymous")

# Lazy compute default
name = find_user(999).unwrap_or_else(lambda: "Guest_" + str(time()))
```

### Chaining with `and_then()`

```python
def get_user_age(user_id: int) -> Maybe[int]:
    # ... lookup ...
    return Some(25) if user_id == 1 else Nothing()

def categorize_age(age: int) -> Maybe[str]:
    return Some("Adult") if age >= 18 else Nothing()

result = (
    get_user_age(1)
    .and_then(categorize_age)
)
assert result.unwrap() == "Adult"
```

### Combining Maybes with `zip()`

```python
first_name = Some("Alice")
last_name = Some("Smith")

full_name = (
    first_name
    .zip(last_name)
    .map(lambda names: f"{names[0]} {names[1]}")
)
assert full_name.unwrap() == "Alice Smith"

# If any is Nothing, result is Nothing
first_name = Some("Alice")
last_name = Nothing()

full_name = first_name.zip(last_name)
assert full_name.is_nothing()
```

### Filtering Values

```python
age = Some(15)

# Filter: Some if predicate true, else Nothing
is_adult = age.filter(lambda a: a >= 18)
assert is_adult.is_nothing()

result = age.filter(lambda a: a >= 10).map(lambda a: a + 1)
assert result.unwrap() == 16
```

### Async Example

```python
from results import AsyncMaybe, Some

async def fetch_user(user_id: int) -> AsyncMaybe[dict]:
    async def fetch():
        # Simulated async lookup
        return Some({"id": 1, "name": "Alice"}) if user_id > 0 else Nothing()
    return AsyncMaybe.from_awaitable(fetch())

async def main():
    user = (
        fetch_user(1)
        .map_async(lambda u: u["name"].upper())
    )
    name = await user.unwrap_async()
```

### Pattern Matching (Python 3.10+)

```python
from results import Some, Nothing

value = Some(42)
match value:
    case Some(n):
        print(f"Found: {n}")
    case Nothing():
        print("Not found")
```

---

## Common Patterns

### Option Chain with Defaults

```python
result = (
    find_config()
    .or_else(lambda: find_env_var())
    .or_else(lambda: Some(DEFAULT_CONFIG))
    .unwrap()
)
```

### Transform or Nothing

```python
user = find_user(1).and_then(lambda u: Some(u["role"]) if "role" in u else Nothing())
```

### Collect Some Values

```python
maybes = [Some(1), Nothing(), Some(3), Nothing(), Some(5)]
values = [v.unwrap() for v in maybes if v.is_some()]
# [1, 3, 5]
```

---

## See Also

- **Root README** — [Complete tutorial and API reference](../../README.md)
- **Result Type** — [Success/failure handling](../result/README.md)
- **Core Contracts** — [Abstract base classes](../core/)
