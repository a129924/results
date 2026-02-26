"""Integration tests for Result and Maybe chaining."""

# pyright: reportArgumentType=false
from __future__ import annotations

import json

from results import Err, Ok, Result
from results.core.maybe_base import Maybe
from results.maybe import Nothing, Some, flatten, get_or_insert, map_or, transpose


def test_result_to_maybe_chain_success() -> None:
    """Result -> Maybe -> Result chain success case."""

    def parse_user(json_str: str) -> Result[dict[str, str], str]:
        try:
            return Ok(json.loads(json_str))
        except json.JSONDecodeError as exc:
            return Err(str(exc))

    def extract_email(user_dict: dict[str, str]) -> Maybe[str]:
        return Some(user_dict["email"]) if "email" in user_dict else Nothing()

    chain = parse_user('{"email": "test@example.com"}').map(
        lambda user: extract_email(user)
    )

    assert chain.is_ok()
    maybe_email = chain.ok()
    assert maybe_email is not None
    assert maybe_email.unwrap() == "test@example.com"


def test_result_to_maybe_chain_missing_email() -> None:
    """Missing email yields Ok(Nothing())."""

    def parse_user(json_str: str) -> Result[dict[str, str], str]:
        return Ok(json.loads(json_str))

    def extract_email(user_dict: dict[str, str]) -> Maybe[str]:
        return Some(user_dict["email"]) if "email" in user_dict else Nothing()

    chain = parse_user("{}").map(lambda user: extract_email(user))
    assert chain.is_ok()
    maybe_email = chain.ok()
    assert maybe_email is not None
    assert maybe_email.is_nothing()


def test_result_to_maybe_chain_parse_error() -> None:
    """Invalid JSON produces Err and bypasses Maybe."""

    def parse_user(json_str: str) -> Result[dict[str, str], str]:
        try:
            return Ok(json.loads(json_str))
        except json.JSONDecodeError as exc:
            return Err(str(exc))

    chain = parse_user("not-json").map(lambda user: Some(user))
    assert chain.is_err()


def test_maybe_to_result_conversion() -> None:
    """Convert Maybe to Result with explicit fallback."""

    def to_result(maybe: Maybe[str]) -> Result[str, str]:
        if maybe.is_some():
            return Ok(maybe.unwrap())
        return Err("missing")

    assert to_result(Some("value")).is_ok()
    assert to_result(Nothing()).is_err()


def test_error_recovery_with_maybe_fallback() -> None:
    """Recover missing values using or_else and unwrap_or."""

    def lookup_config(key: str) -> Maybe[str]:
        configs = {"timeout": "30s"}
        return Some(configs[key]) if key in configs else Nothing()

    timeout = (
        lookup_config("timeout")
        .or_else(lambda: lookup_config("default_timeout"))
        .unwrap_or("60s")
    )
    assert timeout == "30s"

    retry = (
        lookup_config("retry_count")
        .or_else(lambda: lookup_config("default_retry"))
        .unwrap_or("3")
    )
    assert retry == "3"


def test_helpers_in_chain() -> None:
    """Helper functions compose with Maybe in realistic flows."""
    nested = Some(Some(7))
    flattened = flatten(nested)
    assert flattened.unwrap() == 7

    transposed = transpose(Some([1, 2]))
    assert [item.unwrap() for item in transposed] == [1, 2]

    mapped = map_or(Some(3), 0, lambda x: x * 3)
    assert mapped == 9

    inserted = get_or_insert(Nothing(), 5)
    assert inserted.unwrap() == 5
