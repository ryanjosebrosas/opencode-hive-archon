"""Trace collection service for retrieval pipeline observability."""

from typing import Callable, Optional

from second_brain.contracts.trace import RetrievalTrace


# Type alias for trace callback
TraceCallback = Callable[[RetrievalTrace], None]


class TraceCollector:
    """
    In-memory trace collector with optional callback hook.

    Stores RetrievalTrace records in a list for inspection.
    Optionally calls a callback for each recorded trace,
    enabling future integration with file/DB/OTel exporters.
    """

    def __init__(
        self,
        callback: Optional[TraceCallback] = None,
        max_traces: int = 1000,
    ):
        self._traces: list[RetrievalTrace] = []
        self._callback = callback
        self._max_traces = max_traces

    def record(self, trace: RetrievalTrace) -> None:
        """
        Record a trace. Calls callback if registered.
        Evicts oldest trace if max_traces exceeded.
        """
        if len(self._traces) >= self._max_traces:
            self._traces.pop(0)
        self._traces.append(trace)
        if self._callback is not None:
            self._callback(trace)

    def get_traces(self) -> list[RetrievalTrace]:
        """Return all recorded traces (newest last)."""
        return list(self._traces)

    def get_by_id(self, trace_id: str) -> Optional[RetrievalTrace]:
        """Look up a trace by ID. Returns None if not found."""
        for trace in self._traces:
            if trace.trace_id == trace_id:
                return trace
        return None

    def get_latest(self, n: int = 1) -> list[RetrievalTrace]:
        """Return the N most recent traces."""
        return list(self._traces[-n:])

    def clear(self) -> None:
        """Clear all stored traces."""
        self._traces.clear()

    @property
    def count(self) -> int:
        """Number of traces currently stored."""
        return len(self._traces)
