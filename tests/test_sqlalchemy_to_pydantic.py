"""Tests for SQLAlchemy to Pydantic conversion."""

from typing import Any, List, Optional

import pytest
from pydantic import ValidationError
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from pysmith.db import (
    RelationshipStrategy,
    create_pydantic_model_from_sqlalchemy,
    extract_type_from_mapped,
    sqlalchemy_to_pydantic_fields,
)


class Base(DeclarativeBase):
    pass


class User(Base):
    """SQLAlchemy User model for testing."""

    __tablename__ = "test_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str]
    age: Mapped[Optional[int]]
    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Address(Base):
    """SQLAlchemy Address model for testing."""

    __tablename__ = "test_addresses"
    id: Mapped[int] = mapped_column(primary_key=True)
    street: Mapped[str]
    city: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("test_users.id"))
    user: Mapped["User"] = relationship(back_populates="addresses")


class TestExtractTypeFromMapped:
    """Test extract_type_from_mapped function."""

    def test_extract_int_type(self):
        """Test extracting int from Mapped[int]."""
        mapped_type = Mapped[int]
        result = extract_type_from_mapped(mapped_type)
        assert result is int

    def test_extract_str_type(self):
        """Test extracting str from Mapped[str]."""
        mapped_type = Mapped[str]
        result = extract_type_from_mapped(mapped_type)
        assert result is str

    def test_extract_optional_type(self):
        """Test extracting Optional[int] from Mapped[Optional[int]]."""
        mapped_type = Mapped[Optional[int]]
        result = extract_type_from_mapped(mapped_type)
        # Result should be Union[int, None] which is Optional[int]
        assert result == Optional[int]

    def test_non_mapped_type_returns_as_is(self):
        """Test that non-Mapped types are returned unchanged."""
        result = extract_type_from_mapped(int)
        assert result is int


class TestSQLAlchemyToPydanticFields:
    """Test sqlalchemy_to_pydantic_fields function."""

    def test_exclude_relationships_by_default(self):
        """Test that relationships are excluded by default."""
        fields = sqlalchemy_to_pydantic_fields(User)

        # Should have column fields but not relationships
        assert "id" in fields
        assert "name" in fields
        assert "email" in fields
        assert "age" in fields
        assert "addresses" not in fields

    def test_optional_relationship_strategy(self):
        """Test OPTIONAL strategy includes relationships."""
        fields = sqlalchemy_to_pydantic_fields(
            User, relationship_strategy=RelationshipStrategy.OPTIONAL
        )

        # Should have all fields including relationships
        assert "id" in fields
        assert "addresses" in fields
        # Relationship should be Optional[Any]
        field_type, _ = fields["addresses"]
        assert field_type == Optional[Any]

    def test_id_only_strategy(self):
        """Test ID_ONLY strategy excludes relationships."""
        fields = sqlalchemy_to_pydantic_fields(
            Address, relationship_strategy=RelationshipStrategy.ID_ONLY
        )

        # Should have columns including foreign key
        assert "id" in fields
        assert "street" in fields
        assert "city" in fields
        assert "user_id" in fields
        # Should not have relationship
        assert "user" not in fields

    def test_field_types_are_correct(self):
        """Test that extracted field types are correct."""
        fields = sqlalchemy_to_pydantic_fields(User)

        id_type, _ = fields["id"]
        assert id_type is int

        name_type, _ = fields["name"]
        assert name_type is str

        age_type, _ = fields["age"]
        assert age_type == Optional[int]


