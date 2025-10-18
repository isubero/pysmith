"""
SQLAlchemy ⟷ Pydantic model conversion utilities.

SQLAlchemy → Pydantic:
- extract_type_from_mapped(): Extract inner type from Mapped[T]
- sqlalchemy_to_pydantic_fields(): Convert SQLAlchemy fields to
    Pydantic-compatible (type, Field) tuples
- create_pydantic_model_from_sqlalchemy(): Create a complete
    Pydantic model from SQLAlchemy model

Pydantic/Model → SQLAlchemy:
- create_sqlalchemy_model_from_model(): Convert pysmith.Model to
    SQLAlchemy model
- python_type_to_sqlalchemy_column(): Convert Python types to
    SQLAlchemy Mapped columns

Relationship handling strategies:
- 'exclude': Remove relationship fields (default)
- 'optional': Include as Optional[Any] (for flexibility)
- 'id_only': Replace with the foreign key ID field
"""

from enum import Enum
from typing import Any, ForwardRef, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel, Field, create_model
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class RelationshipStrategy(str, Enum):
    """Strategy for handling SQLAlchemy relationships."""

    EXCLUDE = "exclude"  # Skip relationship fields
    OPTIONAL = "optional"  # Include as Optional[Any]
    ID_ONLY = "id_only"  # Use foreign key IDs only


# ============================================================================
# SQLAlchemy → Pydantic Conversion
# ============================================================================


def extract_sqlalchemy_fields(
    sqlalchemy_model: type[DeclarativeBase],
) -> dict[str, Any]:
    """Extract fields from a SQLAlchemy model."""
    return {
        field_name: field_type
        for field_name, field_type in sqlalchemy_model.__annotations__.items()
    }


def extract_type_from_mapped(mapped_type: Any) -> Any:
    """
    Extract the inner type from a SQLAlchemy Mapped annotation.

    Example:
        Mapped[int] -> int
        Mapped[Optional[str]] -> Optional[str]
        Mapped[List[Address]] -> List[Address]
    """
    # Check if it's a Mapped type by checking if it has __origin__
    origin = get_origin(mapped_type)

    # If it's a Mapped type, extract the first type argument
    if origin is Mapped:
        args = get_args(mapped_type)
        if args:
            return args[0]

    # If it's not a Mapped type, return as-is
    return mapped_type


def is_relationship_field(
    sqlalchemy_model: type[DeclarativeBase], field_name: str
) -> bool:
    """
    Check if a field is a SQLAlchemy relationship (not a column).

    Args:
        sqlalchemy_model: The SQLAlchemy model class
        field_name: The name of the field to check

    Returns:
        True if the field is a relationship, False otherwise
    """
    from sqlalchemy.orm import RelationshipProperty

    # Check if the field is defined with relationship() by
    # inspecting the class dict. This avoids triggering
    # SQLAlchemy's mapper configuration
    if field_name in sqlalchemy_model.__dict__:
        field_value = sqlalchemy_model.__dict__[field_name]
        # Check if it's a RelationshipProperty directly
        if isinstance(field_value, RelationshipProperty):
            return True

    # Alternative: Check if we can safely access the descriptor
    # without triggering config
    try:
        if hasattr(sqlalchemy_model, field_name):
            field_value = getattr(sqlalchemy_model, field_name)
            if hasattr(field_value, "property"):
                return isinstance(field_value.property, RelationshipProperty)
    except Exception:
        # If accessing the field triggers an error, we can't
        # determine safely. Let's check the annotation type to
        # see if it's a relationship. Relationships typically
        # use List or forward references
        pass

    return False


def has_forward_ref(type_hint: Any) -> bool:
    """
    Check if a type hint contains a ForwardRef.

    Args:
        type_hint: The type hint to check

    Returns:
        True if the type contains a ForwardRef
    """
    # Check if it's directly a ForwardRef
    if isinstance(type_hint, ForwardRef):
        return True

    # Check if it's a generic type with ForwardRef args
    args = get_args(type_hint)
    if args:
        return any(has_forward_ref(arg) for arg in args)

    return False


