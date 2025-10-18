# SQLAlchemy to Pydantic: Relationship Handling Strategies

## Overview

When converting SQLAlchemy models to Pydantic models, relationships can be tricky because they reference other models (often creating circular dependencies). This guide explains the three strategies available.

## Strategies

### 1. EXCLUDE (Default) ⭐ Recommended for DTOs

**What it does:** Completely removes relationship fields from the Pydantic model.

**Use when:**

- Creating Data Transfer Objects (DTOs) for API responses
- You want clean, simple models without nested objects
- The API client doesn't need relationship data
- You're using a separate endpoint for related data

**Example:**

```python
from pysmith.db.adapters import (
    create_pydantic_model_from_sqlalchemy,
    RelationshipStrategy
)

# SQLAlchemy model with relationship
class User(Base):
    id: Mapped[int]
    name: Mapped[str]
    addresses: Mapped[List["Address"]] = relationship(...)

# Create Pydantic model without relationships
UserDTO = create_pydantic_model_from_sqlalchemy(
    User,
    relationship_strategy=RelationshipStrategy.EXCLUDE
)

# Result: Only id and name fields
user = UserDTO(id=1, name="Alice")
```

### 2. OPTIONAL - Include relationships as Optional[Any]

**What it does:** Includes relationship fields but types them as `Optional[Any]`.

**Use when:**

- You want flexibility to optionally include relationship data
- You're manually populating relationships after querying
- You need the field to exist but don't care about type safety
- Working with lazy-loaded relationships

**Example:**

```python
UserDTO = create_pydantic_model_from_sqlalchemy(
    User,
    relationship_strategy=RelationshipStrategy.OPTIONAL
)

# Can create without relationship
user1 = UserDTO(id=1, name="Alice", addresses=None)

# Can also pass relationship data if needed
user2 = UserDTO(id=2, name="Bob", addresses=[{"id": 1, "email": "..."}])
```

### 3. ID_ONLY - Use foreign key IDs only

**What it does:** Skips relationships but keeps foreign key ID fields.

**Use when:**

- Building REST APIs that use resource IDs
- Creating models for POST/PUT requests
- You want clients to reference related resources by ID
- Following REST best practices

**Example:**

```python
# Address model has a user_id foreign key
class Address(Base):
    id: Mapped[int]
    email: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship(...)

AddressDTO = create_pydantic_model_from_sqlalchemy(
    Address,
    relationship_strategy=RelationshipStrategy.ID_ONLY
)

# Result: Has id, email, and user_id (but not user relationship)
address = AddressDTO(id=1, email="alice@example.com", user_id=1)
```

## Comparison Table

| Strategy     | Relationships?   | Foreign Keys? | Use Case                    |
| ------------ | ---------------- | ------------- | --------------------------- |
| **EXCLUDE**  | ❌ Removed       | ✅ Included   | Clean DTOs, API responses   |
| **OPTIONAL** | ✅ Optional[Any] | ✅ Included   | Flexible, optionally nested |
| **ID_ONLY**  | ❌ Removed       | ✅ Included   | RESTful APIs with IDs       |

## Real-World Example: Building a REST API

```python
from pysmith.db.adapters import (
    create_pydantic_model_from_sqlalchemy,
    RelationshipStrategy
)

# For GET responses - exclude relationships
UserResponse = create_pydantic_model_from_sqlalchemy(
    User,
    model_name="UserResponse",
    relationship_strategy=RelationshipStrategy.EXCLUDE
)

# For POST/PUT requests - use IDs for relationships
AddressCreate = create_pydantic_model_from_sqlalchemy(
    Address,
    model_name="AddressCreate",
    relationship_strategy=RelationshipStrategy.ID_ONLY
)

# FastAPI endpoint example
@app.post("/addresses")
def create_address(address: AddressCreate):
    # address.user_id is available as an integer
    # No nested user object, just the ID
    return {...}
```

## Advanced: Nested Models

If you need **true nested Pydantic models** (e.g., User with full Address objects), you'll need to:

1. Create Pydantic models for both
2. Manually define the relationship in Pydantic
3. Handle circular dependencies with `model_rebuild()`

```python
# Create base models first (no relationships)
AddressPydantic = create_pydantic_model_from_sqlalchemy(
    Address,
    relationship_strategy=RelationshipStrategy.ID_ONLY
)

# Then manually create a User model with nested Address
from pydantic import create_model

UserWithAddresses = create_model(
    "UserWithAddresses",
    id=(int, ...),
    name=(str, ...),
    addresses=(List[AddressPydantic], [])
)
```

## Key Takeaways

- **Default (EXCLUDE)** works for 80% of use cases
- **ID_ONLY** is perfect for RESTful APIs
- **OPTIONAL** provides flexibility when needed
- For complex nested structures, consider using libraries like `sqlmodel` or manually defining nested Pydantic models
