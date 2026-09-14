"""Persistence abstraction."""

from app.store.base import Store
from app.store.sqlalchemy_store import SqlAlchemyStore

__all__ = ["Store", "SqlAlchemyStore"]
