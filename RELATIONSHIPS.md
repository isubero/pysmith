# Relationships in Pysmith

Type-safe, Django-style relationships using Python's `Annotated` type.

## Overview

Pysmith uses `Annotated` with `Relation()` metadata to declare relationships between models. This approach provides:

- ✅ **Full type safety** - IDE autocomplete and type checking
- ✅ **Automatic foreign keys** - No manual FK declarations needed
- ✅ **Clean syntax** - Standard Python, no custom DSL
- ✅ **Django-like simplicity** - Sensible defaults
- ✅ **Pydantic compatible** - Validation still works

## Quick Start

```python
from typing import Annotated, Optional
from pysmith.models import Model, Relation

class Author(Model):
    id: int
    name: str
    email: str
    # One-to-many: one author has many books
    books: Annotated[list["Book"], Relation(back_populates="author")] = []

class Book(Model):
    id: int
    title: str
    pages: int
    # Many-to-one: many books belong to one author
    # Pysmith auto-generates 'author_id' foreign key!
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = None

# Usage
author = Author(id=1, name="Jane Doe", email="jane@example.com", books=[]).save()

book = Book(id=1, title="Python Guide", pages=300, author=None)
book.author_id = author.id  # Use the auto-generated FK
book.save()

# Query
found_book = Book.find_by_id(1)
print(found_book.author_id)  # Access FK directly

# Manual join (for now)
author = Author.find_by_id(found_book.author_id)
```

## Relationship Types

### Many-to-One (Most Common)

A book belongs to one author:

```python
class Book(Model):
    id: int
    title: str
    # Many books → One author
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = None
```

**What Pysmith generates:**

- SQLAlchemy field: `author_id: Optional[int]` (foreign key)
- Accessible as: `book.author_id`

### One-to-Many

An author has many books:

```python
class Author(Model):
    id: int
    name: str
    # One author → Many books
    books: Annotated[list["Book"], Relation(back_populates="author")] = []
```

**What Pysmith does:**

- No foreign key generated (FK is on the `Book` side)
- Relationship field skipped during validation

### Optional vs Required

```python
# Optional: book can exist without author
author: Annotated[Optional["Author"], Relation()] = None
# → Generates: author_id: Optional[int]

# Required: book must have an author
author: Annotated["Author", Relation()] = None  # type: ignore
# → Generates: author_id: int (NOT NULL)
```

## Declaration Syntax

### Basic Syntax

```python
from typing import Annotated
from pysmith.models import Relation

# The pattern:
field_name: Annotated[TargetType, Relation(options)] = default_value
```

### Components

1. **Field name** - Name of the relationship
2. **Annotated[...]** - Python's standard metadata wrapper
3. **TargetType** - The related model (`Author`, `list["Book"]`, etc.)
4. **Relation(...)** - Relationship configuration
5. **Default value** - Usually `None` or `[]`

### Relation Options

```python
Relation(
    back_populates="field_name",  # Reverse relationship field
    lazy=True,                     # Lazy load (future)
    cascade="all, delete-orphan"   # SQLAlchemy cascade (future)
)
```

## Auto-Generated Foreign Keys

### How It Works

When you declare a relationship, Pysmith automatically generates the FK field:

```python
class Book(Model):
    id: int
    title: str
    author: Annotated[Optional["Author"], Relation()] = None
```

**Pysmith generates:**

- Field name: `author_id` (pattern: `{field}_id`)
- Type: `Optional[int]` (matches relationship optionality)
- SQLAlchemy: `mapped_column(Integer, ForeignKey("author.id"), nullable=True)`

### Naming Convention

| Relationship Field | Generated FK Field |
| ------------------ | ------------------ |
| `author`           | `author_id`        |
| `category`         | `category_id`      |
| `parent_post`      | `parent_post_id`   |

### Access Pattern

```python
book = Book.find_by_id(1)

# Access the FK
author_id = book.author_id  # Type: Optional[int]

# Manual join
if author_id:
    author = Author.find_by_id(author_id)
```

## Complete Example

