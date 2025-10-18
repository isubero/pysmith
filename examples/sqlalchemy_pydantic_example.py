"""
Example: Converting SQLAlchemy models to Pydantic models

This example demonstrates how to use the SQLAlchemy to Pydantic
conversion utilities with different relationship strategies.
"""

from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pysmith.db.adapters import (
    RelationshipStrategy,
    create_pydantic_model_from_sqlalchemy,
    sqlalchemy_to_pydantic_fields,
)


# Define SQLAlchemy models
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))
    age: Mapped[Optional[int]]

    # Relationship to addresses
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    street: Mapped[str]
    city: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationship back to user
    user: Mapped["User"] = relationship(back_populates="addresses")


# Example 1: Create DTOs without relationships (most common)
print("=" * 70)
print("Example 1: DTO Pattern (EXCLUDE strategy)")
print("=" * 70)

UserDTO = create_pydantic_model_from_sqlalchemy(
    User,
    model_name="UserDTO",
    relationship_strategy=RelationshipStrategy.EXCLUDE,
)

AddressDTO = create_pydantic_model_from_sqlalchemy(
    Address,
    model_name="AddressDTO",
    relationship_strategy=RelationshipStrategy.EXCLUDE,
)

print(f"UserDTO fields: {list(UserDTO.model_fields.keys())}")
print(f"AddressDTO fields: {list(AddressDTO.model_fields.keys())}")

user_dto = UserDTO(id=1, name="Alice", email="alice@example.com", age=30)
print(f"\nUser: {user_dto.model_dump_json()}")

address_dto = AddressDTO(id=1, street="123 Main St", city="Boston", user_id=1)
print(f"Address: {address_dto.model_dump_json()}")
print()


# Example 2: REST API pattern with ID references
print("=" * 70)
print("Example 2: REST API Pattern (ID_ONLY strategy)")
print("=" * 70)

# For creating new addresses via API
AddressCreate = create_pydantic_model_from_sqlalchemy(
    Address,
    model_name="AddressCreate",
    relationship_strategy=RelationshipStrategy.ID_ONLY,
)

print(f"AddressCreate fields: {list(AddressCreate.model_fields.keys())}")

# Simulating an API request
new_address = AddressCreate(
    id=2, street="456 Oak Ave", city="New York", user_id=1
)
print(f"\nNew address payload: {new_address.model_dump_json()}")
print()


# Example 3: Flexible pattern with optional relationships
print("=" * 70)
print("Example 3: Flexible Pattern (OPTIONAL strategy)")
print("=" * 70)

UserFlexible = create_pydantic_model_from_sqlalchemy(
    User,
    model_name="UserFlexible",
    relationship_strategy=RelationshipStrategy.OPTIONAL,
)

print(f"UserFlexible fields: {list(UserFlexible.model_fields.keys())}")

# Can omit relationships
user1 = UserFlexible(
    id=1, name="Bob", email="bob@example.com", age=25, addresses=None
)
print(f"\nUser without addresses: {user1.model_dump_json()}")

# Can include relationships if needed
user2 = UserFlexible(
    id=2,
    name="Carol",
    email="carol@example.com",
    age=28,
    addresses=[{"street": "789 Pine St", "city": "Seattle"}],
)
print(f"User with addresses: {user2.model_dump_json()}")
print()


# Example 4: Manual inspection of field types
print("=" * 70)
print("Example 4: Inspecting Extracted Field Types")
print("=" * 70)

fields = sqlalchemy_to_pydantic_fields(
    User, relationship_strategy=RelationshipStrategy.EXCLUDE
)

print("User model field types:")
for field_name, (field_type, field_info) in fields.items():
    print(f"  {field_name}: {field_type}")
print()


# Example 5: Building a FastAPI-style response model
print("=" * 70)
print("Example 5: FastAPI Response Pattern")
print("=" * 70)


# Simulate a FastAPI endpoint response
class UserResponse(BaseModel):
    """Response model for GET /users/{id}"""

    id: int
    name: str
    email: str
    age: Optional[int]
    # No relationships - keep it simple


class AddressResponse(BaseModel):
    """Response model for GET /addresses/{id}"""

    id: int
    street: str
    city: str
    user_id: int  # Reference to user by ID
    # No user object - just the ID


class UserWithAddresses(BaseModel):
    """Response model for GET /users/{id}?include=addresses"""

    id: int
    name: str
    email: str
    age: Optional[int]
    addresses: List[AddressResponse]  # Nested, but without user backref


# You can generate these automatically:
UserResponseGenerated = create_pydantic_model_from_sqlalchemy(User)
AddressResponseGenerated = create_pydantic_model_from_sqlalchemy(Address)

print(
    f"UserResponse fields: {list(UserResponseGenerated.model_fields.keys())}"
)
print(
    f"AddressResponse fields: "
    f"{list(AddressResponseGenerated.model_fields.keys())}"
)

print()
print("=" * 70)
print("All examples completed successfully! ✓")
print("=" * 70)
