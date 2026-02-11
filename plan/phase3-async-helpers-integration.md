# Phase 3.X - Maybe Extended Features (AsyncMaybe, Helpers, Integration)

> **Status**: 🔄 PLANNING → IN-PROGRESS  
> **Phase 3 Baseline**: ✅ Complete (248 tests, mypy --strict, ruff clean)  
> **Estimated Duration**: 4-5 hours total  
> **Feature Branch**: `feature/phase3-maybe-monad`

---

## 🎯 Phase Overview

Extend Maybe monad with asynchronous support, utility methods, and comprehensive integration tests.

| Phase | Component | Status | ETA | Priority |
|-------|-----------|--------|-----|----------|
| **3.A** | AsyncMaybe | 🔄 Ready to Start | 2-3h | 🔴 Critical |
| **3.B** | Utility Methods | ⏳ Planned | 1h | 🟡 Important |
| **3.C** | Integration Tests | ⏳ Planned | 1h | 🟢 Value-Add |
| **3→dev** | Merge to dev | ⏳ Planned | 30m | 🔴 Blocking |

---

## Phase 3.A - AsyncMaybe Implementation

### 目標 & 範圍

**Goal**: Bring async support to Maybe monad with full async/await support  
**Scope**:
- AsyncSome[T] with async transformations
- AsyncNothing with async short-circuit
- Symmetric with AsyncResult pattern (Phase 2)

### Architecture

**Key Design Decision**: Single `AsyncMaybe[T]` type (not `AsyncSome/AsyncNothing`)

Rationale: Just like `AsyncResult[T, E]` wraps `Awaitable[Result[T, E]]`, `AsyncMaybe[T]` wraps `Awaitable[Maybe[T]]`. 
You get a concrete `Some | Nothing` only when you await. This matches Rust's async semantics and keeps type count lean.

```python
# Implementation Structure
src/results/
├── core/
│   └── async_maybe_base.py (new - 250+ lines)
│       └── AsyncMaybeBase ABC protocols
├── maybe/
│   └── asyncio/
│       ├── __init__.py (update - exports)
│       └── maybe.py (new - 250+ lines)
│           └── AsyncMaybe[T] unified implementation
```

### Methods to Implement

#### AsyncMaybeBase ABC (Protocols)

```python
class AsyncMaybeBase(Protocol[T]):
    """Base protocol: AsyncMaybe wraps Awaitable[Maybe[T]]."""
    
    # Core awaitable interface
    def __await__(self) -> Generator[Any, None, Maybe[T]]: ...
    
    # Async transformations
    async def map_async(self, fn: Callable[[T], Awaitable[U]]) -> 'AsyncMaybe[U]': ...
    async def and_then_async(self, fn: Callable[[T], Awaitable['Maybe[U]']]) -> 'AsyncMaybe[U]': ...
    async def or_else_async(self, fn: Callable[[], Awaitable['Maybe[T]']]) -> 'AsyncMaybe[T]': ...
    
    # Async inspection & unwrapping
    async def inspect_async(self, fn: Callable[[T], Awaitable[None]]) -> 'AsyncMaybe[T]': ...
    async def unwrap_async(self) -> T: ...  # Raises UnwrapError if Nothing
    async def unwrap_or_async(self, default: T) -> T: ...
    async def unwrap_or_else_async(self, fn: Callable[[], Awaitable[T]]) -> T: ...
    
    # Context management
    def context(self, msg: str) -> 'AsyncMaybe[T]': ...
```

#### AsyncMaybe[T] Implementation

```python
@dataclass(frozen=True)
class AsyncMaybe(Generic[T]):
    """Awaitable wrapper for Maybe[T].
    
    When awaited, resolves to concrete Some(T) | Nothing.
    Provides async transformation methods that naturally short-circuit on Nothing.
    """
    
    _resolver: Callable[[], Awaitable[Maybe[T]]]
    _context_chain: ContextChain = ContextChain()
    
    def __await__(self) -> Generator[Any, None, Maybe[T]]:
        """Await returns concrete Maybe[T] (Some | Nothing)"""
        return self._resolver().__await__()
    
    async def map_async(self, fn: Callable[[T], Awaitable[U]]) -> 'AsyncMaybe[U]':
        """Transform Some value; short-circuit on Nothing."""
        maybe = await self
        match maybe:
            case Some(value):
                transformed = await fn(value)
                return AsyncMaybe.from_maybe(Some(transformed))
            case Nothing():
                return AsyncMaybe.from_maybe(maybe)  # Short-circuit
    
    async def and_then_async(self, fn: Callable[[T], Awaitable['Maybe[U]']]) -> 'AsyncMaybe[U]':
        """Chain async operations returning Maybe."""
        maybe = await self
        match maybe:
            case Some(value):
                return AsyncMaybe.from_awaitable(fn(value))
            case Nothing():
                return AsyncMaybe.from_maybe(maybe)  # Short-circuit
    
    async def unwrap_async(self) -> T:
        """Extract value or raise UnwrapError with context."""
        maybe = await self
        if isinstance(maybe, Nothing):
            unwrap_with_context(maybe, self._context_chain)
        return maybe._value  # type: ignore
    
    @staticmethod
    def from_maybe(m: Maybe[T]) -> 'AsyncMaybe[T]':
        """Wrap sync Maybe as AsyncMaybe."""
        async def resolved():
            return m
        return AsyncMaybe(lambda: resolved())
    
    @staticmethod
    def from_awaitable(aw: Awaitable[Maybe[T]]) -> 'AsyncMaybe[T]':
        """Wrap Awaitable[Maybe[T]]."""
        return AsyncMaybe(AsyncMaybe._wrap_awaitable(aw))
```

