# Bidirectional Model Conversion - Summary

## 🎯 What We Built

Complete **bidirectional conversion** system between:

- `pysmith.Model` ⟷ SQLAlchemy models
- SQLAlchemy models ⟷ Pydantic models

## 🔄 Conversion Flows

```
┌─────────────────┐
│  pysmith.Model  │
│  (Validation)   │
└────────┬────────┘
         │
         ↓ to_sqlalchemy_model()
         │
┌────────┴────────┐
│   SQLAlchemy    │
│  (Persistence)  │
└────────┬────────┘
         │
         ↓ create_pydantic_model_from_sqlalchemy()
         │
┌────────┴────────┐
│    Pydantic     │
│  (API/DTO)      │
└─────────────────┘
```

## 📦 New Functions

### Model → SQLAlchemy

1. **`Model.to_sqlalchemy_model()`** - Convenience method on Model class

   ```python
   UserSQLAlchemy = User.to_sqlalchemy_model(Base, table_name="users")
   ```

2. **`create_sqlalchemy_model_from_model()`** - Standalone function

   ```python
   from pysmith.db import create_sqlalchemy_model_from_model
   UserSQLAlchemy = create_sqlalchemy_model_from_model(User, Base)
   ```

3. **`create_sqlalchemy_model_from_annotations()`** - From raw annotations

   ```python
   annotations = {'id': int, 'name': str}
   UserSQLAlchemy = create_sqlalchemy_model_from_annotations('User', annotations, Base)
   ```

4. **`python_type_to_sqlalchemy_column()`** - Type mapping helper

### SQLAlchemy → Pydantic

1. **`create_pydantic_model_from_sqlalchemy()`** - Main conversion function

   ```python
   UserDTO = create_pydantic_model_from_sqlalchemy(UserSQLAlchemy)
   ```

2. **`extract_type_from_mapped()`** - Extract type from `Mapped[T]`

   ```python
   inner_type = extract_type_from_mapped(Mapped[int])  # Returns: int
   ```

3. **`sqlalchemy_to_pydantic_fields()`** - Get Pydantic field definitions

4. **`RelationshipStrategy` enum** - Three strategies for handling relationships:
   - `EXCLUDE`: Remove relationships (default)
   - `OPTIONAL`: Include as `Optional[Any]`
   - `ID_ONLY`: Use foreign key IDs only

## 🗂️ Files Added/Modified

### New Files

- ✨ `MODEL_SQLALCHEMY_CONVERSION.md` - Complete conversion guide
- ✨ `RELATIONSHIP_STRATEGIES.md` - Relationship handling guide
- ✨ `CONVERSION_SUMMARY.md` - This file
- ✨ `examples/model_to_sqlalchemy_example.py` - Model → SQLAlchemy examples
- ✨ `examples/sqlalchemy_pydantic_example.py` - SQLAlchemy → Pydantic examples
- ✨ `examples/quick_model_to_sqlalchemy_test.py` - Quick test

### Modified Files

- ♻️ `src/pysmith/db/adapters.py` - All conversion logic
- ♻️ `src/pysmith/db/__init__.py` - Exports all functions
- ♻️ `src/pysmith/models/__init__.py` - Added `to_sqlalchemy_model()` method

## 🎨 Type Mapping

| Python Type     | SQLAlchemy Type | Notes               |
| --------------- | --------------- | ------------------- |
| `int`           | `Integer`       | Required by default |
| `Optional[int]` | `Integer`       | `nullable=True`     |
| `str`           | `String(255)`   | Configurable length |
| `Optional[str]` | `String(255)`   | `nullable=True`     |
| `float`         | `Float`         |                     |
| `bool`          | `Boolean`       |                     |

## 🚀 Usage Examples

### Basic Conversion

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

# Convert to Pydantic DTO
from pysmith.db import create_pydantic_model_from_sqlalchemy
UserDTO = create_pydantic_model_from_sqlalchemy(UserSQLAlchemy)
```

### Complete Workflow

```python
# 1. Validate with Model
user_data = {"id": 1, "name": "Alice", "email": "alice@example.com"}
user = User(**user_data)  # Pydantic validation

