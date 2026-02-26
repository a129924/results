#!/usr/bin/env python3
"""
Async Workflow Example

Demonstrates AsyncResult in a realistic async pipeline.

Run: python async_workflow.py

Install httpx for real HTTP: pip install httpx
"""

import asyncio
from datetime import datetime
from typing import TypedDict

from results import AsyncResult, Err, Ok, Result

# ============================================================================
# 1. Simulated Async Operations
# ============================================================================


class User(TypedDict):
    id: int
    name: str
    company_id: int


class Company(TypedDict):
    name: str
    company_id: int


class UserCompanyInfo(TypedDict):
    user: User
    company: Company


async def fetch_user_data(user_id: int) -> Result[User, str]:
    """Simulate fetching user data from API."""
    await asyncio.sleep(0.1)  # Simulate I/O

    db: dict[int, User] = {
        1: {"id": 1, "name": "Alice", "company_id": 100},
        2: {"id": 2, "name": "Bob", "company_id": 101},
    }

    if user_id in db:
        return Ok(db[user_id])
    else:
        return Err("user_not_found")


async def fetch_company_data(company_id: int) -> Result[Company, str]:
    """Simulate fetching company data from API."""
    await asyncio.sleep(0.1)  # Simulate I/O

    db: dict[int, Company] = {
        100: {"name": "Acme Inc", "company_id": 100},
        101: {"name": "Tech Corp", "company_id": 101},
    }

    if company_id in db:
        return Ok(db[company_id])
    else:
        return Err("company_not_found")


async def validate_user(
    user: User,
) -> Result[User, str]:
    """Validate user data."""
    await asyncio.sleep(0.05)  # Simulate processing

    if not user.get("name"):
        return Err("user_has_no_name")
    if user.get("id", 0) <= 0:
        return Err("invalid_user_id")

    return Ok(user)


# ============================================================================
# 2. Single Async Operation
# ============================================================================


async def example_single_async():
    print("--- Single Async Operation ---")

    result = await AsyncResult[User, str].from_awaitable(fetch_user_data(1))

    match result:
        case Ok(user):
            print(f"✓ User fetched: {user['name']}")
        case Err(error):
            print(f"✗ Error: {error}")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 3. Chaining Async Operations
# ============================================================================


async def example_async_chain():
    print("\n--- Chaining Async Operations ---")

    async def fetch_user_and_company(
        user: User,
    ) -> Result[UserCompanyInfo, str]:
        """Fetch user and then their company."""
        return (
            await AsyncResult[Company, str].from_awaitable(
                fetch_company_data(user["company_id"])
            )
        ).map(lambda company: UserCompanyInfo(user=user, company=company))

    # Fetch user, then fetch their company
    result: Result[UserCompanyInfo, str] = (
        await AsyncResult[User, str]
        .from_awaitable(fetch_user_data(1))
        .and_then_async(fetch_user_and_company)
    )

    match result:
        case Ok(data):
            print(f"✓ {data['user']['name']} works at {data['company']['name']}")
        case Err(error):
            print(f"✗ Error: {error}")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 4. Validation in Async Chain
# ============================================================================


async def example_async_validation():
    async def validate_and_fetch_company(user: User) -> Result[Company, str]:
        return await fetch_company_data(user["company_id"])

    print("\n--- Async with Validation ---")

    result: Result[Company, str] = await (
        AsyncResult[User, str]
        .from_awaitable(fetch_user_data(2))
        .and_then_async(validate_user)
        .and_then_async(validate_and_fetch_company)
    )

    match result:
        case Ok(company):
            print(f"✓ Found company: {company['name']}")
        case Err(error):
            print(f"✗ Validation/fetch failed: {error}")
        case unexpected:
            print(f"Unexpected: {unexpected}")


# ============================================================================
# 5. Error Handling and Recovery
# ============================================================================


async def example_error_recovery():
    print("\n--- Error Handling and Recovery ---")

    # Fetch non-existent user, recover with default
    result = await AsyncResult[User, str].from_awaitable(fetch_user_data(999))
    user = result.unwrap_or({"id": 0, "name": "Anonymous", "company_id": 0})

    match result:
        case Ok(_):
            print(f"✓ Final user: {user['name']}")
        case Err(error):
            # Error, but we have default user
            print(f"✓ Error recovered with default user: {user['name']}")
            print(f"  (Original error: {error})")