### Test Plan (20+ tests)

**File**: `tests/asyncio/test_async_maybe_basic.py`

Core test cases:
- `test_async_maybe_from_maybe` - Create from sync Maybe
- `test_async_maybe_map_async` - Transform Some value
- `test_async_maybe_map_async_short_circuit` - Nothing skips function
- `test_async_maybe_and_then_async` - Chain returning Maybe
- `test_async_maybe_and_then_async_to_nothing` - Chain can produce Nothing  
- `test_async_maybe_unwrap_async` - Extract Some value
- `test_async_maybe_unwrap_async_error` - UnwrapError on Nothing
- `test_async_maybe_unwrap_or_async` - Fallback to default
- `test_async_maybe_context_chain` - Context accumulates
- `test_async_maybe_chain_multiple` - Chain 3+ operations
- `test_async_maybe_or_else_async` - Fall back to alternative async
- `test_async_maybe_inspect_async` - Side effects without modification

**File**: `tests/asyncio/test_async_maybe_interop.py`

Interop test cases:
- `test_async_maybe_with_real_async` - Use asyncio.sleep, actual delays
- `test_async_maybe_concurrent` - Multiple AsyncMaybes in parallel
- `test_async_maybe_with_sync_maybe` - Mix async and sync Maybes

**Expected Coverage**: ~20 tests covering:
- ✅ Basic async transformations (map_async, and_then_async)
- ✅ Short-circuit behavior on Nothing
- ✅ Chaining async operations
- ✅ Error handling (UnwrapError)
- ✅ Sync method delegation
- ✅ Context chain on Nothing

### Implementation Checklist

- [ ] Create `src/results/core/async_maybe_base.py` (AsyncMaybeBase ABC protocols)
- [ ] Create `src/results/maybe/asyncio/maybe.py` (AsyncMaybe[T] unified type)
- [ ] Update `src/results/maybe/asyncio/__init__.py` (exports AsyncMaybe)
- [ ] Create `tests/asyncio/test_async_maybe_basic.py` (12+ basic tests)
- [ ] Create `tests/asyncio/test_async_maybe_interop.py` (8+ interop tests)
- [ ] Validate: mypy --strict, ruff clean
- [ ] Coverage: Verify ≥80% overall, ≥90% core/
- [ ] Git commit: `feat(async): add AsyncMaybe with unified type design`

---

## Phase 3.B - Utility Methods (flatten, transpose, etc.)

### 目標 & 範圍

**Goal**: Add convenience methods for common Maybe transformations  
**Scope**: Helper methods that complement map/filter/and_then

### Methods to Implement

#### 1. `flatten(maybe: Maybe[Maybe[T]]) -> Maybe[T]`

```python
# Standalone function for now (can add as method later)
def flatten(m: Maybe[Maybe[T]]) -> Maybe[T]:
    """Flatten nested Maybe structure.
    
    Args:
        m: Maybe[Maybe[T]]
    
    Returns:
        Flattened Maybe[T]
    
    Examples:
        >>> flatten(Some(Some(42)))
        Some(42)
        
        >>> flatten(Some(Nothing()))
        Nothing()
        
        >>> flatten(Nothing())
        Nothing()
    """
    match m:
        case Some(inner):
            return inner
        case Nothing() as n:
            return n
```

**Location**: `src/results/maybe/sync/flatten.py` or `src/results/maybe/__init__.py`

#### 2. `transpose(maybe: Maybe[list[T]]) -> list[Maybe[T]]`

```python
def transpose(m: Maybe[list[T]]) -> list[Maybe[T]]:
    """Convert Maybe[List[T]] to List[Maybe[T]].
    
    Args:
        m: Maybe[list[T]]
    
    Returns:
        list[Maybe[T]], where Some wraps each element
    
    Examples:
        >>> transpose(Some([1, 2, 3]))
        [Some(1), Some(2), Some(3)]
        
        >>> transpose(Nothing())
        []
    """
    match m:
        case Some(lst):
            return [Some(item) for item in lst]
        case Nothing():
            return []
```

