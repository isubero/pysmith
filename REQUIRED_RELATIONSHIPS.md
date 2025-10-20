# Required Relationships Implementation

## Overview

Pysmith now validates required relationships (non-Optional) **before** hitting the database, providing clear, immediate error messages when relationships are missing.

## Feature Summary

### What It Does

When you declare a relationship without `Optional`, Pysmith treats it as **required**:

```python
class Book(Model):
    id: int
    title: str
    # Required - book MUST have an author
    author: Annotated["Author", Relation()] = None  # type: ignore
    # Optional - book may or may not have a publisher
    publisher: Annotated[Optional["Publisher"], Relation()] = None
```

### Validation Behavior

**✅ With Required Relationship (Works):**

```python
author = Author(id=1, name="Jane").save()
book = Book(id=1, title="Guide", author=author).save()
# ✓ Success!
```

**❌ Without Required Relationship (Fails Fast):**

```python
book = Book(id=1, title="Guide", author=None)
book.save()
# ✗ ValueError: Required relationship 'author' cannot be None.
#              Please provide a Author instance.
```

## Key Benefits

### 1. 🚨 Fail Fast

- Errors occur at Python level, **not** at the database
- Immediate feedback during development
- No confusing database constraint errors

### 2. 💬 Clear Error Messages

```
ValueError: Required relationship 'author' cannot be None.
            Please provide a Author instance.
```

- States exactly what's wrong
- Includes the field name (`author`)
- Includes the target type (`Author`)
- Suggests what to do (`provide a ... instance`)

### 3. 🎯 Type Safety

- IDE knows which relationships are required
- Autocomplete guides you to provide the relationship
- Type checkers can catch mistakes early

### 4. 🔒 Data Integrity

- Enforces NOT NULL constraints at the Python level
- Prevents invalid data from reaching the database
- Consistent with database schema

## Implementation Details

### How It Works

1. **FK Type Detection**: When `_generate_foreign_keys()` runs, it determines if the foreign key should be `int` (required) or `Optional[int]` (optional) based on whether the relationship uses `Optional`.

2. **Validation Method**: `_validate_required_relationships()` checks all relationships before save:

   - Identifies which FKs are required (not `Optional[int]`)
   - Checks if their values are `None`
   - Raises `ValueError` with clear message if missing

3. **Save Integration**: The `save()` method calls validation before any database operations:
   ```python
   def save(self) -> Self:
       # Validate required relationships before hitting the database
       self._validate_required_relationships()
       # ... rest of save logic
   ```

### Database Schema

```sql
-- Required relationship
CREATE TABLE book (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author_id INTEGER NOT NULL,  -- NOT NULL constraint!
    FOREIGN KEY (author_id) REFERENCES author(id)
);

-- Optional relationship
CREATE TABLE book (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    publisher_id INTEGER NULL,  -- Nullable!
    FOREIGN KEY (publisher_id) REFERENCES publisher(id)
);
```

## Usage Patterns

### Pattern 1: All Required

```python
class OrderItem(Model):
    id: int
    quantity: int
    # Both required
    product: Annotated["Product", Relation()] = None  # type: ignore
    order: Annotated["Order", Relation()] = None  # type: ignore

# Must provide both
item = OrderItem(
    id=1,
    quantity=5,
    product=product_obj,
    order=order_obj
).save()
```

### Pattern 2: Mixed Required and Optional

```python
class Book(Model):
    id: int
    title: str
    # Required
    author: Annotated["Author", Relation()] = None  # type: ignore
    # Optional
    publisher: Annotated[Optional["Publisher"], Relation()] = None
    category: Annotated[Optional["Category"], Relation()] = None

# Only author is required
book = Book(
    id=1,
    title="Guide",
    author=author_obj,
    # publisher and category can be None
).save()
```

### Pattern 3: All Optional

```python
class User(Model):
    id: int
    name: str
    # All optional
    avatar: Annotated[Optional["Image"], Relation()] = None
    department: Annotated[Optional["Department"], Relation()] = None

# Can omit all relationships
user = User(id=1, name="Alice").save()
```

## Error Scenarios

### Scenario 1: Missing Required Relationship

```python
book = Book(id=1, title="Test", author=None)
book.save()

# ValueError: Required relationship 'author' cannot be None.
#             Please provide a Author instance.
```

### Scenario 2: Updating to None

