from abc import ABC
from typing import (
    Annotated,
    Any,
    Optional,
    Self,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import BaseModel, Field, create_model

T = TypeVar("T", bound="Model")


class Relation:
    """
    Metadata class for declaring relationships between models.

    Use with Annotated to declare type-safe relationships that automatically
    generate foreign keys in the database.

    Args:
        back_populates: Name of the reverse relationship field (optional)
        lazy: Whether to lazy-load the relationship (default: True)
        cascade: SQLAlchemy cascade options (e.g., "all, delete-orphan")

    Example:
        ```python
        from typing import Annotated, Optional
        from pysmith.models import Model, Relation

        class Author(Model):
            id: int
            name: str
            books: Annotated[list["Book"], Relation(back_populates="author")]

        class Book(Model):
            id: int
            title: str
            # Foreign key auto-generated as 'author_id'
            author: Annotated[Optional["Author"], Relation(back_populates="books")]
        ```
    """

    def __init__(
        self,
        back_populates: Optional[str] = None,
        lazy: bool = True,
        cascade: Optional[str] = None,
    ):
        self.back_populates = back_populates
        self.lazy = lazy
        self.cascade = cascade

    def __repr__(self) -> str:
        return f"Relation(back_populates={self.back_populates!r})"


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
        # Extract relationships and handle Model objects
        relationships = self.__class__._extract_relationships()

        # Separate relationship objects from regular data
        relationship_objects = {}
        pydantic_data = {}

        for key, value in kwargs.items():
            if key in relationships:
                # This is a relationship field - store the object
                relationship_objects[key] = value
                # Don't pass to Pydantic (it doesn't know about these fields)
            else:
                pydantic_data[key] = value

        # Get or create the Pydantic model class (cached at class level)
        PydanticModelCls = self._get_or_create_pydantic_model()
        self.pydantic_instance = PydanticModelCls(**pydantic_data)

        # Set validated fields
        for key, value in self.pydantic_instance.model_dump().items():
            setattr(self, key, value)

        # Set relationship objects and auto-extract FKs
        foreign_keys = self.__class__._generate_foreign_keys(relationships)
        for rel_field, rel_object in relationship_objects.items():
            # Set the relationship field
            setattr(self, rel_field, rel_object)

            # Auto-extract FK if the relationship is a Model instance
            fk_field = f"{rel_field}_id"
            if isinstance(rel_object, Model) and fk_field in foreign_keys:
                # Extract the ID from the related model
                if hasattr(rel_object, "id"):
                    setattr(self, fk_field, getattr(rel_object, "id"))
            elif rel_object is None and fk_field in foreign_keys:
                # Relationship is None, set FK to None
                setattr(self, fk_field, None)

        self._db_instance = None

    @classmethod
    def _extract_relationships(cls) -> dict[str, Relation]:
        """
        Extract relationship metadata from Annotated type hints.

        Returns:
            Dictionary mapping field names to Relation metadata
        """
        relationships = {}

        for field_name, type_hint in cls.__annotations__.items():
            # Skip internal fields
            if field_name in {
                "pydantic_instance",
                "_pydantic_model_cache",
                "_sqlalchemy_model_cache",
                "_db_instance",
            }:
                continue

            # Check if this is an Annotated type
            origin = get_origin(type_hint)
            # Use == instead of is for typing special forms (mypy prefers this)
            if origin == Annotated:  # type: ignore[comparison-overlap]
                args = get_args(type_hint)
                # Check metadata for Relation
                for metadata in args[1:]:
                    if isinstance(metadata, Relation):
                        relationships[field_name] = metadata
                        break

        return relationships

    @classmethod
    def _unwrap_type(cls, type_hint: Any) -> Any:
        """
        Unwrap a type hint to get the actual model type.

        Handles: Annotated, Optional, list, etc.
        Returns the core type (e.g., Author from Annotated[Optional[Author], ...])
        """
        # Unwrap Annotated
        if get_origin(type_hint) is Annotated:
            type_hint = get_args(type_hint)[0]

        # Unwrap Optional (Union[X, None])
        origin = get_origin(type_hint)
        if origin is type(None) or (
            hasattr(type_hint, "__origin__")
            and type_hint.__origin__ is type(None)
        ):
            return type_hint

        # Check for Union (Optional is Union[X, None])
        import typing

        if hasattr(typing, "Union") and origin is typing.Union:
            args = get_args(type_hint)
            # Get the non-None type
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                type_hint = non_none_types[0]

        # Unwrap list
        if get_origin(type_hint) is list:
            type_hint = get_args(type_hint)[0]

        return type_hint

    @classmethod
    def _generate_foreign_keys(
        cls, relationships: dict[str, Relation]
    ) -> dict[str, Any]:
        """
        Auto-generate foreign key fields for relationships.

        For each relationship field (except one-to-many), generates a
        corresponding {field_name}_id field.

        Args:
            relationships: Dictionary of relationship field names to Relation metadata

        Returns:
            Dictionary of foreign key field names to their types

        Example:
            author: Annotated[Optional[Author], Relation()]
            → Generates: author_id: Optional[int]

            books: Annotated[list[Book], Relation()]
            → Skipped (one-to-many, FK is on the other side)
        """
        foreign_keys: dict[str, Any] = {}

        for field_name, relation_meta in relationships.items():
            # Get the type hint
            type_hint = cls.__annotations__[field_name]

            # Check if it's a list relationship BEFORE unwrapping
            # Unwrap Annotated first
            check_type = type_hint
            origin = get_origin(check_type)
            if origin == Annotated:  # type: ignore[comparison-overlap]
                check_type = get_args(check_type)[0]

            # Check for Optional/Union
            import typing

            check_origin = get_origin(check_type)
            if check_origin == typing.Union:  # type: ignore[comparison-overlap]
                args = get_args(check_type)
                non_none_types = [arg for arg in args if arg is not type(None)]
                if non_none_types:
                    check_type = non_none_types[0]

            # Now check if it's a list
            list_origin = get_origin(check_type)
            if list_origin == list:  # type: ignore[comparison-overlap]
                # One-to-many relationship, skip FK generation
                continue

            # Generate FK field name: {field}_id
            fk_name = f"{field_name}_id"

            # Determine if FK is optional based on original type
            is_optional = False
            unwrapped_for_optional = type_hint
            unwrap_origin = get_origin(unwrapped_for_optional)
            if unwrap_origin == Annotated:  # type: ignore[comparison-overlap]
                unwrapped_for_optional = get_args(unwrapped_for_optional)[0]

            final_origin = get_origin(unwrapped_for_optional)
            if final_origin == typing.Union:  # type: ignore[comparison-overlap]
                args = get_args(unwrapped_for_optional)
                if type(None) in args:
                    is_optional = True

            # Add FK field
            foreign_keys[fk_name] = Optional[int] if is_optional else int

        return foreign_keys

    @classmethod
    def _get_pydantic_fields(cls) -> dict[str, Any]:
        """
        Extract pydantic fields from class annotations.

        Skips relationship fields (Annotated with Relation) as they will be
        handled separately during persistence.
        """
        relationships = cls._extract_relationships()
        pydantic_fields = {}

        for key, expected_type in cls.__annotations__.items():
            # Skip internal fields
            if key in {
                "pydantic_instance",
                "_pydantic_model_cache",
                "_sqlalchemy_model_cache",
                "_db_instance",
            }:
                continue

            # Skip relationship fields - they're not part of validation
            if key in relationships:
                continue

            pydantic_fields[key] = (expected_type, Field(...))

        return pydantic_fields

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
        1. For Annotated relationship fields: extract FK from current object state
        2. Include auto-generated FK fields (author_id, category_id, etc.)
        3. If field value is a Model instance with an id, extract just the id
        4. If field value is a Model instance without an id, raise an error
           (the nested model must be saved first)
        5. Otherwise, use the value as-is

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
                author: Annotated[Optional["Author"], Relation()] = None

            # New ORM-style usage:
            author = Author(id=1, name="Jane").save()
            book = Book(id=1, title="My Book", author=author)
            book.save()  # Auto-extracts author.id to author_id
            ```
        """
        data = {}
        relationships = self.__class__._extract_relationships()
        foreign_keys = self.__class__._generate_foreign_keys(relationships)

        # First pass: Update FKs from current relationship object state
        for rel_field in relationships.keys():
            if hasattr(self, rel_field):
                rel_object = getattr(self, rel_field)
                fk_field = f"{rel_field}_id"

                if fk_field in foreign_keys:
                    if isinstance(rel_object, Model):
                        # Extract ID from the related model
                        if hasattr(rel_object, "id"):
                            setattr(self, fk_field, getattr(rel_object, "id"))
                    elif rel_object is None:
                        # Relationship is None, set FK to None
                        setattr(self, fk_field, None)

        # Second pass: Build data dict for SQLAlchemy
        for key, value in self.__dict__.items():
            if key.startswith("_") or key == "pydantic_instance":
                continue

            # Skip relationship fields (they're not DB columns)
            if key in relationships:
                continue

            # Include FK fields (they may have been updated above)
            if key in foreign_keys:
                data[key] = value
                continue

            # Check if value is a Model instance (nested relation)
            # This handles old-style manual nesting (backward compatible)
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
            # Get relationships to skip them when reading from DB
            relationships = cls._extract_relationships()
            foreign_keys = cls._generate_foreign_keys(relationships)

            # Convert SQLAlchemy instance to Model instance
            # Only read actual DB columns (skip relationship fields)
            data = {
                key: getattr(db_instance, key)
                for key in cls.__annotations__.keys()
                if key
                not in {
                    "pydantic_instance",
                    "_pydantic_model_cache",
                    "_sqlalchemy_model_cache",
                    "_db_instance",
                }
                and key not in relationships  # Skip relationship fields
            }

            instance = cls(**data)
            instance._db_instance = db_instance

            # Manually set FK attributes on the instance
            for fk_name in foreign_keys.keys():
                if hasattr(db_instance, fk_name):
                    setattr(instance, fk_name, getattr(db_instance, fk_name))

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

        # Get relationships to skip them when reading from DB
        relationships = cls._extract_relationships()
        foreign_keys = cls._generate_foreign_keys(relationships)

        instances: list[T] = []
        for db_instance in db_instances:
            # Only read actual DB columns (skip relationship fields)
            data = {
                key: getattr(db_instance, key)
                for key in cls.__annotations__.keys()
                if key
                not in {
                    "pydantic_instance",
                    "_pydantic_model_cache",
                    "_sqlalchemy_model_cache",
                    "_db_instance",
                }
                and key not in relationships  # Skip relationship fields
            }

            instance = cls(**data)
            instance._db_instance = db_instance

            # Manually set FK attributes on the instance
            for fk_name in foreign_keys.keys():
                if hasattr(db_instance, fk_name):
                    setattr(instance, fk_name, getattr(db_instance, fk_name))

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

        Automatically includes foreign key fields for relationships declared
        with Annotated[Type, Relation()].

        Args:
            base: The SQLAlchemy DeclarativeBase to inherit from
            table_name: Optional table name (defaults to lowercase class name)
            primary_key_field: Name of the primary key field (default: "id")
            string_length: Default length for String columns (default: 255)

        Returns:
            A SQLAlchemy model class

        Example:
            ```python
            from typing import Annotated, Optional
            from sqlalchemy.orm import DeclarativeBase
            from pysmith.models import Model, Relation

            class Base(DeclarativeBase):
                pass

            class Author(Model):
                id: int
                name: str
                books: Annotated[list["Book"], Relation(back_populates="author")]

            class Book(Model):
                id: int
                title: str
                # Foreign key 'author_id' auto-generated!
                author: Annotated[Optional["Author"], Relation(back_populates="books")]

            # Convert to SQLAlchemy
            AuthorSQLAlchemy = Author.to_sqlalchemy_model(Base)
            BookSQLAlchemy = Book.to_sqlalchemy_model(Base)
            ```
        """
        from pysmith.db.adapters import create_sqlalchemy_model_from_model

        # Get relationships and generate foreign keys
        relationships = cls._extract_relationships()
        foreign_keys = cls._generate_foreign_keys(relationships)

        # Create new annotations: regular fields + FKs, BUT exclude relationship fields
        enhanced_annotations = {}
        for key, value in cls.__annotations__.items():
            # Skip internal fields
            if key in {
                "pydantic_instance",
                "_pydantic_model_cache",
                "_sqlalchemy_model_cache",
                "_db_instance",
            }:
                continue
            # Skip relationship fields (they're not actual DB columns)
            if key in relationships:
                continue
            # Include regular fields
            enhanced_annotations[key] = value

        # Add generated foreign keys
        for fk_name, fk_type in foreign_keys.items():
            enhanced_annotations[fk_name] = fk_type

        # Temporarily replace annotations for SQLAlchemy generation
        original_annotations = cls.__annotations__
        cls.__annotations__ = enhanced_annotations

        try:
            sqlalchemy_model = create_sqlalchemy_model_from_model(
                cls,
                base=base,
                table_name=table_name,
                primary_key_field=primary_key_field,
                string_length=string_length,
            )
        finally:
            # Restore original annotations
            cls.__annotations__ = original_annotations

        return sqlalchemy_model
