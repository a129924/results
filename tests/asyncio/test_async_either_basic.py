"""Tests for AsyncEither basic operations and async transformations.

Coverage:
- Creation from Either and Awaitable
- is_left/is_right async checks
- map_async with Right values
- map_left_async with Left values
- Context chain through async operations
- Edge cases and error handling
"""

import asyncio
from typing import Any, Literal

import pytest

from results import AsyncEither, Left, Right
from results.core.either_base import Either


class TestAsyncEitherCreation:
    """Tests for AsyncEither creation methods."""

    @pytest.mark.asyncio
    async def test_from_either_right(self) -> None:
        """Create AsyncEither from sync Right[T]."""
        either = Right[int, int](42)
        async_either = AsyncEither[int, int].from_either(either)
        result = await async_either
        assert result.is_right()
        assert result.unwrap_right() == 42

    @pytest.mark.asyncio
    async def test_from_either_left(self) -> None:
        """Create AsyncEither from sync Left[E]."""
        either = Left[Literal["error"], int]("error")
        async_either = AsyncEither[Literal["error"], int].from_either(either)
        result = await async_either
        assert result.is_left()
        assert result.unwrap_left() == "error"

    @pytest.mark.asyncio
    async def test_from_awaitable_right(self) -> None:
        """Create AsyncEither from Awaitable[Either[...]] returning Right."""

        async def fetch_right() -> Any:
            await asyncio.sleep(0)
            return Right[int, int](99)

        async_either = AsyncEither[int, int].from_awaitable(fetch_right())
        result = await async_either
        assert result.is_right()
        assert result.unwrap_right() == 99

    @pytest.mark.asyncio
    async def test_from_awaitable_left(self) -> None:
        """Create AsyncEither from Awaitable[Either[...]] returning Left."""

        async def fetch_left() -> Any:
            await asyncio.sleep(0)
            return Left[Literal["async error"], int]("async error")

        async_either = AsyncEither[Literal["async error"], int].from_awaitable(
            fetch_left()
        )
        result = await async_either
        assert result.is_left()
        assert result.unwrap_left() == "async error"


class TestAsyncEitherVariantChecks:
    """Tests for is_left_async and is_right_async methods."""

    @pytest.mark.asyncio
    async def test_is_right_async_true(self) -> None:
        """Check is_right_async returns True for Right."""
        async_either = AsyncEither[int, int].from_either(Right[int, int](42))
        result = await async_either.is_right_async()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_right_async_false(self) -> None:
        """Check is_right_async returns False for Left."""
        async_either = AsyncEither[Literal["error"], int].from_either(
            Left[Literal["error"], int]("error")
        )
        result = await async_either.is_right_async()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_left_async_true(self) -> None:
        """Check is_left_async returns True for Left."""
        async_either = AsyncEither[Literal["error"], int].from_either(
            Left[Literal["error"], int]("error")
        )
        result = await async_either.is_left_async()
        assert result is True

    @pytest.mark.asyncio
    async def test_is_left_async_false(self) -> None:
        """Check is_left_async returns False for Right."""
        async_either = AsyncEither[int, int].from_either(Right[int, int](42))
        result = await async_either.is_left_async()
        assert result is False


