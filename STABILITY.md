# Stability & API Commitment

This document outlines the stability guarantees and commitment levels for different parts of the `results` package.

## Versioning

This project follows **Semantic Versioning 2.0.0**:

- **MAJOR** version when API changes are incompatible
- **MINOR** version when new features are added (backward-compatible)
- **PATCH** version when bug fixes are released (backward-compatible)

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## API Stability Tiers

### 🟢 Tier 1: Stable (Public API)

**Status:** Committed to long-term stability

Core Result type system:

| API | Version Added | Status |
|-----|----------------|--------|
| `Result[T, E]` (ABC) | v0.1.0 | ✅ Stable |
| `Ok[T]` | v0.1.0 | ✅ Stable |
| `Err[E]` | v0.1.0 | ✅ Stable |
| `Result.is_ok()` | v0.1.0 | ✅ Stable |
| `Result.is_err()` | v0.1.0 | ✅ Stable |
| `Result.ok()` | v0.1.0 | ✅ Stable |
| `Result.err()` | v0.1.0 | ✅ Stable |
| `Result.unwrap()` | v0.1.0 | ✅ Stable |
| `Result.map()` | v0.1.0 | ✅ Stable |
| `Result.map_err()` | v0.1.0 | ✅ Stable |
| `Result.and_then()` | v0.1.0 | ✅ Stable |

**Commitment:**
- No breaking changes to these methods in future releases
- Only additive changes (new parameters, new methods, new variants)
- Full backward compatibility across major versions

### 🟡 Tier 2: Stable (Released Functional Enhancement)

**Status:** Committed to stability, released as part of v0.2.0

Debug and context chain tools:

| API | Version Added | Status |
|-----|----------------|--------|
| `Result.inspect()` | v0.2.0 | ✅ Stable |
| `Result.inspect_err()` | v0.2.0 | ✅ Stable |
| `Result.context()` | v0.2.0 | ✅ Stable |
| `Result.with_context()` | v0.2.0 | ✅ Stable |
| `Err._context_chain` | v0.2.0 | ✅ Stable (Private) |

**Commitment:**
- Considered stable and suitable for production use
- LIFO context chain behavior is guaranteed
- No breaking changes planned

---

## Exceptions & Error Types

| Exception | Version | Status | Guarantees |
|-----------|---------|--------|-----------|
| `UnwrapError` | v0.1.0 | ✅ Stable | Raised on `unwrap()` of Err |
| `ResultError` | v0.1.0 | ✅ Stable | Base exception class |
| `BaseError` | v0.1.0 | ✅ Stable | Optional base for business errors |

---

## Implementation Guarantees

### Performance

- **Ok operations:** O(1) with no allocations beyond frozen dataclass
- **Err operations:** O(1) for operations, O(n) for context chain display only on `unwrap()`
- **Context chain:** Immutable tuple, no hidden allocations in chain traversal

### Thread Safety

- All types use frozen dataclasses (immutable)
- No global state or shared resources
- Safe to share across threads
- Safe to use in async contexts

### Backward Compatibility

- v0.1.0 code runs unchanged on v0.2.0+
- No breaking changes to existing APIs
- Private attributes (prefixed with `_`) are not part of public API and may change

---

## Future API Plans

### 🔵 Tier 3: Planned (Not Yet Released)

Features planned for future releases:

| Feature | Planned Version | Purpose |
|---------|-----------------|---------|
| `AsyncResult[T, E]` | v0.3.0 | Async/await support |
| Context managers | v0.3.0 | Resource management |
| Logging integration | v0.4.0 | Built-in diagnostic logging |
| Performance tools | v0.5.0 | Benchmarking utilities |

**Note:** Planned features may be adjusted or postponed based on user feedback and priorities.

---

## Support Policy

### Supported Versions

| Version | Released | End of Support | Status |
|---------|----------|-----------------|--------|
| 0.2.x   | 2026-01-24 | TBD | Current |
| 0.1.x   | 2026-01-23 | TBD | Maintenance |
| 0.0.x   | (none)   | N/A | Not released |

**Note:** Exact end-of-support dates will be determined based on adoption and release cadence.

### Security

- No external dependencies (zero supply chain risk)
- Frozen dataclasses prevent mutable state exploits
- No unsafe type operations

---

## Deprecation Policy

When APIs must change:

1. **Deprecation Warning:** Add warning in current version (minimum 1 minor version)
2. **Documentation:** Update docs with migration guide
3. **Removal:** Remove in next MAJOR version

Example:
- v1.0.0: Introduce `new_method()`, deprecate `old_method()`
- v1.x.x: Both work, warning on `old_method()` use
- v2.0.0: Remove `old_method()`

---

## Reporting Issues

If you discover stability issues or breaking changes:

1. Create a GitHub issue with version and reproduction steps
2. Label as `bug` or `breaking-change`
3. Include minimal reproducible example

---

## FAQ

**Q: Can I rely on v0.x APIs for production?**

A: Yes. While on 0.x versions, Tier 1 & 2 APIs are stable and supported. The project uses semantic versioning; breaking changes require MAJOR version bump.

**Q: Will my v0.1.0 code work on v0.2.0?**

A: Yes, 100% backward compatible. You can upgrade freely.

**Q: What about v0.3.0 with AsyncResult?**

A: Planned for v0.3.0, will be purely additive. Existing sync APIs unchanged.

**Q: Is `_context_chain` private?**

A: Yes. Use public API (`context()`, `with_context()`) instead. Private fields may change.

---

## References

- [CHANGELOG.md](CHANGELOG.md) — Version history and feature additions
- [README.md](README.md) — Quick start and examples
- [pyproject.toml](pyproject.toml) — Python version and dependency constraints

---

**Last Updated:** 2026-01-24  
**Stability Policy Version:** 1.0