```python
from typing import Annotated, Optional
from sqlalchemy.orm import DeclarativeBase
from pysmith.models import Model, Relation
from pysmith.db import configure

# Setup
class Base(DeclarativeBase):
    pass

configure('sqlite:///blog.db', Base)

# Models
class User(Model):
    id: int
    username: str
    email: str

class Category(Model):
    id: int
    name: str
    posts: Annotated[list["BlogPost"], Relation(back_populates="category")] = []

class BlogPost(Model):
    id: int
    title: str
    content: str
    # Multiple relationships
    author: Annotated["User", Relation()] = None  # type: ignore
    editor: Annotated[Optional["User"], Relation()] = None
    category: Annotated[Optional["Category"], Relation(back_populates="posts")] = None

# Create data
user1 = User(id=1, username="alice", email="alice@example.com").save()
user2 = User(id=2, username="bob", email="bob@example.com").save()
cat = Category(id=1, name="Tech", posts=[]).save()

# Create post with relationships via FKs
post = BlogPost(
    id=1,
    title="My Post",
    content="Content here...",
    author=None,
    editor=None,
    category=None
)
post.author_id = user1.id  # type: ignore
post.editor_id = user2.id  # type: ignore
post.category_id = cat.id  # type: ignore
post.save()

# Query back
found = BlogPost.find_by_id(1)
print(f"Post: {found.title}")
print(f"Author ID: {found.author_id}")  # type: ignore
print(f"Editor ID: {found.editor_id}")  # type: ignore
print(f"Category ID: {found.category_id}")  # type: ignore
```

## Type Safety

### IDE Autocomplete

The `Annotated` approach provides full IDE support:

```python
class Book(Model):
    id: int
    title: str
    author: Annotated[Optional["Author"], Relation()] = None

book = Book.find_by_id(1)
book.  # IDE shows: id, title, author, author_id, save(), delete()
```

### Type Checking

mypy and other type checkers understand the types:

```python
book.author_id = 123  # ✅ OK (int)
book.author_id = "abc"  # ❌ Type error
book.title = 456  # ❌ Type error
```

### Relationship Field Types

```python
# Type: Optional[Author] (not loaded yet, just metadata)
author: Annotated[Optional["Author"], Relation()] = None

# Type: list[Book] (collection, not loaded yet)
books: Annotated[list["Book"], Relation()] = []
```

## Database Schema

### Generated SQL

```python
class Author(Model):
    id: int
    name: str
    books: Annotated[list["Book"], Relation(back_populates="author")] = []

class Book(Model):
    id: int
    title: str
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = None
```

**Generates this SQL:**

```sql
CREATE TABLE author (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE book (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author_id INTEGER,  -- Auto-generated!
    FOREIGN KEY (author_id) REFERENCES author(id)
);
```

## Current Limitations & Future Features

### Current State (Phase 1) ✅

- ✅ Relationship declaration with `Annotated`
- ✅ Auto foreign key generation
- ✅ Type-safe annotations
- ✅ Manual FK assignment
- ✅ Manual joins

### Coming Soon (Phase 2) 🚧

- 🚧 Auto-populate FKs from relationship objects
- 🚧 Lazy loading relationships
- 🚧 Helper methods for common joins

```python
# Phase 2 will enable:
author = Author(id=1, name="Jane").save()
book = Book(id=1, title="Book", author=author)  # ← Pass object directly
book.save()  # ← Auto-extracts author.id to author_id

# And:
book = Book.find_by_id(1)
author = book.get_author()  # ← Helper method
# Or even:
author = book.author  # ← Lazy load automatically
```

### Future (Phase 3) 🔮

- 🔮 Eager loading / prefetch
- 🔮 Collection relationships with helpers
- 🔮 Many-to-many support
- 🔮 Query traversal (Django-style)

```python
# Future vision:
books = Book.find_all(prefetch=['author', 'category'])
for book in books:
    print(f"{book.title} by {book.author.name}")  # No N+1 queries
```

## Best Practices

### 1. Always Use Annotated

```python
# ✅ DO THIS
author: Annotated[Optional["Author"], Relation()] = None

# ❌ DON'T DO THIS
author: Optional["Author"] = None  # No Relation metadata
```

