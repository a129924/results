"""Integration tests for context chain propagation across Maybe/Result."""

# pyright: reportPrivateUsage=false
from __future__ import annotations

import pytest

from results import AsyncMaybe, Err, Ok
from results.core.base import Result
from results.exceptions import UnwrapError
from results.maybe import Nothing


def test_maybe_context_chain_lifo() -> None:
    """Context chain preserves LIFO order on Nothing."""
    nothing: Nothing[None] = (  # type: ignore
        Nothing().context("step1").context("step2").context("step3")
    )
    assert nothing._context_chain.messages == ("step3", "step2", "step1")


def test_result_context_chain_lifo() -> None:
    """Context chain preserves LIFO order on Err."""
    err: Result[str, str] = Err[str, str]("boom").context("layer1").context("layer2")
    assert err._context_chain.messages == ("layer2", "layer1")  # type: ignore


def test_maybe_unwrap_error_includes_context() -> None:
    """UnwrapError shows context from Nothing."""
    value: Nothing[None] = Nothing().context("missing user")  # type: ignore
    with pytest.raises(UnwrapError) as exc_info:
        value.unwrap()
    assert "missing user" in str(exc_info.value)


def test_result_unwrap_error_includes_context() -> None:
    """UnwrapError shows context from Err."""
    result: Err[str, str] = Err[str, str]("fail").context("operation")  # type: ignore
    with pytest.raises(UnwrapError) as exc_info:
        result.unwrap()
    assert "operation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_async_maybe_unwrap_error_includes_context() -> None:
    """Async unwrap error contains formatted context chain."""
    async_maybe = AsyncMaybe[None].from_maybe(Nothing()).context("fetching")
    with pytest.raises(UnwrapError) as exc_info:
        await async_maybe.unwrap_async()
    assert "fetching" in str(exc_info.value)


def test_context_chain_with_successful_result() -> None:
    """Ok values do not accumulate context without errors."""
    result = Ok[int, str](1).context("ignored")
    assert result.is_ok()
    assert result.ok() == 1
