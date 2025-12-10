from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import lru_cache
import hashlib
from pathlib import Path

from ca.config import load_config


# Configure logging
logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    OLLAMA = "ollama"
    LITELLM = "litellm"
    MOCK = "mock"  # For testing


@dataclass
class LLMResponse:
    """Structured LLM response."""
    content: str
    model: str
    tokens_used: int
    cost_estimate: float = 0.0
    latency_ms: float = 0.0
    cache_hit: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    """Structured LLM request."""
    system: str
    user: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    provider: Optional[LLMProvider] = None
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMAdapter:
    """
    Advanced LLM adapter with multiple backend support.
    Handles provider abstraction, caching, error handling, and monitoring.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_config().get("llm", {})
        self.provider = LLMProvider(self.config.get("provider", "openai"))
        self.default_model = self.config.get("model", "gpt-3.5-turbo")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1000)
        
        # Cache configuration
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.cache_max_size = self.config.get("cache_max_size", 1000)
        self._response_cache: Dict[str, LLMResponse] = {}
        
        # Rate limiting
        self.rate_limit_requests = self.config.get("rate_limit_requests", 60)
        self.rate_limit_period = self.config.get("rate_limit_period", 60)  # seconds
        self._request_timestamps: List[float] = []
        
        # Initialize provider client
        self.client = self._initialize_client()
        
        logger.info(f"LLM Adapter initialized with provider: {self.provider.value}")
    
    def _initialize_client(self) -> Any:
        """Initialize the appropriate LLM client based on provider."""
        try:
            if self.provider == LLMProvider.OPENAI:
                return self._init_openai_client()
            elif self.provider == LLMProvider.ANTHROPIC:
                return self._init_anthropic_client()
            elif self.provider == LLMProvider.LOCAL:
                return self._init_local_client()
            elif self.provider == LLMProvider.OLLAMA:
                return self._init_ollama_client()
            elif self.provider == LLMProvider.LITELLM:
                return self._init_litellm_client()
            elif self.provider == LLMProvider.MOCK:
                return self._init_mock_client()
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except ImportError as e:
            logger.error(f"Failed to import required package for {self.provider}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} client: {e}")
            raise
    
    def _init_openai_client(self) -> Any:
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            api_key = self.config.get("api_key") or self.config.get("openai_api_key")
            if not api_key:
                logger.warning("OpenAI API key not found in config")
            return OpenAI(api_key=api_key)
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            raise
    
    def _init_anthropic_client(self) -> Any:
        """Initialize Anthropic client."""
        try:
            import anthropic
            api_key = self.config.get("api_key") or self.config.get("anthropic_api_key")
            if not api_key:
                logger.warning("Anthropic API key not found in config")
            return anthropic.Anthropic(api_key=api_key)
        except ImportError:
            logger.error("Anthropic package not installed. Install with: pip install anthropic")
            raise
    
    def _init_local_client(self) -> Any:
        """Initialize local model client."""
        try:
            # This is a stub - implement based on your local model setup
            # Could be transformers, llama.cpp, etc.
            logger.info("Using local model provider (stub implementation)")
            return {"type": "local", "model_path": self.config.get("model_path")}
        except Exception as e:
            logger.error(f"Failed to initialize local client: {e}")
            raise
    
    def _init_ollama_client(self) -> Any:
        """Initialize Ollama client."""
        try:
            import ollama
            host = self.config.get("ollama_host", "http://localhost:11434")
            logger.info(f"Using Ollama at {host}")
            return ollama.Client(host=host)
        except ImportError:
            logger.error("Ollama package not installed. Install with: pip install ollama")
            raise
    
    def _init_litellm_client(self) -> Any:
        """Initialize LiteLLM client."""
        try:
            import litellm
            # LiteLLM uses environment variables for configuration
            logger.info("Using LiteLLM for multi-provider support")
            return litellm
        except ImportError:
            logger.error("LiteLLM package not installed. Install with: pip install litellm")
            raise
    
    def _init_mock_client(self) -> Any:
        """Initialize mock client for testing."""
        logger.info("Using mock LLM client (testing only)")
        return {"type": "mock"}
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        if not self.rate_limit_requests:
            return True
        
        now = time.time()
        # Remove timestamps outside the period
        self._request_timestamps = [
            ts for ts in self._request_timestamps 
            if now - ts < self.rate_limit_period
        ]
        
        if len(self._request_timestamps) >= self.rate_limit_requests:
            wait_time = self.rate_limit_period - (now - self._request_timestamps[0])
            logger.warning(f"Rate limit exceeded. Wait {wait_time:.1f}s")
            return False
        
        return True
    
    def _get_cache_key(self, request: LLMRequest) -> str:
        """Generate cache key for request."""
        content = f"{request.system}|{request.user}|{request.model}|{request.temperature}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def call(self, request: LLMRequest) -> LLMResponse:
        """
        Main method to call LLM with structured request.
        
        Args:
            request: LLMRequest object with system and user prompts
            
        Returns:
            LLMResponse object with content and metadata
        """
        start_time = time.time()
        
        # Check rate limit
        if not self._check_rate_limit():
            return LLMResponse(
                content="Rate limit exceeded. Please try again shortly.",
                model=request.model or self.default_model,
                tokens_used=0,
                cost_estimate=0.0,
                latency_ms=0.0,
                error="Rate limit exceeded",
                metadata={"rate_limited": True}
            )
        
        # Check cache
        cache_key = self._get_cache_key(request)
        if self.cache_enabled and cache_key in self._response_cache:
            cached = self._response_cache[cache_key]
            cached.cache_hit = True
            cached.latency_ms = (time.time() - start_time) * 1000
            logger.debug(f"Cache hit for request: {cache_key[:16]}...")
            return cached
        
        try:
            # Record request timestamp
            self._request_timestamps.append(time.time())
            
            # Call appropriate provider
            if self.provider == LLMProvider.OPENAI:
                response = self._call_openai(request)
            elif self.provider == LLMProvider.ANTHROPIC:
                response = self._call_anthropic(request)
            elif self.provider == LLMProvider.LOCAL:
                response = self._call_local(request)
            elif self.provider == LLMProvider.OLLAMA:
                response = self._call_ollama(request)
            elif self.provider == LLMProvider.LITELLM:
                response = self._call_litellm(request)
            elif self.provider == LLMProvider.MOCK:
                response = self._call_mock(request)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Calculate latency
            response.latency_ms = (time.time() - start_time) * 1000
            
            # Cache the response
            if self.cache_enabled and not response.error:
                if len(self._response_cache) >= self.cache_max_size:
                    # Remove oldest entry (FIFO)
                    oldest_key = next(iter(self._response_cache))
                    del self._response_cache[oldest_key]
                self._response_cache[cache_key] = response
            
            logger.info(f"LLM call completed: {response.tokens_used} tokens, "
                       f"{response.latency_ms:.0f}ms, model: {response.model}")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return LLMResponse(
                content=f"Error processing request: {str(e)[:100]}",
                model=request.model or self.default_model,
                tokens_used=0,
                cost_estimate=0.0,
                latency_ms=(time.time() - start_time) * 1000,
                error=str(e),
                metadata={"failed": True}
            )
    
    def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """Call OpenAI API."""
        try:
            model = request.model or self.default_model
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user}
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=request.stream
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Estimate cost (very rough)
            cost_estimate = self._estimate_openai_cost(model, tokens_used)
            
            return LLMResponse(
                content=content or "",
                model=model,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "provider": "openai"
                }
            )
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _call_anthropic(self, request: LLMRequest) -> LLMResponse:
        """Call Anthropic API."""
        try:
            model = request.model or self.default_model
            response = self.client.messages.create(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=request.system,
                messages=[{"role": "user", "content": request.user}]
            )
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            # Estimate cost (very rough)
            cost_estimate = self._estimate_anthropic_cost(model, tokens_used)
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                metadata={
                    "finish_reason": response.stop_reason,
                    "provider": "anthropic"
                }
            )
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def _call_local(self, request: LLMRequest) -> LLMResponse:
        """Call local model."""
        # This is a stub implementation
        # In practice, you'd integrate with your local model here
        model = request.model or self.default_model
        mock_response = f"[Local model: {model}]\n\nSystem: {request.system[:50]}...\n\nUser: {request.user[:100]}..."
        
        return LLMResponse(
            content=mock_response,
            model=model,
            tokens_used=len(mock_response.split()),
            cost_estimate=0.0,
            metadata={"provider": "local", "stub": True}
        )
    
    def _call_ollama(self, request: LLMRequest) -> LLMResponse:
        """Call Ollama API."""
        try:
            model = request.model or self.default_model
            response = self.client.chat(
                model=model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user}
                ],
                options={
                    "temperature": request.temperature,
                    "num_predict": request.max_tokens
                }
            )
            
            content = response["message"]["content"]
            # Ollama doesn't return token counts by default
            tokens_used = len(content.split()) * 1.3  # Rough estimate
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=int(tokens_used),
                cost_estimate=0.0,
                metadata={"provider": "ollama"}
            )
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    def _call_litellm(self, request: LLMRequest) -> LLMResponse:
        """Call via LiteLLM."""
        try:
            model = request.model or self.default_model
            response = self.client.completion(
                model=model,
                messages=[
                    {"role": "system", "content": request.system},
                    {"role": "user", "content": request.user}
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                cost_estimate=0.0,  # LiteLLM might provide cost tracking
                metadata={"provider": "litellm"}
            )
        except Exception as e:
            logger.error(f"LiteLLM error: {e}")
            raise
    
    def _call_mock(self, request: LLMRequest) -> LLMResponse:
        """Mock LLM call for testing."""
        model = request.model or self.default_model
        mock_response = f"[Mock LLM Response]\nSystem context: {request.system[:30]}...\n\nBased on your input: {request.user[:50]}...\n\nI understand and will respond thoughtfully."
        
        return LLMResponse(
            content=mock_response,
            model=model,
            tokens_used=len(mock_response.split()),
            cost_estimate=0.0,
            metadata={"provider": "mock", "test": True}
        )
    
    def _estimate_openai_cost(self, model: str, tokens: int) -> float:
        """Very rough OpenAI cost estimation."""
        # Prices per 1K tokens (as of 2024, approximate)
        prices = {
            "gpt-4": (0.03, 0.06),  # input, output per 1K tokens
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-3.5-turbo": (0.0005, 0.0015),
        }
        
        for model_prefix, (input_price, output_price) in prices.items():
            if model.startswith(model_prefix):
                # Rough estimate: assume 2:1 input:output ratio
                input_tokens = tokens * 0.67
                output_tokens = tokens * 0.33
                cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
                return round(cost, 4)
        
        return 0.0
    
    def _estimate_anthropic_cost(self, model: str, tokens: int) -> float:
        """Very rough Anthropic cost estimation."""
        prices = {
            "claude-3-opus": (0.015, 0.075),
            "claude-3-sonnet": (0.003, 0.015),
            "claude-3-haiku": (0.00025, 0.00125),
        }
        
        for model_prefix, (input_price, output_price) in prices.items():
            if model.startswith(model_prefix):
                # Rough estimate: assume 2:1 input:output ratio
                input_tokens = tokens * 0.67
                output_tokens = tokens * 0.33
                cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
                return round(cost, 4)
        
        return 0.0
    
    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._response_cache.clear()
        logger.info("LLM response cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "provider": self.provider.value,
            "cache_size": len(self._response_cache),
            "cache_hits": sum(1 for r in self._response_cache.values() if r.cache_hit),
            "total_calls": len(self._request_timestamps),
            "rate_limit": {
                "requests": self.rate_limit_requests,
                "period": self.rate_limit_period,
                "current_window": len(self._request_timestamps)
            }
        }


# Global adapter instance for convenience
_adapter_instance: Optional[LLMAdapter] = None


def get_llm_adapter(config: Optional[Dict[str, Any]] = None) -> LLMAdapter:
    """Get or create global LLM adapter instance."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = LLMAdapter(config)
    return _adapter_instance


