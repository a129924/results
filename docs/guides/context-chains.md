# Context Chains Guide

Using context chains for production debugging and diagnostics.

## What Are Context Chains?

Context chains provide a LIFO (Last-In-First-Out) stack of diagnostic messages that track how an error occurred through your application.

```python
from results import Err

error = Err("database timeout")
error_with_context = (
    error
    .context("fetching user profile")
    .context("processing order #1001")
    .context("in checkout handler")
)

# On unwrap:
try:
    error_with_context.unwrap()
except Exception as e:
    print(e)
    # Output:
    # database timeout
    # Context:
    #   - in checkout handler
    #   - processing order #1001
    #   - fetching user profile
```

---

## Why Context Chains?

Traditional logging creates scattered context:

```python
# ❌ Traditional approach
def fetch_user(user_id):
    logger.info(f"Fetching user {user_id}")
    try:
        response = requests.get(f"/api/users/{user_id}")
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise

def process_order(order_id):
    logger.info(f"Processing order {order_id}")
    try:
        user = fetch_user(order_id.user_id)
    except Exception:
        logger.error(f"User fetch failed for order {order_id}")
        raise  # Context lost!

# Problem: Multiple log lines, context tangled
```

With context chains:

```python
# ✅ Context chain approach
def fetch_user(user_id: int) -> Result[dict, str]:
    result = Err("network timeout")
    return result.context(f"fetching user {user_id}")

def process_order(order: dict) -> Result[dict, str]:
    return (
        fetch_user(order["user_id"])
        .context(f"processing order #{order['id']}")
    )

# Problem: Single, cohesive error trace
```

---

## Building Effective Context Chains

### Principle 1: Add Context at Operations Boundaries

```python
def save_to_database(data: dict) -> Result[dict, str]:
    if not validate(data):
        return Err("validation failed").context("saving to database")
    
    try:
        db.insert(data)
        return Ok(data)
    except DatabaseError as e:
        return Err(str(e)).context("saving to database")
```

### Principle 2: Include Relevant Variables

```python
def fetch_and_process(user_id: int, order_id: int) -> Result[dict, str]:
    return (
        fetch_user(user_id)
        .and_then(lambda user:
            fetch_order(order_id)
            .map(lambda order: process(user, order))
        )
        .context(f"user_id={user_id}")
        .context(f"order_id={order_id}")
    )

# Helps debugging: immediately see which user/order failed
```

### Principle 3: Use Lazy Context for Expensive Operations

```python
def fetch_with_diagnostics(user_id: int) -> Result[dict, str]:
    result = fetch_user(user_id)
    
    # Only evaluate expensive_debuginfo() if error occurs
    return result.with_context(lambda: 
        f"user_id={user_id}, cache_size={get_cache_size()}"
    )
```

---

## Production Patterns

### Pattern 1: Per-Request Context

```python
from results import Err

async def handle_request(request_id: str, payload: dict):
    """Add request context to all errors in this flow."""
    return (
        process_payload(payload)
        .context(f"request_id={request_id}")
        .context(f"handler=checkout")
        .context(f"timestamp={now()}")
    )
```

### Pattern 2: Error Classification with Context

```python
def process_payment(order: dict) -> Result[dict, PaymentError]:
    if not order.get("card"):
        return Err(PaymentError("no payment method"))
    
    try:
        charge(order)
        return Ok(order)
    except InsufficientFundsError as e:
        return Err(
            PaymentError(f"insufficient funds: {e.amount}")
        ).context(f"order_id={order['id']}")
    except TemporaryError as e:
        return Err(
            PaymentError(f"temporary failure: {e}")
        ).context(f"order_id={order['id']}")
```

### Pattern 3: Middleware-Level Context

```python
async def request_handler(request):
    """Add context at edge of application."""
    result = await process_request(request)
    
    # Add request metadata to all errors
    if result.is_err():
        result = result.context(f"user_agent={request.headers.get('user-agent')}")
        result = result.context(f"ip={request.client.host}")
        result = result.context(f"path={request.url.path}")
    
    return result
```

