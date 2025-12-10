from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from .enums import RecoveryState


@dataclass
class UserState:
    """
    Comprehensive user state container for BLUX-cA.
    
    Designed to be serializable and user-controlled.
    Contains both recovery state and interaction metadata.
    """
    recovery_state: RecoveryState = RecoveryState.CRISIS
    history_hint: int = 0
    state_confidence: float = 0.7
    last_state_change: Optional[str] = None
    state_duration_minutes: int = 0
    interaction_count: int = 0
    clarity_scores: Dict[str, float] = field(default_factory=lambda: {
        "logical": 0.0,
        "emotional": 0.0,
        "shadow": 0.0
    })
    safety_flags: List[str] = field(default_factory=list)
    session_markers: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "recovery_state": self.recovery_state.value,
            "history_hint": self.history_hint,
            "state_confidence": self.state_confidence,
            "last_state_change": self.last_state_change,
            "state_duration_minutes": self.state_duration_minutes,
            "interaction_count": self.interaction_count,
            "clarity_scores": self.clarity_scores,
            "safety_flags": self.safety_flags,
            "session_markers": self.session_markers,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> UserState:
        """Create UserState from dictionary."""
        return cls(
            recovery_state=RecoveryState(data.get("recovery_state", "CRISIS")),
            history_hint=data.get("history_hint", 0),
            state_confidence=data.get("state_confidence", 0.7),
            last_state_change=data.get("last_state_change"),
            state_duration_minutes=data.get("state_duration_minutes", 0),
            interaction_count=data.get("interaction_count", 0),
            clarity_scores=data.get("clarity_scores", {}),
            safety_flags=data.get("safety_flags", []),
            session_markers=data.get("session_markers", {}),
            metadata=data.get("metadata", {})
        )