def call_llm(system: str, user: str, **kwargs) -> str:
    """
    Convenience function for backward compatibility.
    
    Args:
        system: System prompt
        user: User prompt
        **kwargs: Additional arguments for LLMRequest
        
    Returns:
        LLM response text
    """
    try:
        adapter = get_llm_adapter()
        request = LLMRequest(system=system, user=user, **kwargs)
        response = adapter.call(request)
        
        if response.error:
            logger.error(f"LLM call failed: {response.error}")
            return f"[Error: {response.error}] Please try again or check configuration."
        
        return response.content
    except Exception as e:
        logger.error(f"Failed to call LLM: {e}")
        # Fallback to simple implementation if adapter fails
        return _fallback_llm(system, user)


def _fallback_llm(system: str, user: str) -> str:
    """Simple fallback LLM implementation."""
    # Very basic rule-based responses for critical functionality
    if "crisis" in system.lower() or "emergency" in system.lower():
        return "I hear this feels urgent. Let's focus on grounding first. Take a breath."
    elif "logical" in system.lower():
        return "Let's break this down logically. What's the core question?"
    elif "emotional" in system.lower():
        return "I hear real feeling in this. Let's acknowledge what's present."
    elif "shadow" in system.lower():
        return "There may be patterns here worth exploring gently."
    else:
        return "I'm here to help you find clarity. Tell me more about what you're experiencing."