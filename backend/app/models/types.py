"""Postgres/pgvector embedding column type.

Thin re-export kept as its own module so the Event model and any future
models have one place to import from, rather than reaching into
pgvector.sqlalchemy directly everywhere.
"""

from __future__ import annotations

from pgvector.sqlalchemy import Vector as EmbeddingType

__all__ = ["EmbeddingType"]