"""
Registration and capability validation for BLUX-cA.

Provides secure key validation and capability management aligned with the
Clarity Agent's ethical guardrails and recovery state machine.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple


class Capability(Enum):
    """Available capabilities within BLUX-cA system."""
    
    # Core Clarity capabilities
    LOGICAL_CLARITY = "logical_clarity"
    EMOTIONAL_CLARITY = "emotional_clarity" 
    SHADOW_CLARITY = "shadow_clarity"
    
    # Recovery state access
    CRISIS_ACCESS = "crisis_access"
    AWARENESS_ACCESS = "awareness_access"
    HONESTY_ACCESS = "honesty_access"
    RECONSTRUCTION_ACCESS = "reconstruction_access"
    INTEGRATION_ACCESS = "integration_access"
    PURPOSE_ACCESS = "purpose_access"
    
    # System capabilities
    SELF_REFLECTION = "self_reflection"
    STATE_PERSISTENCE = "state_persistence"
    GUARDRAIL_ENFORCEMENT = "guardrail_enforcement"
    SESSION_MANAGEMENT = "session_management"
    
    # Safety capabilities
    NO_HARM_ENFORCED = "no_harm_enforced"
    TRUTH_OVER_APPROVAL = "truth_over_approval"
    USER_STATE_OWNERSHIP = "user_state_ownership"
    
    # New integrated capabilities
    CROSS_DOMAIN_SYNC = "cross_domain_sync"
    REAL_TIME_MONITORING = "real_time_monitoring"
    ADAPTIVE_LEARNING = "adaptive_learning"


@dataclass
class RegistrationResult:
    """Result of a registration validation attempt."""
    
    valid: bool
    reason: str
    capabilities: Set[Capability] = field(default_factory=set)
    key_type: Optional[str] = None
    expires_at: Optional[float] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def has_capability(self, capability: Capability) -> bool:
        """Check if result includes specific capability."""
        return capability in self.capabilities
    
    def is_expired(self) -> bool:
        """Check if registration has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def get_remaining_seconds(self) -> Optional[float]:
        """Get remaining validity time in seconds."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - time.time()
        return max(0.0, remaining)
    
    def to_dict(self) -> Dict[str, any]:
        """Convert result to dictionary for serialization."""
        return {
            "valid": self.valid,
            "reason": self.reason,
            "capabilities": [cap.value for cap in self.capabilities],
            "key_type": self.key_type,
            "expires_at": self.expires_at,
            "expires_in": self.get_remaining_seconds(),
            "metadata": self.metadata
        }


@dataclass
class KeyValidationRules:
    """Rules for validating registration keys."""
    
    min_length: int = 32
    max_length: int = 256
    required_prefix: str = "BLUX-"
    allowed_chars: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    max_age_days: int = 90
    require_checksum: bool = True
    checksum_length: int = 4
    
    def __post_init__(self):
        """Validate rule configuration."""
        if self.min_length <= 0:
            raise ValueError("min_length must be positive")
        if self.max_length <= self.min_length:
            raise ValueError("max_length must be greater than min_length")
        if not self.required_prefix:
            raise ValueError("required_prefix cannot be empty")
        if self.checksum_length < 0 or self.checksum_length > 8:
            raise ValueError("checksum_length must be between 0 and 8")


class RegistryValidator:
    """
    Performs comprehensive capability validation with security enhancements.
    
    Implements defense-in-depth validation including:
    - Format validation
    - Cryptographic verification
    - Capability mapping
    - Expiration tracking
    - Ethical guardrail enforcement
    """
    
    # Standard capability sets for different key types
    CAPABILITY_SETS = {
        "basic": {
            Capability.LOGICAL_CLARITY,
            Capability.EMOTIONAL_CLARITY,
            Capability.NO_HARM_ENFORCED,
            Capability.TRUTH_OVER_APPROVAL,
        },
        "recovery": {
            Capability.LOGICAL_CLARITY,
            Capability.EMOTIONAL_CLARITY,
            Capability.SHADOW_CLARITY,
            Capability.CRISIS_ACCESS,
            Capability.AWARENESS_ACCESS,
            Capability.HONESTY_ACCESS,
            Capability.RECONSTRUCTION_ACCESS,
            Capability.NO_HARM_ENFORCED,
            Capability.TRUTH_OVER_APPROVAL,
            Capability.SELF_REFLECTION,
        },
        "integration": {
            Capability.LOGICAL_CLARITY,
            Capability.EMOTIONAL_CLARITY,
            Capability.SHADOW_CLARITY,
            Capability.INTEGRATION_ACCESS,
            Capability.PURPOSE_ACCESS,
            Capability.SELF_REFLECTION,
            Capability.STATE_PERSISTENCE,
            Capability.USER_STATE_OWNERSHIP,
            Capability.CROSS_DOMAIN_SYNC,
            Capability.ADAPTIVE_LEARNING,
        },
        "monitoring": {
            Capability.LOGICAL_CLARITY,
            Capability.EMOTIONAL_CLARITY,
            Capability.SHADOW_CLARITY,
            Capability.SELF_REFLECTION,
            Capability.STATE_PERSISTENCE,
            Capability.REAL_TIME_MONITORING,
            Capability.ADAPTIVE_LEARNING,
        },
        "system": {
            *Capability,  # All capabilities
        }
    }
    
    def __init__(self, rules: Optional[KeyValidationRules] = None):
        """
        Initialize validator with optional custom rules.
        
        Args:
            rules: Custom validation rules, defaults to standard BLUX rules
        """
        self.rules = rules or KeyValidationRules()
        self._key_cache: Dict[str, Tuple[RegistrationResult, float]] = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._revoked_keys: Set[str] = set()
        
    def _clean_cache(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._key_cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        for key in expired_keys:
            del self._key_cache[key]
    
    def _validate_checksum(self, key: str) -> Tuple[bool, str]:
        """Validate key checksum if required."""
        if not self.rules.require_checksum or self.rules.checksum_length == 0:
            return True, "Checksum validation not required"
        
        key_body = key[len(self.rules.required_prefix):-self.rules.checksum_length]
        checksum = key[-self.rules.checksum_length:]
        
        # Simple checksum calculation (production would use proper crypto)
        calculated = hashlib.sha256(key_body.encode()).hexdigest()[:self.rules.checksum_length].upper()
        
        if checksum != calculated:
            return False, f"Invalid checksum. Expected {calculated}, got {checksum}"
        
        return True, "Checksum valid"
    
    def _validate_format(self, key: str) -> Tuple[bool, str]:
        """Validate key format against rules."""
        # Check prefix
        if not key.startswith(self.rules.required_prefix):
            return False, f"Key must start with '{self.rules.required_prefix}'"
        
        # Check length
        if len(key) < self.rules.min_length:
            return False, f"Key too short (min {self.rules.min_length} chars)"
        if len(key) > self.rules.max_length:
            return False, f"Key too long (max {self.rules.max_length} chars)"
        
        # Check character set (after prefix)
        key_body = key[len(self.rules.required_prefix):]
        if not all(c in self.rules.allowed_chars for c in key_body):
            invalid_chars = set(c for c in key_body if c not in self.rules.allowed_chars)
            return False, f"Invalid characters: {''.join(sorted(invalid_chars))}"
        
        # Check for sequential patterns (simple entropy check)
        if re.search(r'(.)\1{3,}', key_body):  # 4 or more repeated chars
            return False, "Key pattern too simple (repeated characters)"
        
        # Check checksum if required
        if self.rules.require_checksum and self.rules.checksum_length > 0:
            checksum_valid, checksum_reason = self._validate_checksum(key)
            if not checksum_valid:
                return False, checksum_reason
        
        return True, "Format valid"
    
    def _determine_capabilities(self, key: str) -> Set[Capability]:
        """
        Determine capabilities based on key characteristics.
        
        This is a simplified implementation. In production, this would
        integrate with a proper key management service or database.
        """
        key_body = key[len(self.rules.required_prefix):]
        
        # Simple heuristic-based capability assignment
        # In production, this would be cryptographic or database-driven
        if key.endswith("-SYS"):
            return self.CAPABILITY_SETS["system"]
        elif key.endswith("-MON"):
            return self.CAPABILITY_SETS["monitoring"]
        elif key.endswith("-INT"):
            return self.CAPABILITY_SETS["integration"]
        elif key.endswith("-REC"):
            return self.CAPABILITY_SETS["recovery"]
        else:
            return self.CAPABILITY_SETS["basic"]
    
    def _determine_key_type(self, key: str) -> str:
        """Determine key type based on suffix pattern."""
        if key.endswith("-SYS"):
            return "system"
        elif key.endswith("-MON"):
            return "monitoring"
        elif key.endswith("-INT"):
            return "integration"
        elif key.endswith("-REC"):
            return "recovery"
        else:
            return "basic"
    
    def _calculate_expiration(self, key: str) -> Optional[float]:
        """
        Calculate expiration timestamp for key.
        
        Uses simple time-based expiration. In production, this would
        extract expiration from key metadata or database.
        """
        key_type = self._determine_key_type(key)
        
        # Different expiration based on key type
        expiration_days = {
            "basic": 30,
            "recovery": 60,
            "integration": 90,
            "monitoring": 45,
            "system": 365,
        }
        
        days = expiration_days.get(key_type, self.rules.max_age_days)
        return time.time() + (days * 24 * 60 * 60)
    
    def _extract_metadata(self, key: str) -> Dict[str, any]:
        """Extract metadata from key structure."""
        key_type = self._determine_key_type(key)
        
        # Simple metadata extraction
        metadata = {
            "key_type": key_type,
            "length": len(key),
            "generated_version": "1.0",
            "validation_timestamp": time.time(),
        }
        
        # Add type-specific metadata
        if key_type == "system":
            metadata["admin_access"] = True
            metadata["debug_mode"] = True
        elif key_type == "monitoring":
            metadata["read_only"] = True
            metadata["analytics_enabled"] = True
        
        return metadata
    
    def validate(self, key: str, use_cache: bool = True) -> RegistrationResult:
        """
        Validate registration key and determine capabilities.
        
        Args:
            key: The registration key to validate
            use_cache: Whether to use result caching (default: True)
            
        Returns:
            RegistrationResult with validation outcome and capabilities
            
        Raises:
            ValueError: If key is empty or None
        """
        if not key or not isinstance(key, str):
            raise ValueError("Key must be a non-empty string")
        
        key = key.strip()
        
        # Check if key is revoked
        if key in self._revoked_keys:
            return RegistrationResult(
                valid=False,
                reason="Key has been revoked",
                metadata={"revoked": True}
            )
        
        # Check cache first
        if use_cache:
            self._clean_cache()
            if key in self._key_cache:
                result, _ = self._key_cache[key]
                if not result.is_expired():
                    return result
        
        # Validate format
        format_valid, format_reason = self._validate_format(key)
        if not format_valid:
            result = RegistrationResult(False, format_reason)
        else:
            # Determine capabilities and expiration
            capabilities = self._determine_capabilities(key)
            key_type = self._determine_key_type(key)
            expires_at = self._calculate_expiration(key)
            metadata = self._extract_metadata(key)
            
            # Enforce ethical guardrails (always add safety capabilities)
            safety_capabilities = {
                Capability.NO_HARM_ENFORCED,
                Capability.TRUTH_OVER_APPROVAL,
                Capability.USER_STATE_OWNERSHIP,
            }
            capabilities.update(safety_capabilities)
            
            result = RegistrationResult(
                valid=True,
                reason="Key validated successfully",
                capabilities=capabilities,
                key_type=key_type,
                expires_at=expires_at,
                metadata=metadata
            )
        
        # Cache result
        if use_cache and result.valid:
            self._key_cache[key] = (result, time.time())
        
        return result
    
    def validate_with_context(self, key: str, required_capabilities: Set[Capability]) -> RegistrationResult:
        """
        Validate key with specific capability requirements.
        
        Args:
            key: The registration key to validate
            required_capabilities: Set of capabilities required for the operation
            
        Returns:
            RegistrationResult with additional validation against required capabilities
        """
        result = self.validate(key)
        
        if not result.valid:
            return result
        
        # Check for required capabilities
        missing_capabilities = required_capabilities - result.capabilities
        if missing_capabilities:
            missing_names = [cap.value for cap in missing_capabilities]
            return RegistrationResult(
                valid=False,
                reason=f"Missing required capabilities: {', '.join(missing_names)}",
                capabilities=result.capabilities,
                key_type=result.key_type,
                expires_at=result.expires_at,
                metadata={**result.metadata, "missing_capabilities": missing_names}
            )
        
        return result
    
    def validate_batch(self, keys: List[str]) -> Dict[str, RegistrationResult]:
        """
        Validate multiple keys efficiently.
        
        Args:
            keys: List of keys to validate
            
        Returns:
            Dictionary mapping keys to validation results
        """
        results = {}
        for key in keys:
            try:
                results[key] = self.validate(key, use_cache=True)
            except Exception as e:
                results[key] = RegistrationResult(
                    valid=False,
                    reason=f"Validation error: {str(e)}",
                    metadata={"error": True, "exception": str(e)}
                )
        return results
    
    def generate_sample_key(self, key_type: str = "basic", include_checksum: bool = True) -> str:
        """
        Generate a sample valid key for testing purposes.
        
        Warning: This generates test keys only. Production keys should
        be generated by a proper key management system.
        
        Args:
            key_type: Type of key to generate (basic, recovery, integration, system, monitoring)
            include_checksum: Whether to include checksum in the key
            
        Returns:
            A sample valid key string
        """
        if key_type not in self.CAPABILITY_SETS:
            raise ValueError(f"Invalid key type. Must be one of: {list(self.CAPABILITY_SETS.keys())}")
        
        # Calculate key body length
        body_length = self.rules.min_length - len(self.rules.required_prefix)
        if include_checksum and self.rules.require_checksum:
            body_length -= self.rules.checksum_length
        
        # Generate random key body
        key_body = ''.join(
            secrets.choice(self.rules.allowed_chars[1:])  # Skip 'A' from allowed_chars
            for _ in range(body_length)
        )
        
        # Add type suffix
        suffix_map = {
            "basic": "",
            "recovery": "-REC",
            "integration": "-INT", 
            "system": "-SYS",
            "monitoring": "-MON"
        }
        
        base_key = f"{self.rules.required_prefix}{key_body}{suffix_map[key_type]}"
        
        # Add checksum if required
        if include_checksum and self.rules.require_checksum:
            checksum = hashlib.sha256(key_body.encode()).hexdigest()[:self.rules.checksum_length].upper()
            return f"{base_key}{checksum}"
        
        return base_key
    
    def revoke_key(self, key: str, permanent: bool = False) -> bool:
        """
        Revoke a key from cache and optionally mark as permanently revoked.
        
        Note: In production, this would integrate with a key revocation
        service or database. This only affects the local validator.
        
        Args:
            key: Key to revoke
            permanent: If True, add to permanent revocation list
            
        Returns:
            True if key was cached and removed, False otherwise
        """
        key = key.strip()
        was_cached = key in self._key_cache
        
        if was_cached:
            del self._key_cache[key]
        
        if permanent:
            self._revoked_keys.add(key)
        
        return was_cached
    
    def clear_cache(self) -> int:
        """
        Clear all cached validation results.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._key_cache)
        self._key_cache.clear()
        return count
    
    def get_stats(self) -> Dict[str, any]:
        """Get validator statistics."""
        self._clean_cache()
        
        return {
            "cache_size": len(self._key_cache),
            "revoked_keys": len(self._revoked_keys),
            "rules": {
                "min_length": self.rules.min_length,
                "max_length": self.rules.max_length,
                "require_checksum": self.rules.require_checksum,
                "max_age_days": self.rules.max_age_days,
            },
            "capability_sets": list(self.CAPABILITY_SETS.keys()),
        }


def create_validator() -> RegistryValidator:
    """
    Factory function to create a properly configured RegistryValidator.
    
    Returns:
        A configured RegistryValidator instance
    """
    return RegistryValidator()


def validate_key_for_capabilities(key: str, required_capabilities: Set[Capability]) -> RegistrationResult:
    """
    Convenience function for single validation with required capabilities.
    
    Args:
        key: The registration key to validate
        required_capabilities: Set of capabilities required
        
    Returns:
        RegistrationResult with validation outcome
    """
    validator = create_validator()
    return validator.validate_with_context(key, required_capabilities)


__all__ = [
    "RegistryValidator",
    "RegistrationResult", 
    "Capability",
    "KeyValidationRules",
    "create_validator",
    "validate_key_for_capabilities",
]