def sqlalchemy_to_pydantic_fields(
    sqlalchemy_model: type[DeclarativeBase],
    relationship_strategy: RelationshipStrategy = RelationshipStrategy.EXCLUDE,
) -> dict[str, tuple[Any, Any]]:
    """
    Convert SQLAlchemy model annotations to Pydantic field
    definitions.

    Args:
        sqlalchemy_model: The SQLAlchemy model class
        relationship_strategy: How to handle relationship fields
            - EXCLUDE: Skip relationship fields (default)
            - OPTIONAL: Include as Optional[Any]
            - ID_ONLY: Use foreign key fields only

    Returns:
        Dictionary mapping field names to (type, Field) tuples
        for use with create_model
    """
    pydantic_fields = {}

    for field_name, field_type in sqlalchemy_model.__annotations__.items():
        is_rel = is_relationship_field(sqlalchemy_model, field_name)

        # Handle relationships based on strategy
        if is_rel:
            if relationship_strategy == RelationshipStrategy.EXCLUDE:
                continue
            elif relationship_strategy == RelationshipStrategy.OPTIONAL:
                # Include as Optional[Any] to avoid ForwardRef issues
                pydantic_fields[field_name] = (
                    Optional[Any],
                    Field(default=None),
                )
                continue
            elif relationship_strategy == RelationshipStrategy.ID_ONLY:
                # Skip - ID fields are already in the model
                continue

        # Extract the inner type from Mapped[...]
        inner_type = extract_type_from_mapped(field_type)

        # Check if the type contains ForwardRef
        if has_forward_ref(inner_type):
            # Can't use types with ForwardRef directly in Pydantic
            # Convert to Optional[Any] as a fallback
            inner_type = Optional[Any]

        # Add to pydantic fields with Field(...)
        pydantic_fields[field_name] = (inner_type, Field(...))

    return pydantic_fields


def create_pydantic_model_from_sqlalchemy(
    sqlalchemy_model: type[DeclarativeBase],
    model_name: str | None = None,
    relationship_strategy: RelationshipStrategy = RelationshipStrategy.EXCLUDE,
) -> type[BaseModel]:
    """
    Dynamically create a Pydantic model from a SQLAlchemy model.

    Args:
        sqlalchemy_model: The SQLAlchemy model class
        model_name: Optional name for the Pydantic model
            (defaults to SQLAlchemy model name)
        relationship_strategy: How to handle relationship fields
            - EXCLUDE: Skip relationship fields (default)
            - OPTIONAL: Include as Optional[Any]
            - ID_ONLY: Use foreign key fields only

    Returns:
        A Pydantic model class
    """
    if model_name is None:
        model_name = sqlalchemy_model.__name__

    fields = sqlalchemy_to_pydantic_fields(
        sqlalchemy_model, relationship_strategy
    )
    return create_model(model_name, **fields)  # type: ignore


# ============================================================================
# Model/Pydantic → SQLAlchemy Conversion
# ============================================================================


def python_type_to_sqlalchemy_column(
    field_name: str,
    field_type: Any,
    primary_key: bool = False,
    string_length: int = 255,
) -> Mapped[Any]:
    """
    Convert a Python type annotation to a SQLAlchemy Mapped column.

    Args:
        field_name: Name of the field
        field_type: Python type annotation (int, str, Optional[str], etc.)
        primary_key: Whether this field is a primary key
        string_length: Default length for String columns

    Returns:
        A SQLAlchemy Mapped column definition
    """
    # Check if it's an Optional type
    origin = get_origin(field_type)
    is_optional = False

    if origin is Union:
        args = get_args(field_type)
        # Optional[X] is Union[X, None]
        if type(None) in args:
            is_optional = True
            # Get the non-None type
            field_type = next(arg for arg in args if arg is not type(None))

    # Handle primary key (typically int)
    if primary_key:
        if field_type is int:
            return mapped_column(Integer, primary_key=True)
        else:
            return mapped_column(primary_key=True)

    # Map Python types to SQLAlchemy types
    if field_type is int:
        if is_optional:
            return mapped_column(Integer, nullable=True)
        return mapped_column(Integer)

    elif field_type is str:
        if is_optional:
            return mapped_column(String(string_length), nullable=True)
        return mapped_column(String(string_length))

    elif field_type is float:
        if is_optional:
            return mapped_column(nullable=True)
        return mapped_column()

    elif field_type is bool:
        if is_optional:
            return mapped_column(nullable=True)
        return mapped_column()

    # Default: try to infer
    if is_optional:
        return mapped_column(nullable=True)
    return mapped_column()


