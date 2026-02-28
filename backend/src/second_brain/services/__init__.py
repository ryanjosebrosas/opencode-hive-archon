"""Services package - export service abstractions."""

from second_brain.services.memory import MemoryService, MemorySearchResult
from second_brain.services.voyage import VoyageRerankService
from second_brain.services.supabase import SupabaseProvider
from second_brain.services.trace import TraceCollector
from second_brain.services.conversation import ConversationStore

# Export pool-related classes
from second_brain.services.pool import CircuitState, CircuitBreaker, ConnectionPool, PoolConfig

# Export transaction-related classes
from second_brain.services.transaction import (
    TransactionContext,
    TransactionError,
    TransactionExecutor,
    TransactionManager,
    TransactionState,
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "ConnectionPool",
    "ConversationStore",
    "MemorySearchResult",
    "MemoryService",
    "PoolConfig",
    "SupabaseProvider",
    "TraceCollector",
    "TransactionContext",
    "TransactionError",
    "TransactionExecutor",
    "TransactionManager",
    "TransactionState",
    "VoyageRerankService",
]
