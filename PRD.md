# Product Requirements Document: Ultima Second Brain

**Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** 2026-02-27  

---

## 1. Executive Summary

Ultima Second Brain is a personal learning operating system designed for lifelong learners who want to accelerate understanding and output, with a near-term target of 2x to 4x productivity gains and a long-term ambition of up to 10x. The product centralizes fragmented knowledge, decisions, notes, and signals from daily tools into one continuously improving context layer.

The core value proposition is not mere storage—it is reliable retrieval, ranking, and synthesis. Instead of re-searching old notes or rethinking from zero, the user can recover relevant context quickly, rerank it for accuracy, connect ideas across sources, and use those insights for better thinking, writing, and execution. The system implements a hybrid memory architecture combining retrieval-augmented generation (RAG), semantic memory, and graph-linked context through Supabase-backed storage, Mem0-style repeat memory, and external knowledge sources.

The MVP focuses on achieving 80-90% retrieval accuracy for the persistent hybrid retrieval layer—the product's core. Content generation capabilities (LinkedIn posts, landing pages, lead magnets) are Phase 2 downstream consumers of this context layer, following pattern-based templates that the system learns and refines over time.

---

## 2. Mission

### Mission Statement

Build a persistent, accurate context layer that captures everything a user knows, learns, and works on—then retrieves, ranks, and synthesizes that context on demand to accelerate thinking, writing, and execution.

### Core Principles

1. **Retrieval Accuracy First** — The retrieval layer IS the product. Ingestion accuracy and retrieval precision are equally critical. Target: 80-90% accuracy at MVP.

2. **Flexible Schema Design** — One generalized schema that handles everything (notes, transcripts, conversations, decisions), not rigid per-source schemas. Easy to pivot as needs evolve.

3. **Local-First, Cloud-Optional** — Ollama-native LLM support (local + cloud with optional API key auth). No mandatory cloud dependencies. Docker deployment works identically on local machine or VPS.

4. **Orchestrator Intelligence** — Big flexible multi-agent orchestrator using Pydantic AI. Routes context to focused agents or orchestrates multi-agent collaboration as needed.

5. **Progressive Enhancement** — Start with core retrieval/ingestion (Phase 1), add content generation agents (Phase 2), expand integrations (Phase 3+). Each layer builds on validated foundations.

---

## 3. Target Users

### Primary Persona: The Lifelong Learner-Builder

**Profile:** Technical solo founder, researcher, or knowledge worker who consumes and produces large amounts of content daily.

**Technical Comfort:** High—comfortable with CLI tools, Docker, environment variables, and self-hosted infrastructure.

**Current Pain Points:**
- Context scattered across Zoom transcripts, markdown notes, Notion, Slack conversations, emails
- When information is needed, it's either gone or requires 15-30 minutes of manual digging
- Rethinking the same problems repeatedly because past decisions aren't recoverable
- Writing content (LinkedIn, blogs) from scratch each time instead of building on existing ideas
- No persistent memory layer that improves over time

**Needs:**
- Automatic ingestion of text/markdown/JSON sources with minimal manual setup
- Accurate retrieval that returns relevant context in seconds, not minutes
- Flexible query interface (natural language + structured filters)
- Ability to trace retrieval decisions for debugging/optimization
- Content generation that follows their established patterns

**Assumption:** User is comfortable running `docker compose up` and setting environment variables in a `.env` file.

---

## 4. MVP Scope

### In Scope — Phase 1 (Core Retrieval & Ingestion)

#### Ingestion Pipeline
- ✅ Markdown file chunking by `##` headings
- ✅ Voyage AI embeddings (1024-dim `voyage-4-large`)
- ✅ Supabase pgvector storage with HNSW index
- ✅ Auto-detection of file types (plain text, markdown, JSON)
- ✅ Lazy-init pattern for external providers (graceful degradation on missing API keys)
- ✅ MCP tool: `ingest_markdown(directory_path: str) -> IngestionResult`

#### Retrieval Engine
- ✅ Hybrid retrieval providers: Supabase (pgvector), Mem0 (semantic + graph)
- ✅ Multi-stage pipeline: `RetrievalRequest -> Router -> Provider -> Rerank -> Branch -> ContextPacket`
- ✅ Voyage AI reranking (`rerank-1` endpoint)
- ✅ Deterministic provider routing based on feature flags + health checks
- ✅ 5 fallback branches: `EMPTY_SET`, `LOW_CONFIDENCE`, `CHANNEL_MISMATCH`, `RERANK_BYPASSED`, `SUCCESS`
- ✅ MCP tool: `recall_search(query: str, session_id?: str) -> RetrievalResponse`

#### Orchestrator
- ✅ Pydantic AI agent: `RecallOrchestrator` with `Planner` loop
- ✅ Full chat loop: `query -> session -> retrieval -> LLM synthesis -> response`
- ✅ Ollama LLM service (local + cloud via optional API key)
- ✅ Trace collection: `RetrievalTrace` records for observability
- ✅ MCP tool: `chat(message: str, session_id?: str) -> ChatResponse`

#### Knowledge Schema
- ✅ 5-table schema: `sources`, `documents`, `chunks`, `entities`, `relationships`
- ✅ Graph types: `IS_RELATED_TO`, `MENTIONS`, `DERIVED_FROM`, `CONFLICTS_WITH`, `ELABORATES`
- ✅ HNSW index for cosine similarity search
- ✅ RPC function: `match_knowledge_chunks(query_embedding, threshold, limit)`