def create_sqlalchemy_model_from_model(
    model_cls: Type[Any],
    base: Type[DeclarativeBase],
    table_name: str | None = None,
    primary_key_field: str = "id",
    string_length: int = 255,
) -> Type[DeclarativeBase]:
    """
    Create a SQLAlchemy model from a pysmith.Model class.

    Args:
        model_cls: The Model class to convert
        base: The SQLAlchemy DeclarativeBase to inherit from
        table_name: Optional table name (defaults to lowercase class name)
        primary_key_field: Name of the primary key field (default: "id")
        string_length: Default length for String columns (default: 255)

    Returns:
        A SQLAlchemy model class

    Example:
        ```python
        from pysmith.models import Model
        from pysmith.db.adapters import create_sqlalchemy_model_from_model

        class User(Model):
            id: int
            name: str
            email: str
            age: Optional[int]

        # Convert to SQLAlchemy
        UserSQLAlchemy = create_sqlalchemy_model_from_model(
            User, Base, table_name="users"
        )
        ```
    """
    if table_name is None:
        table_name = model_cls.__name__.lower()

    # Get annotations from the Model class
    annotations = {
        key: value
        for key, value in model_cls.__annotations__.items()
        if key not in {"pydantic_instance", "_pydantic_model_cache"}
    }

    # Build the class attributes
    class_attrs: dict[str, Any] = {
        "__tablename__": table_name,
        "__annotations__": {},
    }

    for field_name, field_type in annotations.items():
        is_primary_key = field_name == primary_key_field

        # Create the Mapped annotation
        class_attrs["__annotations__"][field_name] = Mapped[
            field_type  # type: ignore
        ]

        # Create the column
        class_attrs[field_name] = python_type_to_sqlalchemy_column(
            field_name,
            field_type,
            primary_key=is_primary_key,
            string_length=string_length,
        )

    # Dynamically create the SQLAlchemy model class
    sqlalchemy_model = type(model_cls.__name__, (base,), class_attrs)

    return sqlalchemy_model


def create_sqlalchemy_model_from_annotations(
    class_name: str,
    annotations: dict[str, Any],
    base: Type[DeclarativeBase],
    table_name: str | None = None,
    primary_key_field: str = "id",
    string_length: int = 255,
) -> Type[DeclarativeBase]:
    """
    Create a SQLAlchemy model from a dictionary of type annotations.

    Args:
        class_name: Name for the generated class
        annotations: Dictionary mapping field names to type annotations
        base: The SQLAlchemy DeclarativeBase to inherit from
        table_name: Optional table name (defaults to lowercase class name)
        primary_key_field: Name of the primary key field (default: "id")
        string_length: Default length for String columns (default: 255)

    Returns:
        A SQLAlchemy model class

    Example:
        ```python
        annotations = {
            'id': int,
            'name': str,
            'email': str,
            'age': Optional[int]
        }

        UserModel = create_sqlalchemy_model_from_annotations(
            'User', annotations, Base, table_name='users'
        )
        ```
    """
    if table_name is None:
        table_name = class_name.lower()

    # Build the class attributes
    class_attrs: dict[str, Any] = {
        "__tablename__": table_name,
        "__annotations__": {},
    }

    for field_name, field_type in annotations.items():
        is_primary_key = field_name == primary_key_field

        # Create the Mapped annotation
        class_attrs["__annotations__"][field_name] = Mapped[
            field_type  # type: ignore
        ]

        # Create the column
        class_attrs[field_name] = python_type_to_sqlalchemy_column(
            field_name,
            field_type,
            primary_key=is_primary_key,
            string_length=string_length,
        )

    # Dynamically create the SQLAlchemy model class
    sqlalchemy_model = type(class_name, (base,), class_attrs)

    return sqlalchemy_model
