"""Unit tests for ConversationStore."""

import time

from second_brain.services.conversation import ConversationStore
from second_brain.contracts.conversation import ConversationTurn, ConversationState


class TestConversationStore:
    """Test ConversationStore session management."""

    def test_invalid_max_turns_raises(self):
        """Constructor rejects non-positive max_turns_per_session."""
        try:
            ConversationStore(max_turns_per_session=0)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "max_turns_per_session" in str(e)

    def test_invalid_max_sessions_raises(self):
        """Constructor rejects non-positive max_sessions."""
        try:
            ConversationStore(max_sessions=0)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "max_sessions" in str(e)

    def test_get_or_create_new_session(self):
        """Creating a new session returns valid ConversationState."""
        store = ConversationStore()
        state = store.get_or_create()

        assert isinstance(state, ConversationState)
        assert state.session_id is not None
        assert len(state.session_id) > 0
        assert state.turns == []
        assert state.created_at is not None
        assert state.last_active is not None

    def test_get_or_create_existing_session(self):
        """Getting existing session returns same state."""
        store = ConversationStore()
        state1 = store.get_or_create()
        state2 = store.get_or_create(state1.session_id)

        assert state1.session_id == state2.session_id
        assert state1 is not state2

    def test_get_or_create_with_explicit_id(self):
        """Passing session_id uses that ID."""
        store = ConversationStore()
        custom_id = "test-session-123"
        state = store.get_or_create(custom_id)

        assert state.session_id == custom_id

    def test_get_or_create_returns_copy(self):
        """get_or_create returns a copy to protect internal store state."""
        store = ConversationStore()
        state = store.get_or_create("copy-create")
        state.turns.append(ConversationTurn(role="user", content="mutated"))

        fresh = store.get_session("copy-create")
        assert fresh is not None
        assert len(fresh.turns) == 0

    def test_add_turn(self):
        """Adding turn appends to session."""
        store = ConversationStore()
        state = store.get_or_create()

        turn = ConversationTurn(role="user", content="Hello")
        store.add_turn(state.session_id, turn)

        current = store.get_session(state.session_id)
        assert current is not None

        assert len(current.turns) == 1
        assert current.turns[0].role == "user"
        assert current.turns[0].content == "Hello"

    def test_add_turn_unknown_session_raises(self):
        """Adding turn to unknown session raises KeyError."""
        store = ConversationStore()

        turn = ConversationTurn(role="user", content="Hello")

        try:
            store.add_turn("nonexistent-session", turn)
            assert False, "Should have raised KeyError"
        except KeyError as e:
            assert "nonexistent-session" in str(e)

    def test_max_turns_enforcement(self):
        """Sessions enforce max turns by trimming oldest."""
        store = ConversationStore(max_turns_per_session=3, max_sessions=10)
        state = store.get_or_create()

        for i in range(5):
            turn = ConversationTurn(role="user", content=f"Message {i}")
            store.add_turn(state.session_id, turn)

        current = store.get_session(state.session_id)
        assert current is not None

        assert len(current.turns) == 3
        assert current.turns[0].content == "Message 2"
        assert current.turns[1].content == "Message 3"
        assert current.turns[2].content == "Message 4"

    def test_session_limit_eviction(self):
        """Oldest inactive sessions evicted when over limit."""
        store = ConversationStore(max_turns_per_session=10, max_sessions=3)

        session_ids = []
        for i in range(4):
            state = store.get_or_create()
            session_ids.append(state.session_id)
            time.sleep(0.01)

        assert len(store._sessions) == 3
        assert session_ids[0] not in store._sessions
        assert session_ids[1] in store._sessions
        assert session_ids[2] in store._sessions
        assert session_ids[3] in store._sessions

    def test_delete_session(self):
        """Deleting session removes it."""
        store = ConversationStore()
        state = store.get_or_create()

        result = store.delete_session(state.session_id)

        assert result is True
        assert store.get_session(state.session_id) is None

    def test_delete_nonexistent_session(self):
        """Deleting nonexistent session returns False."""
        store = ConversationStore()

        result = store.delete_session("nonexistent")

        assert result is False

    def test_get_session_returns_none_for_missing(self):
        """get_session returns None for unknown ID."""
        store = ConversationStore()

        result = store.get_session("unknown")

        assert result is None

    def test_get_session_returns_copy(self):
        """get_session returns a copy to protect internal store state."""
        store = ConversationStore()
        state = store.get_or_create("copy-test")
        store.add_turn(state.session_id, ConversationTurn(role="user", content="hello"))

        snapshot = store.get_session(state.session_id)
        assert snapshot is not None
        snapshot.turns.append(ConversationTurn(role="assistant", content="mutated"))

        fresh = store.get_session(state.session_id)
        assert fresh is not None
        assert len(fresh.turns) == 1

    def test_last_active_updated_on_turn(self):
        """last_active timestamp updates when turn added."""
        store = ConversationStore()
        state = store.get_or_create()

        initial_active = state.last_active
        time.sleep(0.01)

        turn = ConversationTurn(role="user", content="Test")
        store.add_turn(state.session_id, turn)

        current = store.get_session(state.session_id)
        assert current is not None

        assert current.last_active > initial_active
