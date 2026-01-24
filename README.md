# Results: Rust-inspired Result Type for Python

A type-safe, Pythonic implementation of Rust's `Result<T, E>` type for elegant error handling and functional programming.

[![Tests](https://img.shields.io/badge/tests-187%2F187-green)](https://github.com/a129924/results)
[![Type Checking](https://img.shields.io/badge/mypy%20%2D%2Dstrict-passing-green)](https://github.com/a129924/results)
[![Code Style](https://img.shields.io/badge/ruff-all%20checks%20passed-green)](https://github.com/a129924/results)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)

## 🎯 Overview

`results` provides a **Result type** that represents either a success (`Ok[T]`) or an error (`Err[E]`). This eliminates silent failures and ensures explicit error handling through the type system.

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

## ✨ Key Features

- ✅ **Type-Safe Contracts** — Result ABC enforces consistent error handling
- ✅ **Functional Chains** — `map()`, `map_err()`, `and_then()` for elegant composition
- ✅ **Debug Tools** — `inspect()` and `inspect_err()` for non-intrusive debugging
- ✅ **Context Chain** — LIFO context stack for rich error diagnostics
- ✅ **Async/Await Support** — `AsyncResult[T, E]` for non-blocking workflows
- ✅ **Zero Runtime Overhead** — Frozen dataclasses, no magic
- ✅ **Python 3.10+ Native** — Uses PEP 604 union syntax (`|` instead of `Union`)
- ✅ **Flexible Error Types** — Support any type as error (Exception, str, int, dict, etc.)
- ✅ **Comprehensive Tests** — 187 tests covering sync/async unit/integration scenarios

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

### Basic Usage

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

### Transform Values with `map()`

```python
# Transform success value, preserve error type
result = Ok(5).map(lambda x: x * 2).map(str)
assert result.ok() == "10"

# Errors pass through unchanged
error_result = Err("failed").map(lambda x: x * 2)
assert error_result.is_err()
assert error_result.err() == "failed"
```

### Handle Errors with `map_err()`

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
