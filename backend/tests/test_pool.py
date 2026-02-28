"""Tests for the connection pool and circuit breaker functionality."""

import time

import pytest

from second_brain.services.pool import CircuitBreaker, CircuitState, ConnectionPool, PoolConfig


def test_circuitbreaker_starts_closed():
    """Test circuit breaker starts in CLOSED state."""
    cb = CircuitBreaker()
    assert cb.get_state() == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuitbreaker_record_success_stays_closed():
    """Test recording success keeps circuit closed."""
    cb = CircuitBreaker()
    cb.record_success()
    assert cb.get_state() == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuitbreaker_record_failures_under_threshold():
    """Test circuit stays closed under failure threshold."""
    cb = CircuitBreaker(failure_threshold=3)
    cb.record_failure()
    assert cb.get_state() == CircuitState.CLOSED
    assert cb.failure_count == 1
    
    cb.record_failure()
    assert cb.get_state() == CircuitState.CLOSED
    assert cb.failure_count == 2


def test_circuitbreaker_opens_after_threshold():
    """Test circuit opens after reaching failure threshold."""
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.get_state() == CircuitState.OPEN
    assert cb.failure_count == 2


def test_circuitbreaker_can_execute_closed():
    """Test can_execute returns True in CLOSED state."""
    cb = CircuitBreaker()
    assert cb.can_execute() is True


def test_circuitbreaker_can_execute_open():
    """Test can_execute returns False in OPEN state."""
    cb = CircuitBreaker(failure_threshold=1)
    cb.record_failure()  # Should open the circuit
    assert cb.can_execute() is False


