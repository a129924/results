# Async Workflows Guide

Working with AsyncResult, AsyncMaybe, and AsyncEither for non-blocking operations.

## Why AsyncResult?

AsyncResult wraps `Awaitable[Result[T, E]]` to provide a clean async/await API:

```python
from results import AsyncResult, Ok, Err

async def fetch_user(user_id: int) -> AsyncResult[dict, str]:
    async def resolver():
        try:
            response = await httpx.get(f"/api/users/{user_id}")
            response.raise_for_status()
            return Ok(response.json())
        except httpx.HTTPError:
            return Err("request failed")
    
    return AsyncResult.from_awaitable(resolver())

# Clean async chaining
async def get_user_name(user_id: int) -> str:
    return await (
        fetch_user(user_id)
        .map_async(lambda u: u.get("name", "Unknown"))
        .unwrap_or_async("Not found")
    )
```

---

## Pattern 1: Async Mapping

Transform success values asynchronously:

```python
import asyncio
from results import AsyncResult, Ok

async def expensive_operation(x: int) -> int:
    await asyncio.sleep(1)  # Simulate work
    return x * 2

async def main():
    result = Ok(5)
    async_result = AsyncResult.from_result(result)
    
    # Transform with async function
    transformed = await async_result.map_async(expensive_operation)
    print(transformed)  # Ok(10)
```

**Key point**: Errors propagate automatically; async function only called on Ok.

---

## Pattern 2: Async Chaining

Chain multiple async operations:

```python
async def fetch_user(user_id: int) -> AsyncResult[dict, str]:
    # Returns AsyncResult
    ...

async def fetch_posts(user: dict) -> AsyncResult[list, str]:
    # Takes user, returns AsyncResult of posts
    ...

async def main():
    result = await (
        fetch_user(123)
        .and_then_async(fetch_posts)  # Chain operations
    )
    # result is Ok([...posts...]) or Err("...")
```

---

## Pattern 3: Concurrent Operations

Run multiple async operations in parallel:

```python
import asyncio

async def fetch_multiple(user_ids: list[int]) -> AsyncResult[list, str]:
    tasks = [
        fetch_user(uid).unwrap_async()
        for uid in user_ids
    ]
    
    try:
        users = await asyncio.gather(*tasks)
        return Ok(users)
    except Exception as e:
        return Err(str(e))
```

---

## Pattern 4: Timeout Handling

Add timeouts to async operations:

```python
async def fetch_with_timeout(user_id: int, timeout: float = 5.0) -> AsyncResult[dict, str]:
    try:
        result = await asyncio.wait_for(
            fetch_user(user_id).unwrap_async(),
            timeout=timeout
        )
        return Ok(result)
    except asyncio.TimeoutError:
        return Err("request timeout")
    except Exception as e:
        return Err(str(e))
```

---

## Pattern 5: Retry Logic

Implement retry with exponential backoff:

```python
async def fetch_with_retry(
    user_id: int, 
    max_retries: int = 3,
    backoff: float = 1.0
) -> AsyncResult[dict, str]:
    for attempt in range(max_retries):
        result = await fetch_user(user_id)
        if result.is_ok():
            return result  # Success
        
        if attempt < max_retries - 1:
            await asyncio.sleep(backoff ** attempt)
    
    return Err("max retries exceeded")
```

---

## Pattern 6: Context Chains in Async

Preserve context through async boundaries:

```python
async def process_order(order_id: int) -> AsyncResult[dict, str]:
    return (
        fetch_order(order_id)
        .context(f"fetching order {order_id}")
        .and_then_async(validate_order)
        .context("validating order")
        .and_then_async(process_payment)
        .context("processing payment")
    )

# On error, full context is preserved
try:
    await process_order(123).unwrap_async()
except Exception as e:
    print(e)  # Shows full context chain
```

---

## Real-World Example: Data Pipeline

```python
import asyncio
import httpx
from results import AsyncResult, Ok, Err

class DataPipeline:
    def __init__(self, api_base: str):
        self.api_base = api_base
        self.client = httpx.AsyncClient()
    
    async def fetch_user(self, user_id: int) -> AsyncResult[dict, str]:
        """Fetch user from API."""
        async def resolver():
            try:
                response = await self.client.get(f"{self.api_base}/users/{user_id}")
                response.raise_for_status()
                return Ok(response.json())
            except httpx.HTTPError as e:
                return Err(f"API error: {e.response.status_code}")
        
        return AsyncResult.from_awaitable(resolver())
    
    async def validate_user(self, user: dict) -> AsyncResult[dict, str]:
        """Validate user data."""
        if not user.get("email"):
            return Err("missing email")
        if not user.get("age") or user["age"] < 18:
            return Err("invalid age")
        return Ok(user)
    
    async def save_user(self, user: dict) -> AsyncResult[dict, str]:
        """Save to database."""
        # Simulate DB write
        await asyncio.sleep(0.1)
        return Ok({**user, "id": 123})
    
    async def process_user(self, user_id: int) -> AsyncResult[dict, str]:
        """Full pipeline: fetch → validate → save."""
        return await (
            self.fetch_user(user_id)
            .context("step: fetch user")
            .and_then_async(self.validate_user)
            .context("step: validate user")
            .and_then_async(self.save_user)
            .context("step: save user")
        )

# Usage
async def main():
    pipeline = DataPipeline("https://api.example.com")
    result = await pipeline.process_user(123)
    
    match result:
        case Ok(user):
            print(f"Saved user: {user}")
        case Err(error):
            print(f"Failed: {error}")

asyncio.run(main())
```

---

## Error Handling in Async

```python
async def safe_process(user_id: int) -> dict:
    """Process with fallback."""
    return await (
        fetch_user(user_id)
        .and_then_async(validate_user)
        .or_else_async(lambda err: 
            Ok({"name": "Unknown", "age": 0})  # Fallback
        )
    ).unwrap_async()
```

---

## Testing Async Results

```python
import pytest

@pytest.mark.asyncio
async def test_fetch_user_success():
    result = await fetch_user(123)
    assert result.is_ok()
    user = result.ok()
    assert user["id"] == 123

@pytest.mark.asyncio
async def test_fetch_user_not_found():
    result = await fetch_user(999)
    assert result.is_err()
    assert "not found" in result.err()
```

Configure in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

---

## Performance Tips

1. **Use concurrent async operations** when fetching multiple resources
2. **Keep async chains short** to avoid deep call stacks
3. **Add timeouts** to prevent hanging
4. **Use context()** for debugging async issues

---

**Next**: Learn about [Context Chains](./context-chains.md) for production debugging.