#### 3. `map_or(maybe: Maybe[T], default: U, fn: Callable[[T], U]) -> U`

```python
def map_or(m: Maybe[T], default: U, fn: Callable[[T], U]) -> U:
    """Map with default value.
    
    Args:
        m: Maybe[T]
        default: Default value if Nothing
        fn: Transformation function
    
    Returns:
        Transformed value or default
    
    Examples:
        >>> map_or(Some(5), 0, lambda x: x * 2)
        10
        
        >>> map_or(Nothing(), 0, lambda x: x * 2)
        0
    """
    return m.map(fn).unwrap_or(default)
```

#### 4. `get_or_insert(maybe: Maybe[T], default: T) -> Maybe[T]`

```python
def get_or_insert(m: Maybe[T], default: T) -> Maybe[T]:
    """Get Some or insert default, returning modified version.
    
    Args:
        m: Maybe[T]
        default: Value to insert if Nothing
    
    Returns:
        Some with original or default value
    
    Examples:
        >>> get_or_insert(Some(42), 0)
        Some(42)
        
        >>> get_or_insert(Nothing(), 99)
        Some(99)
    """
    match m:
        case Some():
            return m
        case Nothing():
            return Some(default)
```

### Test Plan

**File**: `tests/sync/test_maybe_helpers.py`

```python
def test_flatten_some_some():
    result = flatten(Some(Some(42)))
    assert result.unwrap() == 42

def test_flatten_some_nothing():
    result = flatten(Some(Nothing()))
    assert result.is_nothing()

def test_flatten_nothing():
    result = flatten(Nothing())
    assert result.is_nothing()

def test_transpose_some():
    result = transpose(Some([1, 2, 3]))
    assert len(result) == 3
    assert result[0].unwrap() == 1

def test_transpose_nothing():
    result = transpose(Nothing())
    assert result == []

def test_map_or_some():
    result = map_or(Some(5), 0, lambda x: x * 2)
    assert result == 10

def test_map_or_nothing():
    result = map_or(Nothing(), 99, lambda x: x * 2)
    assert result == 99

def test_get_or_insert_some():
    result = get_or_insert(Some(42), 0)
    assert result.unwrap() == 42

def test_get_or_insert_nothing():
    result = get_or_insert(Nothing(), 99)
    assert result.unwrap() == 99
```

### Implementation Checklist

- [ ] Create helper functions file (flatten, transpose, map_or, get_or_insert)
- [ ] Add sufficient docstrings with examples
- [ ] Create comprehensive tests (8+ tests)
- [ ] Consider: Add as methods on Some/Nothing vs standalone functions
- [ ] Validate: mypy --strict, ruff clean
- [ ] Git commit: `feat(helpers): add flatten, transpose, map_or, get_or_insert`

---

## Phase 3.C - Integration Tests

### 目標 & 範圍

**Goal**: Test complex scenarios and interoperability  
**Scope**: Cross-type interactions, real-world patterns, context propagation

### Test Scenarios

#### 1. Result ↔ Maybe Chains

```python
def test_result_to_maybe_chain():
    """Result -> Maybe -> Result chain."""
    def parse_user(json_str: str) -> Result[dict, str]:
        try:
            return Ok(json.loads(json_str))
        except json.JSONDecodeError as e:
            return Err(str(e))
    
    def extract_email(user_dict: dict) -> Maybe[str]:
        return Some(user_dict.get("email")) if "email" in user_dict else Nothing()
    
    chain = (
        parse_user('{"email": "test@example.com"}')
        .and_then(lambda u: Ok(extract_email(u)))
    )
    assert isinstance(chain, Ok)
    assert chain.unwrap().unwrap() == "test@example.com"
```

#### 2. Real-World Scenario: API Response Handling

```python
async def test_api_response_chain():
    """Real-world pattern: Fetch, parse, extract, validate."""
    async def fetch_user(user_id: int) -> Result[dict, str]:
        # Simulated API call
        if user_id > 0:
            return Ok({
                "id": user_id,
                "email": "user@example.com",
                "profile": {"bio": "Test user"}
            })
        return Err("Invalid user ID")
    
    async def extract_bio(user: dict) -> Maybe[str]:
        profile = user.get("profile")
        if profile:
            return Some(profile.get("bio", ""))
        return Nothing()
    
    user = await fetch_user(123)
    match user:
        case Ok(u):
            maybe_bio = await extract_bio(u)
            match maybe_bio:
                case Some(bio):
                    assert bio == "Test user"
                case Nothing():
                    pytest.fail()
        case Err(e):
            pytest.fail()
```