def test_circuitbreaker_transitions_to_half_open_after_timeout():
    """Test circuit transitions to HALF_OPEN after recovery timeout."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)  # 10ms timeout
    cb.record_failure()  # Open the circuit
    assert cb.get_state() == CircuitState.OPEN
    
    time.sleep(0.02)  # Wait for recovery timeout
    assert cb.can_execute() is True  # This should trigger the transition
    assert cb.get_state() == CircuitState.HALF_OPEN


def test_circuitbreaker_half_open_success_goes_closed():
    """Test half-open success closes the circuit."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
    cb.record_failure()  # Open the circuit
    time.sleep(0.02)  # Wait for recovery timeout
    # Call can_execute to trigger possible transition
    _ = cb.can_execute()  # This will trigger any pending state changes due to timeout
    assert cb.get_state() == CircuitState.HALF_OPEN
    
    cb.record_success()  # Success after half-open should close circuit
    assert cb.get_state() == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuitbreaker_half_open_failure_goes_open():
    """Test half-open failure opens the circuit."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.01)  # Higher threshold
    cb.record_failure()
    cb.record_failure()  
    assert cb.get_state() == CircuitState.OPEN
    
    time.sleep(0.02)  # Wait for recovery timeout
    # Calling can_execute triggers the transition to half-open
    _ = cb.can_execute()  # This will transition from OPEN to HALF_OPEN
    assert cb.get_state() == CircuitState.HALF_OPEN
    
    cb.record_failure()  # Failure in half-open state should go back to open
    assert cb.get_state() == CircuitState.OPEN
    assert cb.failure_count == 3  # 2 initial + 1 after reopening


def test_connectionpool_get_client_creates_new():
    """Test get_client creates and caches a client."""
    config = PoolConfig()
    pool = ConnectionPool(config)
    
    client1 = pool.get_client()
    client2 = pool.get_client()
    
    # Clients should be the same (cached)
    assert client1 is not None
    assert client1 == client2


def test_connectionpool_execute_success_first_attempt():
    """Test execute_with_retry succeeds on first attempt."""
    config = PoolConfig()
    pool = ConnectionPool(config)
    
    def success_operation():
        return "success_result"
    
    result = pool.execute_with_retry(success_operation)
    assert result == "success_result"
    
    # Metrics reflect successful operation
    metrics = pool.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["failed_requests"] == 0
    assert metrics["circuit_state"] == "closed"


def test_connectionpool_execute_success_after_retry():
    """Test execute_with_retry eventually succeeds after failures."""
    config = PoolConfig(max_retries=2)
    pool = ConnectionPool(config)
    
    call_count = 0
    
    def sometimes_fails():
        nonlocal call_count
        call_count += 1
        if call_count < 2:  # First call fails
            raise Exception("transient error")
        return f"success_after_{call_count}_attempts"
    
    result = pool.execute_with_retry(sometimes_fails)
    assert result == "success_after_2_attempts"
    assert call_count == 2  # Called twice: once failed, once succeeded
    
    # Metrics reflect eventual success
    metrics = pool.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["failed_requests"] == 1  # One failure before success


def test_connectionpool_execute_fails_after_max_retries():
    """Test execute_with_retry fails after max retries."""
    config = PoolConfig(max_retries=2)
    pool = ConnectionPool(config)
    
    def always_fails():
        raise Exception("permanent_error")
    
    with pytest.raises(Exception) as exc_info:
        pool.execute_with_retry(always_fails)
    
    assert str(exc_info.value) == "permanent_error"
    
    # Metrics reflect failures
    metrics = pool.get_metrics()
    assert metrics["total_requests"] == 1
    assert metrics["failed_requests"] == 3  # Initial call + 2 retries


def test_connectionpool_execute_respects_circuit_breaker():
    """Test execute_with_retry respects circuit breaker OPEN state."""
    config = PoolConfig(max_retries=2)
    pool = ConnectionPool(config)
    
    # Force circuit to OPEN by causing enough failures 
    pool.circuit_breaker.record_failure()
    pool.circuit_breaker.record_failure()
    pool.circuit_breaker.record_failure()
    pool.circuit_breaker.record_failure()
    pool.circuit_breaker.record_failure()  # Threshold reached
    
    def operation():
        return "should_not_be_called"
    
    # Now execution should fail due to circuit breaker
    with pytest.raises(Exception) as exc_info:
        pool.execute_with_retry(operation)
    
    assert "Circuit breaker is OPEN" in str(exc_info.value)


def test_connectionpool_health_check_returns_metrics():
    """Test health_check returns expected metrics."""
    config = PoolConfig(
        max_retries=3,
        retry_delay=1.5,
        retry_backoff=2.0,
        circuit_failure_threshold=5,
        circuit_recovery_timeout=60.0
    )
    pool = ConnectionPool(config)
    
    # Execute an operation to update metrics
    def operation():
        return "ok"
    
    pool.execute_with_retry(operation)
    
    health = pool.health_check()
    
    assert "state" in health
    assert "active_connections" in health
    assert "total_requests" in health
    assert "failed_requests" in health
    assert "failure_rate" in health
    assert "config" in health
    
    assert health["state"] == "closed"
    assert health["total_requests"] == 1
    assert health["config"]["max_retries"] == 3
    assert health["config"]["retry_delay"] == 1.5


def test_connectionpool_get_metrics_format():
    """Test get_metrics returns correct format."""
    config = PoolConfig()
    pool = ConnectionPool(config)
    
    # Execute to update metrics
    def operation():
        raise Exception("fake error")  # This will be caught and counted
    
    # We expect this to fail, so wrap it to not break the test
    try:
        pool.execute_with_retry(operation)
    except Exception:
        pass  # Expected
    
    metrics = pool.get_metrics()
    
    expected_keys = ["active_connections", "total_requests", "failed_requests", "circuit_state"]
    for key in expected_keys:
        assert key in metrics


def test_connectionpool_thread_safety():
    """Test thread safety of active connection counting."""
    config = PoolConfig()
    pool = ConnectionPool(config)
    
    # Shared counter among threads
    operation_call_count = 0
    
    def test_operation():
        import time
        # Sleep to simulate an operation and increase chance of race condition
        time.sleep(0.001)  # Very brief sleep
        nonlocal operation_call_count
        operation_call_count += 1
        return f"result_{operation_call_count}"
    
    # Run multiple threads executing operations in parallel
    import threading
    threads = []
    
    for _ in range(5):
        t = threading.Thread(target=lambda: pool.execute_with_retry(test_operation))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # The result should be consistent despite parallel execution
    # Active connections should balance properly
    metrics = pool.get_metrics()
    assert metrics["active_connections"] == 0  # Should be zero after all operations
    assert metrics["total_requests"] == 5


def test_pool_config_from_settings():
    """Test PoolConfig can be created from settings."""
    # Test default values
    config = PoolConfig()
    assert config.max_retries == 3
    assert config.retry_delay == 1.0
    assert config.circuit_failure_threshold == 5
    assert config.circuit_recovery_timeout == 30.0
    
    # Test custom values
    config = PoolConfig(
        max_retries=2,
        retry_delay=0.5,
        circuit_failure_threshold=3,
        circuit_recovery_timeout=15.0
    )
    assert config.max_retries == 2
    assert config.retry_delay == 0.5
    assert config.circuit_failure_threshold == 3
    assert config.circuit_recovery_timeout == 15.0


def test_circuitbreaker_half_open_single_probe():
    """Test that HALF_OPEN state allows only one probe request."""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)  # Fail immediately & set short timeout
    
    # Force circuit to OPEN by failing once
    cb.record_failure()
    assert cb.get_state() == CircuitState.OPEN
    
    # Wait for recovery timeout to pass
    time.sleep(0.02)
    
    # Transition to HALF_OPEN by calling can_execute
    assert cb.can_execute() is True  # First probe allowed
    assert cb.get_state() == CircuitState.HALF_OPEN
    # At this point, _half_open_probe_active should be True
    
    # Try to execute another operation while still in HALF_OPEN  
    # This should return False because probe is already active
    assert cb.can_execute() is False  # Second call blocked since first probe is still active


def test_settings_has_pool_config_fields():
    """Test Settings has the new pool configuration fields."""
    import second_brain.config
    settings = second_brain.config.get_settings()
    
    # Verify the settings class has the new fields
    assert hasattr(settings, 'supabase_max_retries')
    assert hasattr(settings, 'supabase_retry_delay') 
    assert hasattr(settings, 'supabase_circuit_failure_threshold')
    assert hasattr(settings, 'supabase_circuit_recovery_timeout')
    assert hasattr(settings, 'supabase_retry_backoff')  # Added new field
    
    # Test that settings are accessible with expected values
    assert settings.supabase_max_retries == 3
    assert settings.supabase_retry_delay == 1.0
    assert settings.supabase_retry_backoff == 2.0  # Added assertion for new field
    assert settings.supabase_circuit_failure_threshold == 5
    assert settings.supabase_circuit_recovery_timeout == 30.0