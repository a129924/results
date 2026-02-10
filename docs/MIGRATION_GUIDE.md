# Migration Guide: Phase 1 Restructuring (v0.3.1)

> **Release Date**: February 6, 2026  
> **Version**: v0.3.1  
> **Status**: ✅ Complete & Backward Compatible

---

## Overview

Phase 1 restructuring reorganized the codebase to support a scalable monad ecosystem (Result, Maybe, Either) while maintaining **100% backward compatibility** with existing code.

### Key Changes

- ✅ **Directory restructuring**: `impl/{sync,async_}` → `result/{sync,asyncio}`
- ✅ **New architecture**: Functional-priority grouping with technical subdivisions
- ✅ **Module aggregation**: Proper `__init__.py` exports for clean imports
- ✅ **Test structure update**: `tests/async_` → `tests/asyncio`
- ✅ **Legacy cleanup**: Removed old `impl/` directory
- ✅ **All tests passing**: 192/192 ✓

---

## What Changed for Users

### Import Paths: **UNCHANGED**

If you use the public API, **no changes required**:

```python
# ✅ Still works exactly the same
from results import Ok, Err, AsyncResult, Result, UnwrapError

result: Result[int, str] = Ok(42)
value = result.map(lambda x: x * 2).ok()
```

### What Happened Internally

```
BEFORE (v0.3.0)              AFTER (v0.3.1)
─────────────────            ──────────────
src/results/
├── impl/
│   ├── sync/
│   │   ├── ok.py      →     result/
│   │   └── err.py          ├── sync/
│   └── async_/       →     │   ├── ok.py
│       └── result.py       │   └── err.py
├── core/                    └── asyncio/
└── ...                          └── result.py
                            ├── core/
                            ├── common/  ← NEW (Phase 2 prep)
                            └── ...
```

**No API changes** — internal restructuring only.

---

## For Contributors

### Update Your Local Imports

If you were importing from internal modules:

#### Old (❌ No longer works)
```python
from results.impl.sync import Ok, Err
from results.impl.async_ import AsyncResult
from results.impl.sync.err import Err
```

#### New (✅ Use this instead)
```python
from results.result.sync import Ok, Err
from results.result.asyncio import AsyncResult
from results.result.sync.err import Err
```

Or better yet, use the public API:
```python
from results import Ok, Err, AsyncResult
```

---

## Directory Structure (v0.3.1)

### Source Code Layout

```
src/results/
├── __init__.py             # Public API exports
├── core/                   # ABC contracts and types
│   ├── base.py            # Result[T, E] abstract class
│   ├── types.py           # TypeVar, type definitions
│   └── exceptions.py      # UnwrapError, etc.
├── result/                # Result monad family
│   ├── __init__.py        # Aggregates sync/asyncio
│   ├── sync/              # Synchronous implementations
│   │   ├── __init__.py
│   │   ├── ok.py          # Ok[T] class
│   │   └── err.py         # Err[E] class
│   └── asyncio/           # Asynchronous implementations
│       ├── __init__.py
│       └── result.py      # AsyncResult class
├── common/                # Shared utilities (Phase 2+)
│   └── __init__.py
├── _private/              # Internal utilities (hidden)
│   └── ...
└── py.typed               # PEP 561 marker
```

### Test Layout

```
tests/
├── sync/                  # Synchronous tests
│   ├── test_ok_impl.py
│   ├── test_err_impl.py
│   ├── test_context_chain.py
│   └── test_debug_tools.py
├── asyncio/               # Asynchronous tests (✨ NEW naming)
│   ├── unit/
│   │   ├── test_async_result_core.py
│   │   └── test_async_sync_interop.py
│   └── integration/
│       └── test_async_real_world.py
├── integration/           # Cross-module integration
│   ├── test_result_integration.py
│   └── test_context_integration.py
├── test_core_base.py
├── test_core_types.py
├── test_exceptions.py
└── fixtures/              # Shared test fixtures
```

---

## Benefits of This Architecture

### 1. **Scalability**
New monad types (Maybe, Either) can follow the same pattern:
```
result/ ← exists
maybe/  ← Phase 3
either/ ← Phase 4
```

### 2. **Consistency**
Each monad family follows identical structure:
- `<monad>/sync/` for synchronous implementations
- `<monad>/asyncio/` for asynchronous implementations
- Shared contracts in `core/`

### 3. **Low Coupling**
- `impl/` dependencies completely eliminated
- Monad families are independent
- `core/` contains only ABC contracts

### 4. **Testability**
- Test structure mirrors source structure
- Clear mapping: `tests/sync/` ↔ `src/results/result/sync/`
- Easy to add new monad tests

---

## Migration Checklist

### For End Users
- ✅ **No action required** — Your code continues to work
- ✅ Update imports if you access internal modules (see "For Contributors")

### For Contributors
- ✅ Use new import paths: `from results.result.sync import ...`
- ✅ Prefer public API: `from results import Ok, Err, AsyncResult`
- ✅ New test files go in `tests/sync/` or `tests/asyncio/`

### For Maintainers
- ✅ Old `impl/` directory removed
- ✅ Test directories renamed: `async_` → `asyncio`
- ✅ All 192 tests passing
- ✅ mypy --strict: 0 errors
- ✅ ruff: all checks passing

---

## Testing & Validation

### Run All Tests
```bash
python -m pytest tests/ -v
# Expected: 192 passed in ~0.10s
```

### Run Specific Test Suite
```bash
# Synchronous tests
python -m pytest tests/sync/ -v

# Asynchronous tests
python -m pytest tests/asyncio/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Core contract tests
python -m pytest tests/test_core_base.py -v
```

### Type Checking
```bash
mypy src/results/ --strict
# Expected: Success: no issues found
```

### Code Quality
```bash
ruff check src/results/ tests/
# Expected: 0 errors
```

---

## What's Next? (Planned Phases)

### Phase 2: Extract Shared Logic
- Centralize `Context Chain` management
- Create `core/context.py` and `common/protocols.py`
- Eliminate duplication across monad types

### Phase 3: Implement Maybe
- Add `maybe/sync.py` (Just, Nothing)
- Add `maybe/asyncio.py` (AsyncMaybe)
- Full test coverage and documentation

### Phase 4: Implement Either
- Add `either/sync.py` (Left, Right)
- Add `either/asyncio.py` (AsyncEither)
- Full test coverage and documentation

---

## Troubleshooting

### ❌ "ModuleNotFoundError: No module named 'results.impl'"

**Solution**: Update your imports
```python
# Old (broken)
from results.impl.sync import Ok

# New (works)
from results.result.sync import Ok

# Best (use public API)
from results import Ok
```

### ❌ "Can't find tests/async_"

**Solution**: Directory was renamed to `tests/asyncio/` in v0.3.1
```bash
# Old
pytest tests/async_/

# New
pytest tests/asyncio/
```

### ✅ All Tests Pass But Build Fails?

Ensure you're using Python 3.10+:
```bash
python --version
# Expected: Python 3.10.x or higher
```

---

## Version Information

| Component | Version |
|-----------|---------|
| Project Version | v0.3.1 |
| Python Minimum | 3.10+ |
| Git Tag | v0.3.1 |
| Feature Branch | feature/phase1-restructure |

---

## Questions or Issues?

- **Bug Report**: Create an issue on GitHub
- **Import Questions**: Check [README.md](README.md#usage) examples
- **Architecture Questions**: See [copilot-instructions.md](.github/copilot-instructions.md)

---

**Last Updated**: February 6, 2026  
**Status**: Complete and Stable ✅
