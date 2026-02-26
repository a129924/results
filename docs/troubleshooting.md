# Troubleshooting

Common issues and solutions when using Results.

## Type Errors

### Type mismatch in chain

**Error**: `Type of "map" argument 1 incompatible with return type`

**Cause**: Returning wrong type from map function.

```python
# ❌ Wrong: map expects T → U, not T → Result[U, E]
Ok(5).map(lambda x: Ok(x * 2))  # Type error!

# ✅ Correct: use and_then for chaining
Ok(5).and_then(lambda x: Ok(x * 2))
```

### Err without type parameter

**Error**: `Type of "Err" is ambiguous`

**Cause**: Type inference issues.

```python
# ❌ Type cannot be inferred
errors = [Err("error1"), Err("error2")]  # What is the Ok type?

# ✅ Provide explicit type
errors: list[Result[int, str]] = [Err("error1"), Err("error2")]
```

---

## Runtime Errors

### UnwrapError on None

**Error**: `UnwrapError: Cannot unwrap None`

**Cause**: Using `.unwrap()` on error variant.

```python
# ❌ Will crash if error
value = Err("failed").unwrap()

# ✅ Use unwrap_or with default
value = Err("failed").unwrap_or(0)

# ✅ Or use pattern matching
match result:
    case Ok(v):
        value = v
    case Err(_):
        value = 0
```

### Async context issues

**Error**: `RuntimeError: no running event loop`

**Cause**: Calling async code without async context.

```python
# ❌ Wrong: not in async function
result = await fetch_user(123)

# ✅ Correct: inside async function
async def main():
    result = await fetch_user(123)

asyncio.run(main())
```

---

## Logic Errors

### Short-circuit chain stops too early

**Symptom**: Error in middle of chain skips remaining operations

**Root cause**: This is intentional! Error propagates through chain.

```python
result = (
    Ok(5)
    .and_then(lambda x: Err("failed"))  # Fails here
    .and_then(lambda x: print(x))  # This never runs
)

# To handle specific errors:
result = (
    Ok(5)
    .and_then(lambda x: Err("failed"))
    .or_else(lambda e: Ok(0))  # Recover
    .and_then(lambda x: print(x))  # Now runs
)
```

### Context not showing in error

**Symptom**: Added context but it doesn't appear in error message

**Cause**: Must unwrap to see context.

```python
# ❌ Context added but never checked
error = Err("failed").context("my context")
# Context is stored but not visible

# ✅ Context appears on unwrap
try:
    error.unwrap()
except Exception as e:
    print(e)  # Shows context
```

### Maybe with None value

**Symptom**: `Some(None)` behaves unexpectedly

**Root cause**: Some wraps the value; it can be None.

```python
# ✅ Correct usage
maybe = Some(42)
maybe = Nothing()  # Explicit absence

# Note: Some(None) is technically valid but confusing
x = Some(None)
x.is_some()  # True! (contains None value)
x.some()     # None

# Better: use Maybe[Optional[T]] in type hints
from typing import Optional
maybe: Maybe[Optional[str]] = Some(None)
```

---

## Integration Issues

### Missing imports

**Error**: `ImportError: cannot import name 'Ok'`

**Solution**:

```python
# ✅ Import from results package
from results import Ok, Err, Result

# Not from submodules:
from results.result.sync.ok import Ok  # ❌ Don't do this
from results import Ok  # ✅ Do this
```

### Mixing sync and async

**Error**: `TypeError: object is not awaitable`

**Cause**: Using sync Result with await.

```python
# ❌ Wrong: Result is not awaitable
result = Ok(5)
value = await result  # Error!

# ✅ Correct: Use AsyncResult for async
async def get_value():
    result = Ok(5)
    return result

result = await get_value()  # Ok, not awaiting Result itself
```

---

## Performance Concerns

### Context chain overhead

**Symptom**: Lots of context() calls slower than expected

**Optimization**: Use `with_context()` to defer computation.

```python
# Good: Always computed
error.context(f"computed={expensive_operation()}")

# Better: Only computed if needed
error.with_context(lambda: f"computed={expensive_operation()}")
```

### Many small Result operations

**Symptom**: Pipeline of many map/and_then calls slow

**Optimization**: Batch operations where possible.

```python
# ❌ Many intermediate Results
result = (
    Ok([1, 2, 3])
    .map(lambda x: [i*2 for i in x])
    .map(lambda x: [i+1 for i in x])
    .map(lambda x: sum(x))
)

# ✅ Fewer intermediate allocations
result = Ok([1, 2, 3]).map(lambda x: sum((i*2)+1 for i in x))
```

---

## Testing Issues

### Mocking Result-returning functions

```python
from results import Ok
from unittest.mock import patch

def fetch_user(user_id):
    # Real implementation
    ...

# Test with mock
@patch('module.fetch_user')
def test_with_mock(mock_fetch):
    mock_fetch.return_value = Ok({"name": "Alice"})
    result = fetch_user(123)
    assert result.is_ok()
```

### Testing errors

```python
def test_error_handling():
    result = Err("something failed")
    assert result.is_err()
    assert result.err() == "something failed"
```

---

## Documentation

### Reading API docs

**Location**: [API Reference](./api-reference.md)

**Key sections**:
- Result[T, E] methods
- Maybe[T] methods
- Either[L, R] methods
- AsyncResult/AsyncMaybe/AsyncEither
- Helper functions

### Browsing guides

1. **[Error Handling](./guides/error-handling.md)** — Patterns and best practices
2. **[Async Workflows](./guides/async-workflows.md)** — Async patterns
3. **[Context Chains](./guides/context-chains.md)** — Debugging with context
4. **[Pattern Matching](./guides/pattern-matching.md)** — Python 3.10+ syntax

### Running examples

```bash
# Install results
pip install results

# Run examples
python docs/examples/basic_result.py
python docs/examples/with_fastapi.py
```

---

## Still Stuck?

### Check the examples

Browse [examples/](../examples/) for real-world usage patterns:
- [basic_result.py](../examples/basic_result.py) — Simple operations
- [with_pydantic.py](../examples/with_pydantic.py) — Validation
- [with_fastapi.py](../examples/with_fastapi.py) — Web API
- [async_workflow.py](../examples/async_workflow.py) — Async patterns

### Check tests

Tests serve as comprehensive examples:

```bash
# Run tests to see patterns in action
pytest tests/ -v

# View test code
cat tests/sync/test_result.py
cat tests/asyncio/test_async_result.py
```

### Review the source

Code is well-documented:

```python
# Read well-documented implementations
from results import Ok  # Implements Result ABC
print(Ok.__doc__)
```

---

## FAQ

**Q: Should I always add context?**
A: Add context at system boundaries (API calls, DB, external services) and at business logic boundaries.

**Q: Result or Exception?**
A: Use Result for recoverable errors. Use exceptions for programming errors (bugs).

**Q: How deep should context chains be?**
A: Usually 5-10 levels. More is possible but becomes harder to debug.

**Q: Can I use Result everywhere?**
A: Yes, but Result is best for error-prone operations. Use basic types for normal values.

**Q: When should I use Either vs Result?**
A: Result when one branch is success (T) and error (E). Either when both are equally valid (L, R).

---

**Having other issues?** Check [API Reference](./api-reference.md) or review test files for examples.
