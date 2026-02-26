# API Reference

Complete documentation for all types and methods in the Results library.

## Table of Contents

- [Result[T, E]](#resultt-e) — Success or Error
- [Maybe[T]](#maybett) — Value or Nothing
- [Either[L, R]](#eitherlr) — Two Symmetric Outcomes
- [AsyncResult[T, E]](#asyncresultt-e) — Async Result
- [AsyncMaybe[T]](#asyncmaybett) — Async Maybe
- [AsyncEither[L, R]](#asynceitherlr) — Async Either
- [Exceptions](#exceptions)
- [Helper Functions](#helper-functions)

---

## Result[T, E]

Represents either a success value (`Ok(T)`) or an error (`Err(E)`).

### Creation

```python
from results import Ok, Err, Result

success: Result[int, str] = Ok(42)
error: Result[int, str] = Err("something went wrong")

# From function that may raise
def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"invalid: {s}")
```

### Variant Checking

| Method | Returns | Example |
|--------|---------|---------|
| `is_ok()` | `bool` | `Ok(1).is_ok()` → `True` |
| `is_err()` | `bool` | `Err("x").is_err()` → `True` |
| `ok()` | `T \| None` | `Ok(1).ok()` → `1` |
| `err()` | `E \| None` | `Err("x").err()` → `"x"` |

### Transformations

#### `map(op: Callable[[T], U]) -> Result[U, E]`

Transform success value (no-op on error).

```python
Ok(5).map(lambda x: x * 2)          # Ok(10)
Err("error").map(lambda x: x * 2)   # Err("error")
```

#### `map_err(op: Callable[[E], F]) -> Result[T, F]`

Transform error value (no-op on success).

```python
Err("error").map_err(str.upper)     # Err("ERROR")
Ok(5).map_err(str.upper)            # Ok(5)
```

#### `and_then(op: Callable[[T], Result[U, E]]) -> Result[U, E]`

Chain operations (flatMap / bind).

```python
Ok(5).and_then(lambda x: Ok(x * 2))           # Ok(10)
Ok(5).and_then(lambda x: Err("failed"))       # Err("failed")
Err("error").and_then(lambda x: Ok(x))        # Err("error")
```

#### `or_else(op: Callable[[E], Result[T, F]]) -> Result[T, F]`

Recover from error.

```python
Err("error").or_else(lambda e: Ok(0))         # Ok(0)
Ok(5).or_else(lambda e: Ok(0))                # Ok(5)
```

### Extraction

#### `unwrap() -> T`

Extract success value or raise exception.

```python
Ok(42).unwrap()         # 42
Err("fail").unwrap()    # raises Exception
```

#### `unwrap_or(default: T) -> T`

Extract success value or return default.

```python
Ok(42).unwrap_or(0)     # 42
Err("fail").unwrap_or(0)  # 0
```

#### `unwrap_or_else(f: Callable[[E], T]) -> T`

Extract success value or compute default from error.

```python
Ok(42).unwrap_or_else(lambda e: 0)       # 42
Err("fail").unwrap_or_else(lambda e: len(e))  # 4
```

#### `unwrap_err() -> E`

Extract error value or raise exception.

```python
Err("fail").unwrap_err()    # "fail"
Ok(42).unwrap_err()         # raises Exception
```

### Inspection (Side Effects)

#### `inspect(f: Callable[[T], None]) -> Result[T, E]`

Execute function with success value (for debugging).

```python
Ok(42).inspect(print)       # prints 42, returns Ok(42)
Err("fail").inspect(print)  # no-op, returns Err("fail")
```

#### `inspect_err(f: Callable[[E], None]) -> Result[T, E]`

Execute function with error value (for debugging).

```python
Err("fail").inspect_err(print)  # prints fail, returns Err("fail")
Ok(42).inspect_err(print)       # no-op, returns Ok(42)
```

### Context Chains (Debugging)

#### `context(msg: str) -> Result[T, E]`

Add diagnostic context message to error chain (LIFO stack).

```python
result = Err("database error")
result.context("updating user").context("processing request")
# On unwrap, shows full chain for tracing
```

#### `with_context(f: Callable[[], str]) -> Result[T, E]`

Add lazy-evaluated context (computed only if needed).

```python
result.with_context(lambda: f"user_id={expensive_lookup()}")
```

---

## Maybe[T]

Represents either a value (`Some(T)`) or absence (`Nothing()`).

### Creation

```python
from results import Some, Nothing, Maybe

value: Maybe[int] = Some(42)
absence: Maybe[int] = Nothing()
```

### Variant Checking

| Method | Returns | Example |
|--------|---------|---------|
| `is_some()` | `bool` | `Some(1).is_some()` → `True` |
| `is_nothing()` | `bool` | `Nothing().is_nothing()` → `True` |
| `some()` | `T \| None` | `Some(1).some()` → `1` |

### Transformations

#### `map(op: Callable[[T], U]) -> Maybe[U]`

Transform value (no-op on Nothing).

```python
Some(5).map(lambda x: x * 2)         # Some(10)
Nothing().map(lambda x: x * 2)       # Nothing()
```

#### `filter(predicate: Callable[[T], bool]) -> Maybe[T]`

Keep value if predicate is True, otherwise Nothing.

```python
Some(5).filter(lambda x: x > 0)      # Some(5)
Some(-5).filter(lambda x: x > 0)     # Nothing()
```

#### `and_then(op: Callable[[T], Maybe[U]]) -> Maybe[U]`

Chain operations (flatMap).

```python
Some(5).and_then(lambda x: Some(x * 2))    # Some(10)
Some(5).and_then(lambda x: Nothing())      # Nothing()
```

#### `or_else(op: Callable[[], Maybe[T]]) -> Maybe[T]`

Use default if Nothing.

```python
Nothing().or_else(lambda: Some(0))    # Some(0)
Some(5).or_else(lambda: Some(0))      # Some(5)
```

### Extraction

#### `unwrap() -> T`

Extract value or raise exception.

```python
Some(42).unwrap()       # 42
Nothing().unwrap()      # raises Exception
```

#### `unwrap_or(default: T) -> T`

Extract value or return default.

```python
Some(42).unwrap_or(0)   # 42
Nothing().unwrap_or(0)  # 0
```

#### `unwrap_or_else(f: Callable[[], T]) -> T`

Extract value or compute default.

```python
Some(42).unwrap_or_else(lambda: 0)    # 42
Nothing().unwrap_or_else(lambda: 0)   # 0
```

---

## Either[L, R]

Represents two symmetric outcomes: `Left(L)` or `Right(R)`.

Unlike Result (where left is always error), Either treats both branches equally.

### Creation

```python
from results import Left, Right, Either

left_value: Either[str, int] = Left("error")
right_value: Either[str, int] = Right(42)
```

### Variant Checking

| Method | Returns | Example |
|--------|---------|---------|
| `is_left()` | `bool` | `Left("x").is_left()` → `True` |
| `is_right()` | `bool` | `Right(1).is_right()` → `True` |
| `left()` | `L \| None` | `Left("x").left()` → `"x"` |
| `right()` | `R \| None` | `Right(1).right()` → `1` |

### Transformations (Right-biased)

#### `map(op: Callable[[R], U]) -> Either[L, U]`

Transform right value (no-op on left).

```python
Right(5).map(lambda x: x * 2)      # Right(10)
Left("error").map(lambda x: x * 2) # Left("error")
```

#### `map_left(op: Callable[[L], V]) -> Either[V, R]`

Transform left value (no-op on right).

```python
Left("error").map_left(str.upper)   # Left("ERROR")
Right(5).map_left(str.upper)        # Right(5)
```

#### `bimap(f: Callable[[L], V], g: Callable[[R], U]) -> Either[V, U]`

Transform both branches simultaneously.

```python
Left("error").bimap(str.upper, lambda x: x * 2)    # Left("ERROR")
Right(5).bimap(str.upper, lambda x: x * 2)         # Right(10)
```

#### `and_then(op: Callable[[R], Either[L, U]]) -> Either[L, U]`

Chain operations (flatMap on right).

```python
Right(5).and_then(lambda x: Right(x * 2))          # Right(10)
Right(5).and_then(lambda x: Left("error"))         # Left("error")
```

#### `and_then_left(op: Callable[[L], Either[V, R]]) -> Either[V, R]`

Chain operations on left.

```python
Left("error").and_then_left(lambda e: Left(e.upper()))  # Left("ERROR")
Right(5).and_then_left(lambda e: Left(e))              # Right(5)
```

### Extraction

#### `unwrap_right() -> R`

Extract right value or raise exception.

```python
Right(42).unwrap_right()    # 42
Left("error").unwrap_right()  # raises Exception
```

#### `unwrap_left() -> L`

Extract left value or raise exception.

```python
Left("error").unwrap_left()  # "error"
Right(42).unwrap_left()      # raises Exception
```

#### `unwrap_right_or(default: R) -> R`

Extract right value or return default.

```python
Right(42).unwrap_right_or(0)    # 42
Left("error").unwrap_right_or(0)  # 0
```

---

## AsyncResult[T, E]

Async wrapper for `Result[T, E]` with awaitable API.

```python
from results import AsyncResult, Ok, Err

async def fetch() -> AsyncResult[dict, str]:
    async def resolver():
        try:
            data = await fetch_data()
            return Ok(data)
        except Exception as e:
            return Err(str(e))
    
    return AsyncResult.from_awaitable(resolver())

# Usage
result = await fetch().map_async(lambda x: x.get("name"))
```

### Factory Methods

#### `from_result(result: Result[T, E]) -> AsyncResult[T, E]`

Wrap synchronous Result.

```python
result = Ok(42)
async_result = AsyncResult.from_result(result)
await async_result  # Ok(42)
```

#### `from_awaitable(awaitable: Awaitable[Result[T, E]]) -> AsyncResult[T, E]`

Create from awaitable returning Result.

```python
async def get_data():
    return Ok(42)

result = AsyncResult.from_awaitable(get_data())
await result  # Ok(42)
```

### Async Transformations

#### `map_async(op: Callable[[T], Awaitable[U]]) -> AsyncResult[U, E]`

Transform success value asynchronously.

```python
async def double(x):
    return x * 2

await Ok(5).map_async(double)  # Ok(10)
```

#### `and_then_async(op: Callable[[T], Awaitable[Result[U, E]]]) -> AsyncResult[U, E]`

Chain async operations.

```python
async def validate(x):
    return Ok(x * 2) if x > 0 else Err("negative")

await Ok(5).and_then_async(validate)  # Ok(10)
```

---

## AsyncMaybe[T]

Async wrapper for `Maybe[T]`.

Similar API to AsyncResult, with `map_async`, `and_then_async`, etc.

---

## AsyncEither[L, R]

Async wrapper for `Either[L, R]`.

Similar API to Either with full async support (`map_async`, `map_left_async`, `bimap_async`, etc.).

---

## Exceptions

### `UnwrapError`

Raised when unwrap operations fail.

```python
from results import UnwrapError

try:
    Err("failed").unwrap()
except UnwrapError as e:
    print(e)  # Shows error with context chain
```

---

## Helper Functions

### Result Helpers

```python
from results import result  # helpers submodule

# flatten(Result[T, Result[T, E]]) -> Result[T, E]
flatten(Ok(Ok(42)))  # Ok(42)

# swap(Result[T, E]) -> Result[E, T]
swap(Ok(42))  # Err(42)

# partition(Sequence[Result[T, E]]) -> (List[T], List[E])
successes, errors = partition([Ok(1), Err("x"), Ok(2)])
```

### Maybe Helpers

```python
from results import maybe  # helpers submodule

# flatten(Maybe[Maybe[T]]) -> Maybe[T]
flatten(Some(Some(42)))  # Some(42)

# transpose(Maybe[Result[T, E]]) -> Result[Maybe[T], E]
transpose(Some(Ok(42)))  # Ok(Some(42))
```

### Either Helpers

```python
from results import either  # helpers submodule

# flatten(Either[L, Either[L, R]]) -> Either[L, R]
flatten(Right(Right(42)))  # Right(42)

# swap(Either[L, R]) -> Either[R, L]
swap(Left("x"))  # Right("x")

# partition(Sequence[Either[L, R]]) -> (List[L], List[R])
lefts, rights = partition([Left("x"), Right(1), Left("y")])
```

---

## Common Patterns

### Chaining Multiple Operations

```python
from results import Ok

result = (
    Ok(10)
    .map(lambda x: x * 2)
    .map(lambda x: x + 5)
    .and_then(lambda x: Ok(x) if x > 20 else Err("too small"))
)
```

### Combining Multiple Results

```python
def combine(r1: Result[int, str], r2: Result[int, str]):
    return r1.and_then(lambda x: 
        r2.map(lambda y: x + y)
    )
```

### Async Request Workflow

```python
async def get_user_orders(user_id: int):
    return (
        await fetch_user(user_id)
        .map_async(lambda user: fetch_orders(user.id))
        .map_async(lambda orders: [order.total for order in orders])
    )
```

---

## Type Hints

All types are fully annotated for mypy --strict:

```python
from typing import TypeVar

T = TypeVar("T")
E = TypeVar("E")

def process(result: Result[int, str]) -> Result[int, str]:
    return result.map(lambda x: x * 2)
```

---

**See the [Guides](./guides/) for more detailed patterns and best practices.**
