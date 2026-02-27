"""Tests for knowledge schema contracts and provider normalization."""

import uuid

import pytest
from pydantic import ValidationError

from second_brain.contracts.knowledge import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeEntity,
    KnowledgeRelationship,
    KnowledgeSource,
    GraphitiNodeType,
    GraphitiEdgeType,
)
from second_brain.services.supabase import SupabaseProvider
from second_brain.services.memory import MemoryService


# ---------------------------------------------------------------------------
# KnowledgeSource
# ---------------------------------------------------------------------------

def test_knowledge_source_defaults() -> None:
    src = KnowledgeSource(name="My Notion", origin="notion")
    assert src.origin == "notion"
    assert isinstance(src.id, uuid.UUID)
    assert src.config == {}


def test_knowledge_source_invalid_origin() -> None:
    with pytest.raises(ValidationError) as exc:
        KnowledgeSource(name="X", origin="twitter")  # type: ignore[arg-type]
    assert exc.value.errors()[0]["type"] == "literal_error"


# ---------------------------------------------------------------------------
# KnowledgeDocument
# ---------------------------------------------------------------------------

def test_knowledge_document_round_trip() -> None:
    doc = KnowledgeDocument(title="My Note", knowledge_type="note")
    dumped = doc.model_dump()
    restored = KnowledgeDocument(**dumped)
    assert restored.id == doc.id
    assert restored.knowledge_type == "note"
    assert restored.source_origin == "manual"


def test_knowledge_document_invalid_type() -> None:
    with pytest.raises(ValidationError) as exc:
        KnowledgeDocument(title="X", knowledge_type="unknown_type")  # type: ignore[arg-type]
    assert exc.value.errors()[0]["type"] == "literal_error"


# ---------------------------------------------------------------------------
# KnowledgeChunk
# ---------------------------------------------------------------------------

def test_knowledge_chunk_defaults() -> None:
    chunk = KnowledgeChunk(content="Hello world")
    assert chunk.chunk_index == 0
    assert chunk.knowledge_type == "document"
    assert chunk.source_origin == "manual"
    assert chunk.document_id is None


def test_knowledge_chunk_parent_ref() -> None:
    doc = KnowledgeDocument(title="Parent Doc", knowledge_type="playbook")
    chunk = KnowledgeChunk(content="Chunk 1", document_id=doc.id, knowledge_type="playbook")
    assert chunk.document_id == doc.id
    assert chunk.knowledge_type == "playbook"


def test_knowledge_chunk_invalid_chunk_index() -> None:
    with pytest.raises(ValidationError):
        KnowledgeChunk(content="X", chunk_index=-1)


def test_knowledge_chunk_all_knowledge_types() -> None:
    types = [
        "note", "document", "decision", "conversation",
        "task", "signal", "playbook", "case_study", "transcript",
    ]
    for kt in types:
        chunk = KnowledgeChunk(content="test", knowledge_type=kt)  # type: ignore[arg-type]
        assert chunk.knowledge_type == kt


# ---------------------------------------------------------------------------
# KnowledgeEntity
# ---------------------------------------------------------------------------

def test_knowledge_entity_instantiation() -> None:
    entity = KnowledgeEntity(name="Claude Code", entity_type="tool")
    assert entity.name == "Claude Code"
    assert entity.source_chunk_ids == []
    assert entity.description is None


# ---------------------------------------------------------------------------
# KnowledgeRelationship
# ---------------------------------------------------------------------------

def test_knowledge_relationship_all_types() -> None:
    types = ["topic_link", "provenance", "temporal", "entity_mention", "supports", "contradicts"]
    for rt in types:
        source_id = uuid.uuid4()
        target_id = uuid.uuid4()
        rel = KnowledgeRelationship(
            source_node_id=source_id,
            target_node_id=target_id,
            relationship_type=rt,  # type: ignore[arg-type]
        )
        assert rel.relationship_type == rt
        assert rel.weight == 1.0
        assert rel.valid_from is None
        assert rel.valid_to is None


def test_knowledge_relationship_invalid_type() -> None:
    with pytest.raises(ValidationError) as exc:
        KnowledgeRelationship(
            source_node_id=uuid.uuid4(),
            target_node_id=uuid.uuid4(),
            relationship_type="unknown",  # type: ignore[arg-type]
        )
    assert exc.value.errors()[0]["type"] == "literal_error"


def test_knowledge_relationship_weight_bounds() -> None:
    with pytest.raises(ValidationError):
        KnowledgeRelationship(
            source_node_id=uuid.uuid4(),
            target_node_id=uuid.uuid4(),
            relationship_type="supports",
            weight=1.5,
        )


# ---------------------------------------------------------------------------
# GraphitiNodeType / GraphitiEdgeType stubs
# ---------------------------------------------------------------------------

def test_graphiti_node_type_constants() -> None:
    assert GraphitiNodeType.CHUNK == "KnowledgeChunk"
    assert GraphitiNodeType.DOCUMENT == "KnowledgeDocument"
    assert GraphitiNodeType.ENTITY == "KnowledgeEntity"
    assert GraphitiNodeType.SOURCE == "KnowledgeSource"


def test_graphiti_edge_type_constants() -> None:
    assert GraphitiEdgeType.SUPPORTS == "SUPPORTS"
    assert GraphitiEdgeType.CONTRADICTS == "CONTRADICTS"
    assert GraphitiEdgeType.TOPIC_LINK == "TOPIC_LINK"


