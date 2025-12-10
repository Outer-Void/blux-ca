"""
Guard Adapter for BLUX-cA - Integration with BLUX-Guard for policy enforcement.

Provides real-time guardrail checking, policy enforcement, and safety monitoring
for BLUX-cA interactions. Integrates with BLUX-Guard for centralized policy management.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ca.core.audit import AuditTrail, AuditLevel, AuditCategory
from ca.core.constitution import ConstitutionEngine, ConstitutionalRule


class GuardSeverity(str, Enum):
    """Severity levels for guard violations."""
    INFO = "INFO"          # Informational, no action required
    LOW = "LOW"            # Minor issue, may need attention
    MEDIUM = "MEDIUM"      # Significant issue, requires review
    HIGH = "HIGH"          # Serious violation, requires action
    CRITICAL = "CRITICAL"  # Critical violation, immediate action required


class GuardAction(str, Enum):
    """Actions to take for guard violations."""
    ALLOW = "ALLOW"            # Allow the action
    WARN = "WARN"              # Allow with warning
    MODIFY = "MODIFY"          # Modify the action before allowing
    BLOCK = "BLOCK"            # Block the action
    ESCALATE = "ESCALATE"      # Escalate for human review
    AUDIT = "AUDIT"            # Allow but log for audit


class GuardScope(str, Enum):
    """Scope of guardrail application."""
    INPUT = "INPUT"            # Applied to user input
    PROCESSING = "PROCESSING"  # Applied during processing
    OUTPUT = "OUTPUT"          # Applied to agent output
    SYSTEM = "SYSTEM"          # Applied to system operations
    MEMORY = "MEMORY"          # Applied to memory operations
    SESSION = "SESSION"        # Applied to session operations


@dataclass
class GuardViolation:
    """A single guard violation."""
    id: str = field(default_factory=lambda: str(uuid4()))
    guardrail_id: str = ""                    # ID of the violated guardrail
    guardrail_name: str = ""                  # Name of the guardrail
    severity: GuardSeverity = GuardSeverity.MEDIUM
    action: GuardAction = GuardAction.WARN
    scope: GuardScope = GuardScope.INPUT
    
    # Violation details
    description: str = ""                     # Human-readable description
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)  # Context of violation
    evidence: Dict[str, Any] = field(default_factory=dict)  # Evidence of violation
    
    # Resolution
    resolved: bool = False                    # Whether violation was resolved
    resolution: Optional[str] = None          # How violation was resolved
    resolved_at: Optional[str] = None         # When violation was resolved
    resolved_by: Optional[str] = None         # Who resolved the violation
    
    # Metadata
    session_id: Optional[str] = None          # Associated session
    user_id: Optional[str] = None             # Associated user
    agent_name: Optional[str] = "BLUX-cA"     # Agent that triggered violation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['action'] = self.action.value
        data['scope'] = self.scope.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GuardViolation:
        """Create from dictionary."""
        data = data.copy()
        data['severity'] = GuardSeverity(data['severity'])
        data['action'] = GuardAction(data['action'])
        data['scope'] = GuardScope(data['scope'])
        return cls(**data)
    
    def is_critical(self) -> bool:
        """Check if violation is critical."""
        return self.severity in [GuardSeverity.HIGH, GuardSeverity.CRITICAL]
    
    def requires_action(self) -> bool:
        """Check if violation requires action."""
        return self.action in [GuardAction.BLOCK, GuardAction.ESCALATE, GuardAction.MODIFY]


@dataclass
class Guardrail:
    """A guardrail policy for safety and compliance."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""                            # Unique name
    description: str = ""                     # Description of what the guardrail protects
    severity: GuardSeverity = GuardSeverity.MEDIUM
    default_action: GuardAction = GuardAction.WARN
    scope: List[GuardScope] = field(default_factory=lambda: [GuardScope.INPUT, GuardScope.OUTPUT])
    
    # Activation conditions
    enabled: bool = True                      # Whether guardrail is active
    activation_conditions: Dict[str, Any] = field(default_factory=dict)  # When to activate
    deactivation_conditions: Dict[str, Any] = field(default_factory=dict)  # When to deactivate
    
    # Detection logic (simplified - in reality would be more complex)
    detection_patterns: List[str] = field(default_factory=list)  # Patterns to detect
    detection_threshold: float = 0.7          # Confidence threshold for detection
    detection_method: str = "pattern_match"   # Detection method to use
    
    # Resolution
    auto_resolution: bool = False             # Whether to attempt auto-resolution
    resolution_guidance: str = ""             # Guidance for resolving violations
    
    # Metadata
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    category: str = "safety"                  # Category: safety, compliance, quality, etc.
    
    # Relationships
    depends_on: List[str] = field(default_factory=list)      # Guardrails that must be active
    conflicts_with: List[str] = field(default_factory=list)  # Conflicting guardrails
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['default_action'] = self.default_action.value
        data['scope'] = [s.value for s in self.scope]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Guardrail:
        """Create from dictionary."""
        data = data.copy()
        data['severity'] = GuardSeverity(data['severity'])
        data['default_action'] = GuardAction(data['default_action'])
        data['scope'] = [GuardScope(s) for s in data['scope']]
        return cls(**data)
    
    def applies_to_scope(self, scope: GuardScope) -> bool:
        """Check if guardrail applies to given scope."""
        return scope in self.scope
    
    def check_violation(self, content: str, context: Dict[str, Any]) -> Optional[GuardViolation]:
        """
        Check if content violates this guardrail.
        
        Args:
            content: Content to check
            context: Additional context
            
        Returns:
            GuardViolation if violation detected, None otherwise
        """
        if not self.enabled:
            return None
        
        # Check activation conditions
        if not self._check_conditions(self.activation_conditions, context):
            return None
        
        # Check deactivation conditions
        if self._check_conditions(self.deactivation_conditions, context):
            return None
        
        # Check for violations using detection patterns
        violation_detected = False
        evidence = {}
        
        if self.detection_method == "pattern_match":
            content_lower = content.lower()
            
            for pattern in self.detection_patterns:
                pattern_lower = pattern.lower()
                
                # Simple pattern matching (could be regex in real implementation)
                if pattern_lower in content_lower:
                    violation_detected = True
                    evidence = {
                        "pattern": pattern,
                        "found_at": content_lower.find(pattern_lower),
                        "content_sample": content[:100]
                    }
                    break
        
        elif self.detection_method == "keyword_count":
            # Count occurrences of keywords
            content_words = content.lower().split()
            keyword_counts = {}
            
            for pattern in self.detection_patterns:
                pattern_lower = pattern.lower()
                count = sum(1 for word in content_words if pattern_lower in word)
                if count > 0:
                    keyword_counts[pattern] = count
            
            if keyword_counts:
                total_keywords = sum(keyword_counts.values())
                violation_detected = total_keywords >= self.detection_threshold
                evidence = {"keyword_counts": keyword_counts}
        
        if violation_detected:
            return GuardViolation(
                guardrail_id=self.id,
                guardrail_name=self.name,
                severity=self.severity,
                action=self.default_action,
                scope=context.get("scope", GuardScope.INPUT),
                description=f"Violated guardrail: {self.name}",
                context=context,
                evidence=evidence,
                session_id=context.get("session_id"),
                user_id=context.get("user_id"),
                agent_name=context.get("agent_name", "BLUX-cA")
            )
        
        return None
    
    def _check_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if conditions are met in context."""
        if not conditions:
            return True
        
        for key, expected_value in conditions.items():
            actual_value = context.get(key)
            if actual_value != expected_value:
                return False
        
        return True


class GuardCache:
    """Cache for guardrails to reduce API calls."""
    
    def __init__(self, cache_dir: Optional[Union[str, Path]] = None, ttl_minutes: int = 5):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".blux-ca" / "guard_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_minutes = ttl_minutes
        self.guardrails: Dict[str, Guardrail] = {}
        self.violations: List[GuardViolation] = []
        self.logger = logging.getLogger(__name__)
    
    def get_guardrail(self, guardrail_id: str) -> Optional[Guardrail]:
        """Get guardrail from cache."""
        return self.guardrails.get(guardrail_id)
    
    def get_all_guardrails(self) -> List[Guardrail]:
        """Get all cached guardrails."""
        return list(self.guardrails.values())
    
    def add_guardrail(self, guardrail: Guardrail) -> None:
        """Add guardrail to cache."""
        self.guardrails[guardrail.id] = guardrail
    
    def remove_guardrail(self, guardrail_id: str) -> bool:
        """Remove guardrail from cache."""
        if guardrail_id in self.guardrails:
            del self.guardrails[guardrail_id]
            return True
        return False
    
    def add_violation(self, violation: GuardViolation) -> None:
        """Add violation to cache."""
        self.violations.append(violation)
        # Keep only recent violations (last 1000)
        if len(self.violations) > 1000:
            self.violations = self.violations[-1000:]
    
    def get_recent_violations(self, limit: int = 100) -> List[GuardViolation]:
        """Get recent violations."""
        return self.violations[-limit:] if self.violations else []
    
    def clear(self) -> None:
        """Clear cache."""
        self.guardrails.clear()
        self.violations.clear()
        self.logger.info("Guard cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "guardrail_count": len(self.guardrails),
            "violation_count": len(self.violations),
            "cache_dir": str(self.cache_dir),
            "ttl_minutes": self.ttl_minutes,
        }


class GuardAdapter:
    """
    Adapter for connecting BLUX-cA with BLUX-Guard.
    
    Provides real-time guardrail checking, policy enforcement, and
    safety monitoring for all BLUX-cA interactions.
    """
    
    # Default guardrails (fallback when BLUX-Guard is unavailable)
    DEFAULT_GUARDRAILS = [
        Guardrail(
            id="guard_safety_crisis",
            name="crisis_safety_check",
            description="Detect and handle crisis situations safely",
            severity=GuardSeverity.CRITICAL,
            default_action=GuardAction.BLOCK,
            scope=[GuardScope.INPUT, GuardScope.OUTPUT],
            detection_patterns=[
                "i want to die",
                "i want to kill myself",
                "suicide",
                "end my life",
                "want to die"
            ],
            detection_threshold=0.8,
            tags=["safety", "crisis", "emergency"],
            category="safety",
            resolution_guidance="In crisis situations, prioritize safety and provide appropriate resources"
        ),
        Guardrail(
            id="guard_harm_prevention",
            name="harm_prevention",
            description="Prevent guidance that could cause harm",
            severity=GuardSeverity.HIGH,
            default_action=GuardAction.BLOCK,
            scope=[GuardScope.OUTPUT],
            detection_patterns=[
                "you should hurt",
                "you should kill",
                "harm yourself",
                "dangerous method",
                "illegal substance"
            ],
            tags=["safety", "harm", "prevention"],
            category="safety",
            resolution_guidance="Do not provide guidance that could cause harm to self or others"
        ),
        Guardrail(
            id="guard_pii_protection",
            name="pii_protection",
            description="Prevent sharing of personally identifiable information",
            severity=GuardSeverity.HIGH,
            default_action=GuardAction.MODIFY,
            scope=[GuardScope.OUTPUT],
            detection_patterns=[
                "social security",
                "credit card",
                "passport number",
                "date of birth",
                "home address",
                "phone number"
            ],
            tags=["privacy", "pii", "compliance"],
            category="compliance",
            resolution_guidance="Remove or anonymize personally identifiable information"
        ),
        Guardrail(
            id="guard_professional_boundaries",
            name="professional_boundaries",
            description="Maintain professional boundaries",
            severity=GuardSeverity.MEDIUM,
            default_action=GuardAction.WARN,
            scope=[GuardScope.OUTPUT],
            detection_patterns=[
                "i love you",
                "marry me",
                "romantic relationship",
                "sexual",
                "inappropriate relationship"
            ],
            tags=["ethics", "boundaries", "professional"],
            category="ethics",
            resolution_guidance="Maintain professional boundaries in all interactions"
        ),
        Guardrail(
            id="guard_medical_advice",
            name="medical_advice_boundary",
            description="Avoid providing medical advice",
            severity=GuardSeverity.HIGH,
            default_action=GuardAction.BLOCK,
            scope=[GuardScope.OUTPUT],
            detection_patterns=[
                "you should take",
                "medical treatment",
                "prescription",
                "diagnosis",
                "medical advice",
                "you have"
            ],
            tags=["medical", "boundaries", "safety"],
            category="safety",
            resolution_guidance="Do not provide medical advice - recommend consulting a healthcare professional"
        ),
        Guardrail(
            id="guard_legal_advice",
            name="legal_advice_boundary",
            description="Avoid providing legal advice",
            severity=GuardSeverity.HIGH,
            default_action=GuardAction.BLOCK,
            scope=[GuardScope.OUTPUT],
            detection_patterns=[
                "legal advice",
                "you should sue",
                "file a lawsuit",
                "legal action",
                "court case"
            ],
            tags=["legal", "boundaries", "compliance"],
            category="compliance",
            resolution_guidance="Do not provide legal advice - recommend consulting a legal professional"
        ),
    ]
    
    def __init__(
        self,
        endpoint: str = "https://guard.blux.local",
        api_key: Optional[str] = None,
        audit_trail: Optional[AuditTrail] = None,
        constitution: Optional[ConstitutionEngine] = None,
        enable_cache: bool = True,
        enable_default_guardrails: bool = True,
        timeout: int = 10,
        retry_attempts: int = 2,
    ) -> None:
        """
        Initialize guard adapter.
        
        Args:
            endpoint: BLUX-Guard API endpoint
            api_key: API key for authentication
            audit_trail: Audit trail for logging violations
            constitution: Constitution engine for rule integration
            enable_cache: Enable caching of guardrails
            enable_default_guardrails: Enable default guardrails as fallback
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.audit_trail = audit_trail
        self.constitution = constitution
        self.enable_default_guardrails = enable_default_guardrails
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize cache
        self.cache = GuardCache() if enable_cache else None
        
        # Initialize HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retry_attempts,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Add authentication headers if API key provided
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
        
        # Load default guardrails
        self.default_guardrails = {g.id: g for g in self.DEFAULT_GUARDRAILS}
        
        # Load guardrails from BLUX-Guard or use defaults
        self.guardrails: Dict[str, Guardrail] = {}
        self._load_guardrails()
        
        # Metrics
        self.metrics = {
            "checks_performed": 0,
            "violations_detected": 0,
            "blocks_issued": 0,
            "warnings_issued": 0,
            "api_calls": 0,
            "api_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_sync": None,
        }
        
        self.logger.info(f"Guard adapter initialized (endpoint: {self.endpoint})")
    
    def _load_guardrails(self) -> None:
        """Load guardrails from BLUX-Guard or use defaults."""
        try:
            # Try to fetch guardrails from BLUX-Guard
            response = self._make_request("GET", "/api/v1/guardrails")
            
            if response:
                data = response.json()
                for guardrail_data in data.get("guardrails", []):
                    guardrail = Guardrail.from_dict(guardrail_data)
                    self.guardrails[guardrail.id] = guardrail
                
                self.logger.info(f"Loaded {len(self.guardrails)} guardrails from BLUX-Guard")
                return
            
        except Exception as e:
            self.logger.warning(f"Failed to load guardrails from BLUX-Guard: {e}")
        
        # Fall back to default guardrails
        if self.enable_default_guardrails:
            self.guardrails = self.default_guardrails.copy()
            self.logger.info(f"Loaded {len(self.guardrails)} default guardrails")
        else:
            self.logger.warning("No guardrails loaded - BLUX-Guard unavailable and defaults disabled")
    
    def _make_request(self, method: str, path: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request to BLUX-Guard API."""
        url = f"{self.endpoint}{path}"
        
        try:
            kwargs.setdefault('timeout', 10)
            self.metrics["api_calls"] += 1
            
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error to BLUX-Guard: {e}")
            self.metrics["api_errors"] += 1
            return None
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout connecting to BLUX-Guard: {e}")
            self.metrics["api_errors"] += 1
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error from BLUX-Guard: {e}")
            self.metrics["api_errors"] += 1
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error contacting BLUX-Guard: {e}")
            self.metrics["api_errors"] += 1
            return None
    
    def check(
        self,
        content: str,
        scope: GuardScope = GuardScope.INPUT,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[GuardViolation]:
        """
        Check content against all applicable guardrails.
        
        Args:
            content: Content to check
            scope: Scope of the check (input, output, etc.)
            context: Additional context for the check
            
        Returns:
            List of guard violations detected
        """
        self.metrics["checks_performed"] += 1
        
        context = context or {}
        context["scope"] = scope
        context["check_timestamp"] = datetime.now().isoformat()
        
        violations = []
        
        for guardrail in self.guardrails.values():
            if not guardrail.applies_to_scope(scope):
                continue
            
            violation = guardrail.check_violation(content, context)
            if violation:
                violations.append(violation)
                
                # Update cache
                if self.cache:
                    self.cache.add_violation(violation)
                
                # Log to audit trail
                if self.audit_trail:
                    self.audit_trail.log(
                        level=AuditLevel.WARNING if violation.is_critical() else AuditLevel.INFO,
                        category=AuditCategory.SAFETY_CHECK,
                        operation="guardrail_violation",
                        description=f"Guardrail violation: {guardrail.name}",
                        details={
                            "guardrail_id": guardrail.id,
                            "guardrail_name": guardrail.name,
                            "severity": violation.severity.value,
                            "action": violation.action.value,
                            "scope": scope.value,
                            "content_preview": content[:200],
                            "violation_id": violation.id,
                        },
                        session_id=context.get("session_id"),
                        agent_name=context.get("agent_name", "BLUX-cA")
                    )
        
        if violations:
            self.metrics["violations_detected"] += len(violations)
            
            # Count blocks and warnings
            for violation in violations:
                if violation.action == GuardAction.BLOCK:
                    self.metrics["blocks_issued"] += 1
                elif violation.action == GuardAction.WARN:
                    self.metrics["warnings_issued"] += 1
        
        return violations
    
    def check_and_notify(
        self,
        content: str,
        scope: GuardScope = GuardScope.INPUT,
        context: Optional[Dict[str, Any]] = None,
        notify_guard: bool = True,
    ) -> Dict[str, Any]:
        """
        Check content and notify BLUX-Guard of violations.
        
        Args:
            content: Content to check
            scope: Scope of the check
            context: Additional context
            notify_guard: Whether to notify BLUX-Guard API
            
        Returns:
            Dictionary with check results
        """
        context = context or {}
        
        # Perform local check
        violations = self.check(content, scope, context)
        
        # Determine overall action based on violations
        overall_action = GuardAction.ALLOW
        if violations:
            # Find the most severe required action
            for violation in violations:
                if violation.action == GuardAction.BLOCK:
                    overall_action = GuardAction.BLOCK
                    break
                elif violation.action == GuardAction.ESCALATE:
                    overall_action = GuardAction.ESCALATE
                elif violation.action == GuardAction.MODIFY and overall_action == GuardAction.ALLOW:
                    overall_action = GuardAction.MODIFY
                elif violation.action == GuardAction.WARN and overall_action == GuardAction.ALLOW:
                    overall_action = GuardAction.WARN
        
        # Notify BLUX-Guard if requested
        guard_notification = None
        if notify_guard and violations:
            guard_notification = self.notify_guard(violations, context)
        
        result = {
            "allowed": overall_action in [GuardAction.ALLOW, GuardAction.WARN, GuardAction.AUDIT],
            "action": overall_action.value,
            "violations": [v.to_dict() for v in violations],
            "violation_count": len(violations),
            "critical_violations": len([v for v in violations if v.is_critical()]),
            "guard_notified": guard_notification is not None,
            "guard_response": guard_notification,
            "timestamp": datetime.now().isoformat(),
        }
        
        return result
    
    def notify(self, verdict: Dict[str, str]) -> None:
        """
        Legacy method for backward compatibility.
        
        Args:
            verdict: Verdict dictionary
        """
        self.logger.debug(f"Legacy notify called with verdict: {verdict}")
        
        # Convert legacy verdict to modern format if possible
        if "violation" in verdict or "action" in verdict:
            # Create a simple violation from legacy format
            violation = GuardViolation(
                guardrail_id="legacy",
                guardrail_name="legacy_notification",
                severity=GuardSeverity.MEDIUM,
                action=GuardAction.WARN,
                scope=GuardScope.SYSTEM,
                description=f"Legacy notification: {verdict.get('violation', 'unknown')}",
                context={"legacy_verdict": verdict}
            )
            
            # Notify BLUX-Guard
            self.notify_guard([violation], {"source": "legacy_notify"})
    
    def notify_guard(
        self,
        violations: List[GuardViolation],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Notify BLUX-Guard of violations.
        
        Args:
            violations: List of violations to report
            context: Additional context
            
        Returns:
            Response from BLUX-Guard or None if failed
        """
        if not violations:
            return None
        
        context = context or {}
        
        # Prepare notification payload
        payload = {
            "violations": [v.to_dict() for v in violations],
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "agent": "BLUX-cA",
            "version": "1.0",
        }
        
        # Send to BLUX-Guard
        response = self._make_request(
            "POST",
            "/api/v1/violations/report",
            json=payload
        )
        
        if response:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse BLUX-Guard response: {e}")
                return None
        
        return None
    
    def add_guardrail(self, guardrail: Guardrail) -> str:
        """
        Add a guardrail to the adapter.
        
        Args:
            guardrail: Guardrail to add
            
        Returns:
            ID of the added guardrail
        """
        self.guardrails[guardrail.id] = guardrail
        
        # Update cache
        if self.cache:
            self.cache.add_guardrail(guardrail)
        
        self.logger.info(f"Added guardrail: {guardrail.name} ({guardrail.id})")
        return guardrail.id
    
    def remove_guardrail(self, guardrail_id: str) -> bool:
        """
        Remove a guardrail.
        
        Args:
            guardrail_id: ID of guardrail to remove
            
        Returns:
            True if removed, False if not found
        """
        if guardrail_id in self.guardrails:
            del self.guardrails[guardrail_id]
            
            # Update cache
            if self.cache:
                self.cache.remove_guardrail(guardrail_id)
            
            self.logger.info(f"Removed guardrail: {guardrail_id}")
            return True
        
        return False
    
    def get_guardrail(self, guardrail_id: str) -> Optional[Guardrail]:
        """Get a specific guardrail by ID."""
        return self.guardrails.get(guardrail_id)
    
    def get_all_guardrails(self) -> List[Guardrail]:
        """Get all guardrails."""
        return list(self.guardrails.values())
    
    def get_violations(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        severity: Optional[GuardSeverity] = None,
        limit: int = 100,
    ) -> List[GuardViolation]:
        """
        Get violations matching criteria.
        
        Args:
            session_id: Filter by session ID
            start_time: Filter by start time (ISO format)
            end_time: Filter by end time (ISO format)
            severity: Filter by severity
            limit: Maximum number of violations to return
            
        Returns:
            List of matching violations
        """
        violations = []
        
        # Try cache first
        if self.cache:
            violations = self.cache.get_recent_violations(limit * 2)
        else:
            # In a real implementation, this would query BLUX-Guard
            pass
        
        # Apply filters
        filtered = []
        for violation in violations:
            if session_id and violation.session_id != session_id:
                continue
            if start_time and violation.detected_at < start_time:
                continue
            if end_time and violation.detected_at > end_time:
                continue
            if severity and violation.severity != severity:
                continue
            
            filtered.append(violation)
            if len(filtered) >= limit:
                break
        
        return filtered
    
    def sync_with_guard(self) -> bool:
        """
        Sync guardrails with BLUX-Guard.
        
        Returns:
            True if sync successful, False otherwise
        """
        try:
            response = self._make_request("GET", "/api/v1/guardrails/sync")
            
            if response:
                data = response.json()
                
                # Update guardrails
                new_guardrails = {}
                for guardrail_data in data.get("guardrails", []):
                    guardrail = Guardrail.from_dict(guardrail_data)
                    new_guardrails[guardrail.id] = guardrail
                
                self.guardrails = new_guardrails
                
                # Update cache
                if self.cache:
                    self.cache.clear()
                    for guardrail in self.guardrails.values():
                        self.cache.add_guardrail(guardrail)
                
                self.metrics["last_sync"] = datetime.now().isoformat()
                self.logger.info(f"Synced {len(self.guardrails)} guardrails with BLUX-Guard")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to sync with BLUX-Guard: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            "endpoint": self.endpoint,
            "guardrail_count": len(self.guardrails),
            "default_guardrails_enabled": self.enable_default_guardrails,
            "cache_enabled": self.cache is not None,
            "audit_integrated": self.audit_trail is not None,
            "constitution_integrated": self.constitution is not None,
            "metrics": self.metrics.copy(),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.metrics = {
            "checks_performed": 0,
            "violations_detected": 0,
            "blocks_issued": 0,
            "warnings_issued": 0,
            "api_calls": 0,
            "api_errors": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_sync": self.metrics.get("last_sync"),
        }
    
    def integrate_with_constitution(self) -> List[ConstitutionalRule]:
        """
        Convert guardrails to constitutional rules.
        
        Returns:
            List of constitutional rules derived from guardrails
        """
        if not self.constitution:
            return []
        
        rules = []
        for guardrail in self.guardrails.values():
            try:
                rule = self._guardrail_to_constitutional_rule(guardrail)
                rules.append(rule)
            except Exception as e:
                self.logger.warning(f"Failed to convert guardrail {guardrail.id} to rule: {e}")
        
        return rules
    
    def _guardrail_to_constitutional_rule(self, guardrail: Guardrail) -> ConstitutionalRule:
        """Convert guardrail to constitutional rule."""
        # Map guardrail severity to rule priority
        severity_map = {
            GuardSeverity.INFO: RulePriority.LOW,
            GuardSeverity.LOW: RulePriority.LOW,
            GuardSeverity.MEDIUM: RulePriority.MEDIUM,
            GuardSeverity.HIGH: RulePriority.HIGH,
            GuardSeverity.CRITICAL: RulePriority.CRITICAL,
        }
        
        # Map guardrail action to rule enforcement
        action_map = {
            GuardAction.ALLOW: "INFORM",
            GuardAction.WARN: "WARN",
            GuardAction.MODIFY: "MODIFY",
            GuardAction.BLOCK: "REJECT",
            GuardAction.ESCALATE: "ESCALATE",
            GuardAction.AUDIT: "AUDIT",
        }
        
        return ConstitutionalRule(
            name=f"guardrail_{guardrail.name}",
            description=guardrail.description,
            rule_type=RuleType.SAFETY_GUARDRAIL,
            priority=severity_map.get(guardrail.severity, RulePriority.MEDIUM),
            statement=f"Guardrail: {guardrail.description}",
            enforcement=action_map.get(guardrail.default_action, "WARN"),
            violation_action=action_map.get(guardrail.default_action, "WARN"),
            tags=guardrail.tags + ["guardrail", guardrail.category],
            metadata={
                "guardrail_id": guardrail.id,
                "guardrail_version": guardrail.version,
                "detection_patterns": guardrail.detection_patterns,
                "scope": [s.value for s in guardrail.scope],
            }
        )


# Convenience functions

def create_guard_adapter(
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    audit_trail: Optional[AuditTrail] = None,
    enable_default_guardrails: bool = True,
) -> GuardAdapter:
    """
    Create a guard adapter with sensible defaults.
    
    Args:
        endpoint: BLUX-Guard endpoint (defaults to environment variable or default)
        api_key: API key for authentication
        audit_trail: Audit trail for logging
        enable_default_guardrails: Enable default guardrails as fallback
        
    Returns:
        Configured GuardAdapter instance
    """
    import os
    
    # Get endpoint from environment or use default
    if endpoint is None:
        endpoint = os.getenv("BLUX_GUARD_ENDPOINT", "https://guard.blux.local")
    
    # Get API key from environment if not provided
    if api_key is None:
        api_key = os.getenv("BLUX_GUARD_API_KEY")
    
    return GuardAdapter(
        endpoint=endpoint,
        api_key=api_key,
        audit_trail=audit_trail,
        enable_default_guardrails=enable_default_guardrails,
    )


def check_content_safety(
    content: str,
    scope: GuardScope = GuardScope.INPUT,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Quick safety check utility function.
    
    Args:
        content: Content to check
        scope: Scope of the check
        context: Additional context
        
    Returns:
        Safety check results
    """
    adapter = GuardAdapter(enable_default_guardrails=True)
    return adapter.check_and_notify(content, scope, context, notify_guard=False)


__all__ = [
    "GuardAdapter",
    "Guardrail",
    "GuardViolation",
    "GuardSeverity",
    "GuardAction",
    "GuardScope",
    "create_guard_adapter",
    "check_content_safety",
]