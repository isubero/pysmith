"""
Tests for required (non-Optional) relationship validation.

These tests verify that Pysmith properly validates required relationships
and provides clear error messages when they are None.
"""

from typing import Annotated, Optional

import pytest

from pysmith.db import close_session, configure
from pysmith.models import Model, Relation


class TestRequiredRelationshipValidation:
    """Tests for required (non-Optional) relationship validation."""

    def setup_method(self) -> None:
        """Set up test database."""
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        configure("sqlite:///:memory:", Base)

    def teardown_method(self) -> None:
        """Clean up after each test."""
        Model._sqlalchemy_model_cache.clear()
        Model._lazy_loaders_setup.clear()
        close_session()

    def test_required_relationship_with_none_raises_error(self) -> None:
        """Test that saving with None for a required relationship raises ValueError."""

        class Product(Model):
            id: int
            name: str

        class OrderItem(Model):
            id: int
            quantity: int
            # Required relationship (no Optional!)
            product: Annotated["Product", Relation()] = None  # type: ignore

        # Create product
        product = Product(id=1, name="Widget").save()

        # Create order item with product - should work
        item1 = OrderItem(id=1, quantity=5, product=product).save()
        assert item1.product_id == 1

        # Create order item with None - should fail with clear message
        item2 = OrderItem(id=2, quantity=3, product=None)

        with pytest.raises(ValueError) as exc_info:
            item2.save()

        assert "Required relationship 'product' cannot be None" in str(
            exc_info.value
        )
        assert "Product instance" in str(exc_info.value)

    def test_optional_relationship_with_none_works(self) -> None:
        """Test that saving with None for an optional relationship works."""

        class Category(Model):
            id: int
            name: str

        class Product(Model):
            id: int
            name: str
            # Optional relationship
            category: Annotated[Optional["Category"], Relation()] = None

        # Create product without category - should work
        product = Product(id=1, name="Widget", category=None).save()
        assert product.category_id is None

        # Create category and product with category - also works
        category = Category(id=1, name="Electronics").save()
        product2 = Product(id=2, name="Gadget", category=category).save()
        assert product2.category_id == 1

    def test_required_relationship_error_message_shows_type(self) -> None:
        """Test that error message includes the target model type."""

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            # Required relationship
            author: Annotated["Author", Relation()] = None  # type: ignore

        book = Book(id=1, title="Test", author=None)

        with pytest.raises(ValueError) as exc_info:
            book.save()

        error_msg = str(exc_info.value)
        assert "author" in error_msg
        assert "Author" in error_msg
        assert "instance" in error_msg

    def test_update_required_relationship_to_none_raises_error(self) -> None:
        """Test that updating a required relationship to None raises ValueError."""

        class Department(Model):
            id: int
            name: str

        class Employee(Model):
            id: int
            name: str
            # Required relationship
            department: Annotated["Department", Relation()] = None  # type: ignore

        # Create with department - works
        dept = Department(id=1, name="Engineering").save()
        employee = Employee(id=1, name="Alice", department=dept).save()
        assert employee.department_id == 1

        # Update to None - should fail
        employee.department = None
        employee.department_id = None  # This would be set by __init__ normally

        with pytest.raises(ValueError) as exc_info:
            employee.save()

        assert "Required relationship 'department' cannot be None" in str(
            exc_info.value
        )

    def test_multiple_required_relationships_all_validated(self) -> None:
        """Test that all required relationships are validated."""

        class Author(Model):
            id: int
            name: str

        class Publisher(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            # Both required!
            author: Annotated["Author", Relation()] = None  # type: ignore
            publisher: Annotated["Publisher", Relation()] = None  # type: ignore

        # Missing both
        book = Book(id=1, title="Test", author=None, publisher=None)

        with pytest.raises(ValueError) as exc_info:
            book.save()

        # Should fail on first missing relationship
        assert "Required relationship" in str(exc_info.value)
        assert "cannot be None" in str(exc_info.value)

    def test_mixed_required_and_optional_relationships(self) -> None:
        """Test model with both required and optional relationships."""

        class Author(Model):
            id: int
            name: str

        class Publisher(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            # Required
            author: Annotated["Author", Relation()] = None  # type: ignore
            # Optional
            publisher: Annotated[Optional["Publisher"], Relation()] = None

        author = Author(id=1, name="Jane").save()

        # Can omit publisher (optional), but not author (required)
        book1 = Book(id=1, title="Book 1", author=None, publisher=None)

        with pytest.raises(ValueError) as exc_info:
            book1.save()

        assert "author" in str(exc_info.value).lower()

        # With author, should work
        book2 = Book(
            id=2, title="Book 2", author=author, publisher=None
        ).save()
        assert book2.author_id == 1
        assert book2.publisher_id is None

    def test_required_relationship_with_unsaved_object_works(self) -> None:
        """Test that a required relationship with an object that has an ID works."""

        class Company(Model):
            id: int
            name: str

        class Employee(Model):
            id: int
            name: str
            # Required
            company: Annotated["Company", Relation()] = None  # type: ignore

        # Create company object (has ID, even if not saved yet)
        company = Company(id=1, name="TechCorp")

        # Create employee with company object - should extract ID and work
        employee = Employee(id=1, name="Bob", company=company)
        assert employee.company_id == 1

        # Save company first, then employee
        company.save()
        employee.save()

        assert employee.company_id == 1

    def test_one_to_many_relationship_not_validated(self) -> None:
        """Test that one-to-many relationships (lists) are not validated as required."""

        class Author(Model):
            id: int
            name: str
            # One-to-many - not validated as "required"
            books: Annotated[list["Book"], Relation()] = []

        class Book(Model):
            id: int
            title: str
            author: Annotated[Optional["Author"], Relation()] = None

        # Can create author with empty books list
        author = Author(id=1, name="Jane", books=[]).save()
        assert author.id == 1

        # books=[] doesn't create a foreign key to validate
        # Only many-to-one (single object) relationships are validated
