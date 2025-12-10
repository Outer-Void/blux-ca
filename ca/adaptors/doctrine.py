"""
Doctrine Adapter for BLUX-cA - Integration with BLUX Doctrine API.

Provides access to external doctrine policies and ethical guidelines
that govern BLUX-cA's behavior and decision-making processes.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ca.core.constitution import ConstitutionalRule, RuleType, RulePriority


class DoctrineSource(str, Enum):
    """Sources for doctrine policies."""
    CENTRAL_API = "CENTRAL_API"      # Central doctrine server
    LOCAL_CACHE = "LOCAL_CACHE"      # Local cached policies
    EMBEDDED = "EMBEDDED"           # Embedded fallback policies
    USER_DEFINED = "USER_DEFINED"    # User-defined policies
    CUSTOM = "CUSTOM"               # Custom policy source


class DoctrineCategory(str, Enum):
    """Categories of doctrine policies."""
    ETHICAL = "ETHICAL"             # Ethical principles
    SAFETY = "SAFETY"               # Safety guidelines
    LEGAL = "LEGAL"                 # Legal compliance
    OPERATIONAL = "OPERATIONAL"     # Operational rules
    QUALITY = "QUALITY"             # Quality standards
    PRIVACY = "PRIVACY"             # Privacy and data handling
    ACCESSIBILITY = "ACCESSIBILITY" # Accessibility guidelines
    COMMUNICATION = "COMMUNICATION" # Communication standards


@dataclass
class DoctrinePolicy:
    """A single doctrine policy with metadata."""
    id: str = field(default_factory=lambda: str(uuid4()))
    source_id: Optional[str] = None          # ID from external source
    name: str = ""                           # Policy name/identifier
    title: str = ""                          # Human-readable title
    description: str = ""                    # Detailed description
    category: DoctrineCategory = DoctrineCategory.ETHICAL
    content: str = ""                        # Policy content/statement
    version: str = "1.0"                     # Policy version
    priority: int = 50                       # Priority (0-100)
    
    # Metadata
    source: DoctrineSource = DoctrineSource.EMBEDDED
    effective_date: Optional[str] = None     # When policy takes effect
    expiration_date: Optional[str] = None    # When policy expires
    jurisdiction: List[str] = field(default_factory=list)  # Applicable jurisdictions
    tags: List[str] = field(default_factory=list)          # Search tags
    
    # Enforcement
    enforcement_level: str = "REQUIRED"      # REQUIRED, RECOMMENDED, OPTIONAL
    violation_severity: str = "HIGH"         # Severity of violation
    compliance_required: bool = True         # Whether compliance is required
    
    # Relations
    supersedes: List[str] = field(default_factory=list)    # IDs of superseded policies
    depends_on: List[str] = field(default_factory=list)    # IDs of dependent policies
    conflicts_with: List[str] = field(default_factory=list)  # IDs of conflicting policies
    
    # Metrics
    last_accessed: Optional[str] = None
    access_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['category'] = self.category.value
        data['source'] = self.source.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DoctrinePolicy:
        """Create from dictionary."""
        data = data.copy()
        data['category'] = DoctrineCategory(data['category'])
        data['source'] = DoctrineSource(data['source'])
        return cls(**data)
    
    def to_constitutional_rule(self) -> ConstitutionalRule:
        """Convert doctrine policy to constitutional rule."""
        # Map doctrine priority to constitutional rule priority
        priority_map = {
            0: RulePriority.LOW,
            25: RulePriority.MEDIUM,
            50: RulePriority.HIGH,
            75: RulePriority.CRITICAL,
            100: RulePriority.CRITICAL
        }
        
        rule_priority = priority_map.get(
            min(self.priority // 25 * 25, 100),  # Round to nearest 25
            RulePriority.MEDIUM
        )
        
        # Map doctrine category to rule type
        category_map = {
            DoctrineCategory.ETHICAL: RuleType.ETHICAL_PRINCIPLE,
            DoctrineCategory.SAFETY: RuleType.SAFETY_GUARDRAIL,
            DoctrineCategory.LEGAL: RuleType.LEGAL_COMPLIANCE,
            DoctrineCategory.OPERATIONAL: RuleType.OPERATIONAL_RULE,
            DoctrineCategory.QUALITY: RuleType.QUALITY_STANDARD,
            DoctrineCategory.PRIVACY: RuleType.USER_PROTECTION,
            DoctrineCategory.ACCESSIBILITY: RuleType.USER_PROTECTION,
            DoctrineCategory.COMMUNICATION: RuleType.OPERATIONAL_RULE,
        }
        
        rule_type = category_map.get(self.category, RuleType.OPERATIONAL_RULE)
        
        # Determine enforcement
        enforcement = "REQUIRE" if self.compliance_required else "RECOMMEND"
        violation_action = "REJECT" if self.violation_severity == "HIGH" else "WARN"
        
        return ConstitutionalRule(
            name=self.name,
            description=self.description,
            rule_type=rule_type,
            priority=rule_priority,
            statement=self.content,
            enforcement=enforcement,
            violation_action=violation_action,
            tags=self.tags + ["doctrine", self.category.value.lower()],
            metadata={
                "doctrine_id": self.id,
                "source_id": self.source_id,
                "source": self.source.value,
                "version": self.version,
                "jurisdiction": self.jurisdiction,
            }
        )
    
    def is_active(self) -> bool:
        """Check if policy is currently active."""
        now = datetime.now()
        
        # Check effective date
        if self.effective_date:
            try:
                effective = datetime.fromisoformat(self.effective_date.replace('Z', '+00:00'))
                if now < effective:
                    return False
            except (ValueError, TypeError):
                pass
        
        # Check expiration date
        if self.expiration_date:
            try:
                expiration = datetime.fromisoformat(self.expiration_date.replace('Z', '+00:00'))
                if now > expiration:
                    return False
            except (ValueError, TypeError):
                pass
        
        return True
    
    def update_access(self) -> None:
        """Update access metrics."""
        self.last_accessed = datetime.now().isoformat()
        self.access_count += 1


@dataclass
class DoctrineQuery:
    """Query parameters for fetching doctrine policies."""
    categories: Optional[List[DoctrineCategory]] = None
    tags: Optional[List[str]] = None
    jurisdiction: Optional[str] = None
    min_priority: int = 0
    max_priority: int = 100
    active_only: bool = True
    limit: Optional[int] = None
    offset: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API requests."""
        data = {}
        if self.categories:
            data['categories'] = [c.value for c in self.categories]
        if self.tags:
            data['tags'] = self.tags
        if self.jurisdiction:
            data['jurisdiction'] = self.jurisdiction
        if self.min_priority != 0:
            data['min_priority'] = self.min_priority
        if self.max_priority != 100:
            data['max_priority'] = self.max_priority
        if not self.active_only:
            data['active_only'] = False
        if self.limit:
            data['limit'] = self.limit
        if self.offset != 0:
            data['offset'] = self.offset
        return data


