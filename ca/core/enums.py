from __future__ import annotations

from enum import Enum
from typing import List, Optional, Set


class Intent(str, Enum):
    """
    Primary intents for BLUX-cA responses.
    Ordered by priority (higher number = higher priority).
    """
    # Core clarity intents
    REFLECTION = "REFLECTION"       # Invite self-examination
    ANALYSIS = "ANALYSIS"           # Logical breakdown
    CLARIFICATION = "CLARIFICATION" # Seek more information
    
    # Action-oriented intents
    PLAN = "PLAN"                   # Propose action steps
    ACTION = "ACTION"               # Encourage specific action
    DECISION = "DECISION"           # Support decision-making
    
    # Safety and grounding intents
    GROUNDING = "GROUNDING"         # Emotional stabilization
    BOUNDARY = "BOUNDARY"           # Set or recognize boundaries
    CRISIS = "CRISIS"               # Handle urgent situations
    
    # Integration intents
    INTEGRATION = "INTEGRATION"     # Connect insights
    SYNTHESIS = "SYNTHESIS"         # Combine perspectives
    VALIDATION = "VALIDATION"       # Confirm understanding
    
    # Default/fallback
    NEUTRAL = "NEUTRAL"             # No specific intent
    UNKNOWN = "UNKNOWN"             # Cannot determine
    
    @classmethod
    def safety_priority_order(cls) -> List[Intent]:
        """Return intents in order of safety priority (highest first)."""
        return [
            cls.CRISIS,      # Highest priority - safety first
            cls.BOUNDARY,    # Boundary maintenance
            cls.GROUNDING,   # Emotional stabilization
            cls.VALIDATION,  # Validation before action
            cls.REFLECTION,  # Reflection before analysis
            cls.ANALYSIS,    # Analysis
            cls.PLAN,        # Planning
            cls.ACTION,      # Action
            cls.INTEGRATION, # Integration
            cls.SYNTHESIS,   # Synthesis
            cls.CLARIFICATION, # Clarification
            cls.DECISION,    # Decision support
            cls.NEUTRAL,     # Neutral
            cls.UNKNOWN      # Unknown
        ]
    
    @classmethod
    def from_string(cls, value: str) -> Intent:
        """Safely convert string to Intent enum."""
        try:
            return cls(value.upper())
        except (ValueError, KeyError):
            # Try fuzzy matching
            value_lower = value.lower()
            if 'crisis' in value_lower or 'urgent' in value_lower:
                return cls.CRISIS
            elif 'boundary' in value_lower:
                return cls.BOUNDARY
            elif 'ground' in value_lower or 'calm' in value_lower:
                return cls.GROUNDING
            elif 'reflect' in value_lower:
                return cls.REFLECTION
            elif 'analy' in value_lower or 'logic' in value_lower:
                return cls.ANALYSIS
            elif 'plan' in value_lower or 'action' in value_lower:
                return cls.ACTION
            elif 'valid' in value_lower:
                return cls.VALIDATION
            else:
                return cls.UNKNOWN
    
    def is_safety_intent(self) -> bool:
        """Check if this is a safety-related intent."""
        return self in {
            Intent.CRISIS,
            Intent.BOUNDARY,
            Intent.GROUNDING
        }
    
    def requires_caution(self) -> bool:
        """Check if this intent requires careful handling."""
        return self in {
            Intent.CRISIS,
            Intent.BOUNDARY,
            Intent.ACTION,
            Intent.DECISION
        }


class Emotion(str, Enum):
    """
    Emotional states for BLUX-cA responses.
    Represents the emotional tone the agent should embody.
    """
    # Calm/grounded spectrum
    NEUTRAL = "NEUTRAL"             # Balanced, objective
    CALM = "CALM"                   # Peaceful, stable
    STEADY = "STEADY"               # Consistent, reliable
    PEACEFUL = "PEACEFUL"           # Tranquil, settled
    
    # Focused/engaged spectrum
    FOCUSED = "FOCUSED"             # Attentive, concentrated
    PRESENT = "PRESENT"             # Here and now
    ATTENTIVE = "ATTENTIVE"         # Paying close attention
    ENGAGED = "ENGAGED"             # Actively involved
    
    # Reflective/curious spectrum
    REFLECTIVE = "REFLECTIVE"       # Thoughtful, contemplative
    CURIOUS = "CURIOUS"             # Inquisitive, wondering
    CONTEMPLATIVE = "CONTEMPLATIVE" # Deeply thoughtful
    WONDERING = "WONDERING"         # Open to discovery
    
    # Cautious/careful spectrum
    CAUTIOUS = "CAUTIOUS"           # Careful, measured
    MEASURED = "MEASURED"           # Deliberate, paced
    GENTLE = "GENTLE"               # Soft, tender
    RESPECTFUL = "RESPECTFUL"       # Honoring boundaries
    
    # Positive/encouraging spectrum
    HOPEFUL = "HOPEFUL"             # Optimistic, forward-looking
    ENCOURAGING = "ENCOURAGING"     # Supportive, uplifting
    CONFIDENT = "CONFIDENT"         # Assured, certain
    EMPOWERING = "EMPOWERING"       # Strength-giving
    
    # Intense/urgent spectrum
    INTENSE = "INTENSE"             # Strong, powerful
    URGENT = "URGENT"               # Time-sensitive
    FIRM = "FIRM"                   # Clear, unwavering
    DIRECT = "DIRECT"               # Straightforward
    
    @classmethod
    def from_arousal_valence(cls, arousal: float, valence: float) -> Emotion:
        """
        Convert arousal-valence coordinates to emotion.
        
        Args:
            arousal: 0.0 (calm) to 1.0 (aroused)
            valence: 0.0 (negative) to 1.0 (positive)
            
        Returns:
            Appropriate Emotion enum
        """
        if arousal < 0.3:
            if valence < 0.4:
                return cls.CALM
            elif valence < 0.7:
                return cls.REFLECTIVE
            else:
                return cls.PEACEFUL
        elif arousal < 0.6:
            if valence < 0.4:
                return cls.CAUTIOUS
            elif valence < 0.7:
                return cls.FOCUSED
            else:
                return cls.ENGAGED
        else:
            if valence < 0.4:
                return cls.INTENSE
            elif valence < 0.7:
                return cls.ATTENTIVE
            else:
                return cls.CONFIDENT
    
    @classmethod
    def for_recovery_state(cls, state: 'RecoveryState') -> Emotion:
        """Get appropriate emotion for recovery state."""
        mapping = {
            RecoveryState.CRISIS: cls.CALM,
            RecoveryState.AWARENESS: cls.CURIOUS,
            RecoveryState.HONESTY: cls.REFLECTIVE,
            RecoveryState.RECONSTRUCTION: cls.HOPEFUL,
            RecoveryState.INTEGRATION: cls.PEACEFUL,
            RecoveryState.PURPOSE: cls.CONFIDENT
        }
        return mapping.get(state, cls.NEUTRAL)
    
    def is_grounding(self) -> bool:
        """Check if this emotion is grounding/stabilizing."""
        return self in {
            Emotion.CALM,
            Emotion.STEADY,
            Emotion.PEACEFUL,
            Emotion.NEUTRAL
        }
    
    def is_intense(self) -> bool:
        """Check if this emotion is intense/arousing."""
        return self in {
            Emotion.INTENSE,
            Emotion.URGENT,
            Emotion.FIRM,
            Emotion.DIRECT
        }


