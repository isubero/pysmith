# Pysmith

> A set of Python tools focused on productivity

[![PyPI](https://img.shields.io/pypi/v/pysmith.svg)](https://pypi.org/project/pysmith/)
[![Python](https://img.shields.io/pypi/pyversions/pysmith.svg)](https://pypi.org/project/pysmith/)
[![License](https://img.shields.io/pypi/l/pysmith.svg)](https://github.com/isubero/pysmith/blob/main/LICENSE)
[![Tests](https://github.com/isubero/pysmith/workflows/Tests/badge.svg)](https://github.com/isubero/pysmith/actions)
[![Code Quality](https://img.shields.io/badge/code%20quality-ruff-blue)](https://github.com/astral-sh/ruff)
[![Type Checked](https://img.shields.io/badge/type%20checked-mypy-blue)](http://mypy-lang.org/)

## ⚠️ Status: Alpha Release

Pysmith is functional and ready for testing! Core features are implemented:

- ✅ Persistance and validation from a single model (DRY)
- ✅ Model class with Pydantic validation
- ✅ Django-style ORM (save, delete, find)
- ✅ Lazy-loading relationships (just access `book.author`!)
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
- [x] Relationship lazy loading
- [ ] Query builder (filter, where, order_by) - next priority
- [ ] Eager loading / prefetch (solve N+1)
- [ ] Async support (async_save, async_find)
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

### Lazy-Loading Relationships

Relationships automatically load when accessed - no manual joins needed!

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

# Lazy loading: Just access the relationship!
found = Book.find_by_id(1)
print(found.author.name)  # ✨ Auto-loads author - no manual query!
```

### Required vs Optional Relationships

Pysmith validates required relationships **before** hitting the database:

```python
class Book(Model):
    id: int
    title: str
    # Required (no Optional) - book MUST have an author
    author: Annotated["Author", Relation()] = None  # type: ignore
    # Optional - book may or may not have a publisher
    publisher: Annotated[Optional["Publisher"], Relation()] = None

# ✅ With required relationship - works
book = Book(id=1, title="Guide", author=author_obj).save()

# ❌ Missing required relationship - clear error
book = Book(id=2, title="Guide", author=None)
book.save()
# ValueError: Required relationship 'author' cannot be None.
#             Please provide a Author instance.
```

**Benefits:**

- 🚨 **Fail Fast** - Errors at Python level, not database
- 💬 **Clear Messages** - Tells you exactly what's missing
- 🎯 **Type Safe** - IDE knows what's required
- 🔒 **Data Integrity** - Enforces NOT NULL constraints

## 🔨 CLI (Planned)

```bash
pysmith new myproject
pysmith forge model User
pysmith forge migration
pysmith db migrate
```

## 📚 Examples

Check out the `examples/` directory for complete working examples:

- `django_style_orm_example.py` - CRUD operations and ORM-style relationships
- `lazy_loading_example.py` - Automatic relationship loading (no manual joins!)
- `relationships_example.py` - Type-safe relationships with Annotated
- `required_relationships_example.py` - Required vs optional relationships with validation
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
