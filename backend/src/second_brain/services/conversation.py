"""In-memory conversation state store."""

import threading
from datetime import datetime, timezone

from second_brain.contracts.conversation import ConversationTurn, ConversationState


class ConversationStore:
    """In-memory conversation state store."""

    def __init__(self, max_turns_per_session: int = 50, max_sessions: int = 100):
        if max_turns_per_session <= 0:
            raise ValueError("max_turns_per_session must be > 0")
        if max_sessions <= 0:
            raise ValueError("max_sessions must be > 0")
        self._sessions: dict[str, ConversationState] = {}
        self._max_turns = max_turns_per_session
        self._max_sessions = max_sessions
        self._lock = threading.Lock()

    def get_or_create(self, session_id: str | None = None) -> ConversationState:
        """Get existing session or create new one."""
        with self._lock:
            if session_id and session_id in self._sessions:
                return self._sessions[session_id].model_copy(deep=True)
            state = ConversationState()
            if session_id:
                state.session_id = session_id
            self._sessions[state.session_id] = state
            self._enforce_session_limit()
            return state.model_copy(deep=True)

    def add_turn(self, session_id: str, turn: ConversationTurn) -> None:
        """Add a turn to session, enforcing max turns."""
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            state = self._sessions[session_id]
            state.turns.append(turn)
            if len(state.turns) > self._max_turns:
                state.turns = state.turns[-self._max_turns :]
            state.last_active = datetime.now(timezone.utc).isoformat()

    def get_session(self, session_id: str) -> ConversationState | None:
        """Get session by ID, or None if not found."""
        with self._lock:
            state = self._sessions.get(session_id)
            if state is None:
                return None
            return state.model_copy(deep=True)

    def has_session(self, session_id: str) -> bool:
        """Check whether a session exists."""
        with self._lock:
            return session_id in self._sessions

    def list_session_ids(self) -> set[str]:
        """Return active session IDs."""
        with self._lock:
            return set(self._sessions.keys())

    def delete_session(self, session_id: str) -> bool:
        """Delete session. Returns True if existed."""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def _enforce_session_limit(self) -> None:
        """Evict oldest sessions if over limit. Must be called with lock held."""
        if len(self._sessions) > self._max_sessions:
            sorted_ids = sorted(
                self._sessions.keys(),
                key=lambda sid: self._sessions[sid].last_active,
            )
            for sid in sorted_ids[: len(self._sessions) - self._max_sessions]:
                del self._sessions[sid]