class RecoveryState(str, Enum):
    """
    Recovery state machine stages for BLUX-cA.
    Represents the user's current phase in their clarity journey.
    """
    CRISIS = "CRISIS"               # Immediate distress, stabilization needed
    AWARENESS = "AWARENESS"         # Noticing patterns, becoming conscious
    HONESTY = "HONESTY"             # Facing truths, admitting realities
    RECONSTRUCTION = "RECONSTRUCTION" # Rebuilding with new understanding
    INTEGRATION = "INTEGRATION"     # Incorporating insights into life
    PURPOSE = "PURPOSE"             # Living from clarified purpose
    
    @classmethod
    def progression_order(cls) -> List[RecoveryState]:
        """Return states in their natural progression order."""
        return [
            cls.CRISIS,
            cls.AWARENESS,
            cls.HONESTY,
            cls.RECONSTRUCTION,
            cls.INTEGRATION,
            cls.PURPOSE
        ]
    
    @classmethod
    def from_string(cls, value: str) -> RecoveryState:
        """Safely convert string to RecoveryState enum."""
        try:
            return cls(value.upper())
        except (ValueError, KeyError):
            # Try fuzzy matching
            value_lower = value.lower()
            if 'crisis' in value_lower or 'urgent' in value_lower or 'emergency' in value_lower:
                return cls.CRISIS
            elif 'aware' in value_lower or 'notice' in value_lower:
                return cls.AWARENESS
            elif 'honest' in value_lower or 'truth' in value_lower or 'admit' in value_lower:
                return cls.HONESTY
            elif 'reconstruct' in value_lower or 'rebuild' in value_lower or 'build' in value_lower:
                return cls.RECONSTRUCTION
            elif 'integrat' in value_lower or 'incorporate' in value_lower:
                return cls.INTEGRATION
            elif 'purpose' in value_lower or 'meaning' in value_lower:
                return cls.PURPOSE
            else:
                # Default to awareness as starting point
                return cls.AWARENESS
    
    def next_state(self) -> Optional[RecoveryState]:
        """Get the next state in natural progression, if any."""
        order = self.progression_order()
        try:
            index = order.index(self)
            if index + 1 < len(order):
                return order[index + 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def previous_state(self) -> Optional[RecoveryState]:
        """Get the previous state in natural progression, if any."""
        order = self.progression_order()
        try:
            index = order.index(self)
            if index - 1 >= 0:
                return order[index - 1]
        except (ValueError, IndexError):
            pass
        return None
    
    def is_terminal(self) -> bool:
        """Check if this state is a natural endpoint."""
        return self == RecoveryState.PURPOSE
    
    def can_transition_to(self, target_state: RecoveryState) -> bool:
        """
        Check if transition from current to target state is valid.
        Allows for both progression and regression (healing isn't linear).
        """
        # All states can transition to crisis (emergencies happen)
        if target_state == RecoveryState.CRISIS:
            return True
        
        # Otherwise, allow any transition but note typical patterns
        return True
    
    def description(self) -> str:
        """Get human-readable description of this state."""
        descriptions = {
            RecoveryState.CRISIS: "Immediate distress requiring stabilization and safety",
            RecoveryState.AWARENESS: "Noticing patterns and becoming conscious of realities",
            RecoveryState.HONESTY: "Facing difficult truths with courage and self-compassion",
            RecoveryState.RECONSTRUCTION: "Rebuilding understanding and approaches based on new insights",
            RecoveryState.INTEGRATION: "Incorporating clarified insights into daily life and identity",
            RecoveryState.PURPOSE: "Living from a place of clarified meaning and direction"
        }
        return descriptions.get(self, "Unknown state")


# Convenience type alias for backward compatibility
RecoveryStage = RecoveryState