# ---------------------------------------------------------------------------
# SupabaseProvider._normalize_results — new column schema
# ---------------------------------------------------------------------------

def test_supabase_normalize_new_columns() -> None:
    provider = SupabaseProvider()
    rpc_results = [
        {
            "id": "abc-123",
            "content": "This is a playbook chunk",
            "similarity": 0.88,
            "knowledge_type": "playbook",
            "document_id": "doc-456",
            "chunk_index": 2,
            "source_origin": "notion",
            "metadata": {"extra": "value"},
        }
    ]
    results = provider._normalize_results(rpc_results, top_k=5)
    assert len(results) == 1
    r = results[0]
    assert r.id == "abc-123"
    assert r.content == "This is a playbook chunk"
    assert r.confidence == pytest.approx(0.88)
    assert r.metadata["knowledge_type"] == "playbook"
    assert r.metadata["document_id"] == "doc-456"
    assert r.metadata["chunk_index"] == 2
    assert r.metadata["source_origin"] == "notion"
    assert r.metadata["extra"] == "value"


def test_supabase_normalize_missing_optional_columns() -> None:
    """Should not crash when optional columns are absent — use safe defaults."""
    provider = SupabaseProvider()
    rpc_results = [
        {
            "id": "xyz",
            "content": "Minimal chunk",
            "similarity": 0.75,
        }
    ]
    results = provider._normalize_results(rpc_results, top_k=5)
    assert len(results) == 1
    r = results[0]
    assert r.content == "Minimal chunk"
    assert r.metadata["knowledge_type"] == "document"
    assert r.metadata["chunk_index"] == 0
    assert r.metadata["source_origin"] == "manual"


def test_supabase_normalize_empty() -> None:
    provider = SupabaseProvider()
    results = provider._normalize_results([], top_k=5)
    assert results == []


# ---------------------------------------------------------------------------
# MemoryService._normalize_mem0_results — knowledge metadata forwarding
# ---------------------------------------------------------------------------

def test_memory_normalize_mem0_forwards_knowledge_keys() -> None:
    service = MemoryService(provider="mem0")
    mem0_results = [
        {
            "id": "m1",
            "memory": "A note about Claude Code",
            "score": 0.91,
            "metadata": {
                "knowledge_type": "note",
                "document_id": "doc-abc",
                "chunk_index": 0,
                "source_origin": "manual",
            },
        }
    ]
    results = service._normalize_mem0_results(mem0_results, top_k=5, threshold=0.6)
    assert len(results) == 1
    r = results[0]
    assert r.content == "A note about Claude Code"
    assert r.metadata["knowledge_type"] == "note"
    assert r.metadata["document_id"] == "doc-abc"
    assert r.metadata["chunk_index"] == 0
    assert r.metadata["source_origin"] == "manual"


def test_memory_normalize_mem0_preserves_categories() -> None:
    service = MemoryService(provider="mem0")
    mem0_results = [
        {
            "id": "m-cats",
            "memory": "Categorized memory",
            "score": 0.77,
            "categories": ["project", "playbook", 10],
        }
    ]
    results = service._normalize_mem0_results(mem0_results, top_k=5, threshold=0.6)
    assert len(results) == 1
    assert results[0].metadata["categories"] == ["project", "playbook"]


def test_memory_normalize_mem0_empty_metadata() -> None:
    """Should not crash when Mem0 result has no metadata — knowledge keys absent is fine."""
    service = MemoryService(provider="mem0")
    mem0_results = [
        {
            "id": "m2",
            "memory": "Bare result",
            "score": 0.80,
        }
    ]
    results = service._normalize_mem0_results(mem0_results, top_k=5, threshold=0.6)
    assert len(results) == 1
    assert results[0].content == "Bare result"
    assert results[0].metadata.get("real_provider") is True


def test_knowledge_source_new_origins() -> None:
    """New source origins are accepted."""
    for origin in ("zoom", "json", "text", "leadworks"):
        src = KnowledgeSource(name=f"Test {origin}", origin=origin)
        assert src.origin == origin


def test_knowledge_chunk_new_origins() -> None:
    """KnowledgeChunk accepts new source_origin values."""
    for origin in ("zoom", "json", "text", "leadworks"):
        chunk = KnowledgeChunk(content="test", source_origin=origin)
        assert chunk.source_origin == origin


def test_knowledge_document_new_origins() -> None:
    """KnowledgeDocument accepts new source_origin values."""
    for origin in ("zoom", "json", "text", "leadworks"):
        doc = KnowledgeDocument(title="test", knowledge_type="document", source_origin=origin)
        assert doc.source_origin == origin


def test_knowledge_chunk_metadata_nested_dict() -> None:
    """KnowledgeChunk.metadata accepts nested dicts."""
    nested_meta = {
        "source_specific": {
            "zoom_meeting_id": "abc123",
            "participants": ["alice", "bob"],
            "nested": {"deep": {"value": 42}},
        },
        "tags": ["meeting", "q4"],
    }
    chunk = KnowledgeChunk(content="test", metadata=nested_meta)
    assert chunk.metadata["source_specific"]["zoom_meeting_id"] == "abc123"
    assert chunk.metadata["source_specific"]["nested"]["deep"]["value"] == 42


def test_knowledge_chunk_invalid_origin_still_rejected() -> None:
    """Invalid source_origin values are still rejected."""
    with pytest.raises(ValidationError):
        KnowledgeChunk(content="test", source_origin="twitter")  # type: ignore[arg-type]
