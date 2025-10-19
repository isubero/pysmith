"""
Session management for Pysmith models.

Provides Django-style hidden session management using contextvars
for thread-safe operation.
"""

from contextvars import ContextVar
from typing import Any, Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Thread-safe context variable for the current session
_current_session: ContextVar[Optional[Session]] = ContextVar(
    "pysmith_session", default=None
)

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker[Session]] = None
_base: Optional[type[DeclarativeBase]] = None


class SessionNotConfiguredError(Exception):
    """Raised when attempting to use database without configuration."""

    pass


def configure(
    database_url: str,
    base: type[DeclarativeBase],
    echo: bool = False,
    **engine_kwargs: Any,
) -> None:
    """
    Configure the database connection for Pysmith models.

    This should be called once at application startup.

    Args:
        database_url: SQLAlchemy database URL (e.g., 'sqlite:///app.db')
        base: SQLAlchemy DeclarativeBase class
        echo: Whether to echo SQL statements (default: False)
        **engine_kwargs: Additional arguments passed to create_engine

    Example:
        ```python
        from sqlalchemy.orm import DeclarativeBase
        from pysmith.db.session import configure

        class Base(DeclarativeBase):
            pass

        configure('sqlite:///myapp.db', Base)
        ```
    """
    global _engine, _session_factory, _base

    _engine = create_engine(database_url, echo=echo, **engine_kwargs)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    _base = base

    # Create all tables
    _base.metadata.create_all(_engine)


def get_engine() -> Engine:
    """Get the configured database engine."""
    if _engine is None:
        raise SessionNotConfiguredError(
            "Database not configured. Call configure() first."
        )
    return _engine


def get_base() -> type[DeclarativeBase]:
    """Get the configured DeclarativeBase."""
    if _base is None:
        raise SessionNotConfiguredError(
            "Database not configured. Call configure() first."
        )
    return _base


def get_session() -> Session:
    """
    Get the current session for the context.

    If no session exists in the current context, creates a new one.

    Returns:
        The current SQLAlchemy Session

    Raises:
        SessionNotConfiguredError: If database is not configured
    """
    if _session_factory is None:
        raise SessionNotConfiguredError(
            "Database not configured. Call configure() first."
        )

    session = _current_session.get()
    if session is None:
        session = _session_factory()
        _current_session.set(session)

    return session


def set_session(session: Session) -> None:
    """
    Manually set the current session for this context.

    Useful for testing or when you want explicit control.

    Args:
        session: The SQLAlchemy Session to use
    """
    _current_session.set(session)


def close_session() -> None:
    """Close the current session if one exists."""
    session = _current_session.get()
    if session is not None:
        try:
            session.rollback()  # Rollback any pending changes
        except Exception:
            pass
        session.close()
        _current_session.set(None)


class SessionContext:
    """
    Context manager for explicit session management.

    Example:
        ```python
        from pysmith.db.session import SessionContext

        with SessionContext() as session:
            user = User(name="Alice")
            user.save()
            # Session auto-commits on exit
        ```
    """

    def __init__(self, commit: bool = True):
        """
        Initialize session context.

        Args:
            commit: Whether to commit on successful exit (default: True)
        """
        self.commit = commit
        self.session: Optional[Session] = None
        self.previous_session: Optional[Session] = None

    def __enter__(self) -> Session:
        """Enter the context and create/get a session."""
        self.previous_session = _current_session.get()
        self.session = get_session()
        return self.session

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context and optionally commit."""
        if self.session is not None:
            if exc_type is None and self.commit:
                self.session.commit()
            elif exc_type is not None:
                self.session.rollback()

        # Restore previous session
        _current_session.set(self.previous_session)


def create_tables() -> None:
    """Create all tables defined in the configured Base."""
    if _base is None or _engine is None:
        raise SessionNotConfiguredError(
            "Database not configured. Call configure() first."
        )
    _base.metadata.create_all(_engine)


def drop_tables() -> None:
    """Drop all tables defined in the configured Base."""
    if _base is None or _engine is None:
        raise SessionNotConfiguredError(
            "Database not configured. Call configure() first."
        )
    _base.metadata.drop_all(_engine)
