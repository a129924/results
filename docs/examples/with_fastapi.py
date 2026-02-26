#!/usr/bin/env python3
"""
Integration with FastAPI

Shows how to use Results for error handling in FastAPI applications.

Run: python with_fastapi.py
Note: This is demonstration code. Install fastapi to run:
      pip install fastapi uvicorn

Example FastAPI route patterns with Results for clean API error handling.
"""

# Demonstration - actual FastAPI imports commented to avoid dependency

from pydantic import BaseModel

from results import Err, Ok, Result

# ============================================================================
# 1. Response Models
# ============================================================================


class SuccessResponse(BaseModel):
    """Generic success response."""

    status: str = "success"
    data: dict


class ErrorResponse(BaseModel):
    """Generic error response."""

    status: str = "error"
    message: str
    code: str


# ============================================================================
# 2. Business Logic with Result
# ============================================================================


class User:
    """Simulated user database."""

    _db = {
        1: {"id": 1, "name": "Alice", "email": "alice@example.com"},
        2: {"id": 2, "name": "Bob", "email": "bob@example.com"},
    }

    @classmethod
    def get_by_id(cls, user_id: int) -> Result[dict, str]:
        """Fetch user by ID."""
        if user_id not in cls._db:
            return Err("user_not_found")
        return Ok(cls._db[user_id])

    @classmethod
    def create(cls, name: str, email: str) -> Result[dict, list[str]]:
        """Create new user."""
        errors = []
        if not name or len(name) < 2:
            errors.append("Name must be at least 2 characters")
        if not email or "@" not in email:
            errors.append("Invalid email address")

        if errors:
            return Err(errors)

        new_id = max(cls._db.keys()) + 1
        user = {"id": new_id, "name": name, "email": email}
        cls._db[new_id] = user
        return Ok(user)


# ============================================================================
# 3. Handler Functions (What FastAPI route would use)
# ============================================================================


def get_user_handler(user_id: int) -> Result[dict, tuple[int, str]]:
    """Handler for GET /users/{user_id}"""
    result = User.get_by_id(user_id)

    # Convert Result to HTTP response tuple (status_code, response)
    match result:
        case Ok(user):
            return Ok(user)
        case Err("user_not_found"):
            return Err((404, "user_not_found"))
        case Err(_):
            return Err((500, "internal_error"))


def create_user_handler(name: str, email: str) -> Result[dict, tuple[int, str]]:
    """Handler for POST /users"""
    result = User.create(name, email)

    match result:
        case Ok(user):
            return Ok(user)
        case Err(errors):
            # Return 400 for validation errors
            return Err((400, "; ".join(errors)))
        case Err(_):
            return Err((500, "internal_error"))


def update_user_handler(
    user_id: int, name: str, email: str
) -> Result[dict, tuple[int, str]]:
    """Handler for PUT /users/{user_id}"""
    # Step 1: Check user exists
    user_result = User.get_by_id(user_id)

    if user_result.is_err():
        return Err((404, "user_not_found"))

    # Step 2: Validate new data
    validation_result = User.create(name, email)

    match validation_result:
        case Ok(_):
            # Step 3: Update user
            user = user_result.ok()
            user_copy = {"id": user["id"], "name": name, "email": email}
            User._db[user_id] = user_copy
            return Ok(user_copy)
        case Err(errors):
            return Err((400, "; ".join(errors)))


# ============================================================================
# 4. HTTP Response Builder (Middleware-like)
# ============================================================================


def result_to_http_response(result: Result[dict, tuple[int, str]]) -> dict:
    """Convert Result to HTTP JSON response."""
    match result:
        case Ok(data):
            return {"status": "success", "data": data}
        case Err((status_code, message)):
            return {"status": "error", "message": message, "code": status_code}


# ============================================================================
# 5. Example Usage (Simulating FastAPI)
# ============================================================================


def example_get_user():
    print("--- GET /users/1 ---")
    result = get_user_handler(1)
    response = result_to_http_response(result)
    print(f"Response: {response}")
    print()


def example_get_user_not_found():
    print("--- GET /users/999 ---")
    result = get_user_handler(999)
    response = result_to_http_response(result)
    print(f"Response: {response}")
    print()


def example_create_user_success():
    print("--- POST /users (valid) ---")
    result = create_user_handler("Charlie", "charlie@example.com")
    response = result_to_http_response(result)
    print(f"Response: {response}")
    print()


def example_create_user_validation_error():
    print("--- POST /users (invalid) ---")
    result = create_user_handler("", "bad-email")
    response = result_to_http_response(result)
    print(f"Response: {response}")
    print()


def example_update_user():
    print("--- PUT /users/1 (valid update) ---")
    result = update_user_handler(1, "Alice Updated", "alice.new@example.com")
    response = result_to_http_response(result)
    print(f"Response: {response}")
    print()


def example_update_user_not_found():
    print("--- PUT /users/999 ---")
    result = update_user_handler(999, "New Name", "new@example.com")
    response = result_to_http_response(result)
    print(f"Response: {response}")
    print()


# ============================================================================
# 6. FastAPI Pseudocode (What actual implementation would look like)
# ============================================================================

FASTAPI_PSEUDOCODE = '''
# Actual FastAPI implementation would look like:

from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID."""
    result = get_user_handler(user_id)

    match result:
        case Ok(user):
            return {"status": "success", "data": user}
        case Err((status_code, message)):
            raise HTTPException(status_code=status_code, detail=message)


@app.post("/users")
async def create_user(request: CreateUserRequest):
    """Create new user."""
    result = create_user_handler(request.name, request.email)

    match result:
        case Ok(user):
            return {"status": "success", "data": user}, 201
        case Err((status_code, message)):
            raise HTTPException(status_code=status_code, detail=message)


@app.put("/users/{user_id}")
async def update_user(user_id: int, request: UpdateUserRequest):
    """Update user."""
    result = update_user_handler(user_id, request.name, request.email)

    match result:
        case Ok(user):
            return {"status": "success", "data": user}
        case Err((status_code, message)):
            raise HTTPException(status_code=status_code, detail=message)
'''


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Integration with FastAPI")
    print("=" * 70)
    print()

    example_get_user()
    example_get_user_not_found()
    example_create_user_success()
    example_create_user_validation_error()
    example_update_user()
    example_update_user_not_found()

    print("=" * 70)
    print("FastAPI Integration Pattern:")
    print()
    print(FASTAPI_PSEUDOCODE)
    print()
    print("Benefits:")
    print("  ✓ Clean separation: business logic (Result) vs HTTP (FastAPI)")
    print("  ✓ Easy testing: handlers return Result, not HTTP responses")
    print("  ✓ Consistent error handling via match/case")
    print("  ✓ Type-safe: Result type enforces success/error handling")
    print("=" * 70)