---

## Extracting Context for Logging

```python
from results import Err

def error_to_log(result: Result[T, str]) -> dict:
    """Convert Result error to loggable dict."""
    if result.is_ok():
        return {}
    
    error = result.context("wrapper_context")  
    # Returns Err with context added
    
    # Extract and format
    try:
        error.unwrap()
    except Exception as e:
        return {
            "error": str(e),
            "context_chain": e.context if hasattr(e, 'context') else [],
        }

# Usage
@app.post("/orders")
def create_order(data):
    result = process_order(data)
    if result.is_err():
        log_dict = error_to_log(result)
        logger.error("Order processing failed", extra=log_dict)
        return {"error": "processing failed"}, 500
```

---

## Real-World: E-Commerce Checkout

```python
from results import Ok, Err, Result

class CheckoutService:
    def checkout(self, cart_id: str, user_id: int) -> Result[Order, str]:
        """Full checkout pipeline with context."""
        return (
            self.fetch_cart(cart_id)
            .context(f"cart_id={cart_id}")
            .and_then(lambda cart: 
                self.validate_items(cart)
                .context(f"items={len(cart.items)}")
            )
            .and_then(lambda cart:
                self.calculate_tax(cart)
                .context(f"country={cart.shipping.country}")
            )
            .and_then(lambda cart:
                self.process_payment(cart)
                .context(f"user_id={user_id}")
            )
            .and_then(lambda cart:
                self.create_order(cart)
                .context(f"total=${cart.total}")
            )
            .context("step: checkout")
        )
    
    def fetch_cart(self, cart_id: str) -> Result[Cart, str]:
        try:
            cart = db.fetchone("SELECT * FROM carts WHERE id = ?", (cart_id,))
            if not cart:
                return Err("cart not found")
            return Ok(cart)
        except Exception as e:
            return Err(f"database error: {e}")
    
    # ... other methods ...

# Usage
service = CheckoutService()
result = service.checkout("cart_123", user_id=456)

if result.is_err():
    try:
        result.unwrap()
    except Exception as e:
        # Full diagnostic info:
        # "database error: [SQL error details]"
        # Context:
        #   - step: checkout
        #   - total=$150.00
        #   - user_id=456
        #   - country=US
        #   - items=3
        #   - cart_id=cart_123
        print(f"Checkout failed: {e}")
        
        # Log for debugging
        sentry.capture_exception(e)
```

---

## Testing Context Chains

```python
from results import Err

def test_error_context():
    error = (
        Err("base error")
        .context("second")
        .context("first")
    )
    
    try:
        error.unwrap()
    except Exception as e:
        error_str = str(e)
        assert "base error" in error_str
        assert "first" in error_str
        assert "second" in error_str
```

---

## Tips for Enterprise Use

1. **Add context at system boundaries** — API calls, DB operations, external services
2. **Include IDs in context** — user_id, request_id, order_id for traceability
3. **Use lazy context** — Don't compute if not needed (use `with_context`)
4. **Standardize formats** — `key=value` for consistent parsing
5. **Keep chains concise** — 5-10 levels typically enough

---

## Anti-Patterns

### ❌ Too Many Contexts

```python
# BAD: Redundant context
result = (
    operation()
    .context("step 1")
    .context("step 2")
    .context("step 3")
    .context("step 4")
)

# GOOD: Meaningful context at boundaries
result = (
    operation()
    .context("validating payment")
    .context("processing order")
)
```

### ❌ Missing Variables

```python
# BAD: No identifying info
result.context("error in user fetch")

# GOOD: Include identifiers
result.context(f"error fetching user_id={user_id}")
```

---

**Next**: Learn [Pattern Matching](./pattern-matching.md) for Python 3.10+ syntax.
