"""Tests for transaction management."""

from __future__ import annotations

from typing import Any

import pytest

from second_brain.services.transaction import (
    TransactionContext,
    TransactionError,
    TransactionManager,
    TransactionState,
)


class MockTransactionExecutor:
    """Satisfies TransactionExecutor protocol via duck typing."""

    def __init__(self) -> None:
        self.operations: list[str] = []
        self.fail_on: str | None = None
        self.fail_on_method: str | None = None

    def begin(self) -> None:
        self.operations.append("BEGIN")

    def commit(self) -> None:
        self.operations.append("COMMIT")

    def rollback(self) -> None:
        self.operations.append("ROLLBACK")

    def create_savepoint(self, name: str) -> None:
        if self.fail_on_method == "create_savepoint":
            raise RuntimeError("create_savepoint failed")
        self.operations.append(f"SAVEPOINT {name}")

    def release_savepoint(self, name: str) -> None:
        if self.fail_on_method == "release_savepoint":
            raise RuntimeError("release_savepoint failed")
        self.operations.append(f"RELEASE SAVEPOINT {name}")

    def rollback_to_savepoint(self, name: str) -> None:
        if self.fail_on_method == "rollback_to_savepoint":
            raise RuntimeError("rollback_to_savepoint failed")
        self.operations.append(f"ROLLBACK TO SAVEPOINT {name}")

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError(f"Simulated failure on: {sql}")
        self.operations.append(sql)
        return {"status": "ok"}


@pytest.fixture
def executor() -> MockTransactionExecutor:
    return MockTransactionExecutor()


@pytest.fixture
def manager(executor: MockTransactionExecutor) -> TransactionManager:
    return TransactionManager(executor)


def test_basic_transaction(executor: MockTransactionExecutor, manager: TransactionManager) -> None:
    with manager.transaction() as ctx:
        ctx.execute("INSERT INTO users (name) VALUES ('alice')")
        ctx.execute("INSERT INTO logs (msg) VALUES ('user created')")

    assert executor.operations == [
        "BEGIN",
        "INSERT INTO users (name) VALUES ('alice')",
        "INSERT INTO logs (msg) VALUES ('user created')",
        "COMMIT",
    ]