# 2. Persist with SQLAlchemy
UserSQLAlchemy = User.to_sqlalchemy_model(Base, table_name="users")
db_user = UserSQLAlchemy(**user_data)
session.add(db_user)
session.commit()

# 3. Return as DTO
UserDTO = create_pydantic_model_from_sqlalchemy(UserSQLAlchemy)
response = UserDTO(**db_user.__dict__)
return response.model_dump_json()
```

## 🎓 Key Features

1. **Type Safety**: Preserves Python type hints throughout conversions
2. **Optional Handling**: Correctly maps `Optional[T]` to nullable columns
3. **Primary Key Detection**: Automatically marks primary key fields
4. **Relationship Strategies**: Three strategies for handling SQLAlchemy relationships
5. **Configurable**: Custom table names, string lengths, primary key fields
6. **Caching**: Efficient conversion with minimal overhead
7. **No Manual Mapping**: Fully automatic based on type annotations

## 📊 Comparison with Alternatives

| Feature                 | Pysmith | SQLModel | Pydantic + SA |
| ----------------------- | ------- | -------- | ------------- |
| Bidirectional           | ✅      | ✅       | ❌            |
| Separate Models         | ✅      | ❌       | ✅            |
| Dynamic Conversion      | ✅      | ❌       | ❌            |
| Relationship Strategies | ✅      | ❌       | ❌            |
| Custom Model Base       | ✅      | ❌       | ✅            |

**Advantage**: Pysmith allows you to keep `Model` and SQLAlchemy models separate, then convert dynamically when needed. This provides maximum flexibility.

## 🧪 Testing

All functionality is tested with working examples:

```bash
# Run the demos
python src/pysmith/db/adapters.py
python examples/model_to_sqlalchemy_example.py
python examples/sqlalchemy_pydantic_example.py
python examples/quick_model_to_sqlalchemy_test.py
```

All tests pass! ✅

## 📚 Documentation

- **[MODEL_SQLALCHEMY_CONVERSION.md](./MODEL_SQLALCHEMY_CONVERSION.md)** - Complete API reference and usage guide
- **[RELATIONSHIP_STRATEGIES.md](./RELATIONSHIP_STRATEGIES.md)** - Detailed guide on relationship handling

## 🎯 Use Cases

### 1. FastAPI with Database

```python
from fastapi import FastAPI
from pysmith.models import Model

class User(Model):
    id: int
    name: str
    email: str

# Use Model for request validation
@app.post("/users")
def create_user(user: User):  # Pydantic validation
    UserSQLAlchemy = User.to_sqlalchemy_model(Base)
    db_user = UserSQLAlchemy(**user.model_dump())
    session.add(db_user)
    return {"id": db_user.id}
```

### 2. Data Migration

```python
# Read from one database, write to another
source_model = create_pydantic_model_from_sqlalchemy(SourceSQLAlchemy)
target_model = create_sqlalchemy_model_from_annotations(
    'Target', source_model.model_fields, TargetBase
)
```

### 3. API DTOs

```python
# Create lightweight DTOs without relationships
UserDTO = create_pydantic_model_from_sqlalchemy(
    User,
    relationship_strategy=RelationshipStrategy.EXCLUDE
)
```

## 💡 Benefits

1. **Flexibility**: Choose the right tool for each task
2. **Type Safety**: Consistent typing across all layers
3. **Validation**: Pydantic validation before database operations
4. **Clean Separation**: Keep validation logic separate from persistence
5. **Easy Testing**: Test validation without database
6. **API-First**: Natural fit for FastAPI and modern Python APIs

## 🔮 Future Enhancements

Possible improvements for the future:

- Support for more complex SQLAlchemy column types (JSON, Array, etc.)
- Automatic relationship inference
- Support for composite primary keys
- Migration generation from Model changes
- Integration with Alembic for schema migrations

## ✅ Summary

You can now:

- ✅ Convert `pysmith.Model` → SQLAlchemy (3 different methods)
- ✅ Convert SQLAlchemy → Pydantic (with relationship strategies)
- ✅ Extract types from `Mapped[T]` annotations
- ✅ Handle Optional types correctly
- ✅ Configure table names, primary keys, and string lengths
- ✅ Use convenient methods directly on Model classes
- ✅ Import everything from `pysmith.db`

**Result**: Complete bidirectional conversion system! 🎉