#### 3. Context Chain Propagation

```python
def test_context_chain_propagation():
    """Verify context accumulates through chains."""
    result = (
        Nothing()
        ._context_chain_push("step1")
        ._context_chain_push("step2")
        ._context_chain_push("step3")
    )
    
    assert len(result._context_chain) == 3
    assert result._context_chain[0] == "step3"  # LIFO
```

#### 4. Error Recovery Pattern

```python
def test_error_recovery_with_maybe():
    """Too many Nothings? Fall back gracefully."""
    def lookup_config(key: str) -> Maybe[str]:
        configs = {"timeout": "30s"}
        return Some(configs.get(key)) if key in configs else Nothing()
    
    timeout = (
        lookup_config("timeout")
        .or_else(lambda: lookup_config("default_timeout"))
        .unwrap_or("60s")
    )
    assert timeout == "30s"
    
    # Fallback case
    retry = (
        lookup_config("retry_count")
        .or_else(lambda: lookup_config("default_retry"))
        .unwrap_or("3")
    )
    assert retry == "3"
```

### Test Plan

**File**: `tests/integration/test_maybe_result_chains.py`

```python
def test_result_maybe_interop():
    """Result and Maybe can be used together."""
    # Implementation test
    pass

@pytest.mark.asyncio
async def test_async_api_response_chain():
    """Async API response handling."""
    # Implementation test
    pass

def test_context_chain_accumulation():
    """Context chain tracks all operations."""
    # Implementation test
    pass

def test_error_recovery_fallback():
    """Error recovery with maybe fallbacks."""
    # Implementation test
    pass
```

### Implementation Checklist

- [ ] Create `tests/integration/test_maybe_result_chains.py`
- [ ] Create `tests/integration/test_maybe_async_scenarios.py`
- [ ] Create `tests/integration/test_context_chain_flow.py`
- [ ] Implement ~15-20 integration tests
- [ ] Coverage: Real-world scenarios from README examples
- [ ] Git commit: `test(integration): add Maybe↔Result and async scenario tests`

---

## 🔄 Quality Gates

### Pre-commit Validation

```bash
# Unit tests
uv run pytest tests/ -v

# Type checking
uv run mypy src/results/ --strict

# Code quality
uv run ruff check src/results/ tests/
uv run ruff format src/results/ tests/

# Coverage (must be ≥80%)
uv run pytest tests/ --cov=src/results --cov-report=term-missing
```

### Target Metrics

| Metric | Target | Phase 3.X Target |
|--------|--------|-----------------|
| **Tests** | ≥248 | ≥300+ (248 + ~60 new) |
| **mypy --strict** | 0 errors | 0 errors |
| **ruff** | All pass | All pass |
| **Coverage** | ≥80% | ≥85% |
| **Type hints** | 100% | 100% |

---

## 📋 Implementation Sequence

### Step 1: AsyncMaybe (3.A) - Estimated 2-3 hours

1. Create `src/results/core/async_maybe_base.py`
2. Create `src/results/maybe/asyncio/maybe.py`
3. Write 20+ async tests
4. Validate quality gates
5. Commit

### Step 2: Helper Methods (3.B) - Estimated 1 hour

1. Create helper functions
2. Write 8+ tests
3. Validate quality gates
4. Commit

### Step 3: Integration Tests (3.C) - Estimated 1 hour

1. Create integration test files
2. Write 15-20 integration tests
3. Validate quality gates
4. Commit

### Step 4: Phase 3 Completion (3→dev)

1. Update CHANGELOG.md with version
2. Verify all 300+ tests passing
3. Final mypy + ruff validation
4. Merge feature/phase3-maybe-monad → dev
5. Tag release (e.g., v0.4.0)

---

## 📝 Success Criteria

✅ **Functional**:
- AsyncMaybe fully mirrors Maybe sync API
- Helper methods simplify common patterns
- Integration tests cover realistic scenarios
- All 300+ tests passing

✅ **Quality**:
- mypy --strict: 0 errors
- ruff: all checks pass
- Coverage: ≥85%
- Type hints: 100%

✅ **Documentation**:
- CHANGELOG updated with all changes
- README.md examples added for async, helpers
- Inline docstrings complete
- Code comments for complex logic

---

## 🎯 Next Action

Ready to start Phase 3.A (AsyncMaybe) implementation.

```bash
# Verify starting point
uv run pytest tests/ -q        # 248 tests
uv run mypy src/results/ --strict  # 0 errors
uv run ruff check src/results/     # all pass

# Begin Phase 3.A...
```

---

**Phase 3.X Plan | v1.0 | 2025-02-10**