class TestCreatePydanticModelFromSQLAlchemy:
    """Test create_pydantic_model_from_sqlalchemy function."""

    def test_basic_conversion(self):
        """Test basic SQLAlchemy to Pydantic conversion."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(User)

        # Check model name
        assert UserPydantic.__name__ == "User"

        # Check fields exist
        assert "id" in UserPydantic.model_fields
        assert "name" in UserPydantic.model_fields
        assert "email" in UserPydantic.model_fields
        assert "age" in UserPydantic.model_fields

        # Relationships should be excluded by default
        assert "addresses" not in UserPydantic.model_fields

    def test_custom_model_name(self):
        """Test conversion with custom model name."""
        UserDTO = create_pydantic_model_from_sqlalchemy(
            User, model_name="UserDTO"
        )
        assert UserDTO.__name__ == "UserDTO"

    def test_validation_works(self):
        """Test that Pydantic validation works on converted model."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(User)

        # Valid data
        user = UserPydantic(
            id=1, name="Alice", email="alice@example.com", age=30
        )
        assert user.id == 1
        assert user.name == "Alice"
        assert user.email == "alice@example.com"
        assert user.age == 30

    def test_validation_fails_on_wrong_types(self):
        """Test that validation fails with wrong types."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(User)

        with pytest.raises(ValidationError):
            UserPydantic(
                id="not_an_int",
                name="Alice",
                email="alice@example.com",
                age=30,
            )

    def test_optional_fields_work(self):
        """Test that Optional fields work correctly."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(User)

        # Age is optional, should work without it
        user = UserPydantic(
            id=1, name="Bob", email="bob@example.com", age=None
        )
        assert user.age is None

    def test_exclude_strategy(self):
        """Test EXCLUDE relationship strategy."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(
            User, relationship_strategy=RelationshipStrategy.EXCLUDE
        )
        assert "addresses" not in UserPydantic.model_fields

    def test_optional_strategy(self):
        """Test OPTIONAL relationship strategy."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(
            User, relationship_strategy=RelationshipStrategy.OPTIONAL
        )
        assert "addresses" in UserPydantic.model_fields

        # Should accept None for relationship
        user = UserPydantic(
            id=1,
            name="Alice",
            email="alice@example.com",
            age=30,
            addresses=None,
        )
        assert user.addresses is None

    def test_id_only_strategy(self):
        """Test ID_ONLY relationship strategy."""
        AddressPydantic = create_pydantic_model_from_sqlalchemy(
            Address, relationship_strategy=RelationshipStrategy.ID_ONLY
        )

        # Should have user_id but not user relationship
        assert "user_id" in AddressPydantic.model_fields
        assert "user" not in AddressPydantic.model_fields

        # Should be able to create instance
        address = AddressPydantic(
            id=1, street="123 Main St", city="Boston", user_id=1
        )
        assert address.user_id == 1

    def test_json_serialization(self):
        """Test that converted models can serialize to JSON."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(User)

        user = UserPydantic(
            id=1, name="Alice", email="alice@example.com", age=30
        )
        json_str = user.model_dump_json()

        assert "Alice" in json_str
        assert "alice@example.com" in json_str

    def test_json_deserialization(self):
        """Test that converted models can deserialize from JSON."""
        UserPydantic = create_pydantic_model_from_sqlalchemy(User)

        json_data = (
            '{"id": 1, "name": "Alice", '
            '"email": "alice@example.com", "age": 30}'
        )
        user = UserPydantic.model_validate_json(json_data)

        assert user.id == 1
        assert user.name == "Alice"


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_model_with_no_relationships(self):
        """Test conversion of model without relationships."""

        class SimpleModel(Base):
            __tablename__ = "simple"
            id: Mapped[int] = mapped_column(primary_key=True)
            value: Mapped[str]

        SimplePydantic = create_pydantic_model_from_sqlalchemy(SimpleModel)
        assert "id" in SimplePydantic.model_fields
        assert "value" in SimplePydantic.model_fields

    def test_model_with_all_optional_fields(self):
        """Test model with all optional fields."""

        class OptionalModel(Base):
            __tablename__ = "optional"
            id: Mapped[int] = mapped_column(primary_key=True)
            field1: Mapped[Optional[str]]
            field2: Mapped[Optional[int]]

        OptionalPydantic = create_pydantic_model_from_sqlalchemy(OptionalModel)

        # Should work with all None
        instance = OptionalPydantic(id=1, field1=None, field2=None)
        assert instance.field1 is None
        assert instance.field2 is None
