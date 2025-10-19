from abc import ABC
from typing import Any, Optional, Self, TypeVar

from pydantic import BaseModel, Field, create_model

T = TypeVar("T", bound="Model")


class Model(ABC):
    """
    Base class for all models with validation and persistence.

    Provides Django-style ORM capabilities with Pydantic validation.

    Example:
        ```python
        from pysmith.models import Model
        from pysmith.db.session import configure

        # Configure database (once at app startup)
        configure('sqlite:///app.db', Base)

        # Define model
        class User(Model):
            id: int
            username: str
            email: str

        # Use it
        user = User(id=1, username="alice", email="alice@example.com")
        user.save()  # Persists to database
        ```
    """

    _pydantic_model_cache: dict[type, type[BaseModel]] = {}
    _sqlalchemy_model_cache: dict[type, type] = {}
    pydantic_instance: BaseModel
    _db_instance: Optional[Any] = None  # SQLAlchemy instance

    def __init__(self, **kwargs: Any) -> None:
        # Get or create the Pydantic model class (cached at class level)
        PydanticModelCls = self._get_or_create_pydantic_model()
        self.pydantic_instance = PydanticModelCls(**kwargs)

        for key, value in self.pydantic_instance.model_dump().items():
            setattr(self, key, value)

        self._db_instance = None

    @classmethod
    def _get_pydantic_fields(cls) -> dict[str, Any]:
        """Extract pydantic fields from class annotations."""
        return {
            key: (expected_type, Field(...))
            for key, expected_type in cls.__annotations__.items()
            if key
            not in {
                "pydantic_instance",
                "_pydantic_model_cache",
            }  # Skip internal fields
        }

    @classmethod
    def _get_or_create_pydantic_model(cls) -> type[BaseModel]:
        """Get the cached Pydantic model or create it if not cached."""
        if cls not in Model._pydantic_model_cache:
            model_name = cls.__name__
            fields = cls._get_pydantic_fields()
            pydantic_model = create_model(model_name, **fields)
            Model._pydantic_model_cache[cls] = pydantic_model
        return Model._pydantic_model_cache[cls]

    @classmethod
    def get_pydantic_model_cls(cls) -> type[BaseModel]:
        """Get the Pydantic model class for this Model class."""
        return cls._get_or_create_pydantic_model()

    @classmethod
    def validate_json(cls: type[T], json_data: str) -> T:
        """Validate and create an instance from JSON data."""
        pyd_model = cls._get_or_create_pydantic_model()
        pyd_instance = pyd_model.model_validate_json(json_data)
        return cls(**pyd_instance.model_dump())

    # ========================================================================
    # Persistence Methods (Django-style ORM)
    # ========================================================================

    @classmethod
    def _get_or_create_sqlalchemy_model(cls) -> type:
        """Get the cached SQLAlchemy model or create it if not cached."""
        if cls not in Model._sqlalchemy_model_cache:
            from pysmith.db.session import get_base, get_engine

            base = get_base()
            sqlalchemy_model = cls.to_sqlalchemy_model(
                base=base, table_name=cls.__name__.lower()
            )
            Model._sqlalchemy_model_cache[cls] = sqlalchemy_model

            # Create the table if it doesn't exist
            engine = get_engine()
            base.metadata.create_all(
                engine, tables=[sqlalchemy_model.__table__]
            )

        return Model._sqlalchemy_model_cache[cls]

    def _extract_nested_models(self) -> dict[str, Any]:
        """
        Extract nested Model instances and convert them to IDs.

        Strategy for nested relations:
        1. If field value is a Model instance with an id, extract just the id
        2. If field value is a Model instance without an id, raise an error
           (the nested model must be saved first)
        3. Otherwise, use the value as-is

        Returns:
            Dictionary of field values ready for SQLAlchemy persistence

        Example:
            ```python
            class Author(Model):
                id: int
                name: str

            class Book(Model):
                id: int
                title: str
                author_id: int  # Use foreign key, not nested object

            # Correct usage:
            author = Author(id=1, name="Jane")
            author.save()

            book = Book(id=1, title="My Book", author_id=author.id)
            book.save()
            ```
        """
        data = {}
        for key, value in self.__dict__.items():
            if key.startswith("_") or key == "pydantic_instance":
                continue

            # Check if value is a Model instance (nested relation)
            if isinstance(value, Model):
                # Try to extract the ID
                if hasattr(value, "id") and getattr(value, "id") is not None:
                    # Replace nested model with its ID
                    # Assume the foreign key field is named {field_name}_id
                    data[f"{key}_id"] = getattr(value, "id")
                else:
                    raise ValueError(
                        f"Nested model '{key}' must be saved first "
                        "(must have an id)"
                    )
            else:
                data[key] = value

        return data

    def save(self) -> Self:
        """
        Save this model instance to the database.

        Uses the configured session to persist the model.

        Returns:
            Self for method chaining

        Raises:
            SessionNotConfiguredError: If database is not configured

        Example:
            ```python
            user = User(id=1, username="alice", email="alice@example.com")
            user.save()  # Persists to database

            # Method chaining
            user = User(**data).save()
            ```

        Note on Relations:
            Currently only supports foreign key IDs, not full nested objects.
            Save nested models first, then use their IDs:

            ```python
            author = Author(id=1, name="Jane").save()
            book = Book(id=1, title="Book", author_id=author.id).save()
            ```
        """
        from pysmith.db.session import get_session

        session = get_session()
        SQLAlchemyModel = self._get_or_create_sqlalchemy_model()

        # Extract data, handling nested models
        data = self._extract_nested_models()

        try:
            # Create or update SQLAlchemy instance
            if self._db_instance is None:
                self._db_instance = SQLAlchemyModel(**data)
                session.add(self._db_instance)
            else:
                # Update existing instance
                for key, value in data.items():
                    setattr(self._db_instance, key, value)

            session.commit()
        except Exception:
            session.rollback()
            raise

        return self

    def delete(self) -> None:
        """
        Delete this model instance from the database.

        Raises:
            ValueError: If instance was never saved
            SessionNotConfiguredError: If database is not configured

        Example:
            ```python
            user = User.find_by_id(1)
            user.delete()  # Removes from database
            ```
        """
        from pysmith.db.session import get_session

        if self._db_instance is None:
            raise ValueError(
                "Cannot delete unsaved instance. Use save() before delete()."
            )

        session = get_session()
        try:
            session.delete(self._db_instance)
            session.commit()
            self._db_instance = None
        except Exception:
            session.rollback()
            raise

    @classmethod
    def find_by_id(cls: type[T], id_value: Any) -> Optional[T]:
        """
        Find a model instance by its ID.

        Args:
            id_value: The ID value to search for

        Returns:
            Model instance if found, None otherwise

        Example:
            ```python
            user = User.find_by_id(1)
            if user:
                print(user.username)
            ```
        """
        from pysmith.db.session import get_session

        session = get_session()
        SQLAlchemyModel = cls._get_or_create_sqlalchemy_model()

        db_instance: Any = session.get(SQLAlchemyModel, id_value)
        if db_instance is not None:
            # Convert SQLAlchemy instance to Model instance
            data = {
                key: getattr(db_instance, key)
                for key in cls.__annotations__.keys()
                if key not in {"pydantic_instance", "_pydantic_model_cache"}
            }

            instance = cls(**data)
            instance._db_instance = db_instance
            return instance

        return None

    @classmethod
    def find_all(cls: type[T]) -> list[T]:
        """
        Find all instances of this model.

        Returns:
            List of all model instances

        Example:
            ```python
            all_users = User.find_all()
            for user in all_users:
                print(user.username)
            ```

        Warning:
            This loads all records into memory. Use with caution
            on large tables.
        """
        from pysmith.db.session import get_session

        session = get_session()
        SQLAlchemyModel = cls._get_or_create_sqlalchemy_model()

        db_instances: list[Any] = session.query(SQLAlchemyModel).all()

        instances: list[T] = []
        for db_instance in db_instances:
            data = {
                key: getattr(db_instance, key)
                for key in cls.__annotations__.keys()
                if key not in {"pydantic_instance", "_pydantic_model_cache"}
            }
            instance = cls(**data)
            instance._db_instance = db_instance
            instances.append(instance)

        return instances

    @classmethod
    def to_sqlalchemy_model(
        cls,
        base: Any,
        table_name: str | None = None,
        primary_key_field: str = "id",
        string_length: int = 255,
    ) -> Any:
        """
        Convert this Model class to a SQLAlchemy model.

        Args:
            base: The SQLAlchemy DeclarativeBase to inherit from
            table_name: Optional table name (defaults to lowercase class name)
            primary_key_field: Name of the primary key field (default: "id")
            string_length: Default length for String columns (default: 255)

        Returns:
            A SQLAlchemy model class

        Example:
            ```python
            from sqlalchemy.orm import DeclarativeBase
            from pysmith.models import Model

            class Base(DeclarativeBase):
                pass

            class User(Model):
                id: int
                name: str
                email: str

            # Convert to SQLAlchemy
            UserSQLAlchemy = User.to_sqlalchemy_model(Base, table_name="users")
            ```
        """
        from pysmith.db.adapters import create_sqlalchemy_model_from_model

        return create_sqlalchemy_model_from_model(
            cls,
            base=base,
            table_name=table_name,
            primary_key_field=primary_key_field,
            string_length=string_length,
        )