#### Deployment & Configuration
- ✅ Docker Compose setup (Postgres + Supabase + backend)
- ✅ Environment variable configuration for all feature flags
- ✅ All flags default to `false` for mock mode (existing tests run without env vars)
- ✅ Lazy-init pattern returns `None` on missing credentials (no hard failures)

### In Scope — Phase 2 (Content Generation)

#### Pattern-Based Writers
- ✅ LinkedIn post generator (hook + body + CTA patterns)
- ✅ Blog post generator (outline + draft + revision)
- ✅ Landing page copy generator (AIDA framework)
- ✅ Pattern learning from past content (embeddings + similarity matching)

#### Orchestrator Extensions
- ✅ Content routing: user request -> appropriate writer agent
- ✅ Multi-agent collaboration (research agent + writer agent + editor agent)
- ✅ Pattern retrieval from Second Brain context layer

### Out of Scope — MVP

#### Phase 1 Exclusions
- ❌ Web UI / frontend interface (MCP server is primary interface)
- ❌ PDF ingestion (add in Phase 3)
- ❌ Audio/video transcription (add in Phase 3)
- ❌ Multi-user support / authentication (single-user MVP)
- ❌ Real-time collaboration features
- ❌ Mobile app
- ❌ Native integrations with Zoom/Notion/Slack (manual export -> ingest workflow)

#### Phase 2 Exclusions
- ❌ Twitter/X thread generator
- ❌ YouTube video script generator
- ❌ Email newsletter generator
- ❌ Advanced pattern learning (ML-based pattern extraction)

#### Future Phases (Not in MVP)
- ❌ Fine-tuned models for specific content types
- ❌ Custom embedding models (Voyage-only for MVP)
- ❌ Advanced analytics dashboard
- ❌ API for third-party integrations

---

## 5. User Stories

### Story 1: Ingest Meeting Notes
**As a** solo founder,  
**I want to** drop my Zoom transcript markdown files into a directory and have them automatically ingested,  
**So that** I can search and retrieve context from past meetings without manual tagging.

**Acceptance Criteria:**
- User runs `mcp call ingest_markdown --directory ./meetings`
- System chunks by `##` headings (each section = 1 chunk)
- Voyage AI generates 1024-dim embeddings
- Chunks stored in Supabase `chunks` table with HNSW index
- User can later query "What did we decide about pricing in last week's call?"

**Example:**
```bash
mcp call ingest_markdown --directory ./zoom-transcripts
# Returns: { ingested: 12, chunks: 47, embeddings: 47 }
```

### Story 2: Accurate Retrieval
**As a** researcher,  
**I want to** query my Second Brain with natural language and get back the most relevant context,  
**So that** I can make decisions based on past learnings instead of rethinking from zero.

**Acceptance Criteria:**
- User sends query: "What were the key insights from my vector database research?"
- Retrieval pipeline routes to Supabase provider (pgvector cosine search)
- Voyage reranking improves precision
- Response includes top 5 chunks with confidence scores
- Retrieval trace shows: provider used, scores, branch decision

**Example:**
```json
{
  "query": "vector database research insights",
  "context_chunks": [
    {
      "content": "pgvector HNSW index gives 10x speedup for 100k+ rows",
      "source": "notes/vector-db-research.md",
      "similarity": 0.89,
      "rerank_score": 0.94
    }
  ],
  "branch": "SUCCESS",
  "trace_id": "trace_abc123"
}
```

### Story 3: Conversational Memory
**As a** knowledge worker,  
**I want to** have multi-turn conversations where the system remembers context from earlier in the session,  
**So that** I can refine queries and build on previous answers.

**Acceptance Criteria:**
- Session ID tracks conversation state
- Follow-up queries include prior context
- `ConversationStore` maintains thread-safe in-memory session history
- User can say "Tell me more about that first result" and system knows which result

**Example:**
```
User: "What do I know about RAG systems?"
System: [provides 5 chunks on RAG architecture]
User: "What about the reranking part specifically?"
System: [retrieves chunks focused on reranking, includes prior context]
```

### Story 4: Content Generation (Phase 2)
**As a** content creator,  
**I want to** generate LinkedIn posts that follow my established writing patterns,  
**So that** I can produce high-quality content 4x faster without starting from scratch.

**Acceptance Criteria:**
- User provides topic: "Lessons from building Second Brain"
- System retrieves relevant context from knowledge base
- Writer agent applies hook patterns (question, contrarian, story)
- Output matches user's past style (learned from embedded examples)
- User can iterate: "Make it more conversational"

**Example:**
```
User: "Write a LinkedIn post about retrieval accuracy"
System: [retrieves user's past posts on accuracy, Second Brain notes]
# Output:
"Most people think RAG is about embeddings. They're wrong.

After 1000+ retrieval queries, here's what actually matters:
[...post continues in user's established style]"
```

