# Results: Rust-inspired Result and Maybe Types for Python

[English](README.md) | [繁體中文](README.zh-TW.md)

A type-safe, Pythonic implementation of Rust's `Result<T, E>` and `Option<T>` types for elegant error handling and functional programming.

[![Tests](https://img.shields.io/badge/tests-488%2F488-green)](https://github.com/a129924/results)
[![Type Checking](https://img.shields.io/badge/mypy%20%2D%2Dstrict-passing-green)](https://github.com/a129924/results)
[![Code Style](https://img.shields.io/badge/ruff-all%20checks%20passed-green)](https://github.com/a129924/results)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)

## 🎯 Overview

`results` provides **two core monad types**:

### Result[T, E] - Success or Failure

A **Result type** represents either a success (`Ok[T]`) or an error (`Err[E]`). This eliminates silent failures and ensures explicit error handling through the type system.

```python
from results import Ok, Err, Result

def divide(x: int, y: int) -> Result[int, str]:
    """Divide x by y, or return error message."""
    if y == 0:
        return Err("Cannot divide by zero")
    return Ok(x // y)

# Usage: explicit error handling
result = divide(10, 2)
if result.is_ok():
    print(f"Result: {result.ok()}")  # Result: 5
else:
    print(f"Error: {result.err()}")
```

### Maybe[T] - Presence or Absence (NEW!)

A **Maybe type** represents either a value (`Some[T]`) or its absence (`Nothing`). Unlike Result, Maybe is NOT about errors—it's about optional values.

```python
from results import Some, Nothing, Maybe

def find_user(user_id: int) -> Maybe[dict]:
    """Find user by ID, or Nothing if not found."""
    if user_id < 0:
        return Nothing().context("invalid user_id")
    
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    return Some(users[user_id]) if user_id in users else Nothing()

# Usage: type-safe optional handling
maybe_user = find_user(1)
match maybe_user:
    case Some(user):
        print(f"Found: {user['name']}")  # Found: Alice
    case Nothing():
        print("User not found")
```

## ✨ Key Features

### Result[T, E] Features
- ✅ **Type-Safe Error Handling** — Result ABC enforces consistent error handling
- ✅ **Functional Chains** — `map()`, `map_err()`, `and_then()` for elegant composition
- ✅ **Error Inspection** — `inspect()` and `inspect_err()` for non-intrusive debugging
- ✅ **Comprehensive Result Type** — Handles both success and failure cases

### Maybe[T] Features
- ✅ **Optional Value Handling** — `Some[T]` and `Nothing` for type-safe optionals
- ✅ **Functional Transformations** — `map()`, `filter()`, `and_then()` without None checks
- ✅ **Value Inspection** — `inspect()` for debugging presence/absence
- ✅ **No Error Semantics** — Nothing is absence, not failure (cleaner than Result)

### Shared Features
- ✅ **Context Chain** — LIFO context stack for rich diagnostic information
- ✅ **Async/Await Support** — `AsyncResult[T, E]` for non-blocking workflows (AsyncMaybe coming soon)
- ✅ **Zero Runtime Overhead** — Frozen dataclasses, no magic
- ✅ **Python 3.10+ Native** — Uses PEP 604 union syntax (`|` instead of `Union`)
- ✅ **Flexible Types** — Support any type (Exception, str, int, dict, etc.)
- ✅ **Comprehensive Tests** — 248 tests covering sync/async unit/integration scenarios

## 📦 Installation

### For Local Development

```bash
# Clone the repository
git clone https://github.com/a129924/results.git
cd results

# Install with UV (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

### For Use as a Dependency

```bash
# Install from GitHub directly
pip install git+https://github.com/a129924/results.git

# Or with UV
uv add git+https://github.com/a129924/results.git
```

> **Note:** `results` is currently in active development and not yet published to PyPI. It's designed for internal use and trusted collaborators. For production use, consider pinning to a specific release tag.

## 🚀 Quick Start

### Result - Error Handling

```python
from results import Ok, Err, Result

# Return success
result: Result[int, str] = Ok(42)
assert result.is_ok()
assert result.ok() == 42
assert result.err() is None

# Return failure
result: Result[int, str] = Err("operation failed")
assert result.is_err()
assert result.ok() is None
assert result.err() == "operation failed"
```

### Maybe - Optional Values

```python
from results import Some, Nothing, Maybe

# Represent presence
maybe_value: Maybe[int] = Some(42)
assert maybe_value.is_some()
assert maybe_value.unwrap() == 42

# Represent absence (no error semantics)
maybe_empty: Maybe[int] = Nothing()
assert maybe_empty.is_nothing()
assert maybe_empty.unwrap_or(0) == 0  # Fallback to default
```

### Transform Values with `map()`

#### Result

```python
# Transform success value, preserve error type
result = Ok(5).map(lambda x: x * 2).map(str)
assert result.ok() == "10"

# Errors pass through unchanged
error_result = Err("failed").map(lambda x: x * 2)
assert error_result.is_err()
assert error_result.err() == "failed"
```

#### Maybe

```python
# Transform value if present
maybe_value = Some(5).map(lambda x: x * 2).map(str)
assert maybe_value.unwrap() == "10"

# Nothing passes through unchanged
maybe_empty = Nothing().map(lambda x: x * 2)
assert maybe_empty.is_nothing()
```

### Filter Values

```python
# Transform error while preserving success value
result = Err(ValueError("parse failed")).map_err(
    lambda e: RuntimeError(f"Critical: {e}")
)
assert isinstance(result.err(), RuntimeError)

# Ok values pass through unchanged
ok_result = Ok(42).map_err(RuntimeError)
assert ok_result.ok() == 42
```

### Chain Operations with `and_then()`

```python
def parse_int(s: str) -> Result[int, ValueError]:
    try:
        return Ok(int(s))
    except ValueError as e:
        return Err(e)

def validate_positive(x: int) -> Result[int, RuntimeError]:
    if x > 0:
        return Ok(x)
    return Err(RuntimeError("must be positive"))

# Chain multiple operations
result = (
    parse_int("42")
    .and_then(validate_positive)
    .map(lambda x: x * 2)
)
assert result.ok() == 84

# Errors short-circuit the chain
error_result = (
    parse_int("invalid")
    .and_then(validate_positive)  # Not called
    .map(lambda x: x * 2)           # Not called
)
assert error_result.is_err()
assert isinstance(error_result.err(), ValueError)
```

## 🔗 Real-World Example: User Registration

```python
from results import Ok, Err, Result

def register_user(email: str, password: str) -> Result[dict, Exception]:
    """Register a user with validation."""
    
    def validate_email(e: str) -> Result[str, ValueError]:
        if "@" not in e:
            return Err(ValueError("Invalid email format"))
        return Ok(e)
    
    def validate_password(p: str) -> Result[str, RuntimeError]:
        if len(p) < 8:
            return Err(RuntimeError("Password must be 8+ characters"))
        return Ok(p)
    
    def check_unique(e: str) -> Result[str, RuntimeError]:
        # Simulate database check
        if e == "admin@example.com":
            return Err(RuntimeError("Email already registered"))
        return Ok(e)
    
    # Compose validations
    return (
        validate_email(email)
        .and_then(check_unique)
        .and_then(lambda e: validate_password(password).map(lambda _: e))
        .map(lambda e: {"email": e, "password": password})
    )

# Usage
result = register_user("user@example.com", "password123")
if result.is_ok():
    user = result.ok()
    print(f"Registered: {user}")
else:
    error = result.err()
    print(f"Registration failed: {error}")
```

## ✅ Recommended Patterns

### Functional Chains (Recommended for Most Cases)

Use method chaining with `map()`, `map_err()`, and `and_then()` for clean, composable code:

```python
# ✅ RECOMMENDED: Functional style
def process_user_age(age: int) -> Result[str, str]:
    """Process user age with validation."""
    return (
        Ok(age)
        .and_then(lambda a: Ok(a) if a >= 18 else Err("Underage"))
        .map(lambda a: f"Adult age: {a}")
        .map_err(lambda e: f"Age validation failed: {e}")
    )

result = process_user_age(21)
assert result.ok() == "Adult age: 21"
```

**Benefits:**
- ✅ Clear error propagation (short-circuits on first Err)
- ✅ No intermediate variable pollution
- ✅ Composable and reusable
- ✅ Type-safe with mypy --strict

### Imperative Checks (For Complex Logic)

Use `is_ok()`, `is_err()`, `ok()`, `err()` when you need branching logic:

```python
# ✅ ACCEPTABLE: Imperative style for complex flows
result = divide(10, 2)

if result.is_err():
    # Handle errors first (fail-fast)
    logger.error(f"Division failed: {result.err()}")
    raise RuntimeError(f"Critical: {result.err()}")

# Proceed with success case
value = result.ok()
print(f"Result: {value * 2}")
```

**When to use:**
- Complex error handling with different recovery strategies
- Logging and monitoring specific error types
- Early termination based on multiple conditions

### Combining Approaches

Mix functional and imperative styles for readability:

```python
# ✅ HYBRID: Combine styles appropriately
result = (
    validate_input(user_input)
    .and_then(transform_data)
)

# Inspect the result
if result.is_err():
    error = result.err()
    if isinstance(error, ValidationError):
        return Err(f"Invalid input: {error}")
    else:
        raise UnexpectedError(error)

# Use with success value
data = result.ok()
return Ok({"processed": data})
```

## 🔍 Working with Maybe - Type-Safe Optionals

Unlike Result which models success/failure, Maybe models presence/absence. Use Maybe when a value might not exist without distinguishing "missing" from "error".

### Basic Maybe Usage

```python
from results import Some, Nothing, Maybe

def find_user_by_email(email: str) -> Maybe[dict]:
    """Find user by email, returning Maybe instead of raising."""
    users = {
        "alice@example.com": {"id": 1, "name": "Alice"},
        "bob@example.com": {"id": 2, "name": "Bob"},
    }
    return Some(users[email]) if email in users else Nothing()

# Get with default value
user = find_user_by_email("alice@example.com").unwrap_or({"name": "Guest"})
assert user["name"] == "Alice"

# Get with computed default
user = find_user_by_email("unknown@example.com").unwrap_or_else(
    lambda: {"name": "Anonymous"}
)
assert user["name"] == "Anonymous"
```

### Chaining Maybe Operations

```python
# Transform values through chain
maybe_username = (
    find_user_by_email("alice@example.com")
    .map(lambda u: u["name"])
    .map(str.upper)
)
assert maybe_username.unwrap() == "ALICE"

# Filter based on predicate
maybe_adult = find_user_by_email("alice@example.com").filter(
    lambda u: u.get("age", 0) >= 18
)
assert maybe_adult.is_some()

# Short-circuit on Nothing
find_user_by_email("unknown@example.com").map(lambda u: u["name"]).unwrap_or("Not found")
# Returns "Not found"
```

### Combining Multiple Maybes

```python
# Zip two Maybes
maybe_names = Some("Alice").zip(Some("Bob"))
assert maybe_names.unwrap() == ("Alice", "Bob")

# Zip returns Nothing if either is Nothing
maybe_names = Some("Alice").zip(Nothing())
assert maybe_names.is_nothing()

# or_else provides alternative when Nothing
maybe_value = Nothing().or_else(lambda: Some("default"))
assert maybe_value.unwrap() == "default"
```

## 🎯 Pattern Matching with match/case (Python 3.10+)

Python 3.10 introduces structural pattern matching via `match`/`case`, perfect for Result types:

### Basic Pattern Matching

```python
from results import Ok, Err, Result

def fetch_user(user_id: int) -> Result[dict, str]:
    """Fetch user by ID."""
    if user_id > 0:
        return Ok({"id": user_id, "name": "Alice"})
    return Err(f"Invalid ID: {user_id}")

# ✅ RECOMMENDED: Pattern matching for Result dispatch
result = fetch_user(123)
match result:
    case Ok(user):
        print(f"Found user: {user['name']}")
    case Err(error):
        print(f"Error: {error}")
```

### Comparison: if/else vs match/case

```python
# ❌ OLD: Imperative if/else (still works)
result = fetch_user(123)
if result.is_ok():
    user = result.ok()
    print(f"Found: {user['name']}")
else:
    error = result.err()
    print(f"Error: {error}")

# ✅ MODERN: Structural pattern matching (cleaner)
result = fetch_user(123)
match result:
    case Ok(user):
        print(f"Found: {user['name']}")
    case Err(error):
        print(f"Error: {error}")
```

### Complex Patterns with Type Guards

```python
from results import Ok, Err
from dataclasses import dataclass

@dataclass
class UserError:
    """Business error type."""
    code: str
    message: str

def validate_and_fetch(user_id: int) -> Result[dict, UserError | ValueError]:
    """Return different error types."""
    if user_id <= 0:
        return Err(ValueError("ID must be positive"))
    if user_id == 666:
        return Err(UserError("FORBIDDEN", "User 666 is restricted"))
    return Ok({"id": user_id, "name": "Alice"})

# ✅ Pattern match on error type
result = validate_and_fetch(666)
match result:
    case Ok(user):
        print(f"Success: {user}")
    case Err(UserError(code, message)):  # Type-specific pattern
        print(f"Business error [{code}]: {message}")
    case Err(ValueError(msg)):  # Exception type pattern
        print(f"Validation error: {msg}")
    case _:  # Catch-all
        print("Unexpected error")
```

### Real-World API Response Handler

```python
from results import Ok, Err, Result
from dataclasses import dataclass

@dataclass
class APIResponse:
    status: int
    data: dict | None = None
    error: str | None = None

def handle_api_response(response: APIResponse) -> Result[dict, str]:
    """Transform API response to Result."""
    match response:
        case APIResponse(status=200, data=data) if data is not None:
            return Ok(data)
        case APIResponse(status=404, _):
            return Err("Resource not found")
        case APIResponse(status=500, error=error):
            return Err(f"Server error: {error}")
        case APIResponse(status=code, _):
            return Err(f"Unexpected status: {code}")

# Usage with pattern matching
result = handle_api_response(APIResponse(200, {"user": "Alice"}))
match result:
    case Ok(data):
        print(f"Data: {data}")
    case Err(message):
        print(f"Failed: {message}")
```

### Chaining Results with Pattern Matching

```python
def process_and_fetch(user_id: int) -> Result[str, str]:
    """Chain multiple operations with pattern matching."""
    result = validate_and_fetch(user_id)
    
    match result:
        case Ok(user):
            # Continue with success
            enriched = enrich_user_data(user)
            return Ok(f"Processed: {enriched}")
        case Err(error):
            # Short-circuit with error
            return Err(f"Processing failed: {error}")

# Or use map/and_then for the same effect (both valid)
result = (
    validate_and_fetch(user_id)
    .and_then(enrich_user_data)
    .map(lambda u: f"Processed: {u}")
)
```

**Pattern Matching Guidelines:**
- ✅ Use `match/case` for explicit Result dispatch at API boundaries
- ✅ Use `map/and_then` for chaining transformations
- ✅ Combine both: use `match` for final result handling, `map` for intermediate transforms
- ✅ Pattern matching excels at type-based routing (different error types)

## 🔍 Debug Tools: Inspect and Context Chain

### Debug with `inspect()` and `inspect_err()`

v0.2.0 introduces debug utilities for non-intrusive inspection of intermediate values:

```python
from results import Ok, Err

# inspect() calls a function with the success value, returns unchanged
result = (
    Ok(5)
    .inspect(lambda x: print(f"Value: {x}"))  # prints "Value: 5"
    .map(lambda x: x * 2)
    .inspect(lambda x: print(f"Doubled: {x}"))  # prints "Doubled: 10"
)
assert result.ok() == 10

# inspect_err() calls a function with the error value, returns unchanged
error_result = (
    Err(ValueError("invalid input"))
    .inspect_err(lambda e: print(f"Error: {e}"))  # prints "Error: invalid input"
    .map_err(lambda e: RuntimeError(f"Wrapped: {e}"))
)
```

### Track Context with Context Chain (LIFO)

v0.2.0 adds Rust anyhow-style context chains for rich error diagnostics:

```python
from results import Err, Ok

# Build context chain (Last In, First Out)
result = (
    Err(ValueError("database connection failed"))
    .context("connecting to User service")
    .context("fetching user data")
    .context("POST /api/users")
)

# Unwrap shows the full context chain in LIFO order
try:
    result.unwrap()
except ValueError as e:
    # Error message shows full context:
    # POST /api/users
    # fetching user data
    # connecting to User service
    # database connection failed
    print(str(e))
```

**Use `with_context()` for dynamic context:**

```python
from datetime import datetime

result = (
    Err("operation failed")
    .with_context(lambda: f"at {datetime.now()}")  # Delayed evaluation
)
# Useful for expensive debug info that's only evaluated if needed
```

**Real-world example with chaining:**

```python
def validate_user_registration(email: str, age: int) -> Result[dict, str]:
    # Validate email
    if "@" not in email:
        return Err("invalid email").context("email validation")
    
    # Validate age
    if age < 18:
        return Err("underage").context("age check").context("user registration")
    
    return Ok({"email": email, "age": age})

# When error occurs, full context is preserved through the chain
result = validate_user_registration("invalid", 15)
# Error message shows:
# user registration
# age check
# underage
```
## � Error Handling: Traceback and Context

**Design Philosophy:** Like Rust's Result type, `results` intentionally does NOT auto-capture tracebacks. This gives you two clear paths:

### Path 1: Simple (No Traceback)
```python
def validate_age(age: int) -> Result[int, str]:
    if age >= 18:
        return Ok(age)
    else:
        return Err("User is underage")  # Simple but no traceback info
```

### Path 2: Preserve Traceback
```python
def validate_age_with_context(age: int) -> Result[int, Exception]:
    try:
        if age >= 18:
            return Ok(age)
        else:
            raise ValueError("User is underage")
    except (ValueError, TypeError) as e:
        return Err(e)  # Preserves exception and traceback
```

> **Note:** v0.2.0+ introduces `with_context()` and v0.3.0+ extends it to async workflows with context preservation across await boundaries.

## �📚 API Reference

### Result Type

```python
class Result[T, E](ABC, Generic[T, E]):
    """Represents either a success value (T) or an error (E)."""
    
    def is_ok(self) -> bool:
        """Check if Result is Ok."""
    
    def is_err(self) -> bool:
        """Check if Result is Err."""
    
    def ok(self) -> T | None:
        """Get the success value, or None if Err."""
    
    def err(self) -> E | None:
        """Get the error value, or None if Ok."""
    
    def map(self, op: Callable[[T], U]) -> Result[U, E]:
        """Transform success value, preserving error type."""
    
    def map_err(self, op: Callable[[E], F]) -> Result[T, F]:
        """Transform error, preserving success value."""
    
    def and_then(self, op: Callable[[T], Result[U, F]]) -> Result[U, F | E]:
        """Chain operations, automatically accumulating error types."""
    
    def inspect(self, f: Callable[[T], None]) -> Result[T, E]:
        """Non-intrusive inspection of success value (v0.2.0+)."""
    
    def inspect_err(self, f: Callable[[E], None]) -> Result[T, E]:
        """Non-intrusive inspection of error value (v0.2.0+)."""
    
    def context(self, msg: str) -> Result[T, E]:
        """Push context message to error chain (v0.2.0+)."""
    
    def with_context(self, f: Callable[[], str]) -> Result[T, E]:
        """Push lazy-evaluated context message (v0.2.0+)."""
    
    def unwrap(self) -> T:
        """Extract value or raise UnwrapError."""
```

### Ok[T]

```python
class Ok(Result[T, E]):
    """Success variant containing value T."""
    
    def __init__(self, value: T) -> None:
        self._value = value
```

### Err[E]

```python
class Err(Result[T, E]):
    """Error variant containing error E."""
    
    def __init__(self, error: E) -> None:
        self._error = error
```

### Exceptions

```python
class UnwrapError(ResultError):
    """Raised when unwrap() is called on Err."""
    
    def __init__(self, message: str, original_error: Any) -> None:
        self.message = message
        self.original_error = original_error
```

## 🔄 Async/Await Support (v0.3.0+)

AsyncResult enables non-blocking error handling with the same ergonomics as sync Result:

```python
from results import AsyncResult, Ok, Err

async def fetch_user(user_id: int) -> AsyncResult[User, FetchError]:
    """Fetch user asynchronously with error handling."""
    async def fetch() -> Result[User, FetchError]:
        try:
            user = await db.fetch_user(user_id)
            return Ok(user)
        except DBError as e:
            return Err(FetchError(str(e))).context("fetching user")
    
    return AsyncResult.from_awaitable(fetch())

# Usage: Same chaining API as sync Result
result = (
    fetch_user(123)
    .context("user service")
    .and_then_async(lambda user: validate_user_async(user))
    .map_async(lambda user: enrich_user_async(user))
)

user = await result.unwrap_async()  # Unwrap with full LIFO context chain
```

**Key Features:**
- ✅ `map_async()`, `map_err_async()`, `and_then_async()` for async chaining
- ✅ `unwrap_async()` with context chain in UnwrapError (same as sync)
- ✅ `inspect_async()`, `inspect_err_async()` for side effects
- ✅ LIFO context preservation across async boundaries
- ✅ Seamless async/sync interoperability with `asyncio.to_thread()`
- ✅ Full type safety with mypy --strict compliance

## 🧪 Testing

Run all tests:

```bash
pytest tests/
```

Run specific test categories:

```bash
# Sync tests
pytest tests/sync/ -v

# Async tests
pytest tests/async_/ -v

# Integration tests
pytest tests/integration/ -v

# Type checking
mypy src/results/ --strict

# Code style
ruff check src/results/ tests/
```

## 🏗️ Architecture

The package follows the **contract-based design pattern**:

```
src/results/
├── core/
│   ├── base.py          # Result ABC (contract)
│   ├── types.py         # TypeVar definitions
│   └── exceptions.py    # ResultError, UnwrapError
└── impl/
    └── sync/
        ├── ok.py        # Ok[T] implementation
        └── err.py       # Err[E] implementation
```

**Design Principles:**
- 🎯 **SRP (Single Responsibility)** — Each class has one reason to change
- 🔗 **CSRP (Complex Single Responsibility)** — ABC methods are cohesive
- 📦 **Low Coupling** — Implementations don't depend on each other
- 🔓 **Public API** — Three-layer exposure in `__init__.py`

## 🤝 Contributing

We follow strict code quality standards:
- ✅ 100% test coverage (or documented exceptions)
- ✅ mypy --strict with 0 errors
- ✅ ruff all checks passing
- ✅ @typing_extensions.override on all ABC implementations

## 📄 License

MIT License — see LICENSE file for details.

## 🔗 Related

- **Rust Result** — Inspiration for this library: https://doc.rust-lang.org/std/result/enum.Result.html
- **PEP 604** — Type union syntax (Python 3.10+)
- **PEP 673** — TypeVar bound parameter for generic constraints

## 📞 Support

- **Documentation** — See [docs/](docs/) for detailed guides
- **Issues** — Report bugs at https://github.com/a129924/results/issues
- **Discussions** — https://github.com/a129924/results/discussions

---

**Built with ❤️ for Python developers who love type safety.**
