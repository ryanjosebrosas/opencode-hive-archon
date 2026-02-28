"""Connection pool with circuit breaker for Supabase clients."""

import threading
import time
from enum import Enum
from typing import Any, Callable, Dict

from pydantic import BaseModel


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # All requests fail fast
    HALF_OPEN = "half_open"  # Allowing one probe request


class CircuitBreaker:
    """Circuit breaker for external service calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self._half_open_probe_active: bool = False
        self._lock = threading.Lock()
    
    def record_success(self) -> None:
        """Record successful operation and close the circuit."""
        with self._lock:
            # If we were in HALF_OPEN, reset the probe flag
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_probe_active = False
                
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
    
    def record_failure(self) -> None:
        """Record failed operation and update circuit state."""
        with self._lock:
            # If we were in HALF_OPEN, reset the probe flag since we're transitioning to another state
            if self.state == CircuitState.HALF_OPEN:
                self._half_open_probe_active = False
                
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold and self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        """Check if an operation can be executed."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.HALF_OPEN:
                if not self._half_open_probe_active:
                    self._half_open_probe_active = True
                    return True
                else:
                    return False  # Only one probe allowed in HALF_OPEN state
            
            # State is OPEN, check if recovery timeout passed
            if self.last_failure_time is not None:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.recovery_timeout:
                    # Transition to HALF_OPEN and allow exactly one operation immediately
                    self.state = CircuitState.HALF_OPEN
                    self._half_open_probe_active = True
                    return True
            
            return False
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            return self.state
    
    def transition_to_half_open(self) -> None:
        """Manually transition to half-open state."""
        with self._lock:
            self.state = CircuitState.HALF_OPEN
    
    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None


class PoolConfig(BaseModel):
    """Configuration for connection pool."""
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout: float = 30.0


class ConnectionPool:
    """Managed Supabase client pool with retry and circuit breaker."""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.circuit_failure_threshold,
            recovery_timeout=config.circuit_recovery_timeout,
        )
        self._client: Any | None = None
        self._active_count = 0
        self._total_requests = 0
        self._failed_requests = 0
        self._lock = threading.Lock()
    
    def get_client(self) -> Any:
        """Get Supabase client with lazy initialization."""
        with self._lock:
            if self._client is None:
                # For testing purposes, return a mock client
                # This would be replaced by actual client initialization in production 
                self._client = {"mock_client": True, "initialized_at": time.time()}
            return self._client
    
    def execute_with_retry(self, operation: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute operation with retry + circuit breaker."""
        if not self.circuit_breaker.can_execute():
            with self._lock:
                self._failed_requests += 1
            raise Exception("Circuit breaker is OPEN. Request blocked.")
        
        # Increment total request count
        with self._lock:
            self._total_requests += 1
        
        # Track active operations
        with self._lock:
            self._active_count += 1
        
        try:
            # Try the operation with retries
            last_exception = None
            delay = self.config.retry_delay
            
            for attempt in range(self.config.max_retries + 1):
                try:
                    if not self.circuit_breaker.can_execute():
                        raise Exception("Circuit breaker is OPEN. Request blocked.")
                    
                    result = operation(*args, **kwargs)
                    self.circuit_breaker.record_success()
                    return result
                    
                except Exception as e:
                    last_exception = e
                    self.circuit_breaker.record_failure()
                    with self._lock:
                        self._failed_requests += 1
                    
                    # If max attempts reached, break out of loop
                    if attempt >= self.config.max_retries:
                        break
                    
                    # Wait before retrying, increasing delay each time
                    time.sleep(delay)
                    delay *= self.config.retry_backoff
            
            # If we get here, all retries have failed
            raise last_exception if last_exception else Exception("Operation failed")
            
        finally:
            # Decrement active count
            with self._lock:
                self._active_count -= 1
    
    def health_check(self) -> Dict[str, Any]:
        """Return pool health metrics."""
        with self._lock:
            total_requests = self._total_requests
            failed_requests = self._failed_requests
            active_count = self._active_count
            state = self.circuit_breaker.get_state().value
        
        return {
            "state": state,
            "active_connections": active_count,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "failure_rate": failed_requests / total_requests if total_requests > 0 else 0,
            "config": {
                "max_retries": self.config.max_retries,
                "retry_delay": self.config.retry_delay,
                "retry_backoff": self.config.retry_backoff,
                "circuit_failure_threshold": self.config.circuit_failure_threshold,
                "circuit_recovery_timeout": self.config.circuit_recovery_timeout,
            }
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return pool metrics."""
        with self._lock:
            return {
                "active_connections": self._active_count,
                "total_requests": self._total_requests,
                "failed_requests": self._failed_requests,
                "circuit_state": self.circuit_breaker.get_state().value,
            }