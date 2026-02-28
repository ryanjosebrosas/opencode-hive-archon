"""Transaction management with nested savepoint support."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Protocol

from pydantic import BaseModel

from second_brain.errors import SecondBrainError
from second_brain.logging_config import get_logger

logger = get_logger(__name__)


class TransactionError(SecondBrainError):
    """Transaction operation failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "TRANSACTION_ERROR",
        context: dict[str, Any] | None = None,
        retry_hint: bool = False,
    ) -> None:
        super().__init__(message, code=code, context=context, retry_hint=retry_hint)


class TransactionExecutor(Protocol):
    """Protocol for database transaction execution."""

    def begin(self) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def create_savepoint(self, name: str) -> None: ...
    def release_savepoint(self, name: str) -> None: ...
    def rollback_to_savepoint(self, name: str) -> None: ...
    def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any: ...


class TransactionState(BaseModel):
    """Current transaction state."""

    active: bool = False
    depth: int = 0
    savepoints: list[str] = []


class TransactionContext:
    """Provides execute() and manual rollback() inside a transaction block."""

    def __init__(self, executor: TransactionExecutor, state: TransactionState) -> None:
        self._executor = executor
        self._state = state
        self._rollback_requested: bool = False

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> Any:
        """Execute SQL within the transaction."""
        if not self._state.active:
            raise TransactionError(
                "Cannot execute outside an active transaction",
                context={"depth": self._state.depth},
            )
        return self._executor.execute(sql, params)

    def rollback(self) -> None:
        """Request manual rollback of current transaction/savepoint level."""
        self._rollback_requested = True

    @property
    def rollback_requested(self) -> bool:
        """Whether manual rollback was requested."""
        return self._rollback_requested


class TransactionManager:
    """Manages transactions with nested savepoint support."""

    def __init__(self, executor: TransactionExecutor) -> None:
        self._executor = executor
        self._state = TransactionState()

    @property
    def state(self) -> TransactionState:
        """Current transaction state (read-only copy)."""
        return self._state.model_copy()

    @contextmanager
    def transaction(self) -> Generator[TransactionContext, None, None]:
        """Context manager for transactions with nested savepoint support.

        First call: BEGIN (depth 0->1)
        Nested calls: SAVEPOINT sp_N (depth increments)
        On success: RELEASE SAVEPOINT (nested) or COMMIT (top-level)
        On exception: ROLLBACK TO SAVEPOINT (nested) or ROLLBACK (top-level), re-raise
        Manual rollback via ctx.rollback(): same as exception but no re-raise
        """
        is_nested = self._state.depth > 0

        if is_nested:
            savepoint_name = f"sp_{self._state.depth + 1}"
            self._executor.create_savepoint(savepoint_name)
            self._state.depth += 1
            self._state.savepoints.append(savepoint_name)
            logger.info("savepoint_created", savepoint=savepoint_name, depth=self._state.depth)
        else:
            self._executor.begin()
            self._state.active = True
            self._state.depth = 1
            logger.info("transaction_begun", depth=1)

        ctx = TransactionContext(self._executor, self._state)

        try:
            yield ctx

            if ctx.rollback_requested:
                if is_nested:
                    savepoint_name = self._state.savepoints[-1]
                    self._executor.rollback_to_savepoint(savepoint_name)
                    self._state.savepoints.pop()
                    self._state.depth -= 1
                    logger.info("savepoint_rolled_back", savepoint=savepoint_name, reason="manual")
                else:
                    self._executor.rollback()
                    self._state.active = False
                    self._state.depth = 0
                    self._state.savepoints = []
                    logger.info("transaction_rolled_back", reason="manual")
            else:
                if is_nested:
                    savepoint_name = self._state.savepoints[-1]
                    self._executor.release_savepoint(savepoint_name)
                    self._state.savepoints.pop()
                    self._state.depth -= 1
                    logger.info("savepoint_released", savepoint=savepoint_name)
                else:
                    self._executor.commit()
                    self._state.active = False
                    self._state.depth = 0
                    logger.info("transaction_committed")

        except Exception:
            if is_nested:
                savepoint_name = self._state.savepoints[-1]
                self._executor.rollback_to_savepoint(savepoint_name)
                self._state.savepoints.pop()
                self._state.depth -= 1
                logger.warning("savepoint_rolled_back", savepoint=savepoint_name, reason="exception")
            else:
                self._executor.rollback()
                self._state.active = False
                self._state.depth = 0
                self._state.savepoints = []
                logger.warning("transaction_rolled_back", reason="exception")
            raise
