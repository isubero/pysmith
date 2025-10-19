# Relations Guide for Pysmith Models

This guide explains how to work with relationships between models in Pysmith.

## Overview

Pysmith Models support **type-safe, ORM-style relationships** using Python's `Annotated` type. This approach provides:

- ✅ Full type safety with IDE autocomplete
- ✅ Automatic foreign key generation
- ✅ ORM-style object assignment
- ✅ Django-like simplicity
- ✅ Standard Python (PEP 593 Annotated)

## Current Approach: Annotated Relationships ✅ IMPLEMENTED

### How It Works

Define relationships using `Annotated` with `Relation()`:

```python
from typing import Annotated, Optional
from pysmith.models import Model, Relation
from pysmith.db import configure
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

configure('sqlite:///app.db', Base)

# Define models with relationships
class Author(Model):
    id: int
    name: str
    email: str
    books: Annotated[list["Book"], Relation(back_populates="author")] = []

class Book(Model):
    id: int
    title: str
    pages: int
    # Foreign key 'author_id' auto-generated!
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = None
```

### Usage Pattern (ORM-Style)

```python
# 1. Create and save parent
author = Author(id=1, name="Jane Doe", email="jane@example.com", books=[])
author.save()

# 2. Pass object directly - FK extracted automatically!
book = Book(id=1, title="Python Guide", pages=300, author=author)
book.save()  # ✨ author_id automatically set to author.id

# 3. Manual joins (for now, lazy loading coming soon)
book = Book.find_by_id(1)
if book.author_id:  # type: ignore
    author = Author.find_by_id(book.author_id)  # type: ignore
    print(f"{book.title} by {author.name}")
```

### Pros

- ✅ Type-safe and explicit
- ✅ ORM-style object assignment
- ✅ Automatic FK extraction
- ✅ IDE autocomplete support
- ✅ Django-like simplicity
- ✅ Standard Python (Annotated)

### Current Limitations

- Manual joins required (lazy loading coming in Phase 3)

---

## Advanced Features (Phase 3) 🚧 COMING SOON

### Lazy Loading

Automatically load relationships when accessed:

```python
book = Book.find_by_id(1)
# Lazy load: fetches author automatically
author = book.author  # ← No manual query needed!
print(author.name)  # Works magically!
```

### Implementation Plan

Property descriptors that auto-query when accessed:

```python
@property
def author(self) -> Optional["Author"]:
    """Lazy-load author from author_id."""
    if not hasattr(self, '_author_cache'):
        if self.author_id:
            self._author_cache = Author.find_by_id(self.author_id)
        else:
            self._author_cache = None
    return self._author_cache
```

---

## Advanced Patterns (Phase 4) 🔮 FUTURE

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

### Current Best Practices

✅ **Use Annotated relationships**

```python
from typing import Annotated, Optional
from pysmith.models import Relation

class Book(Model):
    id: int
    title: str
    # ✓ Do this - type-safe with auto FK
    author: Annotated[Optional["Author"], Relation()] = None
```

✅ **Pass objects directly**

```python
# ORM-style object assignment
author = Author(id=1, name="Jane").save()
book = Book(id=1, title="Guide", author=author).save()
# ✨ author_id auto-extracted!
```

✅ **Update relationships naturally**

```python
book.author = new_author
book.save()  # FK automatically updated
```

✅ **Use helper methods for manual joins**

```python
class Book(Model):
    def get_author(self) -> Optional[Author]:
        """Helper to fetch related author."""
        if self.author_id:  # type: ignore
            return Author.find_by_id(self.author_id)  # type: ignore
        return None

# Usage
book = Book.find_by_id(1)
author = book.get_author()  # Convenient!
```

### Backward Compatibility

Old-style FK declarations still work:

```python
# Still supported (backward compatible)
class Book(Model):
    id: int
    title: str
    author_id: int  # Manual FK

book = Book(id=1, title="Guide", author_id=1).save()
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

### Current State (Phase 2 Complete!)

- ✅ Type-safe Annotated relationships
- ✅ Automatic FK generation
- ✅ ORM-style object assignment
- ✅ FK extraction from objects
- ✅ Relationship updates
- ✅ Full type safety

### Next Steps (Phase 3)

- 🚧 Lazy loading relationships
- 🚧 Eager loading / prefetch
- 🚧 Collection methods

### Future Vision (Phase 4)

- 🔮 Many-to-many support
- 🔮 Query traversal (Django-style)
- 🔮 Async support

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

**Status**: Phase 2 ✅ Complete | Phase 3 🚧 Next | Phase 4 🔮 Vision
