# Pysmith

> A set of Python tools focused on productivity

[![PyPI](https://img.shields.io/pypi/v/pysmith.svg)](https://pypi.org/project/pysmith/)
[![Python](https://img.shields.io/pypi/pyversions/pysmith.svg)](https://pypi.org/project/pysmith/)
[![License](https://img.shields.io/pypi/l/pysmith.svg)](https://github.com/isubero/pysmith/blob/main/LICENSE)

## ⚠️ Status: Alpha Release

Pysmith is functional and ready for testing! Core features are implemented:

- ✅ Persistance and validation from a single model (DRY)
- ✅ Model class with Pydantic validation
- ✅ Django-style ORM (save, delete, find)
- ✅ Type-safe relationships with auto FK generation
- ✅ Automatic table creation
- ✅ Full type safety with IDE support

Visit the github repository for updates and to report issues.

## 🎯 Vision

Pysmith is a modern set of python tools that combines:

- 🎨 **Elegance** - Clean, intuitive API design
- 🔧 **Craftsmanship** - Tools for artisan developers
- 📦 **Modularity** - Use only what you need
- 🚀 **Simplicity** - One model class for validation and persistence

## 🚀 Roadmap

- [x] Core Model class
- [x] Pydantic validation integration
- [x] SQLAlchemy adapters
- [x] Django-style ORM (save, find, delete)
- [x] DB Session management
- [x] Type-safe relationships with Annotated
- [x] Auto foreign key generation
- [ ] Relationship lazy loading (next priority)
- [ ] Query builder (filter, where, order_by)
- [ ] Async support (async_save, async_find)
- [ ] Eager loading / prefetch
- [ ] Many-to-many relationships
- [ ] Migrations system
- [ ] Auth utilities
- [ ] CLI tooling
- [ ] Testing utilities
- [ ] Complete documentation

## 📦 Installation

```bash
pip install pysmith
```

**Dependencies:**

- Python 3.10+
- SQLAlchemy 2.0+
- Pydantic 2.0+

## 💻 Quick Start

```python
from typing import Optional
from sqlalchemy.orm import DeclarativeBase
from pysmith.models import Model
from pysmith.db import configure

# 1. Setup database (once at app startup)
class Base(DeclarativeBase):
    pass

configure('sqlite:///myapp.db', Base)

# 2. Define your Model (validation + persistence)
class User(Model):
    id: int
    username: str
    email: str
    age: Optional[int]

# 3. Create and validate
user = User(id=1, username="alice", email="alice@example.com", age=30)
# ✅ Pydantic validates automatically

# 4. Save to database
user.save()  # ✅ Persists to database

# 5. Query
found = User.find_by_id(1)
all_users = User.find_all()

# 6. Update
found.email = "newemail@example.com"
found.save()

# 7. Delete
found.delete()
```

## 🔥 Features

### Single Model Class

Define your model once, get both validation and persistence:

```python
class User(Model):
    id: int
    username: str
    email: str
```

### Automatic Validation

Pydantic validates on instantiation:

```python
user = User(id=1, username="alice", email="invalid-email")
# ❌ Raises ValidationError
```

### Django-Style ORM

Familiar, intuitive database operations:

```python
# Create
user = User(id=1, username="alice", email="alice@example.com").save()

# Read
user = User.find_by_id(1)
users = User.find_all()

# Update
user.email = "new@example.com"
user.save()

# Delete
user.delete()
```

### Hidden Session Management

No manual session handling required:

```python
from pysmith.db import configure

configure('sqlite:///app.db', Base)  # Once at startup
# Sessions managed automatically!
```

### Type-Safe Relationships

Use `Annotated` with `Relation()` for ORM-style object relationships:

```python
from typing import Annotated, Optional
from pysmith.models import Relation

class Author(Model):
    id: int
    name: str
    books: Annotated[list["Book"], Relation(back_populates="author")] = []

class Book(Model):
    id: int
    title: str
    # Foreign key 'author_id' auto-generated!
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = None

# ORM-style: Pass objects directly!
author = Author(id=1, name="Jane", books=[]).save()
book = Book(id=1, title="Python Guide", author=author).save()
# author_id automatically extracted! ✨
```

## 🔨 CLI (Planned)

```bash
pysmith new myproject
pysmith forge model User
pysmith forge migration
pysmith db migrate
```

## 📚 Examples

Check out the `examples/` directory for complete working examples:

- `django_style_orm_example.py` - CRUD operations and basic relationships
- `relationships_example.py` - Type-safe relationships with Annotated
- `type_safety_example.py` - Type safety benefits
- `sqlalchemy_pydantic_example.py` - Converting between models

## 📖 Documentation

- `RELATIONSHIPS.md` - Complete guide to type-safe relationships
- `TYPE_SAFETY_IMPROVEMENTS.md` - How type safety works
- `NESTED_RELATIONS_GUIDE.md` - Relationship strategies and roadmap
- `IMPLEMENTATION_SUMMARY.md` - Architecture overview

## 🤝 Contributing

Interested in contributing? Watch this repo for updates!

### Development Setup

```bash
git clone https://github.com/isubero/pysmith.git
cd pysmith
uv sync
uv run pytest
```

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

## 🔗 Links

- **PyPI**: [pypi.org/project/pysmith](https://pypi.org/project/pysmith)
- **Repository**: [github.com/isubero/pysmith](https://github.com/isubero/pysmith)
- **Issues**: [github.com/isubero/pysmith/issues](https://github.com/isubero/pysmith/issues)

---

_Forging the future of Python web development_ ⚒️
