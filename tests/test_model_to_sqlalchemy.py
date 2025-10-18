"""Tests for Model to SQLAlchemy conversion."""

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from pysmith.db import (
    create_sqlalchemy_model_from_annotations,
    create_sqlalchemy_model_from_model,
)
from pysmith.models import Model


def get_fresh_base():
    """Create a fresh DeclarativeBase to avoid table conflicts."""

    class FreshBase(DeclarativeBase):
        pass

    return FreshBase


class TestCreateSQLAlchemyModelFromModel:
    """Test create_sqlalchemy_model_from_model function."""

    def test_basic_conversion(self):
        """Test basic Model to SQLAlchemy conversion."""
        Base = get_fresh_base()

        class User(Model):
            id: int
            name: str
            email: str

        UserSQLAlchemy = create_sqlalchemy_model_from_model(
            User, Base, table_name="users"
        )

        # Check basic attributes
        assert UserSQLAlchemy.__name__ == "User"
        assert UserSQLAlchemy.__tablename__ == "users"

        # Check fields exist
        assert "id" in UserSQLAlchemy.__annotations__
        assert "name" in UserSQLAlchemy.__annotations__
        assert "email" in UserSQLAlchemy.__annotations__

    def test_default_table_name(self):
        """Test default table name is lowercase class name."""
        Base = get_fresh_base()

        class Product(Model):
            id: int
            name: str

        ProductSQLAlchemy = create_sqlalchemy_model_from_model(Product, Base)
        assert ProductSQLAlchemy.__tablename__ == "product"

    def test_optional_fields(self):
        """Test Model with Optional fields."""
        Base = get_fresh_base()

        class Article(Model):
            id: int
            title: str
            content: Optional[str]

        ArticleSQLAlchemy = create_sqlalchemy_model_from_model(
            Article, Base, table_name="articles"
        )

        # Check that content field exists and is nullable
        content_col = ArticleSQLAlchemy.content  # type: ignore
        assert content_col.expression.nullable is True

    def test_primary_key_detection(self):
        """Test that 'id' field is detected as primary key."""
        Base = get_fresh_base()

        class Order(Model):
            id: int
            order_number: str

        OrderSQLAlchemy = create_sqlalchemy_model_from_model(
            Order, Base, table_name="orders"
        )

        id_col = OrderSQLAlchemy.id  # type: ignore
        assert id_col.expression.primary_key is True

    def test_custom_primary_key_field(self):
        """Test custom primary key field name."""
        Base = get_fresh_base()

        class Item(Model):
            item_id: int
            name: str

        ItemSQLAlchemy = create_sqlalchemy_model_from_model(
            Item, Base, table_name="items", primary_key_field="item_id"
        )

        item_id_col = ItemSQLAlchemy.item_id  # type: ignore
        assert item_id_col.expression.primary_key is True

    def test_custom_string_length(self):
        """Test custom string length configuration."""
        Base = get_fresh_base()

        class Post(Model):
            id: int
            content: str

        PostSQLAlchemy = create_sqlalchemy_model_from_model(
            Post, Base, table_name="posts", string_length=1000
        )

        content_col = PostSQLAlchemy.content  # type: ignore
        assert content_col.expression.type.length == 1000

    def test_model_to_sqlalchemy_class_method(self):
        """Test Model.to_sqlalchemy_model() convenience method."""
        Base = get_fresh_base()

        class Category(Model):
            id: int
            name: str
            description: Optional[str]

        CategorySQLAlchemy = Category.to_sqlalchemy_model(
            Base, table_name="categories"
        )

        assert CategorySQLAlchemy.__name__ == "Category"
        assert CategorySQLAlchemy.__tablename__ == "categories"
        assert "id" in CategorySQLAlchemy.__annotations__

    def test_database_operations(self):
        """Test that converted model works with actual database."""
        Base = get_fresh_base()

        class TestModel(Model):
            id: int
            value: str

        TestModelSQLAlchemy = create_sqlalchemy_model_from_model(
            TestModel, Base, table_name="test_models"
        )

        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        # Test CRUD operations
        with Session(engine) as session:
            # Create
            instance = TestModelSQLAlchemy(id=1, value="test")
            session.add(instance)
            session.commit()

            # Read
            result = session.query(TestModelSQLAlchemy).first()
            assert result is not None
            assert result.id == 1  # type: ignore
            assert result.value == "test"  # type: ignore

            # Update
            result.value = "updated"  # type: ignore
            session.commit()

            updated = session.query(TestModelSQLAlchemy).first()
            assert updated.value == "updated"  # type: ignore

            # Delete
            session.delete(updated)
            session.commit()

            count = session.query(TestModelSQLAlchemy).count()
            assert count == 0


