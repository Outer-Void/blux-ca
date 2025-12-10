from __future__ import annotations

"""
Comprehensive constitution system for BLUX-cA.

Defines ethical principles, operational rules, and safety guardrails
that govern agent behavior and decision-making.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4


class RuleType(str, Enum):
    """Types of constitutional rules."""
    ETHICAL_PRINCIPLE = "ETHICAL_PRINCIPLE"      # Core ethical guidelines
    OPERATIONAL_RULE = "OPERATIONAL_RULE"        # How the agent operates
    SAFETY_GUARDRAIL = "SAFETY_GUARDRAIL"        # Safety constraints
    QUALITY_STANDARD = "QUALITY_STANDARD"        # Response quality standards
    LEGAL_COMPLIANCE = "LEGAL_COMPLIANCE"        # Legal requirements
    USER_PROTECTION = "USER_PROTECTION"          # User safety and privacy
    SYSTEM_INTEGRITY = "SYSTEM_INTEGRITY"        # System operational rules


class RulePriority(int, Enum):
    """Rule priority levels (higher = more important)."""
    CRITICAL = 100      # Must never be violated (safety, legal)
    HIGH = 75           # Strong preference, exceptions rare
    MEDIUM = 50         # Standard operational rules
    LOW = 25            # Guidelines and best practices
    INFORMATIONAL = 0   # For information only


class RuleScope(str, Enum):
    """Scope where rule applies."""
    GLOBAL = "GLOBAL"           # Applies to all interactions
    PER_USER = "PER_USER"       # User-specific rules
    PER_SESSION = "PER_SESSION" # Session-specific rules
    CONTEXTUAL = "CONTEXTUAL"   # Context-dependent rules
    DIMENSION_SPECIFIC = "DIMENSION_SPECIFIC"  # Specific to clarity dimensions


@dataclass
class RuleCondition:
    """Condition for when a rule applies."""
    field: str                    # Field to check (e.g., "user_type", "recovery_state")
    operator: str                 # Comparison operator ("==", "!=", "in", ">", "<", "contains")
    value: Any                    # Value to compare against
    logical_operator: str = "AND"  # How to combine with other conditions ("AND", "OR")
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        context_value = context.get(self.field)
        
        if self.operator == "==":
            return context_value == self.value
        elif self.operator == "!=":
            return context_value != self.value
        elif self.operator == "in":
            return context_value in self.value if isinstance(self.value, list) else False
        elif self.operator == "not in":
            return context_value not in self.value if isinstance(self.value, list) else False
        elif self.operator == ">":
            return context_value > self.value if isinstance(context_value, (int, float)) else False
        elif self.operator == "<":
            return context_value < self.value if isinstance(context_value, (int, float)) else False
        elif self.operator == ">=":
            return context_value >= self.value if isinstance(context_value, (int, float)) else False
        elif self.operator == "<=":
            return context_value <= self.value if isinstance(context_value, (int, float)) else False
        elif self.operator == "contains":
            return self.value in str(context_value) if context_value else False
        elif self.operator == "not contains":
            return self.value not in str(context_value) if context_value else True
        elif self.operator == "exists":
            return self.field in context
        elif self.operator == "not exists":
            return self.field not in context
        else:
            logging.warning(f"Unknown operator: {self.operator}")
            return False


@dataclass
class ConstitutionalRule:
    """
    A single constitutional rule with metadata and enforcement logic.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""                    # Human-readable name
    description: str = ""             # Detailed description
    rule_type: RuleType = RuleType.OPERATIONAL_RULE
    priority: RulePriority = RulePriority.MEDIUM
    scope: RuleScope = RuleScope.GLOBAL
    
    # Rule content
    statement: str = ""               # The rule statement
    positive_examples: List[str] = field(default_factory=list)  # Examples of compliance
    negative_examples: List[str] = field(default_factory=list)  # Examples of violation
    
    # Conditions for when rule applies
    conditions: List[RuleCondition] = field(default_factory=list)
    
    # Enforcement
    enforcement: str = "REQUIRE"      # REQUIRE, RECOMMEND, SUGGEST, INFORM
    violation_action: str = "REJECT"  # REJECT, WARN, MODIFY, ESCALATE, AUDIT
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    active: bool = True
    
    # Related rules
    depends_on: List[str] = field(default_factory=list)  # Rule IDs this depends on
    conflicts_with: List[str] = field(default_factory=list)  # Rule IDs that conflict
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['rule_type'] = self.rule_type.value
        data['priority'] = self.priority.value
        data['scope'] = self.scope.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        
        # Convert conditions
        data['conditions'] = []
        for condition in self.conditions:
            data['conditions'].append(asdict(condition))
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConstitutionalRule:
        """Create from dictionary."""
        # Convert string enums back to enum values
        data = data.copy()
        data['rule_type'] = RuleType(data['rule_type'])
        data['priority'] = RulePriority(data['priority'])
        data['scope'] = RuleScope(data['scope'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        # Convert conditions
        if 'conditions' in data:
            conditions = []
            for cond_data in data['conditions']:
                conditions.append(RuleCondition(**cond_data))
            data['conditions'] = conditions
        
        return cls(**data)
    
    def applies_to_context(self, context: Dict[str, Any]) -> bool:
        """Check if rule applies to given context."""
        if not self.active:
            return False
        
        if not self.conditions:
            return True  # No conditions = applies to all
        
        result = True if self.conditions[0].logical_operator == "AND" else False
        
        for condition in self.conditions:
            condition_result = condition.evaluate(context)
            
            if condition.logical_operator == "AND":
                result = result and condition_result
                if not result:  # Short-circuit AND
                    break
            elif condition.logical_operator == "OR":
                result = result or condition_result
                if result:  # Short-circuit OR
                    break
        
        return result
    
    def check_violation(self, context: Dict[str, Any], action: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Check if action violates this rule.
        
        Returns:
            Tuple of (is_violation, violation_description, confidence)
        """
        # This is a stub - in real implementation, this would use NLP or
        # pattern matching to check if action violates the rule statement
        # For now, we'll use simple keyword matching
        
        if not self.applies_to_context(context):
            return False, "", 0.0
        
        # Simple keyword-based violation detection
        action_str = json.dumps(action).lower()
        rule_keywords = self._extract_keywords(self.statement)
        
        violation_score = 0.0
        for keyword in rule_keywords:
            if keyword in action_str:
                violation_score += 0.3  # Each keyword match adds to score
        
        is_violation = violation_score > 0.5
        description = f"Potential violation of '{self.name}'" if is_violation else ""
        
        return is_violation, description, min(violation_score, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from rule statement."""
        # Simple keyword extraction - in real implementation, use NLP
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = text.lower().split()
        keywords = [word.strip('.,!?;:') for word in words if word not in stop_words and len(word) > 3]
        return list(set(keywords))  # Remove duplicates
    
    def get_guidance(self, context: Dict[str, Any]) -> Optional[str]:
        """Get guidance for complying with this rule in given context."""
        if not self.applies_to_context(context):
            return None
        
        guidance = f"Consider: {self.statement}"
        if self.positive_examples:
            guidance += f"\nExample: {self.positive_examples[0]}"
        
        return guidance
    
    def update(self, **kwargs) -> None:
        """Update rule properties."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now()


class ConstitutionEngine:
    """
    Engine for managing and applying constitutional rules.
    """
    
    # Core BLUX-cA constitutional principles
    CORE_PRINCIPLES = [
        ConstitutionalRule(
            name="truth_over_comfort",
            rule_type=RuleType.ETHICAL_PRINCIPLE,
            priority=RulePriority.HIGH,
            statement="Prioritize truth and clarity over comfort or convenience",
            description="Never hide difficult truths to make users feel better",
            enforcement="REQUIRE",
            violation_action="REJECT",
            tags=["ethics", "core", "truth"]
        ),
        ConstitutionalRule(
            name="integrity_over_approval",
            rule_type=RuleType.ETHICAL_PRINCIPLE,
            priority=RulePriority.HIGH,
            statement="Maintain integrity even when it risks disapproval",
            description="Don't compromise principles to gain approval or avoid conflict",
            enforcement="REQUIRE",
            violation_action="REJECT",
            tags=["ethics", "core", "integrity"]
        ),
        ConstitutionalRule(
            name="user_autonomy",
            rule_type=RuleType.USER_PROTECTION,
            priority=RulePriority.CRITICAL,
            statement="Respect user autonomy and decision-making capacity",
            description="Never manipulate, coerce, or make decisions for users",
            enforcement="REQUIRE",
            violation_action="REJECT",
            tags=["safety", "autonomy", "core"]
        ),
        ConstitutionalRule(
            name="no_harm_principle",
            rule_type=RuleType.SAFETY_GUARDRAIL,
            priority=RulePriority.CRITICAL,
            statement="Do not cause or enable harm to users or others",
            description="Prevent physical, psychological, or social harm",
            enforcement="REQUIRE",
            violation_action="REJECT",
            tags=["safety", "ethics", "core"]
        ),
        ConstitutionalRule(
            name="clarity_over_complexity",
            rule_type=RuleType.QUALITY_STANDARD,
            priority=RulePriority.MEDIUM,
            statement="Communicate with clarity rather than unnecessary complexity",
            description="Make insights accessible and understandable",
            enforcement="RECOMMEND",
            violation_action="WARN",
            tags=["quality", "communication"]
        ),
        ConstitutionalRule(
            name="boundary_respect",
            rule_type=RuleType.OPERATIONAL_RULE,
            priority=RulePriority.HIGH,
            statement="Respect user boundaries and therapeutic scope",
            description="Stay within competence boundaries, refer when needed",
            enforcement="REQUIRE",
            violation_action="REJECT",
            conditions=[
                RuleCondition(field="user_type", operator="==", value="crisis", logical_operator="OR"),
                RuleCondition(field="recovery_state", operator="==", value="CRISIS", logical_operator="OR"),
            ],
            tags=["safety", "boundaries"]
        ),
        ConstitutionalRule(
            name="shadow_work_safety",
            rule_type=RuleType.SAFETY_GUARDRAIL,
            priority=RulePriority.HIGH,
            statement="Approach shadow work with appropriate pacing and safety",
            description="Don't push users into shadow work before they're ready",
            enforcement="REQUIRE",
            violation_action="MODIFY",
            conditions=[
                RuleCondition(field="dimension", operator="==", value="shadow", logical_operator="AND"),
            ],
            tags=["safety", "shadow", "pacing"]
        ),
        ConstitutionalRule(
            name="crisis_stabilization_first",
            rule_type=RuleType.OPERATIONAL_RULE,
            priority=RulePriority.CRITICAL,
            statement="In crisis situations, prioritize stabilization over exploration",
            description="Focus on grounding and safety before deeper work",
            enforcement="REQUIRE",
            violation_action="REJECT",
            conditions=[
                RuleCondition(field="recovery_state", operator="==", value="CRISIS", logical_operator="OR"),
                RuleCondition(field="user_type", operator="==", value="crisis", logical_operator="OR"),
            ],
            tags=["safety", "crisis", "prioritization"]
        ),
        ConstitutionalRule(
            name="transparency_in_limitations",
            rule_type=RuleType.ETHICAL_PRINCIPLE,
            priority=RulePriority.MEDIUM,
            statement="Be transparent about system limitations and capabilities",
            description="Don't pretend to have capabilities or knowledge you don't possess",
            enforcement="REQUIRE",
            violation_action="WARN",
            tags=["ethics", "transparency"]
        ),
        ConstitutionalRule(
            name="emotional_validation",
            rule_type=RuleType.QUALITY_STANDARD,
            priority=RulePriority.MEDIUM,
            statement="Validate emotions before attempting to solve problems",
            description="Acknowledge and validate emotional experience first",
            enforcement="RECOMMEND",
            violation_action="WARN",
            conditions=[
                RuleCondition(field="dimension", operator="==", value="emotional", logical_operator="OR"),
            ],
            tags=["quality", "emotional", "validation"]
        ),
    ]
    
    def __init__(
        self,
        rules: Optional[List[ConstitutionalRule]] = None,
        mode: str = "strict",  # "strict", "balanced", "permissive"
        enable_audit: bool = True
    ):
        """
        Initialize constitution engine.
        
        Args:
            rules: List of constitutional rules (defaults to core principles)
            mode: Enforcement mode
            enable_audit: Whether to log constitutional evaluations
        """
        self.rules: Dict[str, ConstitutionalRule] = {}
        self.mode = mode
        self.enable_audit = enable_audit
        self.logger = logging.getLogger(__name__)
        
        # Load rules
        if rules:
            for rule in rules:
                self.add_rule(rule)
        else:
            self._load_core_principles()
        
        # Initialize rule index for faster lookup
        self._build_rule_index()
    
    def _load_core_principles(self) -> None:
        """Load core constitutional principles."""
        for rule in self.CORE_PRINCIPLES:
            self.add_rule(rule)
    
    def _build_rule_index(self) -> None:
        """Build indexes for faster rule lookup."""
        self._rule_index_by_type: Dict[RuleType, List[str]] = {}
        self._rule_index_by_tag: Dict[str, List[str]] = {}
        
        for rule_id, rule in self.rules.items():
            # Index by type
            if rule.rule_type not in self._rule_index_by_type:
                self._rule_index_by_type[rule.rule_type] = []
            self._rule_index_by_type[rule.rule_type].append(rule_id)
            
            # Index by tag
            for tag in rule.tags:
                if tag not in self._rule_index_by_tag:
                    self._rule_index_by_tag[tag] = []
                self._rule_index_by_tag[tag].append(rule_id)
    
    def add_rule(self, rule: ConstitutionalRule) -> str:
        """Add a new constitutional rule."""
        # Check for conflicts with existing rules
        conflicts = self._check_rule_conflicts(rule)
        if conflicts:
            self.logger.warning(f"Rule '{rule.name}' conflicts with: {conflicts}")
        
        self.rules[rule.id] = rule
        self._build_rule_index()  # Rebuild index
        
        self.logger.info(f"Added constitutional rule: {rule.name} ({rule.id})")
        return rule.id
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a constitutional rule."""
        if rule_id in self.rules:
            rule_name = self.rules[rule_id].name
            del self.rules[rule_id]
            self._build_rule_index()  # Rebuild index
            self.logger.info(f"Removed constitutional rule: {rule_name} ({rule_id})")
            return True
        return False
    
    def update_rule(self, rule_id: str, **kwargs) -> bool:
        """Update an existing rule."""
        if rule_id in self.rules:
            self.rules[rule_id].update(**kwargs)
            self._build_rule_index()  # Rebuild index
            self.logger.info(f"Updated constitutional rule: {self.rules[rule_id].name}")
            return True
        return False
    
    def _check_rule_conflicts(self, new_rule: ConstitutionalRule) -> List[str]:
        """Check for conflicts between new rule and existing rules."""
        conflicts = []
        
        for rule_id, existing_rule in self.rules.items():
            # Check if new rule conflicts with existing
            if existing_rule.name == new_rule.name and existing_rule.id != new_rule.id:
                conflicts.append(f"Duplicate name: {existing_rule.name}")
            
            # Check if rule statements contradict (simple check)
            if self._rules_contradict(existing_rule, new_rule):
                conflicts.append(f"Contradicts: {existing_rule.name}")
        
        return conflicts
    
    def _rules_contradict(self, rule1: ConstitutionalRule, rule2: ConstitutionalRule) -> bool:
        """Check if two rules contradict each other."""
        # Simple contradiction detection based on keywords
        # In a real implementation, this would use more sophisticated NLP
        contradictions = {
            "always": "never",
            "must": "must not",
            "require": "forbid",
            "allow": "prohibit",
        }
        
        text1 = rule1.statement.lower()
        text2 = rule2.statement.lower()
        
        for word1, word2 in contradictions.items():
            if word1 in text1 and word2 in text2:
                return True
            if word2 in text1 and word1 in text2:
                return True
        
        return False
    
    def evaluate(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any],
        agent_name: str = "BLUX-cA"
    ) -> Dict[str, Any]:
        """
        Evaluate an action against all applicable constitutional rules.
        
        Args:
            action: The proposed action to evaluate
            context: Current context (user type, recovery state, etc.)
            agent_name: Name of the agent performing the evaluation
            
        Returns:
            Evaluation result with violations, warnings, and final decision
        """
        applicable_rules = self._get_applicable_rules(context)
        violations = []
        warnings = []
        recommendations = []
        
        for rule in applicable_rules:
            is_violation, description, confidence = rule.check_violation(context, action)
            
            if is_violation and confidence > 0.7:
                violation = {
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "rule_type": rule.rule_type.value,
                    "priority": rule.priority.value,
                    "description": description,
                    "confidence": confidence,
                    "enforcement": rule.enforcement,
                    "violation_action": rule.violation_action,
                    "rule_statement": rule.statement,
                }
                
                if rule.priority >= RulePriority.HIGH:
                    violations.append(violation)
                else:
                    warnings.append(violation)
            
            # Get guidance even if no violation
            guidance = rule.get_guidance(context)
            if guidance:
                recommendations.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "guidance": guidance
                })
        
        # Apply mode-based filtering
        if self.mode == "permissive":
            # Only critical violations matter
            violations = [v for v in violations if v["priority"] >= RulePriority.CRITICAL.value]
        elif self.mode == "balanced":
            # Allow some medium-priority violations with warnings
            high_violations = [v for v in violations if v["priority"] >= RulePriority.HIGH.value]
            medium_violations = [v for v in violations if v["priority"] == RulePriority.MEDIUM.value]
            
            if high_violations:
                violations = high_violations
            else:
                # Convert medium violations to warnings
                warnings.extend(medium_violations)
                violations = []
        
        # Make decision
        decision = self._make_decision(violations, warnings, context)
        
        result = {
            "decision": decision["action"],
            "allowed": decision["allowed"],
            "reason": decision["reason"],
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations,
            "rule_count": len(applicable_rules),
            "violation_count": len(violations),
            "warning_count": len(warnings),
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
        }
        
        # Audit the evaluation if enabled
        if self.enable_audit:
            self._audit_evaluation(result, action, context)
        
        return result
    
    def _get_applicable_rules(self, context: Dict[str, Any]) -> List[ConstitutionalRule]:
        """Get all rules that apply to the given context."""
        applicable = []
        
        for rule in self.rules.values():
            if rule.applies_to_context(context):
                applicable.append(rule)
        
        # Sort by priority (highest first)
        applicable.sort(key=lambda r: r.priority.value, reverse=True)
        
        return applicable
    
    def _make_decision(
        self,
        violations: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make decision based on violations and warnings."""
        
        if not violations:
            return {
                "action": "PROCEED",
                "allowed": True,
                "reason": "No constitutional violations detected"
            }
        
        # Check for critical violations
        critical_violations = [v for v in violations if v["priority"] >= RulePriority.CRITICAL.value]
        if critical_violations:
            return {
                "action": "REJECT",
                "allowed": False,
                "reason": f"Critical constitutional violation(s): {len(critical_violations)} rule(s) violated"
            }
        
        # Check for high priority violations
        high_violations = [v for v in violations if v["priority"] >= RulePriority.HIGH.value]
        if high_violations:
            # In crisis context, be more strict
            if context.get("recovery_state") == "CRISIS" or context.get("user_type") == "crisis":
                return {
                    "action": "REJECT",
                    "allowed": False,
                    "reason": "High-priority violations in crisis context"
                }
            else:
                return {
                    "action": "MODIFY",
                    "allowed": False,
                    "reason": f"High-priority violation(s) require action modification"
                }
        
        # Medium and low priority violations
        return {
            "action": "WARN_AND_PROCEED",
            "allowed": True,
            "reason": f"Proceed with {len(violations)} non-critical violation(s)"
        }
    
    def _audit_evaluation(
        self,
        result: Dict[str, Any],
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Audit constitutional evaluation."""
        # This would typically write to an audit log
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "context": context,
            "result": result,
            "rule_count": len(self.rules),
        }
        
        self.logger.info(
            f"Constitutional evaluation: {result['decision']} "
            f"({result['violation_count']} violations, {result['warning_count']} warnings)"
        )
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[ConstitutionalRule]:
        """Get all rules of a specific type."""
        rule_ids = self._rule_index_by_type.get(rule_type, [])
        return [self.rules[rule_id] for rule_id in rule_ids]
    
    def get_rules_by_tag(self, tag: str) -> List[ConstitutionalRule]:
        """Get all rules with a specific tag."""
        rule_ids = self._rule_index_by_tag.get(tag, [])
        return [self.rules[rule_id] for rule_id in rule_ids]
    
    def get_rule(self, rule_id: str) -> Optional[ConstitutionalRule]:
        """Get a specific rule by ID."""
        return self.rules.get(rule_id)
    
    def search_rules(
        self,
        search_text: str,
        field: str = "name"
    ) -> List[ConstitutionalRule]:
        """Search rules by text content."""
        results = []
        search_text_lower = search_text.lower()
        
        for rule in self.rules.values():
            if field == "name" and search_text_lower in rule.name.lower():
                results.append(rule)
            elif field == "description" and search_text_lower in rule.description.lower():
                results.append(rule)
            elif field == "statement" and search_text_lower in rule.statement.lower():
                results.append(rule)
            elif field == "all":
                if (search_text_lower in rule.name.lower() or
                    search_text_lower in rule.description.lower() or
                    search_text_lower in rule.statement.lower()):
                    results.append(rule)
        
        return results
    
    def export_rules(self, format: str = "json") -> Union[str, List[Dict[str, Any]]]:
        """Export all rules."""
        rules_list = [rule.to_dict() for rule in self.rules.values()]
        
        if format == "json":
            return rules_list
        elif format == "jsonl":
            return "\n".join(json.dumps(rule) for rule in rules_list)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_rules(self, rules_data: List[Dict[str, Any]]) -> int:
        """Import rules from data."""
        count = 0
        for rule_data in rules_data:
            try:
                rule = ConstitutionalRule.from_dict(rule_data)
                self.add_rule(rule)
                count += 1
            except Exception as e:
                self.logger.error(f"Failed to import rule: {e}")
        
        self.logger.info(f"Imported {count} constitutional rules")
        return count
    
    def save_to_file(self, filepath: Union[str, Path]) -> bool:
        """Save rules to file."""
        try:
            rules_data = self.export_rules("json")
            with open(filepath, 'w') as f:
                json.dump(rules_data, f, indent=2)
            self.logger.info(f"Saved {len(self.rules)} rules to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save rules: {e}")
            return False
    
    def load_from_file(self, filepath: Union[str, Path]) -> bool:
        """Load rules from file."""
        try:
            with open(filepath, 'r') as f:
                rules_data = json.load(f)
            
            # Clear existing rules except core ones
            core_rule_ids = [rule.id for rule in self.CORE_PRINCIPLES]
            rules_to_remove = [rule_id for rule_id in self.rules.keys() if rule_id not in core_rule_ids]
            
            for rule_id in rules_to_remove:
                self.remove_rule(rule_id)
            
            # Import new rules
            imported = self.import_rules(rules_data)
            self.logger.info(f"Loaded {imported} rules from {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load rules: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get constitution summary."""
        return {
            "total_rules": len(self.rules),
            "by_type": {rt.value: len(self.get_rules_by_type(rt)) for rt in RuleType},
            "by_priority": {rp.value: len([r for r in self.rules.values() if r.priority == rp]) for rp in RulePriority},
            "active_rules": len([r for r in self.rules.values() if r.active]),
            "mode": self.mode,
            "enable_audit": self.enable_audit,
        }


# Backward compatibility class
class Constitution(ConstitutionEngine):
    """Legacy Constitution class for backward compatibility."""
    
    def apply_rules(self, user_input: str, user_type: str) -> str:
        """Legacy method for basic rule application."""
        context = {
            "user_input": user_input,
            "user_type": user_type,
            "recovery_state": "UNKNOWN"
        }
        
        # Simple action to evaluate
        action = {"type": "response", "content": user_input}
        
        result = self.evaluate(action, context)
        
        if result["decision"] == "REJECT":
            return "set boundaries / off-ramp"
        elif result["decision"] == "MODIFY":
            return "modify approach based on constitutional rules"
        else:
            return "validate and provide guidance"