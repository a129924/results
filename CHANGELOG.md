# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.4.0] - 2026-02-12

### Added

**Maybe Monad: Optional Value Handling (Phase 3)** — Type-safe alternative to None
- New `Maybe[T]` monad type with `Some[T]` (presence) and `Nothing` (absence) variants
- Core methods: `map()`, `filter()`, `and_then()`, `or_else()`, `zip()`, `zip_with()`
- Value extraction: `unwrap()`, `unwrap_or()`, `unwrap_or_else()`
- Diagnostics: `inspect()` for debugging, `context()` for optional diagnostic messages
- Context chain support: `Nothing` can carry diagnostic context via LIFO stack
- 56 comprehensive tests for Maybe implementation
- Pattern matching support with Python 3.10+ `match`/`case`
- Architecture aligned with Result: `maybe/sync/` and `maybe/asyncio/` structure
- AsyncMaybe for async/await workflows with `map_async`, `and_then_async`, `or_else_async`, `inspect_async`
- AsyncMaybe unwrap helpers: `unwrap_async`, `unwrap_or_async`, `unwrap_or_else_async`
- Maybe helper functions: `flatten`, `transpose`, `map_or`, `get_or_insert`
- Integration tests for Result ↔ Maybe interop and async scenarios

### Changed

- Updated README with Maybe examples and comparison to Result
- Test suite expanded from 192 to 297 tests
- Badge updates: tests count, monad type documentation

### Technical Details

- Frozen dataclass implementation (immutable)
- `@override` decorators on all public methods
- Full mypy --strict compliance (0 errors)
- All ruff checks passing
- No new dependencies

---

## [0.3.1] - 2026-02-06

### Changed

**Architecture Restructuring (Phase 1)** — Reorganized for scalable monad ecosystem
- Directory structure: `impl/{sync,async_}` → `result/{sync,asyncio}`
- Functional-priority grouping: Each monad type (Result, Maybe, Either) in separate directory
- Aggregation modules: Proper `result/__init__.py` for clean public imports
- Test structure: `tests/async_` → `tests/asyncio` for consistency
- Removed legacy `impl/` directory (fully migrated to `result/`)
- Removed empty `tests/unit/` directory (tests now in `sync/asyncio/unit/`)

### Added

- `MIGRATION_GUIDE.md` — Comprehensive guide for v0.3.1 transition
- `common/` directory — Foundation for Phase 2 shared utilities
- Improved code organization supporting future Maybe and Either implementations

### Backward Compatibility

✅ **100% backward compatible** — No API changes, only internal restructuring
- All public imports unchanged: `from results import Ok, Err, AsyncResult`
- All 192 tests passing
- mypy --strict: 0 errors
- ruff: all checks passing

---

## [0.3.0] - 2026-01-25

### Added

**AsyncResult: Async/Await Support** — New `AsyncResult[T, E]` type for non-blocking workflows
- `AsyncResult` as `Awaitable[Result[T, E]]` wrapper for seamless async chaining
- `__await__()` and `resolve()` methods for awaitable operations
- Async combinators: `map_async()`, `map_err_async()`, `and_then_async()`
- Async inspection: `inspect_async()`, `inspect_err_async()`
- `unwrap_async()` with LIFO context chain in UnwrapError
- Context preservation via `context()` and `with_context()` across await boundaries
- Factory methods: `from_result()`, `from_awaitable()` for async/sync interoperability
- Full type support with mypy --strict compliance

**Async/Sync Interoperability** — Seamless integration between workflows
- Mix sync Results with async operations using `asyncio.to_thread()`
- Chain across sync/async boundaries with error type accumulation
- LIFO context stack preserved through await boundaries

**Comprehensive Async Testing** — 35+ new tests covering async scenarios
- Unit tests for AsyncResult core (map_async, and_then_async, unwrap_async, etc.)
- Async/sync interoperability tests with mixed handler chains
- Integration tests with realistic async pipelines (fetch → validate → persist)
- All tests use pytest-asyncio with proper marker support

### Changed

- Test count updated from 166 to 187 (35+ new async tests)
- Updated README with AsyncResult usage examples and async test categories
- Dev dependencies: Added `pytest-asyncio>=0.24.0`

### Fixed

- AsyncResult resolver uses task caching to support multiple awaits (no "cannot reuse coroutine" errors)

### Backward Compatibility

✅ **Full backward compatibility maintained** — v0.2.0 code requires no changes
- All sync Result methods unchanged
- Async operations purely additive (new AsyncResult type)
- No breaking changes to existing APIs

---

## [0.2.0] - 2026-01-20

### Added

