"""Tests for async/sync interoperability of AsyncResult."""

import asyncio
from typing import Any

import pytest

from results import AsyncResult, Err, Ok, Result


def sync_ok(val: int) -> Result[int, Any]:
    return Ok(val)


def sync_err(msg: str) -> Result[Any, str]:
    return Err(msg)


def sync_inc(val: int) -> int:
    return val + 1


async def async_ok(val: int) -> Result[int, Any]:
    await asyncio.sleep(0)
    return Ok(val)


async def async_err(msg: str) -> Result[Any, str]:
    await asyncio.sleep(0)
    return Err(msg)


async def async_inc(val: int) -> int:
    await asyncio.sleep(0)
    return val + 1


@pytest.mark.asyncio
async def test_chain_sync_into_async() -> None:
    res = AsyncResult.from_result(sync_ok(1)).map_async(async_inc)
    inner = await res
    assert isinstance(inner, Ok)
    assert inner.ok() == 2


@pytest.mark.asyncio
async def test_chain_async_into_sync() -> None:
    res = AsyncResult.from_awaitable(async_ok(2)).map_async(
        lambda v: asyncio.to_thread(sync_inc, v)
    )
    inner = await res
    assert isinstance(inner, Ok)
    assert inner.ok() == 3


@pytest.mark.asyncio
async def test_and_then_async_with_sync_handler() -> None:
    res = AsyncResult.from_result(sync_ok(5)).and_then_async(
        lambda v: asyncio.to_thread(sync_ok, v * 2)
    )
    inner = await res
    assert isinstance(inner, Ok)
    assert inner.ok() == 10


@pytest.mark.asyncio
async def test_and_then_async_propagates_async_success() -> None:
    res = AsyncResult.from_result(sync_ok(5)).and_then_async(
        lambda v: async_ok(v)  # Return Ok to match the type
    )
    inner = await res
    assert isinstance(inner, Ok)
    assert inner.ok() == 5


@pytest.mark.asyncio
async def test_context_stack_preserved_across_sync_async() -> None:
    res = AsyncResult.from_result(sync_err("boom")).context("outer")
    res = res.and_then_async(async_ok).context("inner")
    inner = await res
    assert inner.is_err()
    assert inner.err() == "boom"
