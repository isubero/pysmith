# Model ⟷ SQLAlchemy Conversion Guide

## Overview

Pysmith provides **bidirectional conversion** between `pysmith.Model` classes and SQLAlchemy models, allowing you to:

- Use `Model` for validation and type safety
- Use SQLAlchemy for database persistence
- Convert seamlessly between them

## Table of Contents

- [Model → SQLAlchemy](#model--sqlalchemy)
- [SQLAlchemy → Pydantic](#sqlalchemy--pydantic)
- [Complete Workflow](#complete-workflow)
- [API Reference](#api-reference)

---

## Model → SQLAlchemy

Convert your `pysmith.Model` classes to SQLAlchemy models for database operations.

### Method 1: Using the Class Method (Recommended)

```python
from sqlalchemy.orm import DeclarativeBase
from pysmith.models import Model

class Base(DeclarativeBase):
    pass

class User(Model):
    id: int
    name: str
    email: str
    age: Optional[int]

# Convert directly on the Model class
UserSQLAlchemy = User.to_sqlalchemy_model(
    Base,
    table_name="users",
    primary_key_field="id",
    string_length=255
)
```

### Method 2: Using the Function

```python
from pysmith.db import create_sqlalchemy_model_from_model

UserSQLAlchemy = create_sqlalchemy_model_from_model(
    User,
    base=Base,
    table_name="users"
)
```

### Method 3: From Raw Annotations

```python
from pysmith.db import create_sqlalchemy_model_from_annotations

annotations = {
    'id': int,
    'name': str,
    'email': str,
    'age': Optional[int]
}

UserSQLAlchemy = create_sqlalchemy_model_from_annotations(
    'User',
    annotations,
    Base,
    table_name='users'
)
```

### Type Mapping

| Python Type     | SQLAlchemy Type | Optional?        |
| --------------- | --------------- | ---------------- |
| `int`           | `Integer`       | `nullable=False` |
| `str`           | `String(255)`   | `nullable=False` |
| `float`         | `Float`         | `nullable=False` |
| `bool`          | `Boolean`       | `nullable=False` |
| `Optional[int]` | `Integer`       | `nullable=True`  |
| `Optional[str]` | `String(255)`   | `nullable=True`  |

**Note:** Primary key field (default: `"id"`) automatically gets `primary_key=True`

---

## SQLAlchemy → Pydantic

Convert SQLAlchemy models to Pydantic models for API responses and validation.

### Basic Usage

```python
from pysmith.db import create_pydantic_model_from_sqlalchemy

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

# Convert to Pydantic
UserDTO = create_pydantic_model_from_sqlalchemy(User)
```

### Handling Relationships

SQLAlchemy relationships need special handling. Choose a strategy:

#### Strategy 1: EXCLUDE (Default)

Remove relationship fields completely. Best for DTOs.

```python
from pysmith.db import RelationshipStrategy

UserDTO = create_pydantic_model_from_sqlalchemy(
    User,
    relationship_strategy=RelationshipStrategy.EXCLUDE
)
# Result: Only column fields (no relationships)
```

#### Strategy 2: OPTIONAL

Include relationships as `Optional[Any]`. Good for flexibility.

```python
UserDTO = create_pydantic_model_from_sqlalchemy(
    User,
    relationship_strategy=RelationshipStrategy.OPTIONAL
)
# Result: Relationships included as Optional[Any]
```

#### Strategy 3: ID_ONLY

Skip relationships but keep foreign key IDs. Best for RESTful APIs.

```python
AddressDTO = create_pydantic_model_from_sqlalchemy(
    Address,
    relationship_strategy=RelationshipStrategy.ID_ONLY
)
# Result: Includes user_id but not user relationship
```

See [RELATIONSHIP_STRATEGIES.md](./RELATIONSHIP_STRATEGIES.md) for detailed information.

---

## Complete Workflow

### Pattern 1: API Validation + Database Persistence

```python
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Session
from pysmith.models import Model

# 1. Define your Model for validation
class User(Model):
    id: int
    username: str
    email: str
    age: Optional[int]

# 2. Validate incoming data
user_data = {"id": 1, "username": "alice", "email": "alice@example.com", "age": 30}
validated_user = User(**user_data)  # Pydantic validation happens here

# 3. Convert to SQLAlchemy for persistence
class Base(DeclarativeBase):
    pass

UserSQLAlchemy = User.to_sqlalchemy_model(Base, table_name="users")

# 4. Save to database
with Session(engine) as session:
    db_user = UserSQLAlchemy(**user_data)
    session.add(db_user)
    session.commit()
```

### Pattern 2: Database → API Response

```python
from pysmith.db import create_pydantic_model_from_sqlalchemy

# 1. Query from database using SQLAlchemy
with Session(engine) as session:
    db_user = session.query(UserSQLAlchemy).first()

# 2. Convert SQLAlchemy model to Pydantic for API response
UserResponse = create_pydantic_model_from_sqlalchemy(UserSQLAlchemy)

# 3. Create response model
response = UserResponse(
    id=db_user.id,
    username=db_user.username,
    email=db_user.email,
    age=db_user.age
)

# 4. Return as JSON
return response.model_dump_json()
```

### Pattern 3: Full Bidirectional Conversion

```python
# Define once
class Product(Model):
    id: int
    name: str
    price: float

# → SQLAlchemy (for DB operations)
ProductSQLAlchemy = Product.to_sqlalchemy_model(Base, table_name="products")

# ← Pydantic (for API responses)
ProductDTO = create_pydantic_model_from_sqlalchemy(ProductSQLAlchemy)

# Use both in your application
def create_product(data: dict):
    # Validate with Model
    validated = Product(**data)

    # Save with SQLAlchemy
    db_product = ProductSQLAlchemy(**data)
    session.add(db_product)
    session.commit()

    # Return as DTO
    return ProductDTO(**db_product.__dict__)
```

---

## API Reference

### Model → SQLAlchemy Functions

#### `Model.to_sqlalchemy_model()`

Class method on `pysmith.Model`.

```python
@classmethod
def to_sqlalchemy_model(
    cls,
    base: Type[DeclarativeBase],
    table_name: str | None = None,
    primary_key_field: str = "id",
    string_length: int = 255,
) -> Type[DeclarativeBase]:
    ...
```

**Parameters:**

- `base`: SQLAlchemy DeclarativeBase to inherit from
- `table_name`: Table name (default: lowercase class name)
- `primary_key_field`: Name of primary key field (default: `"id"`)
- `string_length`: Default String column length (default: 255)

#### `create_sqlalchemy_model_from_model()`

Standalone function.

```python
from pysmith.db import create_sqlalchemy_model_from_model

create_sqlalchemy_model_from_model(
    model_cls: Type[Any],
    base: Type[DeclarativeBase],
    table_name: str | None = None,
    primary_key_field: str = "id",
    string_length: int = 255,
) -> Type[DeclarativeBase]
```

#### `create_sqlalchemy_model_from_annotations()`

Create from raw type annotations.

```python
from pysmith.db import create_sqlalchemy_model_from_annotations

create_sqlalchemy_model_from_annotations(
    class_name: str,
    annotations: dict[str, Any],
    base: Type[DeclarativeBase],
    table_name: str | None = None,
    primary_key_field: str = "id",
    string_length: int = 255,
) -> Type[DeclarativeBase]
```

### SQLAlchemy → Pydantic Functions

#### `create_pydantic_model_from_sqlalchemy()`

```python
from pysmith.db import create_pydantic_model_from_sqlalchemy

create_pydantic_model_from_sqlalchemy(
    sqlalchemy_model: Type[DeclarativeBase],
    model_name: str | None = None,
    relationship_strategy: RelationshipStrategy = RelationshipStrategy.EXCLUDE,
) -> Type[BaseModel]
```

**Parameters:**

- `sqlalchemy_model`: The SQLAlchemy model to convert
- `model_name`: Name for Pydantic model (default: SQLAlchemy model name)
- `relationship_strategy`: How to handle relationships (see strategies above)

#### `extract_type_from_mapped()`

Extract inner type from `Mapped[T]` annotations.

```python
from pysmith.db import extract_type_from_mapped

field_type = extract_type_from_mapped(Mapped[int])  # Returns: int
```

---

## Examples

See the `examples/` directory for complete working examples:

- **`model_to_sqlalchemy_example.py`**: Complete examples of Model → SQLAlchemy conversion
- **`sqlalchemy_pydantic_example.py`**: Examples of SQLAlchemy → Pydantic conversion with different relationship strategies
- **`quick_model_to_sqlalchemy_test.py`**: Quick test of the `Model.to_sqlalchemy_model()` method

---

## Best Practices

1. **Use Model for validation**: Define your models as `pysmith.Model` subclasses for automatic Pydantic validation
2. **Convert to SQLAlchemy for persistence**: Use `to_sqlalchemy_model()` when you need database operations
3. **Create DTOs from SQLAlchemy**: Use `create_pydantic_model_from_sqlalchemy()` for API responses
4. **Handle relationships carefully**: Choose the appropriate `RelationshipStrategy` based on your use case
5. **Cache converted models**: Store converted SQLAlchemy models as class variables to avoid repeated conversions

---

## Tips & Tricks

### Custom String Lengths

```python
# For models with long text fields
ArticleSQLAlchemy = Article.to_sqlalchemy_model(
    Base,
    table_name="articles",
    string_length=1000  # Longer strings
)
```

### Different Primary Key

```python
# If your primary key isn't named "id"
ProductSQLAlchemy = Product.to_sqlalchemy_model(
    Base,
    primary_key_field="product_id"
)
```

### Testing Without Database

```python
# Use in-memory SQLite for testing
from sqlalchemy import create_engine

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
```

---

## Limitations

1. **Relationships**: Forward references in relationships (`Mapped[List["Address"]]`) are automatically detected and handled based on your chosen strategy
2. **Complex Types**: Custom types may need manual mapping
3. **Constraints**: Database constraints (unique, check, etc.) are not automatically inferred
4. **Relationships Structure**: For complex nested models, you may need to manually define relationships

For complex use cases, consider using libraries like `sqlmodel` which provide native integration between Pydantic and SQLAlchemy.

---

## See Also

- [RELATIONSHIP_STRATEGIES.md](./RELATIONSHIP_STRATEGIES.md) - Detailed guide on handling SQLAlchemy relationships
- [pysmith.models](./src/pysmith/models/__init__.py) - Model class documentation
- [pysmith.db.adapters](./src/pysmith/db/adapters.py) - Full adapter implementation
