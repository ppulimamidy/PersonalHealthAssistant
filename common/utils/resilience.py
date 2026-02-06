"""
Resilience Patterns
Provides circuit breakers, retries, timeouts, and other resilience patterns for microservices.
"""

import asyncio
import time
import logging
from typing import Any, Callable, Optional, Type, Union
from functools import wraps
from enum import Enum
import redis.asyncio as redis

from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
        name: str = "circuit_breaker"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.redis_client: Optional[redis.Redis] = None
        
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis for distributed circuit breaker state"""
        try:
            self.redis_client = redis.from_url(
                settings.external_services.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info(f"Redis client initialized for circuit breaker: {self.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis for circuit breaker {self.name}: {e}")
            self.redis_client = None
    
    async def _get_state_from_redis(self) -> Optional[CircuitState]:
        """Get circuit breaker state from Redis"""
        if not self.redis_client:
            return None
        
        try:
            state_data = await self.redis_client.get(f"circuit_breaker:{self.name}")
            if state_data:
                return CircuitState(state_data)
        except Exception as e:
            logger.error(f"Error getting circuit breaker state from Redis: {e}")
        return None
    
    async def _set_state_to_redis(self, state: CircuitState):
        """Set circuit breaker state to Redis"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.set(
                f"circuit_breaker:{self.name}",
                state.value,
                ex=self.recovery_timeout
            )
        except Exception as e:
            logger.error(f"Error setting circuit breaker state to Redis: {e}")
    
    async def _record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            await self._set_state_to_redis(self.state)
            logger.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")
    
    async def _record_success(self):
        """Record a success and potentially close the circuit"""
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            await self._set_state_to_redis(self.state)
            logger.info(f"Circuit breaker {self.name} closed after successful request")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    async def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        if self.state == CircuitState.OPEN:
            if self.last_failure_time and time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                await self._set_state_to_redis(self.state)
                logger.info(f"Circuit breaker {self.name} moved to half-open state")
                return True
        return False
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        # Check Redis state first
        redis_state = await self._get_state_from_redis()
        if redis_state:
            self.state = redis_state
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if not await self._should_attempt_reset():
                raise Exception(f"Circuit breaker {self.name} is open")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._record_success()
            return result
            
        except self.expected_exception as e:
            await self._record_failure()
            raise e
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for circuit breaker"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper

class RetryHandler:
    """Retry pattern implementation"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except self.exceptions as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    logger.error(f"Function {func.__name__} failed after {self.max_attempts} attempts")
                    raise last_exception
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_delay * (self.backoff_factor ** attempt),
                    self.max_delay
                )
                
                logger.warning(
                    f"Function {func.__name__} failed (attempt {attempt + 1}/{self.max_attempts}), "
                    f"retrying in {delay:.2f}s: {str(e)}"
                )
                
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for retry pattern"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper

class TimeoutHandler:
    """Timeout pattern implementation"""
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with timeout"""
        if asyncio.iscoroutinefunction(func):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout)
        else:
            # For sync functions, run in thread pool
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, func, *args, **kwargs),
                timeout=self.timeout
            )
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for timeout pattern"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper

class Bulkhead:
    """Bulkhead pattern implementation"""
    
    def __init__(self, max_concurrent: int = 10, name: str = "bulkhead"):
        self.max_concurrent = max_concurrent
        self.name = name
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead protection"""
        async with self.semaphore:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, func, *args, **kwargs)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for bulkhead pattern"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper

class ResiliencePatterns:
    """Combined resilience patterns"""
    
    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry: Optional[RetryHandler] = None,
        timeout: Optional[TimeoutHandler] = None,
        bulkhead: Optional[Bulkhead] = None
    ):
        self.circuit_breaker = circuit_breaker
        self.retry = retry
        self.timeout = timeout
        self.bulkhead = bulkhead
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with all resilience patterns"""
        # Apply patterns in order: bulkhead -> timeout -> retry -> circuit_breaker
        wrapped_func = func
        
        if self.circuit_breaker:
            wrapped_func = self.circuit_breaker(wrapped_func)
        
        if self.retry:
            wrapped_func = self.retry(wrapped_func)
        
        if self.timeout:
            wrapped_func = self.timeout(wrapped_func)
        
        if self.bulkhead:
            wrapped_func = self.bulkhead(wrapped_func)
        
        if asyncio.iscoroutinefunction(wrapped_func):
            return await wrapped_func(*args, **kwargs)
        else:
            return wrapped_func(*args, **kwargs)
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator for combined resilience patterns"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper

# Pre-configured resilience patterns
def create_service_resilience(
    service_name: str,
    max_concurrent: int = 10,
    timeout: float = 30.0,
    max_retries: int = 3
) -> ResiliencePatterns:
    """Create pre-configured resilience patterns for a service"""
    
    circuit_breaker = CircuitBreaker(
        failure_threshold=settings.resilience.circuit_breaker_fail_max,
        recovery_timeout=settings.resilience.circuit_breaker_reset_timeout,
        name=f"{service_name}_circuit_breaker"
    )
    
    retry = RetryHandler(
        max_attempts=max_retries,
        base_delay=settings.resilience.retry_base_delay,
        max_delay=settings.resilience.retry_max_delay
    )
    
    timeout_handler = TimeoutHandler(timeout=timeout)
    
    bulkhead = Bulkhead(max_concurrent=max_concurrent, name=f"{service_name}_bulkhead")
    
    return ResiliencePatterns(
        circuit_breaker=circuit_breaker,
        retry=retry,
        timeout=timeout_handler,
        bulkhead=bulkhead
    )

# Convenience decorators
def with_resilience(
    service_name: str,
    max_concurrent: int = 10,
    timeout: float = 30.0,
    max_retries: int = 3
):
    """Decorator to add resilience patterns to a function"""
    resilience = create_service_resilience(service_name, max_concurrent, timeout, max_retries)
    return resilience

def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    name: str = "default"
):
    """Decorator to add circuit breaker to a function"""
    circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout, name=name)
    return circuit_breaker

def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    """Decorator to add retry logic to a function"""
    retry = RetryHandler(max_attempts, base_delay, max_delay)
    return retry

def with_timeout(timeout: float = 30.0):
    """Decorator to add timeout to a function"""
    timeout_handler = TimeoutHandler(timeout)
    return timeout_handler

def with_bulkhead(max_concurrent: int = 10, name: str = "default"):
    """Decorator to add bulkhead pattern to a function"""
    bulkhead = Bulkhead(max_concurrent, name)
    return bulkhead 