### Story 5: Debugging Retrieval
**As a** technical user,  
**I want to** see exactly why the system retrieved (or didn't retrieve) specific chunks,  
**So that** I can optimize my queries or adjust system configuration.

**Acceptance Criteria:**
- `RetrievalTrace` records: provider used, scores, branch decision, timing
- User can query trace by session ID or trace ID
- Trace shows: which providers were healthy, which were skipped, why
- Debug MCP tool validates branch logic

**Example:**
```json
{
  "trace_id": "trace_xyz789",
  "provider_routing": {
    "supabase": { "healthy": true, "used": true },
    "mem0": { "healthy": false, "used": false, "error": "API key missing" }
  },
  "reranking": {
    "applied": true,
    "model": "voyage-rerank-1",
    "original_scores": [0.72, 0.68, 0.65],
    "reranked_scores": [0.91, 0.84, 0.79]
  },
  "branch_decision": "SUCCESS",
  "total_latency_ms": 342
}
```

### Story 6: Graceful Degradation
**As a** self-hoster,  
**I want to** run the system with only local Ollama and no external API keys,  
**So that** I can test and use core functionality without mandatory cloud dependencies.

**Acceptance Criteria:**
- All external provider flags default to `false`
- Missing API keys -> provider returns `None`, system continues with available providers
- Existing tests pass without any environment variables set
- User can add API keys later for enhanced functionality

**Example:**
```bash
# No .env file at all
docker compose up
# System runs in mock mode, all providers return mock data
# Tests pass, core functionality works

# Later, add VOYAGE_API_KEY to .env
# Voyage reranking + embeddings automatically enabled
```

### Story 7: Docker Deployment
**As a** deployment-conscious user,  
**I want to** deploy with a single `docker compose up` command,  
**So that** the same setup works on my local machine and a VPS.

**Acceptance Criteria:**
- `docker-compose.yml` includes: Postgres (Supabase-compatible), backend service
- Environment variables passed via `.env` file
- Migrations run automatically on startup
- MCP server accessible from host machine
- Same compose file works on local Docker Desktop and DigitalOcean VPS

---

## 6. Core Architecture & Patterns

### High-Level Architecture

```
+-------------------------------------------------------------+
|                     MCP Server (FastMCP)                     |
|  Tools: recall_search | chat | ingest_markdown | debug_*    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                  Pydantic AI Orchestrator                    |
|  RecallOrchestrator -> Planner -> route_retrieval()         |
+-------------------------------------------------------------+
                              |
                +-------------+-------------+
                v                           v
+--------------------------+  +------------------------------+
|   Ingestion Pipeline     |  |    Retrieval Pipeline        |
|  - Markdown chunking     |  |  - Router -> Provider        |
|  - Voyage embeddings     |  |  - Rerank -> Branch          |
|  - Supabase insert       |  |  - ContextPacket             |
+--------------------------+  +------------------------------+
                |                           |
                v                           v
+-------------------------------------------------------------+
|              Supabase (Postgres + pgvector)                  |
|  Tables: sources | documents | chunks | entities | relations |
|  Index: HNSW cosine similarity (vector(1024))                |
|  RPC: match_knowledge_chunks(query_embedding, threshold)     |
+-------------------------------------------------------------+
```

### Directory Structure

```
backend/
├── src/second_brain/
│   ├── __init__.py
│   ├── contracts/           # Pydantic models
│   │   ├── __init__.py
│   │   ├── retrieval.py     # RetrievalRequest, RetrievalResponse, ContextPacket
│   │   ├── knowledge.py     # KnowledgeDocument, KnowledgeChunk, etc.
│   │   ├── conversation.py  # ConversationTurn, ConversationState
│   │   └── trace.py         # RetrievalTrace, Span
│   ├── services/            # External providers
│   │   ├── __init__.py
│   │   ├── memory.py        # MemoryService (Mem0, Supabase providers)
│   │   ├── voyage.py        # VoyageRerankService + VoyageEmbedService
│   │   ├── supabase.py      # SupabaseProvider (pgvector search)
│   │   ├── ollama.py        # OllamaLLMService (REST API)
│   │   └── trace.py         # TraceCollector (in-memory)
│   ├── orchestration/       # Agent logic
│   │   ├── __init__.py
│   │   ├── planner.py       # Planner loop (query -> retrieval -> response)
│   │   ├── router.py        # route_retrieval() deterministic routing
│   │   ├── branch.py        # determine_branch() + FallbackEmitter
│   │   └── recall.py        # RecallOrchestrator agent
│   ├── ingestion/           # Data ingestion
│   │   ├── __init__.py
│   │   ├── parser.py        # MarkdownChunker, TextParser, JsonParser
│   │   └── pipeline.py      # ingest_markdown_directory()
│   ├── mcp_server.py        # FastMCP server definition
│   └── deps.py              # Lazy-init, feature flags, configuration
├── migrations/
│   └── 001_knowledge_schema.sql
├── tests/
│   ├── contracts/           # Pydantic model tests
│   ├── services/            # Provider tests (mock + real)
│   ├── orchestration/       # Orchestrator logic tests
│   └── integration/         # End-to-end retrieval tests
├── pyproject.toml
└── docker-compose.yml
```

### Design Patterns

#### Lazy-Init Pattern (All External Providers)
All external providers use lazy initialization with graceful degradation:

```python
# backend/src/second_brain/deps.py
def get_voyage_rerank() -> VoyageRerankService | None:
    """Lazy-init: returns None if API key missing (not an error)."""
    if not os.getenv("VOYAGE_API_KEY"):
        return None
    try:
        return VoyageRerankService()
    except Exception as e:
        logger.warning(f"Voyage init failed: {e}")
        return None
```

**Assumption:** Returning `None` is preferred over raising exceptions for missing optional dependencies.

#### Deterministic Provider Routing
Router uses explicit feature flags + health checks—no AI-based routing for MVP:

```python
# backend/src/second_brain/orchestration/router.py
def route_retrieval(request: RetrievalRequest, flags: FeatureFlags) -> ProviderRoute:
    """Deterministic routing: flags + health -> provider selection."""
    if flags.use_supabase and supabase_healthy():
        return ProviderRoute.SUPABASE
    if flags.use_mem0 and mem0_healthy():
        return ProviderRoute.MEM0
    return ProviderRoute.MOCK
```

#### Pydantic AI Agent Pattern
Agents are Pydantic models with tool access and conversation state:

```python
# backend/src/second_brain/orchestration/recall.py
class RecallOrchestrator(BaseModel):
    """Core retrieval agent with tool access."""
    planner: Planner
    trace_collector: TraceCollector
    
    async def run(self, query: str, session_id: str) -> RetrievalResponse:
        # 1. Update session state
        # 2. Build RetrievalRequest
        # 3. Route -> Search -> Rerank -> Branch
        # 4. LLM synthesis via Ollama
        # 5. Record trace, return response
```

### Pydantic AI Patterns

**Agent Definition:**
```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

class RetrievalAgent(BaseModel):
    """Pydantic AI agent for retrieval orchestration."""
    
    model_config = {"arbitrary_types_allowed": True}
    
    agent: Agent[None, RetrievalResponse] = field(default_factory=lambda: Agent(
        model="ollama:llama3.1:8b",
        result_type=RetrievalResponse,
    ))
```

**Tool Registration:**
```python
@agent.tool
async def search_knowledge(ctx: RunContext[None], query: str) -> list[KnowledgeChunk]:
    """Search knowledge base, return ranked chunks."""
    service = ctx.deps.supabase_provider
    results = await service.search(query, limit=10)
    return results
```

---

## 7. Tools/Features

### 7.1 Ingestion Pipeline

#### Markdown Ingestion (`ingest_markdown_directory()`)
**Location:** `backend/src/second_brain/ingestion/pipeline.py`

**Flow:**
1. Scan directory for `.md` files
2. Parse each file with `MarkdownChunker` (split by `##` headings)
3. Generate embeddings via Voyage AI (`voyage-4-large`, 1024-dim)
4. Insert into Supabase: `documents` -> `chunks` tables
5. Return ingestion summary

**Chunking Strategy:**
```python
# backend/src/second_brain/ingestion/parser.py
class MarkdownChunker:
    def chunk(self, markdown: str, source_path: str) -> list[KnowledgeChunk]:
        """Split by ## headings. Each section = 1 chunk."""
        sections = re.split(r'\n## ', markdown)
        chunks = []
        for section in sections:
            heading, content = section.split('\n', 1)
            chunks.append(KnowledgeChunk(
                content=content.strip(),
                heading=heading.strip(),
                source_path=source_path,
            ))
        return chunks
```

**MCP Tool:**
```python
@mcp.tool()
async def ingest_markdown(directory_path: str) -> dict:
    """Ingest all markdown files in directory.
    
    Args:
        directory_path: Path to directory containing .md files
    
    Returns:
        { ingested: int, chunks: int, embeddings: int, errors: list[str] }
    """
```

### 7.2 Retrieval Engine

#### Multi-Stage Pipeline
**Location:** `backend/src/second_brain/orchestration/recall.py`

**Stages:**
1. **RetrievalRequest** — User query + session context + filters
2. **Router** — Select provider (Supabase/Mem0/Mock) based on flags + health
3. **Provider Search** — Cosine similarity search (Supabase pgvector)
4. **Rerank** — Voyage AI `rerank-1` improves precision
5. **Branch** — Determine next action (SUCCESS/EMPTY_SET/LOW_CONFIDENCE/etc.)
6. **ContextPacket** — Final retrieved context + metadata

**Branch Codes:**
```python
# backend/src/second_brain/orchestration/branch.py
class BranchCode(str, Enum):
    SUCCESS = "SUCCESS"           # High-confidence results
    EMPTY_SET = "EMPTY_SET"       # No results found
    LOW_CONFIDENCE = "LOW_CONFIDENCE"  # Results below threshold
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"  # Provider returned wrong type
    RERANK_BYPASSED = "RERANK_BYPASSED"  # Reranking skipped (missing API key)
```

**FallbackEmitter:**
```python
class FallbackEmitter:
    """Determines branch based on results + config."""
    
    def determine_branch(
        self,
        results: list[KnowledgeChunk],
        threshold: float,
        rerank_applied: bool,
    ) -> NextAction:
        if not results:
            return NextAction(branch=BranchCode.EMPTY_SET)
        if max(r.similarity for r in results) < threshold:
            return NextAction(branch=BranchCode.LOW_CONFIDENCE)
        if not rerank_applied:
            return NextAction(branch=BranchCode.RERANK_BYPASSED)
        return NextAction(branch=BranchCode.SUCCESS)
```

### 7.3 Orchestrator

#### RecallOrchestrator Agent
**Location:** `backend/src/second_brain/orchestration/recall.py`

**Responsibilities:**
- Receive user query (via MCP `chat` tool)
- Build `RetrievalRequest` with session context
- Call `route_retrieval()` -> select provider
- Execute provider search + reranking
- Determine branch -> handle fallbacks
- Synthesize response via Ollama LLM
- Record `RetrievalTrace` for observability

**Planner Loop:**
```python
# backend/src/second_brain/orchestration/planner.py
class Planner:
    """Full chat loop orchestrator."""
    
    async def plan_and_execute(
        self,
        query: str,
        session_id: str,
    ) -> RetrievalResponse:
        # 1. Load or create session state
        # 2. Build retrieval request
        # 3. Execute retrieval pipeline
        # 4. LLM synthesis
        # 5. Update session, return response
```

#### OllamaLLMService
**Location:** `backend/src/second_brain/services/ollama.py`

**Configuration:**
```python
class OllamaLLMService:
    def __init__(self):
        self.api_key = os.getenv("OLLAMA_API_KEY")  # Optional for cloud
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    async def chat(self, messages: list, model: str) -> str:
        """Call Ollama REST API with stream: false."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,  # Critical: full JSON response
                },
            )
            return response.json()["message"]["content"]
```

**Assumption:** User sets `OLLAMA_API_KEY` only if using Ollama Cloud. Local Ollama requires no auth.

### 7.4 MCP Tools

#### recall_search
```python
@mcp.tool()
async def recall_search(
    query: str,
    session_id: str | None = None,
) -> RetrievalResponse:
    """Search Second Brain for relevant context.
    
    Args:
        query: Natural language search query
        session_id: Optional session ID for conversation tracking
    
    Returns:
        RetrievalResponse with:
        - context_chunks: list[KnowledgeChunk]
        - branch: BranchCode
        - trace_id: str (for debugging)
    """
```

#### chat
```python
@mcp.tool()
async def chat(
    message: str,
    session_id: str | None = None,
) -> ChatResponse:
    """Conversational chat with Second Brain context.
    
    Args:
        message: User message
        session_id: Optional session ID (auto-generated if not provided)
    
    Returns:
        ChatResponse with:
        - response: str (LLM synthesis)
        - context_used: list[KnowledgeChunk]
        - session_id: str
    """
```

#### ingest_markdown
```python
@mcp.tool()
async def ingest_markdown(
    directory_path: str,
) -> IngestionResult:
    """Ingest markdown files from directory.
    
    Args:
        directory_path: Path to directory with .md files
    
    Returns:
        IngestionResult with:
        - files_ingested: int
        - chunks_created: int
        - embeddings_generated: int
        - errors: list[str]
    """
```

#### Debug Tools (Development)
```python
@mcp.tool()
async def debug_branch(branch_code: str) -> dict:
    """Test branch logic with mock data."""

@mcp.tool()
async def debug_provider_health() -> dict:
    """Check health of all providers."""

@mcp.tool()
async def debug_trace(trace_id: str) -> RetrievalTrace:
    """Retrieve trace by ID for debugging."""
```

### 7.5 Content Agents (Phase 2)

#### LinkedIn Writer Agent
**Pattern:** Hook -> Body -> CTA

**Agent Definition:**
```python
class LinkedInWriter(BaseModel):
    """Generate LinkedIn posts following user's patterns."""
    
    async def generate(
        self,
        topic: str,
        context: list[KnowledgeChunk],
    ) -> str:
        # 1. Retrieve user's past LinkedIn posts (pattern examples)
        # 2. Extract hook patterns (question, contrarian, story)
        # 3. Generate post using Ollama LLM
        # 4. Return draft for user review
```

**Pattern Learning:**
```python
class PatternLearner:
    """Learn writing patterns from past content."""
    
    def extract_patterns(self, past_posts: list[str]) -> dict:
        """Embed past posts, cluster by style, extract common structures."""
        embeddings = voyage.embed(past_posts)
        clusters = hdbscan.cluster(embeddings)
        return {
            "hook_patterns": self._extract_hooks(clusters),
            "body_structure": self._extract_structure(clusters),
            "cta_patterns": self._extract_ctas(clusters),
        }
```

---

## 8. Technology Stack

### Core Technologies

| Technology | Version | Purpose | Required |
|------------|---------|---------|----------|
| Python | 3.11+ | Backend runtime | Yes |
| Pydantic | 2.0+ | Data models, validation, agents | Yes |
| Pydantic AI | Latest | Agent framework | Yes |
| FastMCP | 2.0+ | MCP server framework | Yes |
| Supabase | 2.0+ | Postgres + pgvector client | Yes |
| Voyage AI | 0.3+ | Embeddings + reranking | Yes (optional for mock mode) |
| httpx | 0.27+ | Async HTTP client (Ollama REST) | Yes |

### Database & Storage

| Technology | Version | Purpose | Required |
|------------|---------|---------|----------|
| PostgreSQL | 15+ | Primary database | Yes |
| pgvector | 0.5+ | Vector similarity search | Yes |
| HNSW Index | Built-in | Approximate nearest neighbors | Yes |

### LLM & AI

| Technology | Version | Purpose | Required |
|------------|---------|---------|----------|
| Ollama | Latest | LLM inference (local + cloud) | Yes |
| Mem0 | Latest | Semantic + graph memory (Phase 2) | No (Phase 2) |

### Deployment & DevOps

| Technology | Version | Purpose | Required |
|------------|---------|---------|----------|
| Docker | Latest | Containerization | Yes |
| Docker Compose | Latest | Multi-service orchestration | Yes |

### Development Tools

| Tool | Purpose | Required |
|------|---------|----------|
| ruff | Linting | Yes |
| mypy | Type checking (strict mode) | Yes |
| pytest | Testing framework | Yes |
| uvicorn | ASGI server (development) | Yes |

### Dependencies (pyproject.toml)

```toml
[project]
name = "second-brain"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "pydantic-ai>=0.0.1",
    "httpx>=0.27",
    "voyageai>=0.3",
    "supabase>=2.0",
    "fastmcp>=2.0",
    "ruff",
    "mypy",
    "pytest",
]
```

### Third-Party Integrations

| Integration | API Key Required | Fallback |
|-------------|------------------|----------|
| Voyage AI (embeddings) | `VOYAGE_API_KEY` | Skip embeddings (mock mode) |
| Voyage AI (reranking) | `VOYAGE_API_KEY` | Skip reranking (lower accuracy) |
| Ollama Cloud | `OLLAMA_API_KEY` | Use local Ollama (no key) |
| Supabase | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | In-memory mock (tests only) |
| Mem0 | `MEM0_API_KEY` | Skip graph memory (Phase 2) |

**Assumption:** All API keys are optional. System runs in mock mode with degraded functionality if keys are missing.

---

## 9. Security & Configuration

### Authentication Approach

**MVP:** Single-user, local-first. No authentication layer.

**Future:** Add Supabase Auth or custom JWT layer for multi-user support (Phase 3+).

### Environment Variables

All configuration via environment variables. None are required—missing keys trigger mock mode.

```bash
# .env.example
# === Required for Production ===
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key  # NOT anon key

# === Optional (enable enhanced features) ===
VOYAGE_API_KEY=your-voyage-key  # Enables embeddings + reranking
OLLAMA_API_KEY=your-ollama-key  # Only for Ollama Cloud (not local)
OLLAMA_BASE_URL=http://localhost:11434  # Default for local

# === Feature Flags (all default to false) ===
USE_SUPABASE=true  # Enable Supabase provider
USE_MEM0=false  # Enable Mem0 provider (Phase 2)
USE_RERANKING=true  # Enable Voyage reranking
USE_TRACING=true  # Enable RetrievalTrace collection

# === Tuning ===
RETRIEVAL_THRESHOLD=0.7  # Cosine similarity threshold
MAX_CHUNKS=10  # Max chunks to return
EMBEDDING_MODEL=voyage-4-large
RERANK_MODEL=voyage-rerank-1
```

**Assumption:** `SUPABASE_SERVICE_KEY` (not anon key) is required for inserts. This is documented in setup instructions.

### Security Scope

**MVP Security Considerations:**
- ✅ No hardcoded secrets (all via environment variables)
- ✅ Service role key for Supabase (not exposed to client)
- ✅ Lazy-init pattern (graceful degradation, no hard failures)
- ✅ Thread-safe in-memory stores (no race conditions)

**Out of Scope:**
- ❌ User authentication/authorization
- ❌ API rate limiting
- ❌ Input sanitization (trusted user input only)
- ❌ Encryption at rest (relies on Postgres/Supabase encryption)

### Deployment Configuration

**Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  db:
    image: supabase/postgres:15.1.0.117
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: second_brain
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  backend:
    build: ./backend
    environment:
      - SUPABASE_URL=postgresql://postgres:postgres@db:5432/second_brain
      - SUPABASE_SERVICE_KEY=postgres
      - VOYAGE_API_KEY=${VOYAGE_API_KEY:-}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL:-http://localhost:11434}
    ports:
      - "8000:8000"
    depends_on:
      - db

volumes:
  postgres_data:
```

**Assumption:** Same `docker-compose.yml` works on local Docker Desktop and VPS (DigitalOcean, Linode, etc.).

---

## 10. API Specification

### MCP Tool Definitions

#### recall_search
```python
@mcp.tool()
async def recall_search(
    query: str,
    session_id: str | None = None,
) -> RetrievalResponse:
    """Search Second Brain for relevant context."""
```

**Request:**
```json
{
  "query": "What did I learn about vector databases?",
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "query": "What did I learn about vector databases?",
  "session_id": "sess_abc123",
  "context_chunks": [
    {
      "id": "chunk_xyz789",
      "content": "pgvector HNSW index gives 10x speedup for 100k+ rows",
      "heading": "Performance Optimization",
      "source": {
        "id": "doc_123",
        "path": "notes/vector-db-research.md",
        "type": "markdown"
      },
      "similarity": 0.89,
      "rerank_score": 0.94,
      "metadata": {
        "ingested_at": "2026-02-25T10:30:00Z",
        "word_count": 127
      }
    }
  ],
  "branch": "SUCCESS",
  "trace_id": "trace_def456",
  "latency_ms": 342
}
```

#### chat
```python
@mcp.tool()
async def chat(
    message: str,
    session_id: str | None = None,
) -> ChatResponse:
    """Conversational chat with Second Brain context."""
```

**Request:**
```json
{
  "message": "Summarize my vector database research",
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "response": "Based on your notes, here are the key insights from your vector database research:\n\n1. **pgvector HNSW index** provides 10x speedup for 100k+ rows compared to flat index...\n2. **Embedding dimension** trade-off: 1024-dim gives better accuracy but 4x storage...\n\n[continues with LLM synthesis]",
  "context_used": [
    {
      "id": "chunk_xyz789",
      "content": "pgvector HNSW index gives 10x speedup...",
      "similarity": 0.89
    }
  ],
  "session_id": "sess_abc123",
  "turn_id": "turn_789"
}
```

#### ingest_markdown
```python
@mcp.tool()
async def ingest_markdown(
    directory_path: str,
) -> IngestionResult:
    """Ingest markdown files from directory."""
```

**Request:**
```json
{
  "directory_path": "/Users/me/notes/zoom-transcripts"
}
```

**Response:**
```json
{
  "files_ingested": 12,
  "chunks_created": 47,
  "embeddings_generated": 47,
  "errors": [],
  "documents": [
    {
      "id": "doc_123",
      "path": "meeting-2026-02-20.md",
      "chunks": 4,
      "word_count": 1247
    }
  ]
}
```

### Request/Response Contracts

#### RetrievalRequest
```python
class RetrievalRequest(BaseModel):
    query: str
    session_id: str | None = None
    filters: dict[str, Any] = {}
    limit: int = 10
    threshold: float = 0.7
    providers: list[str] = ["supabase", "mem0"]
```

#### RetrievalResponse
```python
class RetrievalResponse(BaseModel):
    query: str
    context_chunks: list[KnowledgeChunk]
    branch: BranchCode
    trace_id: str
    latency_ms: int
    session_id: str | None = None
```

#### KnowledgeChunk
```python
class KnowledgeChunk(BaseModel):
    id: str
    content: str
    heading: str
    source: KnowledgeSource
    similarity: float
    rerank_score: float | None = None
    metadata: dict[str, Any] = {}
```

---

## 11. Success Criteria

### MVP Success Definition

**Primary Metric:** 80-90% retrieval accuracy on test queries.

**Validation Method:**
- Curated test set of 50 queries with known relevant chunks
- Precision@5: At least 4 of top 5 results are relevant
- Recall@10: At least 8 of top 10 results are relevant
- User-verified: User marks results as relevant/not relevant over 100 queries

### Functional Requirements

#### Ingestion
- ✅ Markdown chunking produces correct heading boundaries
- ✅ Voyage embeddings are 1024-dimensional
- ✅ Supabase inserts succeed with service_role key
- ✅ Ingestion summary accurately reports files/chunks/embeddings

#### Retrieval
- ✅ Cosine similarity search returns results in correct order
- ✅ Reranking improves precision (measured A/B test)
- ✅ Branch logic correctly identifies EMPTY_SET, LOW_CONFIDENCE, SUCCESS
- ✅ Trace records capture all pipeline stages

#### Orchestrator
- ✅ Chat loop maintains session state across turns
- ✅ Ollama LLM synthesis produces coherent responses
- ✅ Fallback handling works when providers fail

#### MCP Server
- ✅ All 3 tools (recall_search, chat, ingest_markdown) respond correctly
- ✅ Debug tools validate branch logic and provider health
- ✅ MCP server runs in stdio mode for CLI integration

### Quality Indicators

| Metric | Target | Measurement |
|--------|--------|-------------|
| Retrieval Precision@5 | 80%+ | Test set of 50 queries |
| Retrieval Recall@10 | 80%+ | Test set of 50 queries |
| Latency (p50) | <500ms | Production monitoring |
| Latency (p95) | <1000ms | Production monitoring |
| Test Coverage | 80%+ | pytest --cov |
| Type Safety | 0 mypy errors | mypy --strict |
| Lint | 0 ruff errors | ruff check |

---

## 12. Implementation Phases

### Phase 1: Core Retrieval & Ingestion (MVP)

**Goal:** Build and validate the persistent hybrid retrieval layer.

**Deliverables:**
- ✅ Knowledge schema (5 tables + HNSW index + RPC)
- ✅ Ingestion pipeline (markdown chunking + Voyage embeddings + Supabase)
- ✅ Retrieval pipeline (router + provider + rerank + branch)
- ✅ RecallOrchestrator agent with Planner loop
- ✅ OllamaLLMService (local + cloud)
- ✅ MCP server with 3 tools (recall_search, chat, ingest_markdown)
- ✅ Docker Compose deployment
- ✅ 230+ passing tests

**Validation Criteria:**
- ✅ All 16 test files pass (pytest ../tests/ -q)
- ✅ ruff check: 0 errors
- ✅ mypy --strict: 0 errors
- ✅ Manual validation: 50-query test set achieves 80%+ precision

### Phase 2: Content Generation

**Goal:** Add pattern-based content writers as downstream consumers.

**Deliverables:**
- ✅ LinkedIn Writer agent (hook + body + CTA)
- ✅ Blog Post Writer agent (outline + draft + revision)
- ✅ Landing Page Writer agent (AIDA framework)
- ✅ Pattern Learner (embed past content, cluster by style)
- ✅ Content routing in orchestrator
- ✅ Multi-agent collaboration (research + write + edit)

**Validation Criteria:**
- ✅ Generated content matches user's past style (user-verified)
- ✅ Pattern extraction correctly identifies hook/body/CTA structures
- ✅ Content generation latency <5s per draft

### Phase 3: Enhanced Integrations

**Goal:** Expand ingestion sources and add multi-user support.

**Deliverables:**
- ❌ PDF ingestion (text extraction + chunking)
- ❌ Audio/video transcription integration (Whisper API or local)
- ❌ Native Zoom/Notion/Slack integrations (OAuth + webhooks)
- ❌ User authentication (Supabase Auth or custom JWT)
- ❌ Multi-user isolation (row-level security)

**Validation Criteria:**
- ❌ PDF ingestion achieves same accuracy as markdown
- ❌ Transcription accuracy >90% for clear audio
- ❌ OAuth flows complete successfully for all integrations
- ❌ Multi-user queries return only user's own data

### Phase 4: Advanced Features

**Goal:** Add analytics, fine-tuning, and API access.

**Deliverables:**
- ❌ Analytics dashboard (usage patterns, retrieval accuracy trends)
- ❌ Fine-tuned models for specific content types
- ❌ Public API for third-party integrations
- ❌ Advanced pattern learning (ML-based extraction)

**Validation Criteria:**
- ❌ Dashboard accurately reflects usage metrics
- ❌ Fine-tuned models outperform base models on evaluation set
- ❌ API rate limiting prevents abuse
- ❌ Pattern learning improves over time (measured A/B test)

---

## 13. Future Considerations

### Post-MVP Enhancements

**Real-Time Ingestion:**
- Webhook-based ingestion from connected services (Zapier, Make)
- Browser extension for clipping web articles
- Mobile app for voice notes and quick capture

**Advanced Retrieval:**
- Query expansion and reformulation
- Multi-hop retrieval (chaining multiple searches)
- Temporal filtering (search by date ranges, recency boosting)
- Entity-based retrieval (search by people, companies, projects)

**Personalization:**
- User preference learning (preferred sources, result formats)
- Adaptive ranking (learn from user click/selection patterns)
- Custom embedding fine-tuning on user's content

**Collaboration:**
- Shared knowledge bases for teams
- Permission systems (read/write/admin)
- Activity feeds and notifications

### Integration Opportunities

**Productivity Tools:**
- Notion bidirectional sync
- Obsidian plugin for Second Brain queries
- Logseq integration for daily notes

**Communication:**
- Gmail integration (auto-archive important emails)
- Slack bot for team knowledge queries
- Calendar integration (meeting notes auto-linked)

**Content Platforms:**
- Direct LinkedIn posting from generated drafts
- Medium/Substack publishing integration
- YouTube transcript auto-ingestion

---

## 14. Risks & Mitigations

### Risk 1: Retrieval Accuracy Below Target

**Risk:** System returns irrelevant results, user loses trust.

**Likelihood:** Medium  
**Impact:** High

**Mitigations:**
- Start with conservative thresholds (0.7+ similarity)
- Implement comprehensive tracing for debugging
- A/B test reranking models before deployment
- User feedback loop: mark results as relevant/not relevant
- Fallback branches guide user to refine queries

### Risk 2: External API Dependencies

**Risk:** Voyage AI or Ollama Cloud API outages disrupt service.

**Likelihood:** Low  
**Impact:** Medium

**Mitigations:**
- Lazy-init pattern: gracefully degrade to mock mode
- Local Ollama as primary, cloud as fallback
- Cache embeddings for frequently accessed content
- Document offline usage patterns for users

### Risk 3: Vector Dimension Mismatch

**Risk:** Voyage `voyage-4-large` outputs 1024-dim, Supabase schema must match.

**Likelihood:** Low (known issue)  
**Impact:** High (blocks ingestion)

**Mitigations:**
- Migration explicitly sets `vector(1024)` in schema
- Test embeddings dimension in CI pipeline
- Document dimension requirement in setup guide
- Version lock Voyage SDK to prevent breaking changes

### Risk 4: Performance at Scale

**Risk:** Retrieval latency increases with 100k+ chunks.

**Likelihood:** Medium (long-term)  
**Impact:** Medium

**Mitigations:**
- HNSW index for approximate nearest neighbors (10x speedup)
- Set reasonable `limit` defaults (10 chunks max)
- Monitor p95 latency, set alerts at 1000ms
- Consider chunk pruning strategies for old/low-value content

### Risk 5: User Adoption Friction

**Risk:** Setup complexity (Docker, env vars, API keys) prevents usage.

**Likelihood:** Medium  
**Impact:** High

**Mitigations:**
- Comprehensive setup documentation with screenshots
- `.env.example` file with clear comments
- Docker Compose health checks for debugging
- Mock mode works out-of-box (no API keys required)
- Video walkthrough for first-time setup

---

## 15. Appendix

### Related Documents

| Document | Location | Purpose |
|----------|----------|---------|
| MVP Definition | `mvp.md` | Product vision, target users, success signals |
| Knowledge Schema | `backend/migrations/001_knowledge_schema.sql` | Database schema, indexes, RPC functions |
| Test Suite | `backend/tests/` | 16 test files, 230+ tests |
| Agent Orchestration | `backend/src/second_brain/orchestration/` | Planner, router, branch logic |
| MCP Server | `backend/src/second_brain/mcp_server.py` | Tool definitions, stdio transport |

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pydantic | >=2.0 | Data validation, BaseModel |
| pydantic-ai | >=0.0.1 | Agent framework |
| httpx | >=0.27 | Async HTTP (Ollama REST) |
| voyageai | >=0.3 | Embeddings + reranking |
| supabase | >=2.0 | Postgres + pgvector client |
| fastmcp | >=2.0 | MCP server framework |
| ruff | latest | Linting |
| mypy | latest | Type checking |
| pytest | latest | Testing |

### Project Structure Summary

```
second-brain-fin/
├── PRD.md                    # This document
├── mvp.md                    # Product vision
├── backend/
│   ├── src/second_brain/     # Python backend
│   │   ├── contracts/        # Pydantic models
│   │   ├── services/         # External providers
│   │   ├── orchestration/    # Agent logic
│   │   ├── ingestion/        # Data ingestion
│   │   └── mcp_server.py     # FastMCP server
│   ├── migrations/           # SQL migrations
│   ├── tests/                # pytest test files
│   └── pyproject.toml        # Dependencies
├── tests/                    # Integration tests
├── docker-compose.yml        # Deployment
└── .env.example              # Configuration template
```

### Glossary

| Term | Definition |
|------|------------|
| RAG | Retrieval-Augmented Generation — LLM responses grounded in retrieved context |
| HNSW | Hierarchical Navigable Small World — approximate nearest neighbor index |
| pgvector | PostgreSQL extension for vector similarity search |
| MCP | Model Context Protocol — standard for AI tool integration |
| Mem0 | Semantic memory service with graph relationships |
| Voyage AI | External provider for embeddings and reranking |
| Ollama | LLM inference engine (local + cloud) |
| Pydantic AI | Agent framework built on Pydantic |

### Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-27 | Initial PRD — complete specification for MVP |

---

**END OF DOCUMENT**