def test_transaction_rollback_on_exception(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with pytest.raises(RuntimeError, match="Simulated failure"):
        with manager.transaction() as ctx:
            ctx.execute("INSERT INTO users (name) VALUES ('alice')")
            executor.fail_on = "INSERT INTO logs"
            ctx.execute("INSERT INTO logs (msg) VALUES ('user created')")

    assert executor.operations == [
        "BEGIN",
        "INSERT INTO users (name) VALUES ('alice')",
        "ROLLBACK",
    ]


def test_nested_transaction_creates_savepoint(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as outer_ctx:
        outer_ctx.execute("INSERT INTO users (name) VALUES ('alice')")
        with manager.transaction() as inner_ctx:
            inner_ctx.execute("INSERT INTO logs (msg) VALUES ('nested')")

    assert executor.operations == [
        "BEGIN",
        "INSERT INTO users (name) VALUES ('alice')",
        "SAVEPOINT sp_2",
        "INSERT INTO logs (msg) VALUES ('nested')",
        "RELEASE SAVEPOINT sp_2",
        "COMMIT",
    ]


def test_nested_transaction_failure_rollback_to_savepoint(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as outer_ctx:
        outer_ctx.execute("INSERT INTO users (name) VALUES ('alice')")
        try:
            with manager.transaction() as inner_ctx:
                executor.fail_on = "INSERT INTO logs"
                inner_ctx.execute("INSERT INTO logs (msg) VALUES ('will fail')")
        except RuntimeError:
            pass  # Inner failure caught, outer continues
        outer_ctx.execute("INSERT INTO users (name) VALUES ('bob')")

    assert executor.operations == [
        "BEGIN",
        "INSERT INTO users (name) VALUES ('alice')",
        "SAVEPOINT sp_2",
        "ROLLBACK TO SAVEPOINT sp_2",
        "INSERT INTO users (name) VALUES ('bob')",
        "COMMIT",
    ]


def test_triple_nested_savepoints(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as ctx1:
        ctx1.execute("L1")
        with manager.transaction() as ctx2:
            ctx2.execute("L2")
            with manager.transaction() as ctx3:
                ctx3.execute("L3")

    assert executor.operations == [
        "BEGIN",
        "L1",
        "SAVEPOINT sp_2",
        "L2",
        "SAVEPOINT sp_3",
        "L3",
        "RELEASE SAVEPOINT sp_3",
        "RELEASE SAVEPOINT sp_2",
        "COMMIT",
    ]


def test_manual_rollback(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as ctx:
        ctx.execute("INSERT INTO users (name) VALUES ('alice')")
        ctx.rollback()

    assert executor.operations == [
        "BEGIN",
        "INSERT INTO users (name) VALUES ('alice')",
        "ROLLBACK",
    ]


def test_manual_rollback_nested(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as outer_ctx:
        outer_ctx.execute("INSERT INTO users (name) VALUES ('alice')")
        with manager.transaction() as inner_ctx:
            inner_ctx.execute("INSERT INTO logs (msg) VALUES ('will rollback')")
            inner_ctx.rollback()
        outer_ctx.execute("INSERT INTO users (name) VALUES ('bob')")

    assert executor.operations == [
        "BEGIN",
        "INSERT INTO users (name) VALUES ('alice')",
        "SAVEPOINT sp_2",
        "INSERT INTO logs (msg) VALUES ('will rollback')",
        "ROLLBACK TO SAVEPOINT sp_2",
        "INSERT INTO users (name) VALUES ('bob')",
        "COMMIT",
    ]


def test_state_during_transaction(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    assert manager.state.active is False
    assert manager.state.depth == 0

    with manager.transaction():
        assert manager.state.active is True
        assert manager.state.depth == 1

        with manager.transaction():
            assert manager.state.depth == 2
            assert manager.state.savepoints == ["sp_2"]

        assert manager.state.depth == 1
        assert manager.state.savepoints == []

    assert manager.state.active is False
    assert manager.state.depth == 0


def test_state_after_successful_commit(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as ctx:
        ctx.execute("SELECT 1")

    state = manager.state
    assert state.active is False
    assert state.depth == 0
    assert state.savepoints == []


def test_state_after_rollback(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with pytest.raises(RuntimeError):
        with manager.transaction():
            raise RuntimeError("force rollback")

    state = manager.state
    assert state.active is False
    assert state.depth == 0
    assert state.savepoints == []


def test_execute_outside_transaction_raises_error(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    state = TransactionState()
    ctx = TransactionContext(executor, state)
    with pytest.raises(TransactionError, match="Cannot execute outside"):
        ctx.execute("SELECT 1")


def test_transaction_context_execute_delegates(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as ctx:
        result = ctx.execute("SELECT 1")
    assert result == {"status": "ok"}
    assert "SELECT 1" in executor.operations


def test_multiple_executes_in_transaction(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as ctx:
        ctx.execute("INSERT INTO a VALUES (1)")
        ctx.execute("INSERT INTO b VALUES (2)")
        ctx.execute("INSERT INTO c VALUES (3)")

    assert executor.operations == [
        "BEGIN",
        "INSERT INTO a VALUES (1)",
        "INSERT INTO b VALUES (2)",
        "INSERT INTO c VALUES (3)",
        "COMMIT",
    ]


def test_exception_in_nested_doesnt_affect_outer(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    with manager.transaction() as outer_ctx:
        outer_ctx.execute("outer_before")
        try:
            with manager.transaction():
                raise ValueError("inner fails")
        except ValueError:
            pass
        outer_ctx.execute("outer_after")

    assert "ROLLBACK TO SAVEPOINT sp_2" in executor.operations
    assert "outer_after" in executor.operations
    assert executor.operations[-1] == "COMMIT"


def test_transaction_error_has_correct_code() -> None:
    err = TransactionError("test error")
    assert err.code == "TRANSACTION_ERROR"
    assert err.retry_hint is False
    d = err.to_dict()
    assert d["code"] == "TRANSACTION_ERROR"
    assert d["message"] == "test error"


def test_transaction_state_model() -> None:
    state = TransactionState()
    assert state.active is False
    assert state.depth == 0
    assert state.savepoints == []
    state.active = True
    state.depth = 2
    state.savepoints = ["sp_2"]
    assert state.model_dump() == {
        "active": True,
        "depth": 2,
        "savepoints": ["sp_2"],
    }


def test_release_savepoint_failure_preserves_state(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    """If release_savepoint raises, state must remain consistent (not double-popped)."""
    with manager.transaction():
        with pytest.raises(RuntimeError, match="release_savepoint failed"):
            with manager.transaction():
                executor.fail_on_method = "release_savepoint"

    # After the inner failure the outer transaction should still be intact
    state = manager.state
    # After outer also exits cleanly, depth=0, active=False
    assert state.depth == 0
    assert state.active is False
    assert state.savepoints == []


def test_rollback_to_savepoint_failure_preserves_state(
    executor: MockTransactionExecutor, manager: TransactionManager
) -> None:
    """If rollback_to_savepoint raises, state must remain consistent (not double-popped)."""
    with pytest.raises(RuntimeError, match="rollback_to_savepoint failed"):
        with manager.transaction():
            with manager.transaction():
                executor.fail_on_method = "rollback_to_savepoint"
                raise ValueError("inner error")

    state = manager.state
    assert state.depth == 0
    assert state.active is False
