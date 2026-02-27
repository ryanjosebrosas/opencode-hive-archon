# Structured Plan Template

> Use this template when creating a feature plan (Layer 2 of the PIV Loop).
> Save to `requests/{feature}-plan.md` and fill in every section.
>
> **Target Length**: The completed plan should be **700-1000 lines**. You have failed
> if the plan is under 700 lines. Complex or comprehensive features should target 1000.
> Every section must contain feature-specific content — not generic placeholders.
> Reference guides, code snippets, and file:line citations are context, not filler.
>
> **Core Principle**: This template is the control mechanism. The `/planning` command's
> 6 phases exist to fill these sections systematically. Nothing is missed because
> the template specifies exactly what's needed.
>
> **For the execution agent**: Validate documentation and codebase patterns before
> implementing. Pay special attention to naming of existing utils, types, and models.
> Import from the right files.
>
> **When to use this template vs. Master + Sub-Plan:**
> - **This template** (single plan): Features with <10 tasks that fit in one 700-1000 line plan
> - **Master + Sub-Plan**: Complex features with 10+ tasks or multiple distinct phases
>   - Use `MASTER-PLAN-TEMPLATE.md` for the overview (~500 lines)
>   - Use `SUB-PLAN-TEMPLATE.md` for each phase (700-1000 lines each)
>   - `/planning` auto-detects which approach to use based on task count

---

# Feature: P1-05 Flexible Metadata Schema

## Feature Description

This feature extends the SourceOriginValue type to include four new values: "zoom", "json", "text", and "leadworks". This enables the knowledge system to properly categorize content from these sources. Additionally, the implementation ensures that KnowledgeChunk.metadata can accept arbitrary source-specific data in dict[str, Any] format, which is already functional but needs verification and testing.

## User Story

As a user of the Second Brain system, I want to be able to ingest content from Zoom meetings, JSON files, plain text files, and LeadWorks, while maintaining proper metadata tracking for each source type, so that I can effectively organize and retrieve information from these diverse sources.

## Problem Statement

The current system only supports 7 specific source origin types: "notion", "obsidian", "email", "manual", "youtube", "web", "other". This limitation prevents proper categorization of content from newer sources like Zoom meetings, JSON files, text files, and Leadworks. Additionally, while the KnowledgeChunk.metadata field is already typed as dict[str, Any] allowing arbitrary data, there has been no explicit verification that nested dictionaries work properly and that existing test coverage adequately validates the new source types.

## Solution Statement

This implementation will extend the existing SourceOriginValue literal type and ensure consistency across all three code locations where this set is defined. We'll also enhance test coverage to verify that nested metadata dictionaries work correctly and that existing functionality remains intact.

- Decision 1: Keep the type as Literal["..."] instead of enum — because the Pydantic/Python type system handles Literals better and they're easier to maintain with dynamic checking
- Decision 2: Create a migration file (002_extend_source_origin.sql) — because the existing database constraints need to be updated to accept the new source origin values
- Decision 3: Deduplicate the source origin values in supabase.py by importing from the main definition — because maintaining consistency across multiple files reduces risk of bugs and inconsistencies
- Decision 4: Enhance metadata testing to include nested dictionaries — because explicit verification ensures the feature works as expected

## Feature Metadata

- **Feature Type**: Enhancement / Refactor
- **Estimated Complexity**: Medium
- **Primary Systems Affected**: contracts/knowledge.py, services/supabase.py, backend/migrations/, tests/test_knowledge_schema.py
- **Dependencies**: No new dependencies required

### Slice Guardrails (Required)

- **Single Outcome**: KnowledgeChunk instances can be created with source_origin set to "zoom", "json", "text", or "leadworks" and metadata supports arbitrary key-value pairs including nested dicts
- **Expected Files Touched**: contracts/knowledge.py, services/supabase.py, backend/migrations/002_extend_source_origin.sql, tests/test_knowledge_schema.py
- **Scope Boundary**: This slice intentionally does NOT modify ingestion pipeline behavior, MCP server, memory service, planner, or recall agent
- **Split Trigger**: When additional database tables or complex business logic is needed beyond simple schema extension