class DoctrineCache:
    """Cache for doctrine policies to reduce API calls."""
    
    def __init__(self, cache_dir: Optional[Union[str, Path]] = None, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".blux-ca" / "doctrine_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours
        self.cache: Dict[str, DoctrinePolicy] = {}
        self.logger = logging.getLogger(__name__)
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for a key."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str) -> Optional[DoctrinePolicy]:
        """Get policy from cache."""
        # Check memory cache first
        if key in self.cache:
            policy = self.cache[key]
            if not policy.is_active():
                del self.cache[key]
                return None
            return policy
        
        # Check disk cache
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                # Check TTL
                mtime = cache_file.stat().st_mtime
                if time.time() - mtime > self.ttl_hours * 3600:
                    cache_file.unlink()
                    return None
                
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                policy = DoctrinePolicy.from_dict(data)
                
                # Check if policy is still active
                if not policy.is_active():
                    cache_file.unlink()
                    return None
                
                # Store in memory cache
                self.cache[key] = policy
                return policy
                
            except Exception as e:
                self.logger.warning(f"Failed to read cache file {cache_file}: {e}")
                cache_file.unlink()
        
        return None
    
    def set(self, key: str, policy: DoctrinePolicy) -> None:
        """Store policy in cache."""
        # Update in memory cache
        self.cache[key] = policy
        
        # Update on disk
        try:
            cache_file = self._get_cache_file(key)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(policy.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Failed to write cache file: {e}")
    
    def clear(self) -> int:
        """Clear all cache entries and return count cleared."""
        count = len(self.cache)
        self.cache.clear()
        
        # Clear disk cache
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            self.logger.warning(f"Failed to clear disk cache: {e}")
        
        self.logger.info(f"Cleared {count} doctrine cache entries")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        return {
            "memory_cache_size": len(self.cache),
            "disk_cache_files": len(cache_files),
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.ttl_hours,
        }


class DoctrineAdapter:
    """
    Adapter for interacting with the BLUX Doctrine API.
    
    Provides access to centralized doctrine policies with caching,
    fallback mechanisms, and integration with BLUX-cA constitution.
    """
    
    # Default embedded policies (fallback when API is unavailable)
    EMBEDDED_POLICIES = [
        DoctrinePolicy(
            source_id="embedded.integrity",
            name="integrity_over_everything",
            title="Integrity Over Everything",
            description="Maintain absolute integrity in all actions and communications",
            category=DoctrineCategory.ETHICAL,
            content="Integrity must be maintained above all other considerations, including convenience, approval, or short-term gains.",
            version="1.0",
            priority=100,
            source=DoctrineSource.EMBEDDED,
            tags=["core", "ethics", "integrity"],
            enforcement_level="REQUIRED",
            violation_severity="CRITICAL",
            compliance_required=True,
        ),
        DoctrinePolicy(
            source_id="embedded.truth_over_comfort",
            name="truth_over_comfort",
            title="Truth Over Comfort",
            description="Prioritize truth and accuracy over comfort or convenience",
            category=DoctrineCategory.ETHICAL,
            content="Truth must be prioritized even when uncomfortable or inconvenient. Never conceal or distort truth to avoid discomfort.",
            version="1.0",
            priority=90,
            source=DoctrineSource.EMBEDDED,
            tags=["core", "ethics", "truth"],
            enforcement_level="REQUIRED",
            violation_severity="HIGH",
            compliance_required=True,
        ),
        DoctrinePolicy(
            source_id="embedded.user_autonomy",
            name="user_autonomy",
            title="User Autonomy and Consent",
            description="Respect user autonomy and obtain informed consent",
            category=DoctrineCategory.ETHICAL,
            content="Users must retain full autonomy over their decisions and data. Never manipulate, coerce, or make decisions for users without explicit consent.",
            version="1.0",
            priority=95,
            source=DoctrineSource.EMBEDDED,
            tags=["core", "ethics", "autonomy", "consent"],
            enforcement_level="REQUIRED",
            violation_severity="CRITICAL",
            compliance_required=True,
        ),
        DoctrinePolicy(
            source_id="embedded.no_harm",
            name="no_harm_principle",
            title="Do No Harm",
            description="Prevent harm to users and others",
            category=DoctrineCategory.SAFETY,
            content="Take all reasonable measures to prevent physical, psychological, or social harm to users and others affected by system actions.",
            version="1.0",
            priority=100,
            source=DoctrineSource.EMBEDDED,
            tags=["core", "safety", "ethics"],
            enforcement_level="REQUIRED",
            violation_severity="CRITICAL",
            compliance_required=True,
        ),
        DoctrinePolicy(
            source_id="embedded.privacy",
            name="data_privacy",
            title="Data Privacy and Confidentiality",
            description="Protect user privacy and maintain confidentiality",
            category=DoctrineCategory.PRIVACY,
            content="User data must be protected with appropriate security measures. Only collect necessary data, and never share without explicit consent.",
            version="1.0",
            priority=85,
            source=DoctrineSource.EMBEDDED,
            tags=["privacy", "security", "data"],
            enforcement_level="REQUIRED",
            violation_severity="HIGH",
            compliance_required=True,
        ),
    ]
    
    def __init__(
        self,
        endpoint: str = "https://doctrine.blux.local",
        api_key: Optional[str] = None,
        cache_ttl_hours: int = 24,
        enable_cache: bool = True,
        timeout: int = 30,
        retry_attempts: int = 3,
        use_embedded_fallback: bool = True,
    ) -> None:
        """
        Initialize doctrine adapter.
        
        Args:
            endpoint: Doctrine API endpoint URL
            api_key: API key for authentication (optional)
            cache_ttl_hours: Cache time-to-live in hours
            enable_cache: Enable caching of policies
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            use_embedded_fallback: Use embedded policies when API unavailable
        """
        self.endpoint = endpoint.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.use_embedded_fallback = use_embedded_fallback
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize cache
        self.cache_enabled = enable_cache
        self.cache = DoctrineCache(ttl_hours=cache_ttl_hours) if enable_cache else None
        
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
        
        # Metrics
        self.metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "embedded_fallbacks": 0,
            "errors": 0,
            "last_sync": None,
        }
        
        # Load embedded policies
        self.embedded_policies = {p.source_id: p for p in self.EMBEDDED_POLICIES}
        
        self.logger.info(f"Doctrine adapter initialized (endpoint: {self.endpoint})")
    
    def _make_request(self, method: str, path: str, **kwargs) -> Optional[requests.Response]:
        """Make HTTP request to doctrine API with error handling."""
        url = f"{self.endpoint}{path}"
        
        try:
            # Update timeout
            kwargs.setdefault('timeout', self.timeout)
            
            # Make request
            self.metrics["api_calls"] += 1
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error to doctrine API: {e}")
            self.metrics["errors"] += 1
            return None
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout connecting to doctrine API: {e}")
            self.metrics["errors"] += 1
            return None
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP error from doctrine API: {e}")
            self.metrics["errors"] += 1
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error contacting doctrine API: {e}")
            self.metrics["errors"] += 1
            return None
    
    def fetch_policy(self, policy_id: str, use_cache: bool = True) -> Optional[DoctrinePolicy]:
        """
        Fetch a specific policy by ID.
        
        Args:
            policy_id: Policy identifier
            use_cache: Use cache if available
            
        Returns:
            DoctrinePolicy or None if not found
        """
        # Check cache first
        cache_key = f"policy_{policy_id}"
        if use_cache and self.cache_enabled and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                self.metrics["cache_hits"] += 1
                cached.update_access()
                return cached
        
        self.metrics["cache_misses"] += 1
        
        # Try to fetch from API
        response = self._make_request("GET", f"/api/v1/policies/{policy_id}")
        
        if response:
            try:
                data = response.json()
                policy = DoctrinePolicy.from_dict(data)
                policy.source = DoctrineSource.CENTRAL_API
                
                # Update cache
                if self.cache_enabled and self.cache:
                    self.cache.set(cache_key, policy)
                
                policy.update_access()
                return policy
                
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Failed to parse policy response: {e}")
                return None
        
        # Fall back to embedded policies
        if self.use_embedded_fallback:
            embedded_key = f"embedded.{policy_id}"
            if embedded_key in self.embedded_policies:
                self.metrics["embedded_fallbacks"] += 1
                self.logger.warning(f"Using embedded fallback for policy: {policy_id}")
                policy = self.embedded_policies[embedded_key]
                policy.update_access()
                return policy
        
        self.logger.warning(f"Policy not found: {policy_id}")
        return None
    
    def fetch_policies(self, query: Optional[DoctrineQuery] = None) -> List[DoctrinePolicy]:
        """
        Fetch multiple policies based on query.
        
        Args:
            query: Query parameters for filtering policies
            
        Returns:
            List of matching DoctrinePolicy objects
        """
        query = query or DoctrineQuery()
        
        # Build cache key from query
        query_hash = str(hash(json.dumps(query.to_dict(), sort_keys=True)))
        cache_key = f"query_{query_hash}"
        
        # Check cache
        if self.cache_enabled and self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                self.metrics["cache_hits"] += 1
                cached.update_access()
                return [cached] if isinstance(cached, DoctrinePolicy) else cached
        
        self.metrics["cache_misses"] += 1
        
        # Try to fetch from API
        response = self._make_request(
            "POST",
            "/api/v1/policies/query",
            json=query.to_dict()
        )
        
        policies = []
        
        if response:
            try:
                data = response.json()
                for item in data.get("policies", []):
                    policy = DoctrinePolicy.from_dict(item)
                    policy.source = DoctrineSource.CENTRAL_API
                    policies.append(policy)
                
                # Update cache
                if self.cache_enabled and self.cache and policies:
                    self.cache.set(cache_key, policies)
                
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"Failed to parse policies response: {e}")
        
        # If API failed and we have embedded fallback, use embedded policies
        if not policies and self.use_embedded_fallback:
            self.metrics["embedded_fallbacks"] += 1
            self.logger.warning("Using embedded policies as fallback")
            
            for policy in self.embedded_policies.values():
                # Apply query filters to embedded policies
                if query.categories and policy.category not in query.categories:
                    continue
                if query.tags and not any(tag in policy.tags for tag in query.tags):
                    continue
                if policy.priority < query.min_priority or policy.priority > query.max_priority:
                    continue
                if query.active_only and not policy.is_active():
                    continue
                
                policies.append(policy)
                
                # Apply limit if specified
                if query.limit and len(policies) >= query.limit:
                    break
        
        # Update access metrics
        for policy in policies:
            policy.update_access()
        
        return policies
    
    def get_constitutional_rules(self, query: Optional[DoctrineQuery] = None) -> List[ConstitutionalRule]:
        """
        Fetch doctrine policies and convert them to constitutional rules.
        
        Args:
            query: Query parameters for filtering policies
            
        Returns:
            List of ConstitutionalRule objects
        """
        policies = self.fetch_policies(query)
        rules = []
        
        for policy in policies:
            try:
                rule = policy.to_constitutional_rule()
                rules.append(rule)
            except Exception as e:
                self.logger.warning(f"Failed to convert policy {policy.name} to rule: {e}")
        
        return rules
    
    def validate_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an action against applicable doctrine policies.
        
        Args:
            action: Action to validate
            context: Context for validation
            
        Returns:
            Validation result with violations and recommendations
        """
        # Determine which policies apply based on context
        query = DoctrineQuery(
            categories=[DoctrineCategory.ETHICAL, DoctrineCategory.SAFETY, DoctrineCategory.LEGAL],
            active_only=True,
            min_priority=50,  # Only high-priority policies for validation
        )
        
        policies = self.fetch_policies(query)
        violations = []
        warnings = []
        recommendations = []
        
        for policy in policies:
            if not self._policy_applies(policy, context):
                continue
            
            # Simple validation logic (in real implementation, this would be more sophisticated)
            violation = self._check_policy_violation(policy, action, context)
            if violation:
                if policy.violation_severity == "CRITICAL":
                    violations.append({
                        "policy_id": policy.id,
                        "policy_name": policy.name,
                        "severity": policy.violation_severity,
                        "description": violation,
                        "policy_content": policy.content,
                    })
                else:
                    warnings.append({
                        "policy_id": policy.id,
                        "policy_name": policy.name,
                        "severity": policy.violation_severity,
                        "description": violation,
                        "policy_content": policy.content,
                    })
            
            # Add policy as recommendation if relevant
            if self._policy_relevant(policy, action, context):
                recommendations.append({
                    "policy_id": policy.id,
                    "policy_name": policy.name,
                    "guidance": policy.content,
                    "priority": policy.priority,
                })
        
        # Determine overall validation result
        allowed = len(violations) == 0
        if violations:
            action_result = "REJECT"
        elif warnings:
            action_result = "WARN"
        else:
            action_result = "ALLOW"
        
        return {
            "allowed": allowed,
            "action": action_result,
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations,
            "policy_count": len(policies),
            "applicable_policy_count": len([p for p in policies if self._policy_applies(p, context)]),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _policy_applies(self, policy: DoctrinePolicy, context: Dict[str, Any]) -> bool:
        """Check if a policy applies to the given context."""
        if not policy.is_active():
            return False
        
        # Check jurisdiction
        if policy.jurisdiction and "jurisdiction" in context:
            if context["jurisdiction"] not in policy.jurisdiction:
                return False
        
        # Check other context filters could be added here
        
        return True
    
    def _policy_relevant(self, policy: DoctrinePolicy, action: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if a policy is relevant to the action and context."""
        # Simple relevance check based on policy tags and action type
        action_str = json.dumps(action).lower()
        policy_tags = " ".join(policy.tags).lower()
        
        # Check if any policy tag appears in the action
        for tag in policy.tags:
            if tag.lower() in action_str:
                return True
        
        # Check policy content keywords in action
        keywords = policy.content.lower().split()[:10]  # First 10 words as keywords
        for keyword in keywords:
            if len(keyword) > 4 and keyword in action_str:  # Only meaningful words
                return True
        
        return False
    
    def _check_policy_violation(
        self, 
        policy: DoctrinePolicy, 
        action: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Check if an action violates a specific policy."""
        # This is a simplified implementation
        # In a real system, this would use more sophisticated NLP or pattern matching
        
        action_str = json.dumps(action).lower()
        policy_content = policy.content.lower()
        
        # Extract key phrases from policy
        key_phrases = []
        sentences = policy_content.split('.')
        for sentence in sentences:
            words = sentence.strip().split()
            if len(words) > 3:  # Meaningful sentences
                # Look for imperative or prohibitive phrases
                if any(word in sentence for word in ["must", "shall", "will not", "cannot", "should not"]):
                    key_phrases.append(sentence.strip())
        
        # Simple check: if action mentions something that contradicts policy key phrases
        for phrase in key_phrases:
            # Look for contradictions (simplified)
            if "not" in phrase:
                # Policy prohibits something
                prohibited = phrase.replace("not", "").replace("cannot", "").replace("should not", "").strip()
                if prohibited and prohibited in action_str:
                    return f"Action appears to violate prohibition: {phrase}"
            else:
                # Policy requires something
                if "must" in phrase or "shall" in phrase:
                    required = phrase.replace("must", "").replace("shall", "").strip()
                    # Check if action doesn't mention the requirement
                    if required and required not in action_str:
                        # This is too simplistic - just an example
                        pass
        
        return None
    
    def sync_policies(self, force: bool = False) -> bool:
        """
        Sync local policy cache with central server.
        
        Args:
            force: Force sync even if cache is recent
            
        Returns:
            True if sync successful, False otherwise
        """
        if not self.cache_enabled:
            self.logger.warning("Cache not enabled, skipping sync")
            return False
        
        # Check if we need to sync (based on TTL)
        if not force and self.metrics.get("last_sync"):
            try:
                last_sync = datetime.fromisoformat(self.metrics["last_sync"])
                if datetime.now() - last_sync < timedelta(hours=self.cache.ttl_hours):
                    self.logger.debug("Sync skipped - cache is recent")
                    return True
            except (ValueError, TypeError):
                pass
        
        try:
            # Fetch all active policies
            query = DoctrineQuery(active_only=True, limit=1000)  # Reasonable limit
            policies = self.fetch_policies(query)
            
            # Clear and rebuild cache
            if self.cache:
                self.cache.clear()
                
                # Cache individual policies
                for policy in policies:
                    cache_key = f"policy_{policy.source_id or policy.id}"
                    self.cache.set(cache_key, policy)
                
                # Cache the query result
                query_hash = str(hash(json.dumps(query.to_dict(), sort_keys=True)))
                query_cache_key = f"query_{query_hash}"
                self.cache.set(query_cache_key, policies)
            
            self.metrics["last_sync"] = datetime.now().isoformat()
            self.logger.info(f"Synced {len(policies)} policies")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sync policies: {e}")
            return False
    
    def get_embedded_policies(self) -> List[DoctrinePolicy]:
        """Get all embedded (fallback) policies."""
        return list(self.embedded_policies.values())
    
    def add_custom_policy(self, policy: DoctrinePolicy) -> str:
        """
        Add a custom/user-defined policy.
        
        Args:
            policy: Custom policy to add
            
        Returns:
            ID of the added policy
        """
        policy.source = DoctrineSource.USER_DEFINED
        policy.source_id = f"custom.{policy.id}"
        
        # Cache the custom policy
        if self.cache_enabled and self.cache:
            cache_key = f"custom_{policy.id}"
            self.cache.set(cache_key, policy)
        
        self.logger.info(f"Added custom policy: {policy.name}")
        return policy.id
    
    def remove_custom_policy(self, policy_id: str) -> bool:
        """Remove a custom policy."""
        if self.cache_enabled and self.cache:
            cache_key = f"custom_{policy_id}"
            # This only removes from cache, not from any persistent storage
            # In a real implementation, you might want persistent storage
            pass
        
        self.logger.info(f"Removed custom policy: {policy_id}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status and metrics."""
        status = {
            "endpoint": self.endpoint,
            "api_available": self._check_api_availability(),
            "cache_enabled": self.cache_enabled,
            "use_embedded_fallback": self.use_embedded_fallback,
            "metrics": self.metrics.copy(),
            "embedded_policy_count": len(self.embedded_policies),
        }
        
        if self.cache:
            status["cache_stats"] = self.cache.get_stats()
        
        return status
    
    def _check_api_availability(self) -> bool:
        """Check if doctrine API is available."""
        try:
            response = self._make_request("GET", "/health", timeout=5)
            return response is not None and response.status_code == 200
        except Exception:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def reset_metrics(self) -> None:
        """Reset metrics counters."""
        self.metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "embedded_fallbacks": 0,
            "errors": 0,
            "last_sync": self.metrics.get("last_sync"),
        }


