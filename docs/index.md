# Results Documentation

Welcome to the **Results** library — a comprehensive toolkit for Rust-inspired monadic types in Python.

## What is Results?

Results provides type-safe error handling and optional value management through three main monad types:

- **Result[T, E]**: Represents either a success value (Ok) or an error (Err)
- **Maybe[T]**: Represents either a value (Some) or absence (Nothing)
- **Either[L, R]**: Represents two symmetric outcomes (Left/Right) for flexible branching

Each monad supports:
- ✅ **Sync operations** (Result, Maybe, Either)
- ⚙️ **Async operations** (AsyncResult, AsyncMaybe, AsyncEither)
- 🔗 **Context chains** for diagnostic tracing
- 📊 **Pattern matching** with Python 3.10+ `match/case`

## Quick Navigation

### Getting Started
- **[Quickstart (5 min)](./quickstart.md)** — Get up and running in seconds
- **[API Reference](./api-reference.md)** — Complete method documentation

### Guides
- **[Error Handling](./guides/error-handling.md)** — Best practices for Result
- **[Async Workflows](./guides/async-workflows.md)** — AsyncResult, AsyncMaybe, AsyncEither
- **[Context Chains](./guides/context-chains.md)** — Diagnostic tracing and debugging
- **[Pattern Matching](./guides/pattern-matching.md)** — Python 3.10+ match/case integration

### Examples
- **[Basic Result](./examples/basic_result.py)** — Simple Result operations
- **[Maybe vs Optional](./examples/maybe_optional.py)** — Why use Maybe?
- **[Either Validation](./examples/either_validation.py)** — Validation with Either
- **[With Pydantic](./examples/with_pydantic.py)** — Model validation integration
- **[With FastAPI](./examples/with_fastapi.py)** — Web API error handling
- **[With SQLAlchemy](./examples/with_sqlalchemy.py)** — Database query handling
- **[Async Workflow](./examples/async_workflow.py)** — End-to-end async example

### Reference
- **[Troubleshooting](./troubleshooting.md)** — Common issues and solutions

## Installation

```bash
pip install results
```

Or with `uv`:
```bash
uv add results
```

## Version

Current version: **0.5.0**

Includes: Result, Maybe, Either with full async support and common protocols for seamless interoperability.

---

## Enterprise Features

Results is designed for production use in enterprise applications:

| Feature | Benefit |
|---------|---------|
| **Type Safety** | mypy --strict compliance, zero untyped operations |
| **Context Chains** | LIFO diagnostic stacks for error tracing |
| **Async Native** | Full async/await support with operation queuing |
| **Immutability** | Frozen dataclasses prevent accidental mutations |
| **Error Composition** | Chain operations safely across sync/async boundaries |

## Module Structure

```
results/
├── core/                    # ABC contracts
│   ├── base.py             # Result[T, E] ABC
│   ├── maybe_base.py       # Maybe[T] ABC
│   ├── either_base.py      # Either[L, R] ABC
│   └── async_*_base.py     # Async ABCs
├── result/
│   ├── sync/               # Ok, Err implementations
│   └── asyncio/            # AsyncResult implementation
├── maybe/
│   ├── sync/               # Some, Nothing implementations
│   └── asyncio/            # AsyncMaybe implementation
├── either/
│   ├── sync/               # Left, Right implementations
│   └── asyncio/            # AsyncEither implementation
└── common/
    └── protocols.py        # Shared protocols (ContextAware, etc.)
```

## Quick Example

```python
from results import Ok, Err, Some, Nothing, Left, Right

# Result: Success or Error
def divide(x: int, y: int):
    if y == 0:
        return Err("division by zero")
    return Ok(x // y)

divide(10, 2).map(lambda x: x * 2).unwrap_or(0)  # 10

# Maybe: Value or Nothing
def find_user(user_id: int):
    if user_id < 0:
        return Nothing()
    return Some(f"User {user_id}")

find_user(1).map(str.upper).unwrap_or("Unknown")  # "USER 1"

# Either: Two symmetric outcomes
def validate(age: int):
    if age < 18:
        return Left("too young")
    return Right(age)

validate(21).map_right(lambda a: a + 1).unwrap_right()  # 22
```

## Next Steps

Start with the **[Quickstart](./quickstart.md)** for a 5-minute introduction, or dive into the **[Guides](./guides/error-handling.md)** for deeper understanding.

---

**Questions?** Check the [Troubleshooting](./troubleshooting.md) guide or review the [API Reference](./api-reference.md).
