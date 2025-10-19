"""
Example: Type-Safe Relationships with Annotated and Relation

Demonstrates Pysmith's relationship system using Python's Annotated type
for type-safe, Django-style relationship declarations with automatic
foreign key generation.
"""

from typing import Annotated, Optional

from sqlalchemy.orm import DeclarativeBase

from pysmith.db import configure
from pysmith.models import Model, Relation


# Setup database
class Base(DeclarativeBase):
    pass


configure("sqlite:///:memory:", Base, echo=False)


# ============================================================================
# Example 1: Many-to-One Relationship
# ============================================================================


class Author(Model):
    """Author model with one-to-many relationship to books."""

    id: int
    name: str
    email: str
    # One-to-many: one author has many books
    # No FK on this side (it's on the Book side)
    books: Annotated[list["Book"], Relation(back_populates="author")] = []


class Book(Model):
    """Book model with many-to-one relationship to author."""

    id: int
    title: str
    pages: int
    # Many-to-one: many books belong to one author
    # Pysmith auto-generates author_id foreign key!
    author: Annotated[Optional["Author"], Relation(back_populates="books")] = (
        None
    )


def example_many_to_one():
    """Demonstrate many-to-one relationship."""
    print("=" * 60)
    print("Example 1: Many-to-One Relationship (ORM-Style)")
    print("=" * 60)

    # Create and save author
    author = Author(id=1, name="Jane Doe", email="jane@example.com", books=[])
    author.save()
    print(f"✓ Saved author: {author.name}")

    # ORM-style: Pass the author object directly!
    book = Book(id=1, title="Python Mastery", pages=350, author=author)
    book.save()
    print(f"✓ Saved book: {book.title}")
    print(f"  author_id auto-extracted: {book.author_id}")  # type: ignore

    # Query back
    found_book = Book.find_by_id(1)
    if found_book:
        print(f"✓ Found book: {found_book.title}")
        print(f"  Foreign key: author_id = {found_book.author_id}")  # type: ignore

        # Manual join (for now)
        found_author = Author.find_by_id(found_book.author_id)  # type: ignore
        if found_author:
            print(f"  Author: {found_author.name}")

    print()


# ============================================================================
# Example 2: Optional vs Required Relationships
# ============================================================================


class Category(Model):
    """Product category."""

    id: int
    name: str
    description: str


class Product(Model):
    """Product with optional category."""

    id: int
    name: str
    price: float
    # Optional relationship - product can exist without category
    category: Annotated[Optional["Category"], Relation()] = None


class OrderItem(Model):
    """Order item with required product."""

    id: int
    quantity: int
    # Required relationship - every item MUST have a product
    # Note: Annotated without Optional means required
    product: Annotated["Product", Relation()] = None  # type: ignore


def example_optional_vs_required():
    """Demonstrate optional vs required relationships."""
    print("=" * 60)
    print("Example 2: Optional vs Required Relationships")
    print("=" * 60)

    # Product without category (optional)
    product1 = Product(id=1, name="Widget", price=19.99, category=None)
    product1.save()
    print(f"✓ Saved product without category: {product1.name}")

    # Product with category - ORM-style!
    category = Category(
        id=1, name="Electronics", description="Electronic items"
    )
    category.save()

    product2 = Product(id=2, name="Gadget", price=29.99, category=category)
    product2.save()
    print(f"✓ Saved product with category: {product2.name}")
    print(f"  category_id auto-set: {product2.category_id}")  # type: ignore

    # Order item with required product - ORM-style!
    order_item = OrderItem(id=1, quantity=2, product=product1)
    order_item.save()
    print(f"✓ Saved order item (quantity: {order_item.quantity})")
    print(f"  product_id auto-set: {order_item.product_id}")  # type: ignore

    print()


# ============================================================================
# Example 3: Multiple Relationships on Same Model
# ============================================================================


class User(Model):
    """User model."""

    id: int
    username: str
    email: str


class BlogPost(Model):
    """Blog post with multiple relationships."""

    id: int
    title: str
    content: str
    # Multiple relationships on one model
    author: Annotated[Optional["User"], Relation()] = None
    editor: Annotated[Optional["User"], Relation()] = None


def example_multiple_relationships():
    """Demonstrate multiple relationships on one model."""
    print("=" * 60)
    print("Example 3: Multiple Relationships (ORM-Style)")
    print("=" * 60)

    # Create users
    author = User(id=1, username="alice", email="alice@example.com")
    author.save()

    editor = User(id=2, username="bob", email="bob@example.com")
    editor.save()

    # ORM-style: Pass objects directly - FKs auto-extracted!
    post = BlogPost(
        id=1,
        title="My Blog Post",
        content="Content here...",
        author=author,
        editor=editor,
    )
    post.save()

    print(f"✓ Saved post: {post.title}")
    print(f"  author_id auto-set: {post.author_id}")  # type: ignore
    print(f"  editor_id auto-set: {post.editor_id}")  # type: ignore

    print()


# ============================================================================
# Example 4: Type Safety Benefits
# ============================================================================


def example_type_safety():
    """Demonstrate type safety with relationships."""
    print("=" * 60)
    print("Example 4: Type Safety with ORM-Style Relationships")
    print("=" * 60)

    # Create author
    author = Author(id=5, name="Type Safe", email="safe@example.com", books=[])
    author.save()

    # ORM-style: Type-safe object assignment
    book = Book(id=10, title="Type-Safe Book", pages=200, author=author)
    print(f"✓ Type-safe object assignment: {book.title}")
    print(f"  author_id auto-extracted: {book.author_id}")  # type: ignore

    # IDE knows:
    # - book.title is str
    # - book.pages is int
    # - book.author is Optional[Author] (relationship object)
    # - book.author_id is Optional[int] (auto-generated FK)

    # Type checker would catch:
    # book.author = "not an Author"  # ❌ Type error!
    # book.title = 123  # ❌ Type error!

    print("✓ Full type safety maintained!")
    print("  IDE provides autocomplete for all fields")
    print("  Type checker catches errors before runtime")
    print("  Pass objects directly - FKs extracted automatically!")

    print()


# ============================================================================
# Key Benefits Summary
# ============================================================================


def print_benefits():
    """Print the key benefits of this approach."""
    print("=" * 60)
    print("Key Benefits of Annotated + Relation")
    print("=" * 60)
    print()
    print("✅ Type-Safe")
    print("   - author: Annotated[Optional[Author], Relation()]")
    print("   - IDE knows the types at every step")
    print()
    print("✅ ORM-Style Object Assignment")
    print("   - Pass objects directly: Book(author=author_obj)")
    print("   - FKs extracted automatically!")
    print()
    print("✅ Auto Foreign Keys")
    print("   - Declare 'author' relationship")
    print("   - Get 'author_id' field automatically")
    print("   - No manual ID extraction needed")
    print()
    print("✅ Django-Style Simplicity")
    print("   - book = Book(title='Book', author=author)")
    print("   - book.save()  # Just works!")
    print()
    print("✅ Pydantic Compatible")
    print("   - Validation still works")
    print("   - Relationship fields excluded from validation")
    print()
    print("✅ SQLAlchemy Power")
    print("   - Generated models use proper FK constraints")
    print("   - Standard SQL schema")
    print()
    print("✅ Fully Declarative")
    print("   - Define relationships with type hints")
    print("   - Use objects naturally")
    print("   - No boilerplate!")
    print()
    print("=" * 60)


if __name__ == "__main__":
    example_many_to_one()
    example_optional_vs_required()
    example_multiple_relationships()
    example_type_safety()
    print_benefits()