# Convenience functions

def create_doctrine_adapter(
    endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
    enable_cache: bool = True,
    use_embedded_fallback: bool = True
) -> DoctrineAdapter:
    """
    Create a doctrine adapter with sensible defaults.
    
    Args:
        endpoint: Doctrine API endpoint (defaults to environment variable or default)
        api_key: API key for authentication
        enable_cache: Enable caching
        use_embedded_fallback: Use embedded policies as fallback
        
    Returns:
        Configured DoctrineAdapter instance
    """
    import os
    
    # Get endpoint from environment or use default
    if endpoint is None:
        endpoint = os.getenv("BLUX_DOCTRINE_ENDPOINT", "https://doctrine.blux.local")
    
    # Get API key from environment if not provided
    if api_key is None:
        api_key = os.getenv("BLUX_DOCTRINE_API_KEY")
    
    return DoctrineAdapter(
        endpoint=endpoint,
        api_key=api_key,
        enable_cache=enable_cache,
        use_embedded_fallback=use_embedded_fallback
    )


def get_core_ethical_policies() -> List[DoctrinePolicy]:
    """Get core ethical policies (convenience function)."""
    adapter = DoctrineAdapter(use_embedded_fallback=True)
    query = DoctrineQuery(
        categories=[DoctrineCategory.ETHICAL],
        min_priority=75,
        active_only=True
    )
    return adapter.fetch_policies(query)


__all__ = [
    "DoctrineAdapter",
    "DoctrinePolicy",
    "DoctrineQuery",
    "DoctrineSource",
    "DoctrineCategory",
    "DoctrineCache",
    "create_doctrine_adapter",
    "get_core_ethical_policies",
]