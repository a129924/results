#!/usr/bin/env python3
"""
Integration with SQLAlchemy

Shows how to use Results with SQLAlchemy ORM for database operations.

Run: python with_sqlalchemy.py
Note: This is demonstration code. Install SQLAlchemy to run:
      pip install sqlalchemy

Demonstrates patterns for wrapping database queries with Result types.
"""

from results import Ok, Err, Result


# ============================================================================
# 1. Simulated Database Models and Operations
# ============================================================================

class User:
    """Simulated user model."""
    def __init__(self, id: int, name: str, email: str, active: bool = True):
        self.id = id
        self.name = name
        self.email = email
        self.active = active
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "active": self.active
        }


# Simulated database
_users_db = {
    1: User(1, "Alice", "alice@example.com", True),
    2: User(2, "Bob", "bob@example.com", True),
    3: User(3, "Charlie", "charlie@example.com", False),
}


# ============================================================================
# 2. Query Wrapping
# ============================================================================

def get_user_by_id(user_id: int) -> Result[User, str]:
    """Get user by ID with Result."""
    try:
        if user_id not in _users_db:
            return Err("user_not_found")
        
        user = _users_db[user_id]
        return Ok(user)
    except Exception as e:
        return Err(f"database_error: {str(e)}")


def get_active_users() -> Result[list[User], str]:
    """Get all active users."""
    try:
        users = [u for u in _users_db.values() if u.active]
        return Ok(users)
    except Exception as e:
        return Err(f"database_error: {str(e)}")


def search_users_by_email(pattern: str) -> Result[list[User], str]:
    """Search users by email pattern."""
    try:
        users = [
            u for u in _users_db.values()
            if pattern.lower() in u.email.lower()
        ]
        return Ok(users)
    except Exception as e:
        return Err(f"database_error: {str(e)}")


# ============================================================================
# 3. Basic Query Result Handling
# ============================================================================

def example_basic_query():
    print("--- Basic Query ---")
    
    result = get_user_by_id(1)
    
    match result:
        case Ok(user):
            print(f"✓ Found user: {user.name} ({user.email})")
        case Err(error):
            print(f"✗ Query failed: {error}")


def example_not_found():
    print("\n--- Not Found Handling ---")
    
    result = get_user_by_id(999)
    
    match result:
        case Ok(user):
            print(f"✓ Found user: {user.name}")
        case Err("user_not_found"):
            print(f"✓ User does not exist (handled gracefully)")
        case Err(error):
            print(f"✗ Unexpected error: {error}")


# ============================================================================
# 4. Transform Query Results
# ============================================================================

def example_transform():
    print("\n--- Transform Query Results ---")
    
    result = (
        get_user_by_id(1)
        .map(lambda user: user.to_dict())
        .map(lambda data: {**data, "processed": True})
    )
    
    match result:
        case Ok(data):
            print(f"✓ Transformed data: {data}")
        case Err(error):
            print(f"✗ Error: {error}")


# ============================================================================
# 5. Chain Multiple Queries
# ============================================================================

def get_user_email(user_id: int) -> Result[str, str]:
    """Chain queries: get user, extract email."""
    return (
        get_user_by_id(user_id)
        .map(lambda user: user.email)
    )


def example_chaining():
    print("\n--- Chaining Queries ---")
    
    result = get_user_email(2)
    
    match result:
        case Ok(email):
            print(f"✓ User email: {email}")
        case Err(error):
            print(f"✗ Error: {error}")


# ============================================================================
# 6. Bulk Operations
# ============================================================================

def example_bulk():
    print("\n--- Bulk Operations ---")
    
    # Fetch multiple users
    result = (
        get_active_users()
        .map(lambda users: len(users))
    )
    
    match result:
        case Ok(count):
            print(f"✓ Active users: {count}")
        case Err(error):
            print(f"✗ Error: {error}")


def example_filter_results():
    print("\n--- Filter Query Results ---")
    
    result = (
        search_users_by_email("alice")
        .map(lambda users: [u.name for u in users])
    )
    
    match result:
        case Ok(names):
            print(f"✓ Found users: {names}")
        case Err(error):
            print(f"✗ Error: {error}")