# ============================================================================
# 6. Concurrent Async Operations (Gather)
# ============================================================================


async def example_concurrent():
    print("\n--- Concurrent Operations ---")

    # Fetch multiple users in parallel
    async def fetch_all_users():
        r1 = asyncio.create_task(fetch_user_data(1))
        r2 = asyncio.create_task(fetch_user_data(2))
        r3 = asyncio.create_task(fetch_user_data(3))

        results = await asyncio.gather(r1, r2, r3)

        # Check if all succeeded
        users = []
        for result in results:
            if result.is_ok():
                users.append(result.ok())
            else:
                return Err(f"One user fetch failed: {result.err()}")

        return Ok(users)

    result = await fetch_all_users()

    match result:
        case Ok(users):
            print(f"✓ Fetched {len(users)} users concurrently")
            for user in users:
                print(f"  - {user['name']}")
        case Err(error):
            print(f"✗ Concurrent fetch failed: {error}")


# ============================================================================
# 7. Timeout Handling
# ============================================================================


async def example_with_timeout():
    print("\n--- Timeout Handling ---")

    async def slow_operation():
        await asyncio.sleep(2)
        return Ok({"data": "result"})

    try:
        # Create task with short timeout
        await asyncio.wait_for(
            AsyncResult.from_awaitable(slow_operation()).unwrap_async(), timeout=1.0
        )
        print("✓ Operation succeeded")
    except asyncio.TimeoutError:
        print("✗ Operation timed out")
    except Exception as e:
        print(f"✗ Operation failed: {e}")


# ============================================================================
# 8. Real-World: Data Pipeline
# ============================================================================


async def example_data_pipeline():
    print("\n--- Real-World Data Pipeline ---")

    async def process_user_pipeline(user_id: int) -> Result[dict, str]:
        """Full pipeline with context."""
        return await (
            AsyncResult.from_awaitable(fetch_user_data(user_id))
            .context(f"fetching user {user_id}")
            .and_then_async(validate_user)
            .context("validating user")
            .and_then_async(
                lambda user: AsyncResult.from_awaitable(
                    fetch_company_data(user["company_id"])
                )
            )
            .context("fetching company")
            .map_async(
                lambda company: {
                    "processed_at": datetime.now().isoformat(),
                    "status": "completed",
                    "company_name": company["name"],
                    "company_size": company.get("employees", "unknown"),
                }
            )
        )

    result = await process_user_pipeline(1)

    match result:
        case Ok(output):
            print("✓ Pipeline succeeded:")
            for key, value in output.items():
                print(f"  {key}: {value}")
        case Err(error):
            print(f"✗ Pipeline failed: {error}")


# ============================================================================
# 9. Retry Logic
# ============================================================================


async def example_retry():
    print("\n--- Retry Logic ---")

    async def fetch_with_retry(user_id: int, max_retries: int = 3) -> Result[dict, str]:
        """Retry failed async operations."""
        for attempt in range(max_retries):
            result = await AsyncResult.from_awaitable(fetch_user_data(user_id))
            if result.is_ok():
                return Ok(result.ok())

            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff
                print(f"  Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)

        return Err("max_retries_exceeded")

    print("Retrying user fetch...")
    result = await fetch_with_retry(1, max_retries=2)

    match result:
        case Ok(user):
            print(f"✓ Retry succeeded: {user['name']}")
        case Err(error):
            print(f"✗ All retries failed: {error}")


# ============================================================================
# Main
# ============================================================================


async def main():
    print("=" * 70)
    print("Async Workflow Example")
    print("=" * 70)
    print()

    await example_single_async()
    await example_async_chain()
    await example_async_validation()
    await example_error_recovery()
    await example_concurrent()
    await example_with_timeout()
    await example_data_pipeline()
    await example_retry()

    print("\n" + "=" * 70)
    print("Key Patterns:")
    print("  1. Use AsyncResult.from_awaitable() to wrap async operations")
    print("  2. Chain with .and_then_async() for dependent operations")
    print("  3. Use asyncio.gather() for concurrent fetches")
    print("  4. Add context() for tracing through async pipelines")
    print("  5. Implement retry logic with exponential backoff")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