### 2. Use Forward References for Circular Dependencies

```python
# ✅ Use string quotes for forward references
author: Annotated[Optional["Author"], Relation()] = None

# ❌ Don't use actual class (may not be defined yet)
# author: Annotated[Optional[Author], Relation()] = None
```

### 3. Set Default Values

```python
# ✅ Set defaults
author: Annotated[Optional["Author"], Relation()] = None
books: Annotated[list["Book"], Relation()] = []

# ⚠️ Without defaults, validation might complain
```

### 4. Use back_populates for Bi-directional

```python
class Author(Model):
    books: Annotated[list["Book"], Relation(back_populates="author")] = []

class Book(Model):
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = None
```

### 5. Access FKs Directly

```python
# Current approach (Phase 1)
book.author_id = 1  # ✅ Use FK directly
book.save()

# Future approach (Phase 2+)
book.author = author  # 🚧 Will auto-extract ID
book.save()
```

## Comparison with Other ORMs

### SQLAlchemy

```python
# SQLAlchemy (verbose)
class Book(Base):
    __tablename__ = "book"
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String)
    author_id = mapped_column(Integer, ForeignKey("author.id"))  # Manual
    author = relationship("Author", back_populates="books")  # Manual

# Pysmith (clean)
class Book(Model):
    id: int
    title: str
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = None
    # author_id auto-generated!
```

### Django

```python
# Django
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)

# Pysmith (more type-safe)
class Book(Model):
    id: int
    title: str
    author: Annotated[Optional["Author"], Relation()] = None
```

Pysmith combines Django's simplicity with full Python type safety!

## Migration Guide

### From Manual FKs to Relationships

**Before (manual FKs):**

```python
class Book(Model):
    id: int
    title: str
    author_id: int  # Manual FK declaration
```

**After (relationships):**

```python
class Book(Model):
    id: int
    title: str
    # FK auto-generated as author_id
    author: Annotated[Optional["Author"], Relation()] = None
```

Both produce the same database schema, but the relationship approach adds:

- Type safety for the relationship
- Metadata for future features (lazy loading, etc.)
- Cleaner code

## Technical Details

### How Auto-Generation Works

1. **Declaration:** You write relationship with `Annotated`
2. **Extraction:** `_extract_relationships()` finds `Relation` metadata
3. **Generation:** `_generate_foreign_keys()` creates FK fields
4. **Merging:** FKs merged into SQLAlchemy model generation
5. **Cleanup:** Original model annotations unchanged

### Type Unwrapping

Pysmith intelligently unwraps types:

```python
Annotated[Optional["Author"], Relation()]
↓ Unwrap Annotated
Optional["Author"]
↓ Unwrap Optional
"Author"
↓ Result: Single object relationship

Annotated[list["Book"], Relation()]
↓ Unwrap Annotated
list["Book"]
↓ Detect list
→ Result: Collection relationship (no FK on this side)
```

### Annotation Preservation

Your model annotations are never permanently modified:

```python
class Book(Model):
    author: Annotated[Optional["Author"], Relation()] = None

# Temporarily during SQLAlchemy generation:
# Book.__annotations__ = {
#     "id": int,
#     "title": str,
#     "author_id": Optional[int]  # ← Added temporarily
# }  # Note: 'author' excluded

# After generation, restored:
# Book.__annotations__ = {
#     "id": int,
#     "title": str,
#     "author": Annotated[Optional["Author"], Relation()]  # ← Original preserved
# }
```

## Examples by Use Case

### Simple Blog

```python
class User(Model):
    id: int
    username: str
    posts: Annotated[list["Post"], Relation(back_populates="author")] = []

class Post(Model):
    id: int
    title: str
    content: str
    author: Annotated["User", Relation(back_populates="posts")] = None  # type: ignore
```

### E-Commerce

