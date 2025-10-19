"""
Database adapters for pysmith.

Provides bidirectional conversion between:
- SQLAlchemy models ⟷ Pydantic models
- pysmith.Model ⟷ SQLAlchemy models
- Session management for Django-style ORM
"""

from pysmith.db.adapters import (
    RelationshipStrategy,
    create_pydantic_model_from_sqlalchemy,
    create_sqlalchemy_model_from_annotations,
    create_sqlalchemy_model_from_model,
    extract_type_from_mapped,
    python_type_to_sqlalchemy_column,
    sqlalchemy_to_pydantic_fields,
)
from pysmith.db.session import (
    SessionContext,
    SessionNotConfiguredError,
    close_session,
    configure,
    create_tables,
    drop_tables,
    get_base,
    get_engine,
    get_session,
    set_session,
)

__all__ = [
    # Enums
    "RelationshipStrategy",
    # SQLAlchemy → Pydantic
    "extract_type_from_mapped",
    "sqlalchemy_to_pydantic_fields",
    "create_pydantic_model_from_sqlalchemy",
    # Model/Pydantic → SQLAlchemy
    "python_type_to_sqlalchemy_column",
    "create_sqlalchemy_model_from_model",
    "create_sqlalchemy_model_from_annotations",
    # Session Management
    "configure",
    "get_session",
    "set_session",
    "close_session",
    "get_engine",
    "get_base",
    "SessionContext",
    "SessionNotConfiguredError",
    "create_tables",
    "drop_tables",
]