```python
book = Book(id=1, title="Test", author=author_obj).save()

# Later...
book.author = None  # type: ignore
book.author_id = None  # type: ignore
book.save()

# ValueError: Required relationship 'author' cannot be None.
#             Please provide a Author instance.
```

### Scenario 3: Multiple Missing

```python
class Book(Model):
    id: int
    title: str
    author: Annotated["Author", Relation()] = None  # type: ignore
    publisher: Annotated["Publisher", Relation()] = None  # type: ignore

book = Book(id=1, title="Test", author=None, publisher=None)
book.save()

# ValueError: Required relationship 'author' cannot be None.
#             Please provide a Author instance.
# (Fails on first missing relationship)
```

## Comparison: Required vs Optional

| Aspect       | Required                          | Optional                                    |
| ------------ | --------------------------------- | ------------------------------------------- |
| Declaration  | `Annotated["Author", Relation()]` | `Annotated[Optional["Author"], Relation()]` |
| FK Type      | `int`                             | `Optional[int]`                             |
| DB Column    | `NOT NULL`                        | Nullable                                    |
| Can be None? | ❌ No                             | ✅ Yes                                      |
| Validation   | Fails if None                     | Allows None                                 |
| Use Case     | Must-have relationships           | Nice-to-have relationships                  |

## Design Rationale

### Why Validate at Python Level?

**Before:**

```python
book = Book(id=1, title="Test", author=None)
book.save()
# ✗ sqlite3.IntegrityError: NOT NULL constraint failed: book.author_id
# (Confusing database error)
```

**After:**

```python
book = Book(id=1, title="Test", author=None)
book.save()
# ✗ ValueError: Required relationship 'author' cannot be None.
#              Please provide a Author instance.
# (Clear Python error)
```

**Benefits:**

1. Earlier detection (Python vs database)
2. Clearer error messages
3. Better developer experience
4. Consistent with Pydantic's validation philosophy

### Why `= None` for Required Relationships?

This is a Python syntax requirement. Type annotations with no default value would require complex metaclass magic:

```python
# Ideal (doesn't work without metaclass magic)
author: Annotated["Author", Relation()]

# Current (requires default)
author: Annotated["Author", Relation()] = None  # type: ignore

# The database enforces the requirement via NOT NULL constraint
# Python validation provides early, clear feedback
```

The `# type: ignore` suppresses the type checker's complaint about assigning `None` to a non-Optional field.

## Testing

See `tests/test_required_relationships.py` for comprehensive test coverage:

- ✅ Required relationship with object works
- ✅ Required relationship with None raises ValueError
- ✅ Optional relationship with None works
- ✅ Error message includes field name and type
- ✅ Updating to None raises ValueError
- ✅ Multiple required relationships validated
- ✅ Mixed required and optional works
- ✅ One-to-many relationships not validated (they don't have FKs)

## Examples

See `examples/required_relationships_example.py` for complete working examples demonstrating:

1. Required relationships (success case)
2. Missing required relationships (error case)
3. Optional relationships (flexibility)
4. Mixed scenarios (real-world usage)

## Future Enhancements

Potential improvements for future versions:

1. **Custom Error Messages**

   ```python
   author: Annotated["Author", Relation(
       required_message="Every book needs an author!"
   )] = None  # type: ignore
   ```

2. **Validation at Initialization**

   ```python
   # Fail immediately when creating the object
   book = Book(id=1, title="Test", author=None)
   # ✗ ValueError: Required relationship 'author' cannot be None.
   ```

3. **Batch Validation**

   ```python
   # Report all missing required relationships at once
   book = Book(id=1, title="Test", author=None, publisher=None)
   book.save()
   # ✗ ValueError: Missing required relationships:
   #   - author (Author)
   #   - publisher (Publisher)
   ```

4. **Integration with Pydantic Validation**
   ```python
   # Use Pydantic validators for relationships
   book = Book(id=1, title="Test", author=None)
   # ✗ ValidationError: 1 validation error for Book
   #   author
   #     Field required
   ```

## Conclusion

Required relationship validation is a critical feature for building robust, maintainable applications with Pysmith. By validating at the Python level with clear error messages, it provides a superior developer experience while maintaining data integrity.

**Key Takeaways:**

- ✅ Use `Annotated["Model", Relation()]` for required relationships
- ✅ Use `Annotated[Optional["Model"], Relation()]` for optional relationships
- ✅ Validation happens before database operations
- ✅ Error messages are clear and actionable
- ✅ Database schema enforces constraints with NOT NULL
