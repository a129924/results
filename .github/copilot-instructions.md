# GitHub Copilot Instructions

This repository is a **Rust-inspired Result/Maybe type implementation in Python**.

## Core Philosophy

Functional, composable error handling is the primary design goal — not imperative branching.

## Key Rules

- **Prefer functional chaining** (`map`, `map_err`, `and_then`) over `is_ok()` / `is_err()` imperative checks
- **Prefer `match/case`** over `if result.is_ok()` when dispatching on Result/Maybe at boundaries
- **Use `context()`** to attach error tracing information to `Err` / `Nothing`
- **All code must pass** `mypy --strict` with zero errors
- **All code must pass** `ruff` checks

Detailed coding style rules are in `.github/skills/result-coding-style/SKILL.md`.
