# API Stability & Versioning Policy

This document outlines the stability guarantees and versioning strategy for the `results` library.

## Overview

The `results` library follows **Semantic Versioning** (SemVer) with explicit API stability tracking:

- **MAJOR** (v0 → v1): Significant changes, possible breaking changes
- **MINOR** (v0.x → v0.y): New features, backward compatible
- **PATCH** (v0.x.y → v0.x.z): Bug fixes, backward compatible

---

## v0.1.0 - Stable APIs ✅

### Tier 1: Core Contract (Guaranteed Stable)

These are foundational and will NOT change before v1.0:

| Component | Status | Notes |
|-----------|--------|-------|
| `Result[T, E]` ABC | ✅ STABLE | Core abstraction - never breaking |
| `Ok[T]` | ✅ STABLE | Success variant implementation |
| `Err[E]` | ✅ STABLE | Error variant implementation |
| `is_ok()` | ✅ STABLE | Boolean check - signature locked |
| `is_err()` | ✅ STABLE | Boolean check - signature locked |
| `ok()` | ✅ STABLE | Success extractor - signature locked |
| `err()` | ✅ STABLE | Error extractor - signature locked |
| `map()` | ✅ STABLE | Transformation - signature locked |
| `map_err()` | ✅ STABLE | Error transformation - signature locked |
| `and_then()` | ✅ STABLE | Chaining - signature locked |
| `unwrap()` | ✅ STABLE | Extraction with exception - signature locked |

**Stability Guarantee:**
```python
# This WILL work in v0.2.0, v0.3.0, ... v1.0
from results import Ok, Err, Result

result: Result[int, str] = Ok(42)
assert result.is_ok()
assert result.ok() == 42
value = result.map(lambda x: x * 2).unwrap()
```

### Tier 2: Exception System (Guaranteed Stable)

| Component | Status | Notes |
|-----------|--------|-------|
| `ResultError` | ✅ STABLE | Base framework exception |
| `UnwrapError` | ✅ STABLE | unwrap() failure exception |
| `BaseError` | ✅ STABLE | Business exception helper ABC |

**Stability Guarantee:**
```python
# Error handling WILL work unchanged
try:
    result.unwrap()
except UnwrapError as e:
    print(e.message)
    print(e.original_error)
```

### Tier 3: Type System (Guaranteed Stable)

| Component | Status | Notes |
|-----------|--------|-------|
| `E` TypeVar (unconstrained) | ✅ STABLE | Supports any error type |
| Type annotations (PEP 561) | ✅ STABLE | Full mypy support |
| Python 3.10+ syntax | ✅ STABLE | PEP 604 (`\|` operator) |

---

## v0.2.0 - Planned Additions (Will NOT Break v0.1.0 APIs)

### New Experimental APIs

| Feature | Status | Planned |
|---------|--------|---------|
| `with_context(msg: str)` | 🔄 PLANNED | Add execution context to errors |
| `inspect()` | 🔄 PLANNED | Debug utility |
| Error chaining | 🔄 PLANNED | `anyhow`-style context |

**Important:** These will be additive - no breaking changes to v0.1.0 APIs.

```python
# v0.2.0 - NEW, but v0.1.0 code still works
result = Ok(42).with_context("parsing user data")

# v0.1.0 code - STILL WORKS UNCHANGED
result = Ok(42).map(lambda x: x * 2)
```

---

## v0.3.0 - Async Support (Separate Module)

| Feature | Status | Type |
|---------|--------|------|
| `AsyncResult[T, E]` | 🔄 PLANNED | New module |
| `async_ok()`, `async_err()` | 🔄 PLANNED | New functions |

**Important:** Async features will be in `results.async_` - separate namespace, no impact on sync APIs.

```python
# v0.3.0 - NEW async module (sync v0.1.0 code unaffected)
from results.async_ import AsyncResult

async def process() -> AsyncResult[int, str]:
    return AsyncResult.Ok(42)
```

---

## Backward Compatibility Policy

### What We Guarantee

✅ **Will NOT change before v1.0:**
- Method signatures (parameters, return types)
- Exception types and hierarchy
- Type inference behavior
- Module structure (import paths)

### What May Change

⚠️ **Before v1.0, these might change:**
- Internal implementation details (prefixed with `_`)
- Docstring formatting (not functionality)
- Performance characteristics
- Experimental APIs (clearly marked 🔄 PLANNED)

### What We Will Never Change

🔒 **Locked for life:**
- Core 8 methods: `is_ok`, `is_err`, `ok`, `err`, `map`, `map_err`, `and_then`, `unwrap`
- Result ABC contract
- Python 3.10+ requirement
- Type safety guarantees

---

## Deprecation Process

When we need to remove/change something (post v1.0):

1. **Announce** — Add deprecation warning to logs
2. **Transition** — Provide migration guide in CHANGELOG
3. **Wait** — Allow 2 minor versions for users to update
4. **Remove** — Delete in MAJOR version

Example:
```python
# v1.1.0 - Hypothetical deprecation
import warnings

def old_method(self):
    warnings.warn(
        "old_method is deprecated, use new_method instead",
        DeprecationWarning,
        stacklevel=2
    )
    return self.new_method()
```

---

## Version Commitment Matrix

| Version | Guarantee | Breaking Changes | New Stable APIs |
|---------|-----------|------------------|-----------------|
| v0.1.x  | ✅ Stable | ❌ None | ❌ None (patch only) |
| v0.2.0  | ✅ Compatible | ❌ None | ✅ Experimental features (additive) |
| v0.3.0  | ✅ Compatible | ❌ None | ✅ Async module |
| v1.0.0  | 🔒 Locked | ❌ None | ⚠️ TBD (post-v1 policy) |
| v2.0.0+ | 🔒 Locked | ✅ Allowed | 📋 With deprecation notice |

---

## For Users: API Stability Checklist

Use this to verify your code is stable:

```python
# ✅ SAFE - All v0.1.0 core APIs
from results import Ok, Err, Result
result = Ok(42).map(lambda x: x * 2).and_then(validate)

# ⚠️ EXPERIMENTAL - May change in v0.2.0
result.with_context("user context")  # Not yet in v0.1.0

# ❌ NEVER USE DIRECTLY - Internal APIs
result._value  # Private! Use result.ok() instead
```

---

## For Contributors: API Changes

### Before Adding to Stable Tier

1. ✅ Does it fit the core philosophy?
2. ✅ Is the signature intuitive?
3. ✅ Can it be tested comprehensively?
4. ✅ Is it documented with examples?
5. ✅ Would removing it break existing code?

### To Mark Something as Stable

1. Add test coverage ≥ 95%
2. Include in main README examples
3. Document in docstring with examples
4. Add to this STABILITY.md file
5. Mention in CHANGELOG as "Stabilized"

---

## Questions & Feedback

If you have concerns about API stability:
1. Check this file first
2. Review CHANGELOG.md for version changes
3. Open an issue for clarification

## Version History

| Version | Date | Stability Status |
|---------|------|------------------|
| v0.1.0  | 2026-01-23 | 🟢 Core APIs Stable |
| v0.2.0  | TBD  | 🟡 Core Stable + Experimental |
| v0.3.0  | TBD  | 🟢 Core + Async Stable |
| v1.0.0  | TBD  | 🔒 All Locked |

---

**Last Updated:** 2026-01-24
**Maintained By:** Andrew
**SemVer Version:** 2.0.0 compatible