**Context Chain (LIFO)** — Rust anyhow-style error context tracking
- `context(msg: str) -> Result[T, E]` for manual context annotation
- `with_context(f: Callable[[], str]) -> Result[T, E]` for lazy evaluation
- LIFO ordering in UnwrapError messages for rich diagnostics

**Debug Tools** — Non-intrusive inspection utilities
- `inspect(f: Callable[[T], None]) -> Result[T, E]` for success side effects
- `inspect_err(f: Callable[[E], None]) -> Result[T, E]` for error side effects
- Zero-cost abstraction (no performance impact)

**Comprehensive Test Suite** — 166 tests covering core and advanced scenarios
- Core Result functionality (Ok, Err, unwrap)
- Functional chains (map, map_err, and_then)
- Context chain behavior (LIFO, immutability)
- Integration scenarios with real-world patterns

### Changed

- `UnwrapError` now includes context chain in formatted message
- Enhanced API documentation with real-world examples

---

## [0.1.0] - 2026-01-23

### Initial Release 🎉

#### Added

**Core Contract Layer**
- `Result[T, E]` — Abstract base class defining the Result contract
- `Ok[T]` — Success variant for wrapping successful values
- `Err[E]` — Error variant for wrapping errors
- Type variables: `T` (success), `E` (error), `U` (transformation), `F` (error composition)

**Result Methods**
- `is_ok()` — Check if Result is Ok
- `is_err()` — Check if Result is Err
- `ok()` — Extract success value or None
- `err()` — Extract error value or None
- `unwrap()` — Extract value or raise UnwrapError
- `map(op)` — Transform success value, preserving error type
- `map_err(op)` — Transform error, preserving success value
- `and_then(op)` — Chain operations with automatic error type accumulation

**Exception Hierarchy**
- `ResultError` — Framework-level base exception
- `UnwrapError` — Raised when unwrap() is called on Err
- `BaseError` — Optional base class for business exceptions (frozen dataclass)

**Features**
- ✅ Type-safe contracts using Python ABC
- ✅ Full type annotations (Python 3.10+ compatible)
- ✅ Frozen dataclasses for immutability
- ✅ Support for any error type (Exception, str, int, dict, etc.)
- ✅ Functional programming support (map, map_err, and_then chaining)
- ✅ Private attributes enforcement (\_value, \_error)
- ✅ Explicit error handling (no silent failures)

**Testing (117 tests)**
- 35 core contract tests
- 67 unit tests (33 Ok, 34 Err)
- 15 integration tests (chaining, real-world patterns, private enforcement)
- 100% test pass rate

**Code Quality**
- ✅ mypy --strict: 0 errors
- ✅ ruff: All checks passed
- ✅ Full docstrings (Google style)
- ✅ @typing_extensions.override on all ABC implementations

**Documentation**
- README.md with quick start and real-world examples
- Comprehensive API reference
- Architecture overview
- Usage patterns and design principles

### Design Decisions

1. **Result as ABC** — Enforces contract consistency across Ok/Err
2. **E TypeVar unconstrained** — Supports any error type (Rust-inspired)
3. **Frozen dataclasses** — Immutability without overhead
4. **Type accumulation** — and_then automatically composes error types via `|` operator
5. **Private attributes** — Only accessible via public methods (ok(), err())
6. **Traceback handling** — No automatic capture (matches Rust Result<T, E> design)
   - Simple path: `return Err(MyError(...))` — Clean but no traceback
   - Rich context path: `try-except` then `return Err(e)` — Preserves traceback
   - v0.2.0: Optional `with_context()` for automatic capture (anyhow-style)

### Known Limitations

- AsyncResult implementation deferred to future release
- No async/await support in v0.1.0
- Private attribute enforcement relies on frozen dataclasses (not cryptographic)

### Future Roadmap

- [x] v0.1.0 — Core Result type system (RELEASED)
- [ ] v0.2.0 — Traceback context capture, error chaining (anyhow-style)
- [ ] v0.3.0 — Async variants (AsyncResult), context manager support
- [ ] v0.4.0 — Logging integration, diagnostic tools
- [ ] v0.5.0 — Performance optimizations, comprehensive benchmarks

---

## Version History

| Version | Release Date | Status |
|---------|-------------|--------|
| 0.3.1   | 2026-02-06  | ✅ Released |
| 0.3.0   | 2026-01-25  | ✅ Released |
| 0.2.0   | 2026-01-20  | ✅ Released |
| 0.1.0   | 2026-01-23  | ✅ Released |

---

## Contributing

See CONTRIBUTING.md for guidelines on reporting issues and submitting contributions.

## License

MIT License — see LICENSE file for details.
