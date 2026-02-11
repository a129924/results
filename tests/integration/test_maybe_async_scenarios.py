"""Integration tests for async Maybe and Result workflows."""

from __future__ import annotations

import asyncio

import pytest

from results import AsyncResult, Err, Ok, Result
from results.core.maybe_base import Maybe
from results.maybe import AsyncMaybe, Nothing, Some


class TestAsyncMaybeIntegration:
    """Async Maybe integration scenarios."""

    @pytest.mark.asyncio
    async def test_async_maybe_chain_success(self) -> None:
        """AsyncMaybe map_async and and_then_async chain."""

        async def double(x: int) -> int:
            await asyncio.sleep(0.001)
            return x * 2

        async def to_even_maybe(x: int) -> Maybe[int]:
            await asyncio.sleep(0.001)
            return Some(x) if x % 2 == 0 else Nothing()

        async_maybe = AsyncMaybe[int].from_maybe(Some(4))
        result_async = async_maybe.map_async(double).and_then_async(to_even_maybe)
        maybe = await result_async

        assert maybe.is_some()
        assert maybe.unwrap() == 8

    @pytest.mark.asyncio
    async def test_async_maybe_short_circuit(self) -> None:
        """Nothing short-circuits async transformations."""
        call_count = 0

        async def record(_x: int) -> int:
            nonlocal call_count
            call_count += 1
            return 1

        async_maybe = AsyncMaybe[int].from_maybe(Nothing())
        result_async = async_maybe.map_async(record)
        maybe = await result_async

        assert maybe.is_nothing()
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_async_maybe_or_else(self) -> None:
        """or_else_async provides fallback value."""

        async def fallback() -> Maybe[int]:
            await asyncio.sleep(0.001)
            return Some(99)

        async_maybe = AsyncMaybe[int].from_maybe(Nothing())
        result_async = async_maybe.or_else_async(fallback)
        maybe = await result_async

        assert maybe.unwrap() == 99

    @pytest.mark.asyncio
    async def test_async_maybe_inspect(self) -> None:
        """inspect_async triggers side effects only on Some."""
        observed: list[int] = []

        async def observe(value: int) -> None:
            await asyncio.sleep(0.001)
            observed.append(value)

        async_maybe = AsyncMaybe[int].from_maybe(Some(7))
        result_async = async_maybe.inspect_async(observe)
        maybe = await result_async

        assert maybe.unwrap() == 7
        assert observed == [7]


class TestAsyncResultToMaybeIntegration:
    """Async Result to Maybe interop scenarios."""

    @pytest.mark.asyncio
    async def test_async_result_to_async_maybe(self) -> None:
        """AsyncResult can feed AsyncMaybe in a pipeline."""

        async def fetch_user(user_id: int) -> Result[dict[str, str], str]:
            if user_id > 0:
                return Ok({"id": str(user_id), "email": "user@example.com"})
            return Err("invalid user id")

        async def extract_email(user: dict[str, str]) -> Maybe[str]:
            await asyncio.sleep(0.001)
            return Some(user["email"]) if "email" in user else Nothing()

        async_result = AsyncResult[dict[str, str], str].from_awaitable(fetch_user(1))
        result = await async_result
        assert result.is_ok()

        user = result.ok()
        assert user is not None

        async_maybe = AsyncMaybe[str].from_awaitable(extract_email(user))
        email = await async_maybe.unwrap_or_async("missing")
        assert email == "user@example.com"
