# Type Safety Improvements

## Overview

The `save()` method now returns `Self` instead of `Model`, providing full type safety and IDE autocomplete support.

## What Changed

### Before (Type-Unsafe)

```python
def save(self) -> "Model":
    # ... implementation
    return self
```

**Problem**: Type checkers couldn't infer the actual type

```python
user = User(id=1, username="alice", email="alice@example.com")
saved = user.save()  # Type: Model (not User!)
saved.username  # ❌ Type checker doesn't know this exists
```

### After (Type-Safe) ✅

```python
from typing import Self

def save(self) -> Self:
    # ... implementation
    return self
```

**Benefit**: Type checkers know the exact return type

```python
user = User(id=1, username="alice", email="alice@example.com")
saved = user.save()  # Type: User ✓
saved.username  # ✅ Type checker knows this exists!
saved.email     # ✅ Full autocomplete support!
```

## Benefits

### 1. IDE Autocomplete

Your IDE now provides intelligent autocomplete after `save()`:

```python
user = User(id=1, username="alice", email="alice@example.com").save()
user.  # IDE shows: id, username, email, age, save(), delete(), etc.
```

### 2. Type Checking

mypy and other type checkers catch errors at development time:

```python
product = Product(id=1, name="Widget", price=19.99, stock=100).save()
product.username  # ❌ Type error: Product has no attribute 'username'
```

### 3. Method Chaining

Type safety is preserved through method chaining:

```python
# Type: User
user = User(id=1, username="alice", email="alice@example.com").save()

# Type: Product
product = Product(id=1, name="Widget", price=19.99, stock=100).save()
```

### 4. Refactoring Safety

When you rename or change model fields, type checkers will flag all usage locations:

```python
class User(Model):
    id: int
    username: str
    email_address: str  # Renamed from 'email'

# Type checker will flag this:
user = User.find_by_id(1)
print(user.email)  # ❌ Error: User has no attribute 'email'
print(user.email_address)  # ✅ Correct!
```

## Examples

### Basic Usage

```python
from pysmith.models import Model
from typing import Optional

class User(Model):
    id: int
    username: str
    email: str
    age: Optional[int]

# Create and save - full type safety
user = User(id=1, username="alice", email="alice@example.com", age=30).save()

# Type: User (not Model!)
assert isinstance(user.username, str)  # ✅ Type-safe
assert isinstance(user.age, int | None)  # ✅ Type-safe
```

### Different Model Types

```python
class Product(Model):
    id: int
    name: str
    price: float

# Each type is correctly inferred
user = User(id=1, username="bob", email="bob@example.com", age=25).save()
product = Product(id=1, name="Widget", price=19.99).save()

# Type checker knows the difference
user.username     # ✅ OK - User has username
product.price     # ✅ OK - Product has price
user.price        # ❌ Error - User doesn't have price
product.username  # ❌ Error - Product doesn't have username
```

### Find Methods

Type safety extends to query methods too:

```python
# Type: Optional[User]
found_user = User.find_by_id(1)

if found_user:
    # Type checker knows this is User
    print(found_user.username)  # ✅ Type-safe

# Type: list[User]
all_users = User.find_all()

for user in all_users:
    # Type checker knows each item is User
    print(f"{user.username}: {user.email}")  # ✅ Type-safe
```

## Implementation Details

### Using Python's `Self` Type

The `Self` type was introduced in Python 3.11 and is available in the standard `typing` module:

```python
from typing import Self

class Model:
    def save(self) -> Self:
        # Returns the same type as the instance
        return self
```

This tells type checkers: "This method returns an instance of the same class it was called on."

### Benefits Over TypeVar

While we could use a `TypeVar`, `Self` is more concise and clear:

```python
# Old approach (verbose)
from typing import TypeVar
T = TypeVar("T", bound="Model")

def save(self: T) -> T:
    return self

# New approach (clean)
from typing import Self

def save(self) -> Self:
    return self
```

## Testing

All 61 tests pass, including specific type safety verification:

```bash
$ uv run pytest -v
============================= 61 passed =============================

$ uv run mypy examples/type_safety_example.py
Success: no issues found in 1 source file
```

## Compatibility

- **Python Version**: Requires Python 3.11+ (for `Self` type)
- **Pysmith Requirement**: Python 3.12.3+ (already compatible)
- **Type Checkers**: Works with mypy, pyright, and other standard type checkers

## Migration

No migration needed! This is a **backward-compatible** change:

- Existing code works without changes
- No runtime behavior changes
- Type checking is optional (but recommended)

## Summary

| Aspect           | Before             | After                     |
| ---------------- | ------------------ | ------------------------- |
| Return Type      | `Model`            | `Self`                    |
| IDE Autocomplete | ❌ Limited         | ✅ Full support           |
| Type Checking    | ❌ Not type-safe   | ✅ Fully type-safe        |
| Method Chaining  | ⚠️ Loses type info | ✅ Preserves type         |
| Refactoring      | ⚠️ Manual search   | ✅ Caught by type checker |

**Result**: Better developer experience, fewer bugs, safer refactoring! 🎉
