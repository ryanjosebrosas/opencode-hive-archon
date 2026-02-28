"""Canonical knowledge schema contracts for all providers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Type aliases — closed sets enforced at model level
# ---------------------------------------------------------------------------

KnowledgeTypeValue = Literal[
    "note",
    "document",
    "decision",
    "conversation",
    "task",
    "signal",
    "playbook",
    "case_study",
    "transcript",
]

ChunkStatusValue = Literal["active", "superseded", "archived", "deleted"]

RelationshipTypeValue = Literal[
    "topic_link",
    "provenance",
    "temporal",
    "entity_mention",
    "supports",
    "contradicts",
]

SourceOriginValue = Literal[
    "notion",
    "obsidian",
    "email",
    "manual",
    "youtube",
    "web",
    "other",
    "zoom",
    "json",
    "text",
    "leadworks",
]


# ---------------------------------------------------------------------------
# Graphiti node/edge type stubs — pure string constants, no SDK dependency
# ---------------------------------------------------------------------------

class GraphitiNodeType:
    """Node type constants for Graphiti graph provider (stub — no SDK dep)."""
    CHUNK = "KnowledgeChunk"
    DOCUMENT = "KnowledgeDocument"
    ENTITY = "KnowledgeEntity"
    SOURCE = "KnowledgeSource"


class GraphitiEdgeType:
    """Edge type constants for Graphiti graph provider (stub — no SDK dep)."""
    TOPIC_LINK = "TOPIC_LINK"
    PROVENANCE = "PROVENANCE"
    TEMPORAL = "TEMPORAL"
    ENTITY_MENTION = "ENTITY_MENTION"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"


# ---------------------------------------------------------------------------
# Core knowledge models
# ---------------------------------------------------------------------------

class KnowledgeSource(BaseModel):
    """Integration origin — where content came from."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    origin: SourceOriginValue
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeDocument(BaseModel):
    """Parent container for knowledge chunks."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    knowledge_type: KnowledgeTypeValue
    source_id: uuid.UUID | None = None
    source_url: str | None = None
    source_origin: SourceOriginValue = "manual"
    author: str | None = None
    raw_content: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeChunk(BaseModel):
    """
    Base retrieval unit — chunk of a document stored with an embedding.

    This is the atomic unit stored in Supabase knowledge_chunks table
    and the primary retrieval target for semantic search.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    document_id: uuid.UUID | None = None
    content: str
    knowledge_type: KnowledgeTypeValue = "document"
    chunk_index: int = Field(default=0, ge=0)
    source_origin: SourceOriginValue = "manual"
    content_hash: str | None = None
    status: ChunkStatusValue = "active"
    # embedding is not stored on the model — it lives in the DB column
    # and is produced by VoyageRerankService.embed() at ingestion time
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeEntity(BaseModel):
    """
    Named concept, person, tool, or organisation — graph node.

    Extracted from chunks during ingestion. Used by Graphiti provider
    and for entity-based retrieval filtering.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    entity_type: str  # open-ended: "person", "tool", "concept", "org", etc.
    description: str | None = None
    source_chunk_ids: list[uuid.UUID] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeRelationship(BaseModel):
    """
    Typed edge between two knowledge nodes.

    Supports bi-temporal tracking via valid_from / valid_to
    (aligned with Graphiti's temporal edge model).
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_node_id: uuid.UUID
    target_node_id: uuid.UUID
    relationship_type: RelationshipTypeValue
    weight: float = Field(default=1.0, ge=0.0, le=1.0)
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
