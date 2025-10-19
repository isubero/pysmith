# Nested Relations Guide for Pysmith Models

This guide explains how to handle relationships between models in Pysmith.

## Overview

Pysmith Models support relationships between entities, but the current implementation prioritizes **explicit foreign keys** over nested object graphs. This design choice provides:

- ✅ Clear, predictable behavior
- ✅ Better control over database operations
- ✅ Easier debugging
- ✅ Compatibility with standard SQL patterns

## Current Approach: Foreign Keys (Phase 1) ✅ IMPLEMENTED

### How It Works

Define relationships using foreign key IDs, not nested objects:

```python
from pysmith.models import Model
from pysmith.db import configure
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

configure('sqlite:///app.db', Base)

# Define models with foreign keys
class Author(Model):
    id: int
    name: str
    email: str

class Book(Model):
    id: int
    title: str
    author_id: int  # Foreign key, not nested Author object
    pages: int
```

### Usage Pattern

```python
# 1. Save the parent first
author = Author(id=1, name="Jane Doe", email="jane@example.com")
author.save()

# 2. Reference it by ID
book = Book(id=1, title="Python Guide", author_id=author.id, pages=300)
book.save()

# 3. Manual joins when needed
book = Book.find_by_id(1)
if book:
    author = Author.find_by_id(book.author_id)
    print(f"{book.title} by {author.name}")
```

### Pros

- ✅ Explicit and predictable
- ✅ No magic behavior
- ✅ Easy to understand
- ✅ Matches SQL semantics
- ✅ Full control over save order

### Cons

- ❌ Manual joins required
- ❌ More verbose
- ❌ No automatic cascade

---

## Future Approach: Nested Objects (Phase 2) 🚧 PLANNED

### Smart Cascade Save

Automatically detect and save nested Model instances:

```python
class Author(Model):
    id: int
    name: str

class Book(Model):
    id: int
    title: str
    author: Author  # Nested object!

# Smart save: detects nested model and saves both
author = Author(id=1, name="Jane")
book = Book(id=1, title="My Book", author=author)
book.save()  # Saves author first, then book with author_id
```

### Strategy Rules (Planned)

1. **If nested model has ID**: Assume it exists, extract ID only
2. **If nested model lacks ID**: Save it first, then use generated ID
3. **Circular dependencies**: Detect and raise clear error
4. **None values**: Handle gracefully as NULL foreign keys

### Implementation Considerations

```python
def _extract_nested_models(self) -> dict[str, Any]:
    """
    Phase 2 enhancement: Auto-save nested models.

    Current behavior (Phase 1):
    - Checks if value is a Model instance
    - Extracts the ID if it exists
    - Raises error if no ID (model must be saved first)

    Planned behavior (Phase 2):
    - Detect nested Model instances
    - Auto-save them if they don't have an ID
    - Extract the ID and create foreign key field
    - Handle circular dependencies
    """
    pass
```

---

## Advanced Patterns (Phase 3) 🔮 FUTURE

### Lazy Loading

```python
book = Book.find_by_id(1)
# Lazy load: only fetches when accessed
author = book.author  # Auto-query Author.find_by_id(book.author_id)
```

### Eager Loading

```python
# Prefetch related objects
books = Book.find_all(prefetch=['author'])
for book in books:
    print(f"{book.title} by {book.author.name}")  # No N+1 queries
```

### Collection Relationships

```python
class Author(Model):
    id: int
    name: str
    books: list[Book]  # Reverse relationship

author = Author.find_by_id(1)
for book in author.books:  # Auto-query
    print(book.title)
```

### Many-to-Many

```python
class Book(Model):
    id: int
    title: str
    categories: list[Category]  # M2M via junction table

book = Book(id=1, title="Python Guide")
book.categories.add(Category(id=1, name="Programming"))
book.save()  # Handles junction table
```

---

## Comparison with Other ORMs

### Django ORM

```python
# Django: Full ORM with nested objects
author = Author.objects.create(name="Jane")
book = Book.objects.create(title="Guide", author=author)  # Nested object
books = Book.objects.filter(author__name="Jane")  # Traversal
```