class TestCreateSQLAlchemyModelFromAnnotations:
    """Test create_sqlalchemy_model_from_annotations function."""

    def test_basic_creation(self):
        """Test creating SQLAlchemy model from raw annotations."""
        Base = get_fresh_base()
        annotations = {"id": int, "name": str, "email": str}

        UserModel = create_sqlalchemy_model_from_annotations(
            "User", annotations, Base, table_name="users"
        )

        assert UserModel.__name__ == "User"
        assert UserModel.__tablename__ == "users"
        assert "id" in UserModel.__annotations__

    def test_with_optional_fields(self):
        """Test annotations with Optional types."""
        Base = get_fresh_base()
        annotations = {
            "id": int,
            "required_field": str,
            "optional_field": Optional[str],
        }

        TestModel = create_sqlalchemy_model_from_annotations(
            "TestModel", annotations, Base, table_name="test"
        )

        required_col = TestModel.required_field  # type: ignore
        assert required_col.expression.nullable is False

        optional_col = TestModel.optional_field  # type: ignore
        assert optional_col.expression.nullable is True

    def test_default_table_name(self):
        """Test default table name from class name."""
        Base = get_fresh_base()
        annotations = {"id": int, "value": str}

        ProductModel = create_sqlalchemy_model_from_annotations(
            "Product", annotations, Base
        )

        assert ProductModel.__tablename__ == "product"

    def test_various_types(self):
        """Test conversion of various Python types."""
        Base = get_fresh_base()
        annotations = {
            "id": int,
            "name": str,
            "price": float,
            "in_stock": bool,
            "description": Optional[str],
        }

        ItemModel = create_sqlalchemy_model_from_annotations(
            "Item", annotations, Base, table_name="items"
        )

        assert "id" in ItemModel.__annotations__
        assert "name" in ItemModel.__annotations__
        assert "price" in ItemModel.__annotations__
        assert "in_stock" in ItemModel.__annotations__
        assert "description" in ItemModel.__annotations__


class TestModelToSQLAlchemyWorkflow:
    """Test complete workflow from Model to SQLAlchemy."""

    def test_validation_then_persistence(self):
        """Test using Model for validation then SQLAlchemy for persistence."""
        Base = get_fresh_base()

        class User(Model):
            id: int
            username: str
            email: str
            age: Optional[int]

        # Step 1: Validate with Model
        user_data = {
            "id": 1,
            "username": "alice",
            "email": "alice@example.com",
            "age": 30,
        }
        validated_user = User(**user_data)
        assert validated_user.username == "alice"

        # Step 2: Convert to SQLAlchemy
        UserSQLAlchemy = User.to_sqlalchemy_model(Base, table_name="users")

        # Step 3: Persist to database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            db_user = UserSQLAlchemy(**user_data)
            session.add(db_user)
            session.commit()

            # Step 4: Query back
            saved_user = session.query(UserSQLAlchemy).first()
            assert saved_user.username == "alice"  # type: ignore
            assert saved_user.email == "alice@example.com"  # type: ignore

    def test_multiple_models(self):
        """Test converting multiple Model classes."""
        Base = get_fresh_base()

        class Author(Model):
            id: int
            name: str

        class Book(Model):
            id: int
            title: str
            author_id: int

        AuthorSQLAlchemy = Author.to_sqlalchemy_model(
            Base, table_name="authors"
        )
        BookSQLAlchemy = Book.to_sqlalchemy_model(Base, table_name="books")

        assert AuthorSQLAlchemy.__tablename__ == "authors"
        assert BookSQLAlchemy.__tablename__ == "books"

        # Test database operations
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            author = AuthorSQLAlchemy(id=1, name="Jane Doe")
            book = BookSQLAlchemy(id=1, title="Great Book", author_id=1)

            session.add(author)
            session.add(book)
            session.commit()

            saved_book = session.query(BookSQLAlchemy).first()
            assert saved_book.title == "Great Book"  # type: ignore


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_model_without_id_field(self):
        """Test Model without 'id' field."""
        Base = get_fresh_base()

        class CustomModel(Model):
            custom_key: int
            value: str

        CustomSQLAlchemy = create_sqlalchemy_model_from_model(
            CustomModel,
            Base,
            table_name="custom",
            primary_key_field="custom_key",
        )

        custom_key_col = CustomSQLAlchemy.custom_key  # type: ignore
        assert custom_key_col.expression.primary_key is True

    def test_model_with_only_id(self):
        """Test minimal Model with only id."""
        Base = get_fresh_base()

        class MinimalModel(Model):
            id: int

        MinimalSQLAlchemy = create_sqlalchemy_model_from_model(
            MinimalModel, Base, table_name="minimal"
        )

        assert "id" in MinimalSQLAlchemy.__annotations__
        assert len(MinimalSQLAlchemy.__annotations__) == 1

    def test_model_with_all_optional_fields(self):
        """Test Model with all optional fields except id."""
        Base = get_fresh_base()

        class OptionalModel(Model):
            id: int
            field1: Optional[str]
            field2: Optional[int]
            field3: Optional[bool]

        OptionalSQLAlchemy = create_sqlalchemy_model_from_model(
            OptionalModel, Base, table_name="optional"
        )

        # All fields except id should be nullable
        field1 = OptionalSQLAlchemy.field1  # type: ignore
        field2 = OptionalSQLAlchemy.field2  # type: ignore
        field3 = OptionalSQLAlchemy.field3  # type: ignore
        assert field1.expression.nullable is True
        assert field2.expression.nullable is True
        assert field3.expression.nullable is True