# ============================================================================
# 7. Write Operations (Simulated)
# ============================================================================

def create_user(name: str, email: str) -> Result[User, list[str]]:
    """Create new user with validation."""
    errors = []
    
    if not name or len(name) < 2:
        errors.append("Name must be at least 2 characters")
    
    if not email or "@" not in email:
        errors.append("Invalid email address")
    
    if errors:
        return Err(errors)
    
    try:
        # Check email uniqueness
        for user in _users_db.values():
            if user.email.lower() == email.lower():
                return Err(["Email already exists"])
        
        # Create user
        new_id = max(_users_db.keys()) + 1
        new_user = User(new_id, name, email, True)
        _users_db[new_id] = new_user
        
        return Ok(new_user)
    except Exception as e:
        return Err([f"database_error: {str(e)}"])


def example_create():
    print("\n--- Create Operation ---")
    
    result = create_user("Diana", "diana@example.com")
    
    match result:
        case Ok(user):
            print(f"✓ User created: {user.name} (ID: {user.id})")
        case Err(errors):
            print(f"✗ Creation failed:")
            for error in errors:
                print(f"  - {error}")


# ============================================================================
# 8. Transaction-like Operations
# ============================================================================

def example_transaction():
    print("\n--- Transaction-like Operation ---")
    
    def transfer_contact(from_id: int, to_id: int) -> Result[dict, str]:
        """Simulate transaction: get user, update status."""
        return (
            get_user_by_id(from_id)
            .and_then(lambda user:
                # Verify recipient exists
                get_user_by_id(to_id)
                .map(lambda _: user)  # Return original user
            )
            .map(lambda user: {
                "transferred_from": user.name,
                "status": "success"
            })
        )
    
    result = transfer_contact(1, 2)
    
    match result:
        case Ok(data):
            print(f"✓ {data['transferred_from']}'s data transferred")
        case Err(error):
            print(f"✗ Transfer failed: {error}")


# ============================================================================
# 9. Error Recovery and Fallbacks
# ============================================================================

def example_fallback():
    print("\n--- Fallback Strategy ---")
    
    def get_user_or_default(user_id: int) -> Result[dict, str]:
        """Get user or use default."""
        return (
            get_user_by_id(user_id)
            .or_else(lambda error:
                Ok(User(-1, "Guest", "guest@example.com", True))
            )
            .map(lambda u: u.to_dict())
        )
    
    result = get_user_or_default(999)
    
    match result:
        case Ok(user):
            print(f"✓ User: {user['name']} (default fallback)")
        case Err(error):
            print(f"✗ Error: {error}")


# ============================================================================
# 10. Real-World: API Handler Pattern
# ============================================================================

def example_api_pattern():
    print("\n--- API Handler Pattern ---")
    
    def get_user_api(user_id: int) -> dict:
        """HTTP API handler using Result."""
        result = get_user_by_id(user_id)
        
        match result:
            case Ok(user):
                return {
                    "status": "success",
                    "data": user.to_dict()
                }
            case Err("user_not_found"):
                return {
                    "status": "not_found",
                    "message": "User does not exist",
                    "code": 404
                }
            case Err(error) if "database_error" in error:
                return {
                    "status": "error",
                    "message": "Database connection failed",
                    "code": 500
                }
            case Err(error):
                return {
                    "status": "error",
                    "message": error,
                    "code": 400
                }
    
    response = get_user_api(1)
    print(f"✓ API Response: {response['status']}")
    
    response = get_user_api(999)
    print(f"✓ API Response (not found): {response['status']} (code: {response.get('code')})")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("Integration with SQLAlchemy")
    print("="*70)
    print()
    
    example_basic_query()
    example_not_found()
    example_transform()
    example_chaining()
    example_bulk()
    example_filter_results()
    example_create()
    example_transaction()
    example_fallback()
    example_api_pattern()
    
    print("\n" + "="*70)
    print("SQLAlchemy Integration Pattern:")
    print("  1. Wrap session.query() in Result")
    print("  2. Return Err on not found / exceptions")
    print("  3. Chain queries with and_then()")
    print("  4. Transform with map()")
    print("  5. Use pattern matching for HTTP status mapping")
    print("="*70)