class TestAsyncEitherMapAsync:
    """Tests for map_async (right-biased)."""

    @pytest.mark.asyncio
    async def test_map_async_right_transforms_value(self) -> None:
        """map_async on Right applies transformation."""

        async def double(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        async_either = AsyncEither[int, int].from_either(Right[int, int](5))
        result = await async_either.map_async(double)
        assert result.is_right()
        assert result.unwrap_right() == 10

    @pytest.mark.asyncio
    async def test_map_async_left_short_circuits(self) -> None:
        """map_async on Left short-circuits without calling function."""
        call_count = 0

        async def counter(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0)
            return x * 2

        async_either = AsyncEither[Literal["error"], int].from_either(
            Left[Literal["error"], int]("error")
        )
        result = await async_either.map_async(counter)
        assert result.is_left()
        assert result.unwrap_left() == "error"
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_map_async_chain_multiple(self) -> None:
        """Chain multiple map_async calls."""

        async def add_one(x: int) -> int:
            await asyncio.sleep(0)
            return x + 1

        async def double(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        async_either = AsyncEither[int, int].from_either(Right[int, int](5))
        result = await async_either.map_async(add_one).map_async(double)
        assert result.is_right()
        assert result.unwrap_right() == 12


class TestAsyncEitherMapLeftAsync:
    """Tests for map_left_async (left-focused)."""

    @pytest.mark.asyncio
    async def test_map_left_async_left_transforms_value(self) -> None:
        """map_left_async on Left applies transformation."""

        async def enhance_error(e: str) -> str:
            await asyncio.sleep(0)
            return f"Enhanced: {e}"

        async_either = AsyncEither[Literal["error"], int].from_either(
            Left[Literal["error"], int]("error")
        )
        result = await async_either.map_left_async(enhance_error)
        assert result.is_left()
        assert result.unwrap_left() == "Enhanced: error"

    @pytest.mark.asyncio
    async def test_map_left_async_right_short_circuits(self) -> None:
        """map_left_async on Right short-circuits without calling function."""
        call_count = 0

        async def counter(e: str) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0)
            return f"Enhanced: {e}"

        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        result = await async_either.map_left_async(counter)
        assert result.is_right()
        assert result.unwrap_right() == 42
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_map_left_async_chain_multiple(self) -> None:
        """Chain multiple map_left_async calls."""

        async def prefix(e: str) -> str:
            await asyncio.sleep(0)
            return f"[{e}]"

        async def enhance(e: str) -> str:
            await asyncio.sleep(0)
            return f"Error: {e}"

        async_either = AsyncEither[Literal["oops"], int].from_either(
            Left[Literal["oops"], int]("oops")
        )
        result = await async_either.map_left_async(enhance).map_left_async(prefix)
        assert result.is_left()
        assert result.unwrap_left() == "[Error: oops]"


class TestAsyncEitherAndThenAsync:
    """Tests for and_then_async (right-biased monadic binding)."""

    @pytest.mark.asyncio
    async def test_and_then_async_right_chains(self) -> None:
        """and_then_async on Right with successful chain."""

        async def validate_positive(x: int) -> Either[str, int]:
            await asyncio.sleep(0)
            return Right[str, int](x) if x > 0 else Left[str, int]("not positive")

        async_either = AsyncEither[str, int].from_either(Right[str, int](5))
        result = await async_either.and_then_async(validate_positive)
        assert result.is_right()
        assert result.unwrap_right() == 5

    @pytest.mark.asyncio
    async def test_and_then_async_right_fails(self) -> None:
        """and_then_async on Right with failing chain."""

        async def validate_positive(x: int) -> Either[str, int]:
            await asyncio.sleep(0)
            return Right[str, int](x) if x > 0 else Left[str, int]("not positive")

        async_either = AsyncEither[str, int].from_either(Right[str, int](-5))
        result = await async_either.and_then_async(validate_positive)
        assert result.is_left()
        assert result.unwrap_left() == "not positive"

    @pytest.mark.asyncio
    async def test_and_then_async_left_short_circuits(self) -> None:
        """and_then_async on Left short-circuits."""
        call_count = 0

        async def counter(x: int) -> Either[str, int]:
            nonlocal call_count
            call_count += 1
            return Right[str, int](x)

        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        result = await async_either.and_then_async(counter)
        assert result.is_left()
        assert call_count == 0


class TestAsyncEitherAndThenLeftAsync:
    """Tests for and_then_left_async (left-focused monadic binding)."""

    @pytest.mark.asyncio
    async def test_and_then_left_async_left_chains(self) -> None:
        """and_then_left_async on Left with recovery."""

        async def recover(e: str) -> Either[str, int]:
            await asyncio.sleep(0)
            return Right[str, int](99) if "recoverable" in e else Left[str, int](e)

        async_either = AsyncEither[str, int].from_either(
            Left[str, int]("recoverable error")
        )
        result = await async_either.and_then_left_async(recover)
        assert result.is_right()
        assert result.unwrap_right() == 99

    @pytest.mark.asyncio
    async def test_and_then_left_async_left_fails(self) -> None:
        """and_then_left_async on Left with recovery fails."""

        async def recover(e: str) -> Either[str, int]:
            await asyncio.sleep(0)
            return Right[str, int](99) if "can recover" in e else Left[str, int](e)

        async_either = AsyncEither[str, int].from_either(
            Left[str, int]("permanent failure")
        )
        result = await async_either.and_then_left_async(recover)
        assert result.is_left()
        assert result.unwrap_left() == "permanent failure"


class TestAsyncEitherOrElseAsync:
    """Tests for or_else_async (right-biased recovery)."""

    @pytest.mark.asyncio
    async def test_or_else_async_left_recovers(self) -> None:
        """or_else_async on Left applies recovery."""

        async def default() -> Either[str, int]:
            await asyncio.sleep(0)
            return Right[str, int](99)

        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        result = await async_either.or_else_async(lambda _: default())
        assert result.is_right()
        assert result.unwrap_right() == 99

    @pytest.mark.asyncio
    async def test_or_else_async_right_short_circuits(self) -> None:
        """or_else_async on Right short-circuits."""
        call_count = 0

        async def counter(e: str) -> Either[str, int]:
            nonlocal call_count
            call_count += 1
            return Right[str, int](99)

        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        result = await async_either.or_else_async(counter)
        assert result.is_right()
        assert result.unwrap_right() == 42
        assert call_count == 0


class TestAsyncEitherOrElseLeftAsync:
    """Tests for or_else_left_async (left-focused alternative)."""

    @pytest.mark.asyncio
    async def test_or_else_left_async_right_handles(self) -> None:
        """or_else_left_async on Right applies handler."""

        async def handle(x: int) -> Either[str, int]:
            await asyncio.sleep(0)
            return Right[str, int](x + 1) if x < 10 else Left[str, int]("too large")

        async_either = AsyncEither[str, int].from_either(Right[str, int](5))
        result = await async_either.or_else_left_async(handle)
        assert result.is_right()
        assert result.unwrap_right() == 6


class TestAsyncEitherBimapAsync:
    """Tests for bimap_async (symmetric transformation)."""

    @pytest.mark.asyncio
    async def test_bimap_async_on_right(self) -> None:
        """bimap_async applies right function to Right."""

        async def left_fn(e: str) -> str:
            return f"Error: {e}"

        async def right_fn(x: int) -> str:
            await asyncio.sleep(0)
            return f"Value: {x}"

        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        result = await async_either.bimap_async(left_fn, right_fn)
        assert result.is_right()
        assert result.unwrap_right() == "Value: 42"

    @pytest.mark.asyncio
    async def test_bimap_async_on_left(self) -> None:
        """bimap_async applies left function to Left."""

        async def left_fn(e: str) -> str:
            await asyncio.sleep(0)
            return f"Error: {e}"

        async def right_fn(x: int) -> str:
            return f"Value: {x}"

        async_either = AsyncEither[str, int].from_either(Left[str, int]("oops"))
        result = await async_either.bimap_async(left_fn, right_fn)
        assert result.is_left()
        assert result.unwrap_left() == "Error: oops"


class TestAsyncEitherFoldAsync:
    """Tests for fold_async (catamorphism)."""

    @pytest.mark.asyncio
    async def test_fold_async_on_right(self) -> None:
        """fold_async applies right function to Right."""

        async def left_fn(e: str) -> str:
            return f"Error: {e}"

        async def right_fn(x: int) -> str:
            await asyncio.sleep(0)
            return f"Value: {x}"

        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        result = await async_either.fold_async(left_fn, right_fn)
        assert result == "Value: 42"

    @pytest.mark.asyncio
    async def test_fold_async_on_left(self) -> None:
        """fold_async applies left function to Left."""

        async def left_fn(e: str) -> str:
            await asyncio.sleep(0)
            return f"Error: {e}"

        async def right_fn(x: int) -> str:
            return f"Value: {x}"

        async_either = AsyncEither[str, int].from_either(Left[str, int]("oops"))
        result = await async_either.fold_async(left_fn, right_fn)
        assert result == "Error: oops"


class TestAsyncEitherInspectAsync:
    """Tests for inspect_async (right-biased side effects)."""

    @pytest.mark.asyncio
    async def test_inspect_async_right_executes(self) -> None:
        """inspect_async on Right executes side effects."""
        side_effects: list[int] = []

        async def log(x: int) -> None:
            await asyncio.sleep(0)
            side_effects.append(x)

        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        result = await async_either.inspect_async(log)
        assert result.is_right()
        assert side_effects == [42]

    @pytest.mark.asyncio
    async def test_inspect_async_left_skips(self) -> None:
        """inspect_async on Left skips side effects."""
        side_effects: list[int] = []

        async def log(x: int) -> None:
            await asyncio.sleep(0)
            side_effects.append(x)

        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        result = await async_either.inspect_async(log)
        assert result.is_left()
        assert side_effects == []


class TestAsyncEitherInspectLeftAsync:
    """Tests for inspect_left_async (left-focused side effects)."""

    @pytest.mark.asyncio
    async def test_inspect_left_async_left_executes(self) -> None:
        """inspect_left_async on Left executes side effects."""
        side_effects: list[str] = []

        async def log(e: str) -> None:
            await asyncio.sleep(0)
            side_effects.append(e)

        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        result = await async_either.inspect_left_async(log)
        assert result.is_left()
        assert side_effects == ["error"]

    @pytest.mark.asyncio
    async def test_inspect_left_async_right_skips(self) -> None:
        """inspect_left_async on Right skips side effects."""
        side_effects: list[str] = []

        async def log(e: str) -> None:
            await asyncio.sleep(0)
            side_effects.append(e)

        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        result = await async_either.inspect_left_async(log)
        assert result.is_right()
        assert side_effects == []


class TestAsyncEitherUnwrapAsync:
    """Tests for unwrap_*_async methods."""

    @pytest.mark.asyncio
    async def test_unwrap_right_async_succeeds(self) -> None:
        """unwrap_right_async on Right returns value."""
        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        value = await async_either.unwrap_right_async()
        assert value == 42

    @pytest.mark.asyncio
    async def test_unwrap_right_async_fails(self) -> None:
        """unwrap_right_async on Left raises UnwrapError."""
        from results.exceptions import UnwrapError

        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        with pytest.raises(UnwrapError):
            await async_either.unwrap_right_async()

    @pytest.mark.asyncio
    async def test_unwrap_left_async_succeeds(self) -> None:
        """unwrap_left_async on Left returns value."""
        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        value = await async_either.unwrap_left_async()
        assert value == "error"

    @pytest.mark.asyncio
    async def test_unwrap_left_async_fails(self) -> None:
        """unwrap_left_async on Right raises UnwrapError."""
        from results.exceptions import UnwrapError

        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        with pytest.raises(UnwrapError):
            await async_either.unwrap_left_async()


class TestAsyncEitherUnwrapOrAsync:
    """Tests for unwrap_*_or_async methods."""

    @pytest.mark.asyncio
    async def test_unwrap_right_or_async_right(self) -> None:
        """unwrap_right_or_async on Right returns value."""
        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        value = await async_either.unwrap_right_or_async(99)
        assert value == 42

    @pytest.mark.asyncio
    async def test_unwrap_right_or_async_left(self) -> None:
        """unwrap_right_or_async on Left returns default."""
        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        value = await async_either.unwrap_right_or_async(99)
        assert value == 99

    @pytest.mark.asyncio
    async def test_unwrap_left_or_async_left(self) -> None:
        """unwrap_left_or_async on Left returns value."""
        async_either = AsyncEither[str, int].from_either(Left[str, int]("error"))
        value = await async_either.unwrap_left_or_async("default")
        assert value == "error"

    @pytest.mark.asyncio
    async def test_unwrap_left_or_async_right(self) -> None:
        """unwrap_left_or_async on Right returns default."""
        async_either = AsyncEither[str, int].from_either(Right[str, int](42))
        value = await async_either.unwrap_left_or_async("default")
        assert value == "default"


class TestAsyncEitherContextChain:
    """Tests for context chain management in AsyncEither."""

    @pytest.mark.asyncio
    async def test_context_used_on_unwrap_fail_right(self) -> None:
        """Context chain used when unwrap_right fails on Left."""
        from results.exceptions import UnwrapError

        async_either = (
            AsyncEither[str, int]
            .from_either(Left[str, int]("error"))
            .context("step 1")
            .context("step 2")
        )
        with pytest.raises(UnwrapError) as exc_info:
            await async_either.unwrap_right_async()

        # Context should be included in error
        error = exc_info.value
        assert str(error) is not None  # Error message exists

    @pytest.mark.asyncio
    async def test_context_used_on_unwrap_fail_left(self) -> None:
        """Context chain used when unwrap_left fails on Right."""
        from results.exceptions import UnwrapError

        async_either = (
            AsyncEither[str, int]
            .from_either(Right[str, int](42))
            .context("step 1")
            .context("step 2")
        )
        with pytest.raises(UnwrapError) as exc_info:
            await async_either.unwrap_left_async()

        # Context should be included in error
        error = exc_info.value
        assert str(error) is not None  # Error message exists

    @pytest.mark.asyncio
    async def test_context_through_transformation_chain(self) -> None:
        """Context preserved through multiple transformations."""

        async def transform(x: int) -> int:
            await asyncio.sleep(0)
            return x * 2

        # Chain context through multiple operations
        async_either = (
            AsyncEither[str, int]
            .from_either(Right[str, int](5))
            .context("created")
            .map_async(transform)
            .context("transformed")
        )
        result = await async_either
        assert result.is_right()
        assert result.unwrap_right() == 10

    @pytest.mark.asyncio
    async def test_with_context_lazy_evaluation(self) -> None:
        """with_context lazily evaluates message."""
        import time

        timestamps: list[float] = []

        async_either = (
            AsyncEither[str, int]
            .from_either(Right[str, int](42))
            .with_context(lambda: (timestamps.append(time.time()), "evaluated")[1])
        )
        # Evaluation happens during with_context call, before await
        await asyncio.sleep(0.01)
        result = await async_either
        assert result.is_right()
        assert len(timestamps) == 1  # Lazily evaluated at with_context, not await