class StateTransitionReason(str, Enum):
    """Reasons for state transitions."""
    CRISIS_MARKER = "crisis_marker"
    PROGRESSION = "progression"
    REGRESSION = "regression"
    PURPOSE_MARKER = "purpose_marker"
    HONESTY_MARKER = "honesty_marker"
    AWARENESS_MARKER = "awareness_marker"
    RECONSTRUCTION_MARKER = "reconstruction_marker"
    INTEGRATION_MARKER = "integration_marker"
    TIME_BASED = "time_based"
    CLARITY_SCORE = "clarity_score"
    SAFETY_CONCERN = "safety_concern"
    USER_DIRECTED = "user_directed"


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: RecoveryState
    to_state: RecoveryState
    reason: StateTransitionReason
    confidence: float
    timestamp: str
    input_text: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RecoveryStateMachine:
    """
    Sophisticated adaptive state machine for BLUX-cA.
    
    Manages user's recovery state with intelligent transitions,
    safety checks, and persistence capabilities.
    """
    
    # State transition patterns with weights and confidence thresholds
    STATE_MARKERS = {
        RecoveryState.CRISIS: {
            "patterns": [
                (r"\b(i can'?t|can'?t go on|overwhelmed|emergency|panic|suicidal)\b", 0.9),
                (r"\b(dying|end it|no hope|helpless|trapped)\b", 0.8),
                (r"\b(urgent|immediate|right now|need help now)\b", 0.7),
                (r"\!{2,}", 0.6),  # Multiple exclamation marks
                (r"\b(crisis|emergency|urgent)\b", 0.8),
            ],
            "min_confidence": 0.6
        },
        RecoveryState.AWARENESS: {
            "patterns": [
                (r"\b(notice|aware|realize|see|observe|pattern)\b", 0.7),
                (r"\b(something is|feels like|seems to be|maybe)\b", 0.6),
                (r"\b(curious|wonder|question|think about)\b", 0.7),
                (r"\?", 0.5),  # Question marks
            ],
            "min_confidence": 0.5
        },
        RecoveryState.HONESTY: {
            "patterns": [
                (r"\b(i was wrong|my fault|i lied|i hurt|i own|admit)\b", 0.8),
                (r"\b(truth|honest|real|actual|fact)\b", 0.7),
                (r"\b(confess|acknowledge|recognize|accept)\b", 0.7),
                (r"\b(vulnerable|exposed|bare|raw)\b", 0.6),
            ],
            "min_confidence": 0.6
        },
        RecoveryState.RECONSTRUCTION: {
            "patterns": [
                (r"\b(rebuild|reconstruct|build|create|make)\b", 0.8),
                (r"\b(plan|routine|schedule|habit|system)\b", 0.7),
                (r"\b(next step|action|do|implement|execute)\b", 0.7),
                (r"\b(structure|framework|approach|method)\b", 0.6),
            ],
            "min_confidence": 0.5
        },
        RecoveryState.INTEGRATION: {
            "patterns": [
                (r"\b(integrate|combine|bring together|merge)\b", 0.8),
                (r"\b(understand|comprehend|make sense|see whole)\b", 0.7),
                (r"\b(part of|belong|fit|connect)\b", 0.6),
                (r"\b(whole picture|bigger picture|overview)\b", 0.7),
            ],
            "min_confidence": 0.5
        },
        RecoveryState.PURPOSE: {
            "patterns": [
                (r"\b(purpose|meaning|calling|mission|why)\b", 0.9),
                (r"\b(help others|give back|contribute|serve)\b", 0.8),
                (r"\b(make difference|impact|change|transform)\b", 0.7),
                (r"\b(direction|path|journey|destiny)\b", 0.6),
            ],
            "min_confidence": 0.6
        }
    }
    
    # Allowed state transitions (from -> to)
    ALLOWED_TRANSITIONS = {
        RecoveryState.CRISIS: [RecoveryState.AWARENESS, RecoveryState.HONESTY],
        RecoveryState.AWARENESS: [RecoveryState.HONESTY, RecoveryState.CRISIS, RecoveryState.RECONSTRUCTION],
        RecoveryState.HONESTY: [RecoveryState.RECONSTRUCTION, RecoveryState.AWARENESS, RecoveryState.INTEGRATION],
        RecoveryState.RECONSTRUCTION: [RecoveryState.INTEGRATION, RecoveryState.HONESTY, RecoveryState.PURPOSE],
        RecoveryState.INTEGRATION: [RecoveryState.PURPOSE, RecoveryState.RECONSTRUCTION],
        RecoveryState.PURPOSE: [RecoveryState.INTEGRATION]  # Can regress from purpose
    }
    
    def __init__(self, state: Optional[UserState] = None, persistence_path: Optional[str] = None) -> None:
        self.state = state or UserState()
        self.persistence_path = Path(persistence_path) if persistence_path else None
        self.transition_history: List[StateTransition] = []
        self._initialize_state()
        
    def _initialize_state(self) -> None:
        """Initialize or validate state on creation."""
        if not self.state.last_state_change:
            self.state.last_state_change = datetime.now().isoformat()
        
        # Validate recovery state
        try:
            # Ensure state is valid enum value
            _ = RecoveryState(self.state.recovery_state.value)
        except ValueError:
            self.state.recovery_state = RecoveryState.CRISIS
        
        # Load from persistence if available
        if self.persistence_path and self.persistence_path.exists():
            self._load_from_persistence()
    
    def update_from_input(self, text: str, clarity_scores: Optional[Dict[str, float]] = None) -> None:
        """
        Update state based on user input and clarity scores.
        
        Args:
            text: User input text
            clarity_scores: Optional clarity scores from dimensions
        """
        self.state.interaction_count += 1
        
        # Update clarity scores if provided
        if clarity_scores:
            self.state.clarity_scores.update(clarity_scores)
        
        # Detect markers in input
        detected_state, confidence, reason = self._detect_state_markers(text)
        
        # Calculate if state should change
        should_change, new_state = self._evaluate_state_change(
            detected_state, confidence, reason, text
        )
        
        if should_change and new_state != self.state.recovery_state:
            self._perform_state_transition(new_state, reason, confidence, text)
        else:
            # Update state confidence and duration
            self._update_state_metrics()
    
    def _detect_state_markers(self, text: str) -> Tuple[Optional[RecoveryState], float, Optional[StateTransitionReason]]:
        """Detect state markers in text and return suggested state with confidence."""
        text_lower = text.lower()
        
        # Check for crisis markers first (highest priority)
        crisis_score = self._score_text_for_state(text_lower, RecoveryState.CRISIS)
        if crisis_score >= self.STATE_MARKERS[RecoveryState.CRISIS]["min_confidence"]:
            return RecoveryState.CRISIS, crisis_score, StateTransitionReason.CRISIS_MARKER
        
        # Check other states
        best_state = None
        best_score = 0.0
        best_reason = None
        
        for state, config in self.STATE_MARKERS.items():
            if state == RecoveryState.CRISIS:
                continue  # Already checked
            
            score = self._score_text_for_state(text_lower, state)
            if score > best_score and score >= config["min_confidence"]:
                best_score = score
                best_state = state
        
        # Determine reason
        if best_state:
            reason_map = {
                RecoveryState.AWARENESS: StateTransitionReason.AWARENESS_MARKER,
                RecoveryState.HONESTY: StateTransitionReason.HONESTY_MARKER,
                RecoveryState.RECONSTRUCTION: StateTransitionReason.RECONSTRUCTION_MARKER,
                RecoveryState.INTEGRATION: StateTransitionReason.INTEGRATION_MARKER,
                RecoveryState.PURPOSE: StateTransitionReason.PURPOSE_MARKER
            }
            reason = reason_map.get(best_state, StateTransitionReason.PROGRESSION)
            return best_state, best_score, reason
        
        return None, 0.0, None
    
    def _score_text_for_state(self, text_lower: str, state: RecoveryState) -> float:
        """Score text for likelihood of belonging to a state."""
        if state not in self.STATE_MARKERS:
            return 0.0
        
        patterns = self.STATE_MARKERS[state]["patterns"]
        total_score = 0.0
        match_count = 0
        
        for pattern, weight in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                total_score += weight * len(matches)
                match_count += 1
        
        # Normalize score
        if match_count > 0:
            score = total_score / match_count
            # Boost score for multiple distinct matches
            if match_count > 1:
                score *= min(1.0 + (match_count * 0.1), 1.3)
            return min(score, 1.0)
        
        return 0.0
    
    def _evaluate_state_change(
        self, 
        detected_state: Optional[RecoveryState],
        confidence: float,
        reason: Optional[StateTransitionReason],
        text: str
    ) -> Tuple[bool, Optional[RecoveryState]]:
        """Evaluate whether state should change and to what."""
        current_state = self.state.recovery_state
        
        # Safety: Always transition to crisis if detected with high confidence
        if detected_state == RecoveryState.CRISIS and confidence > 0.7:
            return True, RecoveryState.CRISIS
        
        # No detected state or low confidence
        if not detected_state or confidence < 0.5:
            # Consider time-based progression
            if self.state.state_duration_minutes > 10:  # Been in state for a while
                next_state = current_state.next_state()
                if next_state and self._is_transition_allowed(current_state, next_state):
                    return True, next_state
            return False, None
        
        # Check if transition is allowed
        if not self._is_transition_allowed(current_state, detected_state):
            return False, None
        
        # Determine if we should change based on confidence and current state confidence
        change_threshold = 0.6 - (self.state.state_confidence * 0.2)
        if confidence > change_threshold:
            # Ensure we're not regressing without good reason
            if self._is_regression(current_state, detected_state):
                # Only allow regression with high confidence
                if confidence > 0.75:
                    return True, detected_state
                else:
                    return False, None
            return True, detected_state
        
        return False, None
    
    def _is_transition_allowed(self, from_state: RecoveryState, to_state: RecoveryState) -> bool:
        """Check if transition is allowed."""
        if from_state == to_state:
            return True  # Staying in same state is always allowed
        
        allowed = self.ALLOWED_TRANSITIONS.get(from_state, [])
        return to_state in allowed
    
    def _is_regression(self, from_state: RecoveryState, to_state: RecoveryState) -> bool:
        """Check if transition is a regression."""
        progression_order = RecoveryState.progression_order()
        try:
            from_index = progression_order.index(from_state)
            to_index = progression_order.index(to_state)
            return to_index < from_index
        except ValueError:
            return False
    
    def _perform_state_transition(
        self, 
        new_state: RecoveryState, 
        reason: StateTransitionReason,
        confidence: float,
        input_text: Optional[str] = None
    ) -> None:
        """Perform state transition and record it."""
        old_state = self.state.recovery_state
        
        # Update state
        self.state.recovery_state = new_state
        self.state.state_confidence = confidence
        self.state.last_state_change = datetime.now().isoformat()
        self.state.state_duration_minutes = 0
        
        # Record transition
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            reason=reason,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            input_text=input_text,
            metadata={
                "interaction_count": self.state.interaction_count,
                "clarity_scores": self.state.clarity_scores.copy()
            }
        )
        self.transition_history.append(transition)
        
        # Limit history size
        if len(self.transition_history) > 100:
            self.transition_history = self.transition_history[-100:]
        
        # Update persistence
        self._save_to_persistence()
        
        logger = self._get_logger()
        logger.info(f"State transition: {old_state.value} -> {new_state.value} "
                   f"(reason: {reason.value}, confidence: {confidence:.2f})")
    
    def _update_state_metrics(self) -> None:
        """Update state duration and confidence metrics."""
        if self.state.last_state_change:
            try:
                last_change = datetime.fromisoformat(self.state.last_state_change)
                duration = (datetime.now() - last_change).total_seconds() / 60
                self.state.state_duration_minutes = int(duration)
            except (ValueError, TypeError):
                pass
        
        # Decay confidence slightly over time if no reinforcement
        self.state.state_confidence *= 0.995
    
    def _save_to_persistence(self) -> None:
        """Save state to persistence path."""
        if not self.persistence_path:
            return
        
        try:
            data = {
                "state": self.state.to_dict(),
                "transition_history": [
                    {
                        "from_state": t.from_state.value,
                        "to_state": t.to_state.value,
                        "reason": t.reason.value,
                        "confidence": t.confidence,
                        "timestamp": t.timestamp,
                        "input_text": t.input_text,
                        "metadata": t.metadata
                    }
                    for t in self.transition_history[-50:]  # Save last 50 transitions
                ]
            }
            
            with open(self.persistence_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger = self._get_logger()
            logger.error(f"Failed to save state to persistence: {e}")
    
    def _load_from_persistence(self) -> None:
        """Load state from persistence path."""
        if not self.persistence_path or not self.persistence_path.exists():
            return
        
        try:
            with open(self.persistence_path, 'r') as f:
                data = json.load(f)
            
            # Load state
            if "state" in data:
                self.state = UserState.from_dict(data["state"])
            
            # Load transition history
            if "transition_history" in data:
                self.transition_history = []
                for t_data in data["transition_history"]:
                    transition = StateTransition(
                        from_state=RecoveryState(t_data["from_state"]),
                        to_state=RecoveryState(t_data["to_state"]),
                        reason=StateTransitionReason(t_data["reason"]),
                        confidence=t_data["confidence"],
                        timestamp=t_data["timestamp"],
                        input_text=t_data.get("input_text"),
                        metadata=t_data.get("metadata", {})
                    )
                    self.transition_history.append(transition)
                    
            logger = self._get_logger()
            logger.info(f"Loaded state from persistence: {self.state.recovery_state.value}")
            
        except Exception as e:
            logger = self._get_logger()
            logger.error(f"Failed to load state from persistence: {e}")
    
    def to_token(self) -> Dict[str, Any]:
        """Convert current state to serializable token."""
        return self.state.to_dict()
    
    @classmethod
    def from_token(cls, token: Optional[Dict[str, Any]], **kwargs) -> RecoveryStateMachine:
        """Create RecoveryStateMachine from token."""
        if not token:
            return cls(**kwargs)
        
        state = UserState.from_dict(token)
        rsm = cls(state=state, **kwargs)
        return rsm
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get comprehensive state summary."""
        return {
            "current_state": self.state.recovery_state.value,
            "state_confidence": self.state.state_confidence,
            "state_duration_minutes": self.state.state_duration_minutes,
            "interaction_count": self.state.interaction_count,
            "clarity_scores": self.state.clarity_scores,
            "safety_flags": self.state.safety_flags,
            "transition_count": len(self.transition_history),
            "recent_transitions": [
                {
                    "from": t.from_state.value,
                    "to": t.to_state.value,
                    "reason": t.reason.value,
                    "time": t.timestamp
                }
                for t in self.transition_history[-5:]
            ] if self.transition_history else []
        }
    
    def add_safety_flag(self, flag: str) -> None:
        """Add a safety flag to state."""
        if flag not in self.state.safety_flags:
            self.state.safety_flags.append(flag)
    
    def clear_safety_flags(self) -> None:
        """Clear all safety flags."""
        self.state.safety_flags.clear()
    
    def _get_logger(self):
        """Get logger instance."""
        import logging
        return logging.getLogger(__name__)