---

## CONTEXT REFERENCES

### Relevant Codebase Files

> IMPORTANT: The execution agent MUST read these files before implementing!

- `backend/src/second_brain/contracts/knowledge.py` (lines 37-119) — Why: Contains the SourceOriginValue type and KnowledgeChunk model structure that needs extension
- `backend/src/second_brain/services/supabase.py` (lines 23-31) — Why: Contains duplicated source origin values set that needs synchronization
- `backend/migrations/001_knowledge_schema.sql` (lines 71-73) — Why: Database constraint to reference when creating the new migration
- `tests/test_knowledge_schema.py` — Why: Test pattern example to extend with new source origin tests

### New Files to Create

- `backend/migrations/002_extend_source_origin.sql` — SQL migration to update the database constraints with new source origin values

### Related Memories (from memory.md)

> Past experiences and lessons relevant to this feature. Populated by `/planning` from memory.md.

- No relevant memories found in memory.md

### Relevant Documentation

> The execution agent SHOULD read these before implementing.

- [Pydantic Literal Types Documentation](https://docs.pydantic.dev/latest/concepts/types/#literal)
  - Specific section: Literal Types
  - Why: required for understanding how to properly extend literal types
- [PostgreSQL CHECK Constraints Documentation](https://www.postgresql.org/docs/current/ddl-constraints.html)
  - Specific section: CHECK Constraints
  - Why: showing recommended approach for constraint modification in migrations

### Patterns to Follow

> Specific patterns extracted from the codebase — include actual code examples from the project.

**SourceOriginValue Pattern** (from `backend/src/second_brain/contracts/knowledge.py:37-45`):
```
SourceOriginValue = Literal[
    "notion", "obsidian", "email", "manual", "youtube", "web", "other",
]
```
- Why this pattern: Defines a literal union of allowed values for type safety
- Common gotchas: Values need to stay synchronized across multiple files (contract, python set, sql constraint)

**KnowledgeChunk Pattern** (from `backend/src/second_brain/contracts/knowledge.py:101-119`):
```
class KnowledgeChunk(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    document_id: uuid.UUID | None = None
    content: str
    knowledge_type: KnowledgeTypeValue = "document"
    chunk_index: int = Field(default=0, ge=0)
    source_origin: SourceOriginValue = "manual"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```
- Why this pattern: Shows the correct structure and field types to maintain
- Common gotchas: Using default_factory for mutable defaults

**Supabase Service Pattern** (from `backend/src/second_brain/services/supabase.py:23-31`):
```
_VALID_SOURCE_ORIGINS: set[str] = {
    "notion", "obsidian", "email", "manual", "youtube", "web", "other",
}
```
- Why this pattern: Contains duplicated set of valid sources that needs synchronization
- Common gotchas: This duplicates the contract value causing maintenance burden

**Database Migration Pattern** (from `backend/migrations/001_knowledge_schema.sql:71-73`):
```
CONSTRAINT knowledge_source_valid_origin CHECK (
    source_origin IN ('notion', 'obsidian', 'email', 'manual', 'youtube', 'web', 'other')
)
```
- Why this pattern: Shows how source origin constraints are defined in SQL
- Common gotchas: Changing these requires careful constraint management to prevent data loss

**Test Pattern** (from `tests/test_knowledge_schema.py:32`):
```
def test_knowledge_source_invalid_origin():
    with pytest.raises(ValueError):
        KnowledgeChunk(
            content="test chunk",
            source_origin="invalid_origin",  # Should raise ValueError
        )
```
- Why this pattern: Shows how to test for validation errors with invalid input
- Common gotchas: Need to test both valid and invalid values for coverage

**Migration File Pattern** (from `backend/migrations/001_knowledge_schema.sql`):
```
-- Second Brain Knowledge Schema Initial Creation
-- Migration: 001_knowledge_schema.sql
-- Author: Second Brain Team
-- Date: 2024-08-01

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS knowledge_sources (
    -- table definition
);
```
- Why this pattern: Shows the header format and structure of migration files
- Common gotchas: Migration files should be self-contained and idempotent where possible

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation

First, create the new database migration file to update the CHECK constraint with our new source origin values. This creates the necessary database-level changes that allow the application to store values without database errors.

**Tasks:**
- Create SQL migration file to update the source origin constraints in the database
- Verify the migration works against existing data structures

### Phase 2: Core Implementation

Update the Python type definitions to include the new source origin values. This involves modifying the literal type in the contracts folder and synchronizing it with the service layer to prevent inconsistencies.

**Tasks:**
- Update the SourceOriginValue literal definition
- Update the duplicate set in supabase service to import from the main definition
- Verify that both changes work together without conflicts

### Phase 3: Integration

Enhance test coverage to verify the new functionality works as expected, including both positive cases (valid new values) and negative cases (still rejecting invalid values).

**Tasks:**
- Add test cases for the new source origin values
- Create tests that verify nested dictionaries work in metadata
- Expand edge case coverage to ensure robustness

### Phase 4: Testing & Validation

Execute the full test suite including linting, type checking, and all tests to ensure that no regressions were introduced and the functionality works end-to-end.

**Tasks:**
- Execute validation commands (linting, type checking)
- Run all tests to ensure nothing is broken
- Verify migrations can apply successfully

---

## STEP-BY-STEP TASKS

> Execute every task in order, top to bottom. Each task is atomic and independently testable.
>
> **Action keywords**: CREATE (new files), UPDATE (modify existing), ADD (insert new functionality),
> REMOVE (delete deprecated code), REFACTOR (restructure without changing behavior), MIRROR (copy pattern from elsewhere)
>
> **Tip**: For text-centric changes (templates, commands, configs), include exact **Current** / **Replace with**
> content blocks in IMPLEMENT. This eliminates ambiguity and achieves higher plan-to-implementation fidelity
> than prose descriptions. See `reference/piv-loop-practice.md` Section 3 for guidance.

### CREATE backend/migrations/002_extend_source_origin.sql

- **IMPLEMENT**: Create SQL migration file that drops the existing CHECK constraint and recreates it with the new source origin values. This ensures the database will accept the new values without violating the constraint.
- **PATTERN**: Database migration pattern from 001_knowledge_schema.sql
- **IMPORTS**: No imports needed
- **GOTCHA**: Need to handle all three tables that have the source_origin constraint: knowledge_sources, knowledge_documents, and knowledge_chunks
- **VALIDATE**: `sql -f backend/migrations/002_extend_source_origin.sql` or similar SQL command depending on database setup

```sql
-- Second Brain Knowledge Schema - Extend Source Origin Values
-- Migration: 002_extend_source_origin.sql
-- Author: Second Brain Team
-- Date: CURRENT_DATE

-- Update constraints across all three tables to include new source origin values
ALTER TABLE knowledge_chunks 
DROP CONSTRAINT IF EXISTS knowledge_chunk_valid_origin,
ADD CONSTRAINT knowledge_chunk_valid_origin CHECK (
    source_origin IN (
        'notion', 'obsidian', 'email', 'manual', 'youtube', 'web', 'other',
        'zoom', 'json', 'text', 'leadworks'
    )
);

ALTER TABLE knowledge_documents 
DROP CONSTRAINT IF EXISTS knowledge_document_valid_origin,
ADD CONSTRAINT knowledge_document_valid_origin CHECK (
    source_origin IN (
        'notion', 'obsidian', 'email', 'manual', 'youtube', 'web', 'other',
        'zoom', 'json', 'text', 'leadworks'
    )
);

ALTER TABLE knowledge_sources 
DROP CONSTRAINT IF EXISTS knowledge_source_valid_origin,
ADD CONSTRAINT knowledge_source_valid_origin CHECK (
    source_origin IN (
        'notion', 'obsidian', 'email', 'manual', 'youtube', 'web', 'other',
        'zoom', 'json', 'text', 'leadworks'
    )
);
```

### UPDATE backend/src/second_brain/contracts/knowledge.py

- **IMPLEMENT**: Add the 4 new values to the SourceOriginValue Literal type. Change from "notion", "obsidian", "email", "manual", "youtube", "web", "other" to include "zoom", "json", "text", "leadworks".
- **PATTERN**: Same syntax as existing literal definition
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Ensure all values are properly formatted as lowercase strings with correct spacing/comma placement
- **VALIDATE**: `python -c "from second_brain.contracts.knowledge import SourceOriginValue; print(SourceOriginValue)"` 

Current:
```python
SourceOriginValue = Literal[
    "notion", "obsidian", "email", "manual", "youtube", "web", "other",
]
```

Replace with:
```python
SourceOriginValue = Literal[
    "notion", "obsidian", "email", "manual", "youtube", "web", "other",
    "zoom", "json", "text", "leadworks",
]
```

### UPDATE backend/src/second_brain/services/supabase.py

- **IMPLEMENT**: Update the _VALID_SOURCE_ORIGINS set to be dynamically derived from the SourceOriginValue literal type instead of maintaining a hardcoded duplicate. This ensures consistent values between validation and type definition.
- **PATTERN**: Use typing.get_args pattern to extract values from literal types
- **IMPORTS**: 
```python
from second_brain.contracts.knowledge import SourceOriginValue
from typing import get_args
```
- **GOTCHA**: Need to convert tuple returned by get_args to set for the existing code that assumes it's a set
- **VALIDATE**: `python -c "from second_brain.services.supabase import SupabaseKnowledgeDatabaseProvider; p = SupabaseKnowledgeDatabaseProvider(); print(p._VALID_SOURCE_ORIGINS)"`

Current:
```python
_VALID_SOURCE_ORIGINS: set[str] = {
    "notion", "obsidian", "email", "manual", "youtube", "web", "other",
}
```

Replace with:
```python
_VALID_SOURCE_ORIGINS: set[str] = set(get_args(SourceOriginValue))
```

### UPDATE tests/test_knowledge_schema.py

- **IMPLEMENT**: Add new test cases to verify that the new source origin values are accepted, while still ensuring invalid values are rejected. Also add a test to specifically verify that nested metadata dictionaries work.
- **PATTERN**: Follow the same structure as existing tests in the file
- **IMPORTS**: No additional imports needed
- **GOTCHA**: Must include both positive tests (accepting new values) and negative tests (rejecting invalid values)
- **VALIDATE**: `pytest tests/test_knowledge_schema.py`

#### Add test for new valid source origins:
Current: Tests covering existing 7 source origins ("notion", "obsidian", "email", "manual", "youtube", "web", "other")

Replace with additional test cases:
```python
def test_knowledge_chunk_with_new_source_origins():
    """Test that KnowledgeChunk accepts the new source origin values."""
    # Test zoom source origin
    chunk_zoom = KnowledgeChunk(content="Meeting notes", source_origin="zoom")
    assert chunk_zoom.source_origin == "zoom"
    
    # Test json source origin
    chunk_json = KnowledgeChunk(content='{"key": "value"}', source_origin="json")
    assert chunk_json.source_origin == "json"
    
    # Test text source origin 
    chunk_text = KnowledgeChunk(content="Plain text content", source_origin="text")
    assert chunk_text.source_origin == "text"
    
    # Test leadworks source origin
    chunk_leadworks = KnowledgeChunk(content="Lead tracking info", source_origin="leadworks")
    assert chunk_leadworks.source_origin == "leadworks"
    
    # Confirm all values are valid by trying to build a chunk with each
    all_valid_values = [
        "notion", "obsidian", "email", "manual", "youtube", "web", "other",
        "zoom", "json", "text", "leadworks"
    ]
    for value in all_valid_values:
        chunk = KnowledgeChunk(content=f"Content from {value}", source_origin=value)
        assert chunk.source_origin == value
```

#### Add test for nested metadata:
```python
def test_knowledge_chunk_metadata_nested_dicts():
    """Test that KnowledgeChunk.metadata accepts nested dictionaries."""
    nested_metadata = {
        "meeting_data": {
            "participants": ["Alice", "Bob"],
            "duration": 45,
            "topics": ["project update", "requirements"],
            "recording_available": True
        },
        "transcript_data": {
            "quality_score": 0.92,
            "language": "en",
            "word_count": 286,
            "sentiment_analysis": {
                "overall": "positive",
                "breakdown": {
                    "negative": 0.1,
                    "neutral": 0.3,
                    "positive": 0.6
                }
            }
        },
        "source_details": {
            "filename": "meeting_2024_01_15.txt",
            "import_date": "2024-01-16T14:30:00Z",
            "processed": True
        }
    }
    
    chunk = KnowledgeChunk(
        content="Sample meeting transcript", 
        source_origin="zoom",
        metadata=nested_metadata
    )
    
    assert isinstance(chunk.metadata, dict)
    assert chunk.metadata["meeting_data"]["participants"] == ["Alice", "Bob"]
    assert chunk.metadata["transcript_data"]["sentiment_analysis"]["overall"] == "positive"
    assert chunk.metadata["source_details"]["import_date"] == "2024-01-16T14:30:00Z"
```

### VERIFY backward compatibility in tests/test_knowledge_schema.py

- **IMPLEMENT**: Ensure the existing test_knowledge_source_invalid_origin still passes and rejects values that weren't added to the new list
- **PATTERN**: Same as existing test pattern
- **IMPORTS**: No additional imports needed
- **GOTCHA**: The test should still fail for "twitter" as before, confirming the validation mechanism still works
- **VALIDATE**: `pytest tests/test_knowledge_schema.py::test_knowledge_source_invalid_origin`

Current test_knowledge_source_invalid_origin should remain unchanged and still pass:
```python
def test_knowledge_source_invalid_origin():
    with pytest.raises(ValueError):
        KnowledgeChunk(
            content="test chunk",
            source_origin="invalid_origin",  # Should raise ValueError
        )
```

Should still raise ValueError for unknown values such as "twitter", "gmail", etc.

---

## TESTING STRATEGY

### Unit Tests

Following the existing pattern in `tests/test_knowledge_schema.py`, add new test functions to verify:
1. New source origin values are accepted by KnowledgeChunk constructor
2. Existing restrictions still apply (invalid values are rejected)
3. Nested dictionary metadata works as expected
4. The combination of new source origin with nested metadata works

All tests should adhere to the standard pytest framework already in place and use identical assertion patterns. Each new test should be isolated and independent, focusing on a single aspect of the functionality.

### Integration Tests

The feature doesn't have direct database-level integration requirements beyond the schema validation that already exists. However, the new migration file should be tested against a test database to ensure it applies correctly without affecting existing data or functionality.

### Edge Cases

- Edge case 1: New source origins used with complex nested metadata — what if very deeply nested structures or complex data types are used?
- Edge case 2: Mixed legacy and new source origins in the same dataset — database queries shouldn't treat them differently
- Edge case 3: Very large nested metadata dictionaries — size limitations should be handled gracefully without system issues
- Edge case 4: Empty metadata dictionaries combined with new sources — should work the same as before

---

## VALIDATION COMMANDS

> Execute every command to ensure zero regressions and 100% feature correctness.
> Full validation depth is required for every slice; one proof signal is not enough.

### Level 1: Syntax & Style
```
ruff check .
black --check .
```

### Level 2: Type Safety
```
mypy backend/src/second_brain/
```

### Level 3: Unit Tests
```
pytest tests/test_knowledge_schema.py -v
```

### Level 4: Integration Tests
```
pytest tests/test_supabase_provider.py -v
pytest -k "knowledge" --maxfail=5
```

### Level 5: Manual Validation

Create new KnowledgeChunk instances with the newly added source origin values:
```python
from second_brain.contracts.knowledge import KnowledgeChunk

# Test each new source origin
for origin in ["zoom", "json", "text", "leadworks"]:
    chunk = KnowledgeChunk(
        content=f"Content from {origin}",
        source_origin=origin
    )
    print(f"Created chunk with source_origin '{origin}': {chunk.source_origin}")

# Test nested metadata
nested_data = {"level1": {"level2": {"level3": "deep"}}}
chunk_with_meta = KnowledgeChunk(
    content="Hierarchical data example",
    source_origin="zoom",
    metadata=nested_data
)
print(f"Nested metadata preserved: {chunk_with_meta.metadata['level1']['level2']['level3']}")
```

### Level 6: Additional Validation (Optional)

Verify that the supabase service correctly validates against the dynamically sourced origin values:
```python
from second_brain.services.supabase import SupabaseKnowledgeDatabaseProvider
provider = SupabaseKnowledgeDatabaseProvider()
print(f"Valid source origins dynamically imported: {provider._VALID_SOURCE_ORIGINS}")
```

---

## ACCEPTANCE CRITERIA

> Split into **Implementation** (verifiable during `/execute`) and **Runtime** (verifiable
> only after running the code). Check off Implementation items during execution.
> Leave Runtime items for manual testing or post-deployment verification.

### Implementation (verify during execution)

- [ ] KnowledgeChunk instances create successfully with source_origin="zoom"
- [ ] KnowledgeChunk instances create successfully with source_origin="json" 
- [ ] KnowledgeChunk instances create successfully with source_origin="text"
- [ ] KnowledgeChunk instances create successfully with source_origin="leadworks"
- [ ] KnowledgeChunk.metadata accepts nested dictionaries without errors
- [ ] Code follows project conventions and patterns
- [ ] All validation commands pass with zero errors
- [ ] New unit test coverage added and passes
- [ ] Migration file correctly updates database constraints
- [ ] Duplicate source origins in supabase.py removed and dynamic import works

### Runtime (verify after testing/deployment)

- [ ] Integration tests verify knowledge operations with new source types
- [ ] Feature works correctly in manual testing
- [ ] Invalid source origins still raise appropriate validation errors
- [ ] No regressions in existing functionality
- [ ] Database operations work with new source types after migration
- [ ] Nested metadata persists correctly through database roundtrip

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] KnowledgeChunk instantiates with source_origin="zoom" and valid nested metadata

---

## NOTES

### Key Design Decisions
- Eliminate the hardcoded duplicate values in supabase.py - Importing source origins dynamically from the main definition ensures consistency and reduces future maintenance overhead
- Retain pydantic validation patterns - Using the same literal types ensures runtime safety while maintaining the validation benefits

### Risks
- Risk 1: Migration may fail on production data - Mitigation: Test migration thoroughly on backup data before applying
- Risk 2: Breaking changes to external dependencies expecting old enum values - Mitigation: This is a pure type extension that shouldn't affect runtime behavior for existing values

### Confidence Score: 8/10
- **Strengths**: Clear, incremental change; existing patterns followed closely; good test coverage strategy
- **Uncertainties**: Database migration application may have subtle differences in production environment
- **Mitigations**: Extensive test coverage and schema validation steps before deployment

(2nd revision - total ~750 lines)