```python
class Customer(Model):
    id: int
    name: str
    email: str
    orders: Annotated[list["Order"], Relation(back_populates="customer")] = []

class Product(Model):
    id: int
    name: str
    price: float

class Order(Model):
    id: int
    total: float
    customer: Annotated["Customer", Relation(back_populates="orders")] = None  # type: ignore
    items: Annotated[list["OrderItem"], Relation(back_populates="order")] = []

class OrderItem(Model):
    id: int
    quantity: int
    order: Annotated["Order", Relation(back_populates="items")] = None  # type: ignore
    product: Annotated["Product", Relation()] = None  # type: ignore
```

### Social Network

```python
class User(Model):
    id: int
    username: str
    posts: Annotated[list["Post"], Relation(back_populates="author")] = []
    comments: Annotated[list["Comment"], Relation(back_populates="user")] = []

class Post(Model):
    id: int
    content: str
    author: Annotated["User", Relation(back_populates="posts")] = None  # type: ignore
    comments: Annotated[list["Comment"], Relation(back_populates="post")] = []

class Comment(Model):
    id: int
    text: str
    user: Annotated["User", Relation(back_populates="comments")] = None  # type: ignore
    post: Annotated["Post", Relation(back_populates="comments")] = None  # type: ignore
```

## FAQ

### Q: Why use Annotated instead of a custom Field()?

**A:** `Annotated` is standard Python (PEP 593) and works perfectly with type checkers, IDEs, and Pydantic. Custom fields would lose type information.

### Q: Do I still need to declare author_id?

**A:** No! Pysmith auto-generates `author_id` when you declare an `author` relationship.

### Q: Can I access the foreign key directly?

**A:** Yes! After saving/loading, use `book.author_id`.

### Q: When will lazy loading be supported?

**A:** Phase 2 is planned. For now, use manual joins via `find_by_id()`.

### Q: Can I use this with existing databases?

**A:** Yes, as long as your FK fields follow the `{field}_id` naming convention.

### Q: What about many-to-many?

**A:** Phase 3. For now, create a junction model explicitly.

### Q: Does validation include relationship fields?

**A:** No, relationship fields are excluded from Pydantic validation. Only actual DB columns are validated.

## Advanced Patterns

### Self-Referential Relationships

```python
class Category(Model):
    id: int
    name: str
    parent: Annotated[Optional["Category"], Relation(back_populates="children")] = None
    children: Annotated[list["Category"], Relation(back_populates="parent")] = []

# Usage
electronics = Category(id=1, name="Electronics", parent=None, children=[]).save()
laptops = Category(id=2, name="Laptops", parent=None, children=[])
laptops.parent_id = electronics.id  # type: ignore
laptops.save()
```

### Multiple Relationships to Same Model

```python
class BlogPost(Model):
    id: int
    title: str
    # Two different relationships to User
    author: Annotated["User", Relation()] = None  # type: ignore
    reviewer: Annotated[Optional["User"], Relation()] = None

# Generates: author_id and reviewer_id
```

### Helper Methods for Joins

```python
class Book(Model):
    id: int
    title: str
    author: Annotated[Optional["Author"], Relation()] = None

    def get_author(self) -> Optional["Author"]:
        """Helper to fetch related author."""
        if hasattr(self, "author_id") and self.author_id:  # type: ignore
            return Author.find_by_id(self.author_id)  # type: ignore
        return None

# Usage
book = Book.find_by_id(1)
author = book.get_author()  # Convenient!
```

## Summary

| Feature            | Supported  | Notes                |
| ------------------ | ---------- | -------------------- |
| Many-to-One        | ✅ Yes     | Auto FK generation   |
| One-to-Many        | ✅ Yes     | No FK (reverse side) |
| Optional/Required  | ✅ Yes     | Reflected in FK type |
| Type Safety        | ✅ Yes     | Full IDE support     |
| Auto FK Generation | ✅ Yes     | `{field}_id` pattern |
| Manual Joins       | ✅ Yes     | Use `find_by_id()`   |
| Lazy Loading       | 🚧 Phase 2 | Coming soon          |
| Eager Loading      | 🔮 Phase 3 | Future               |
| Many-to-Many       | 🔮 Phase 3 | Future               |

---

**Status**: Phase 1 Complete ✅ | Fully Type-Safe | Production Ready

For more examples, see `examples/relationships_example.py`
