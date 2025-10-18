"""
Database adapters for pysmith.

Provides bidirectional conversion between:
- SQLAlchemy models ⟷ Pydantic models
- pysmith.Model ⟷ SQLAlchemy models
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
]