**Pysmith Phase 1**: Simpler, more explicit (foreign keys only)  
**Pysmith Phase 2+**: Will approach Django's convenience

### SQLAlchemy ORM

```python
# SQLAlchemy: Explicit relationships
class Book(Base):
    author_id = Column(Integer, ForeignKey('author.id'))
    author = relationship("Author", back_populates="books")

book.author = author  # Nested object via relationship()
```

**Pysmith Phase 1**: Similar explicitness, simpler API  
**Pysmith Phase 2+**: Will add relationship() equivalents

---

## Recommendations

### For Now (Phase 1)

✅ **Use foreign key IDs explicitly**

```python
class Book(Model):
    id: int
    title: str
    author_id: int  # ✓ Do this
```

❌ **Don't try to nest objects**

```python
class Book(Model):
    id: int
    title: str
    author: Author  # ✗ Not yet supported
```

✅ **Create helper methods for joins**

```python
class Book(Model):
    id: int
    title: str
    author_id: int

    def get_author(self) -> Optional[Author]:
        """Helper to fetch related author."""
        return Author.find_by_id(self.author_id)

# Usage
book = Book.find_by_id(1)
author = book.get_author()
```

### When Phase 2 Arrives

You'll be able to upgrade gradually:

```python
# Phase 1 code (still works)
book = Book(id=1, title="Guide", author_id=1)
book.save()

# Phase 2 code (new capability)
author = Author(id=1, name="Jane")
book = Book(id=1, title="Guide", author=author)  # Nested object
book.save()  # Auto-saves author first
```

---

## Technical Details

### How `_extract_nested_models()` Works

```python
def _extract_nested_models(self) -> dict[str, Any]:
    """
    Extract nested Model instances and convert them to IDs.

    Current implementation (Phase 1):
    1. Iterate through instance attributes
    2. Check if value is a Model instance
    3. If yes, extract its ID (must exist)
    4. Convert field name to foreign key format (field_name_id)
    5. Return flat dictionary for SQLAlchemy

    Example:
        Input:  {title: "Book", author: Author(id=1, name="Jane")}
        Output: {title: "Book", author_id: 1}
    """
```

### Database Schema

With foreign keys, your database schema is clear and standard:

```sql
CREATE TABLE author (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255)
);

CREATE TABLE book (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255),
    author_id INTEGER,  -- Foreign key
    FOREIGN KEY (author_id) REFERENCES author(id)
);
```

This is standard SQL that works with any database system.

---

## Migration Path

### Current State (Phase 1)

- ✅ Simple foreign key IDs
- ✅ Manual relationship traversal
- ✅ Full control over saves

### Next Steps (Phase 2)

- 🚧 Auto-detect nested Model instances
- 🚧 Smart cascade saves
- 🚧 Circular dependency detection

### Future Vision (Phase 3)

- 🔮 Lazy loading relationships
- 🔮 Eager loading / prefetch
- 🔮 Collection relationships
- 🔮 Many-to-many support
- 🔮 Query traversal (Django-style)

---

## Contributing

Interested in implementing Phase 2 features? Check out:

- `/src/pysmith/models/__init__.py` - Model class
- `_extract_nested_models()` method - Where the magic happens
- Test suite for relationship handling

Ideas for Phase 2 implementation:

1. Detect nested models in `_extract_nested_models()`
2. Recursively save nested models
3. Extract IDs after saving
4. Handle circular dependencies
5. Add tests for complex scenarios

---

## Questions?

- **Q: Why not support nested objects now?**  
  A: We want to get Phase 1 solid first. Nested objects add complexity (circular deps, save order, etc.)

- **Q: Can I use SQLAlchemy's relationship() directly?**  
  A: Not with Pysmith Models. If you need that, use `.to_sqlalchemy_model()` and work with SQLAlchemy directly.

- **Q: Will Phase 1 code break when Phase 2 is released?**  
  A: No! Foreign key IDs will always be supported. Phase 2 adds capabilities, doesn't remove them.

- **Q: How do I do joins/queries?**  
  A: For now, manual queries. Phase 2+ will add query traversal.

---

**Status**: Phase 1 ✅ Complete | Phase 2 🚧 Planned | Phase 3 🔮 Vision
