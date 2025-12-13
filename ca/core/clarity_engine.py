from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Tuple

from .dimensions import EmotionalClarity, LogicalClarity, ShadowClarity, DimensionOutput
from .enums import Emotion, Intent, RecoveryState
from .states import RecoveryStateMachine


@dataclass
class ClarityResponse:
    message: str
    intent: str
    emotion: str
    confidence: float
    avatar: Dict[str, Any]
    user_state_token: Dict[str, Any]
    recovery_state: str
    clarity_scores: Dict[str, float]


class ClarityEngine:
    """
    Core orchestrator for the 3D Clarity model.
    Enhanced with state-aware response fusion and improved avatar directives.
    """

    def __init__(self) -> None:
        self.logical = LogicalClarity()
        self.emotional = EmotionalClarity()
        self.shadow = ShadowClarity()
        
        # Weighting for dimension confidence (emotional gets higher weight in human interactions)
        self.dimension_weights = {
            'emotional': 0.45,
            'logical': 0.35,
            'shadow': 0.20
        }
        
        # State-specific response modifiers
        self.state_modifiers = {
            RecoveryState.CRISIS: {
                'urgency': 0.9,
                'directness': 0.8,
                'validation': 1.0
            },
            RecoveryState.AWARENESS: {
                'curiosity': 0.9,
                'openness': 0.8,
                'reflection': 0.7
            },
            RecoveryState.HONESTY: {
                'authenticity': 0.9,
                'vulnerability': 0.7,
                'acceptance': 0.8
            },
            RecoveryState.RECONSTRUCTION: {
                'creativity': 0.8,
                'pragmatism': 0.9,
                'hope': 0.7
            },
            RecoveryState.INTEGRATION: {
                'integration': 0.9,
                'wisdom': 0.8,
                'balance': 0.9
            },
            RecoveryState.PURPOSE: {
                'clarity': 1.0,
                'direction': 0.9,
                'empowerment': 0.8
            }
        }

    def process(
        self,
        text: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        user_state_token: Optional[Dict[str, Any]] = None,
    ) -> ClarityResponse:
        # Initialize or restore recovery state machine
        rsm = RecoveryStateMachine.from_token(user_state_token)
        previous_state = rsm.state.recovery_state
        
        # Update state based on input
        rsm.update_from_input(text)
        current_state = rsm.state.recovery_state
        state_changed = previous_state != current_state
        
        # Analyze through all three dimensions
        logical_out = self.logical.analyze(text, current_state)
        emotional_out = self.emotional.analyze(text, current_state)
        shadow_out = self.shadow.analyze(text, current_state)
        
        # Fuse the dimension outputs
        fused = self._fuse(logical_out, emotional_out, shadow_out, current_state)
        
        # Apply state-aware adjustments
        adjusted_message = self._adjust_for_state(
            fused.message, 
            current_state, 
            state_changed,
            [logical_out, emotional_out, shadow_out]
        )
        
        # Build avatar directives with state awareness
        avatar = self._build_avatar_directives(
            fused, 
            current_state,
            [logical_out, emotional_out, shadow_out]
        )
        
        # Calculate clarity scores for feedback
        clarity_scores = {
            'logical': logical_out.confidence,
            'emotional': emotional_out.confidence,
            'shadow': shadow_out.confidence,
            'overall': fused.confidence
        }
        
        return ClarityResponse(
            message=adjusted_message,
            intent=fused.intent.value,
            emotion=fused.emotion.value,
            confidence=fused.confidence,
            avatar=avatar,
            user_state_token=rsm.to_token(),
            recovery_state=current_state.value,
            clarity_scores=clarity_scores
        )

    def _fuse(
        self,
        logical_out: DimensionOutput,
        emotional_out: DimensionOutput,
        shadow_out: DimensionOutput,
        state: RecoveryState,
    ) -> DimensionOutput:
        # Weighted confidence calculation
        weighted_confidence = (
            self.dimension_weights['logical'] * logical_out.confidence +
            self.dimension_weights['emotional'] * emotional_out.confidence +
            self.dimension_weights['shadow'] * shadow_out.confidence
        )
        
        # Enhanced message composition
        base_msg = emotional_out.message
        
        # Add logical insights when confidence is high
        if logical_out.confidence > 0.7:
            logical_insight = f" Logically, {logical_out.message.lower()}"
            base_msg += logical_insight
        
        # Add shadow insights when appropriate and confident
        if shadow_out.confidence > 0.6 and shadow_out.intent != Intent.NEUTRAL:
            shadow_insight = f" There may be deeper patterns here worth exploring."
            base_msg += shadow_insight
        
        # State-specific closing
        state_closings = {
            RecoveryState.CRISIS: " Let's focus on stabilizing first.",
            RecoveryState.AWARENESS: " What do you notice about this?",
            RecoveryState.HONESTY: " How does acknowledging this feel?",
            RecoveryState.RECONSTRUCTION: " What's one small step forward?",
            RecoveryState.INTEGRATION: " How can this fit into your broader understanding?",
            RecoveryState.PURPOSE: " How might this align with your sense of purpose?"
        }
        
        if state in state_closings:
            base_msg += state_closings[state]
        else:
            base_msg += " Let's explore this with care."
        
        # Intent selection with state awareness
        intent_priority = {
            Intent.BOUNDARY: 5,  # Highest priority for safety
            Intent.CRISIS: 4,    # High priority for crisis
            Intent.ACTION: 3,    # Action-oriented
            Intent.ANALYSIS: 2,  # Analytical
            Intent.GROUNDING: 1, # Grounding
            Intent.NEUTRAL: 0    # Neutral
        }
        
        # Choose intent based on priority and state
        candidates = [logical_out.intent, emotional_out.intent, shadow_out.intent]
        chosen_intent = max(candidates, key=lambda i: intent_priority.get(i, 0))
        
        # If in crisis, prefer grounding or boundary intents
        if state == RecoveryState.CRISIS and chosen_intent not in [Intent.GROUNDING, Intent.BOUNDARY, Intent.CRISIS]:
            chosen_intent = Intent.GROUNDING
        
        # Emotion selection with nuance
        emotion_candidates = [logical_out.emotion, emotional_out.emotion, shadow_out.emotion]
        
        # Default emotion order with state awareness
        if state == RecoveryState.CRISIS:
            emotion_order = [Emotion.CALM, Emotion.FOCUSED, Emotion.CAUTIOUS, Emotion.NEUTRAL]
        elif state == RecoveryState.PURPOSE:
            emotion_order = [Emotion.CONFIDENT, Emotion.CURIOUS, Emotion.REFLECTIVE, Emotion.NEUTRAL]
        else:
            emotion_order = [Emotion.REFLECTIVE, Emotion.CURIOUS, Emotion.FOCUSED, Emotion.NEUTRAL]
        
        chosen_emotion = next(
            (e for e in emotion_order if e in emotion_candidates),
            emotional_out.emotion  # Fallback to emotional dimension's emotion
        )
        
        # Metadata for debugging and transparency
        meta: Dict[str, Any] = {
            "logical": asdict(logical_out),
            "emotional": asdict(emotional_out),
            "shadow": asdict(shadow_out),
            "state_aware": {
                "current_state": state.value,
                "intent_priority": intent_priority[chosen_intent],
                "weighted_confidence": weighted_confidence
            }
        }
        
        return DimensionOutput(
            message=base_msg.strip(),
            intent=chosen_intent,
            emotion=chosen_emotion,
            confidence=weighted_confidence,
            meta=meta,
        )

    def _adjust_for_state(
        self,
        message: str,
        state: RecoveryState,
        state_changed: bool,
        dimension_outputs: list[DimensionOutput]
    ) -> str:
        """Apply state-specific adjustments to the message."""
        
        if state_changed:
            state_transitions = {
                RecoveryState.CRISIS: "I notice this feels overwhelming. ",
                RecoveryState.AWARENESS: "I sense you're becoming more aware of something. ",
                RecoveryState.HONESTY: "There's courage in this honesty. ",
                RecoveryState.RECONSTRUCTION: "This seems like a rebuilding moment. ",
                RecoveryState.INTEGRATION: "I see integration happening. ",
                RecoveryState.PURPOSE: "This feels purposeful. "
            }
            if state in state_transitions:
                message = state_transitions[state] + message
        
        # Check for high emotional intensity
        emotional_out = dimension_outputs[1]  # Emotional dimension is second
        if emotional_out.emotion in [Emotion.INTENSE, Emotion.URGENT] and state != RecoveryState.CRISIS:
            message = "I sense strong feelings here. " + message
        
        # Check for logical clarity
        logical_out = dimension_outputs[0]  # Logical dimension is first
        if logical_out.confidence > 0.8:
            message = message.replace("may be", "appears to be").replace("might be", "seems to be")
        
        return message

    def _build_avatar_directives(
        self,
        fused: DimensionOutput,
        state: RecoveryState,
        dimension_outputs: list[DimensionOutput]
    ) -> Dict[str, Any]:
        """Create avatar directives based on fused output and current state."""
        
        # Base directives
        movement = "IDLE"
        target = "CENTER"
        animation = "THINKING"
        light_intensity = 0.35
        light_color = "WHITE"
        
        # State-based adjustments
        state_based = {
            RecoveryState.CRISIS: {
                "movement": "SLOW",
                "animation": "CALMING",
                "light_intensity": 0.2,
                "light_color": "BLUE"
            },
            RecoveryState.AWARENESS: {
                "movement": "GENTLE",
                "animation": "OBSERVING",
                "light_intensity": 0.4,
                "light_color": "SOFT_WHITE"
            },
            RecoveryState.HONESTY: {
                "movement": "STILL",
                "animation": "LISTENING",
                "light_intensity": 0.3,
                "light_color": "WARM_WHITE"
            },
            RecoveryState.RECONSTRUCTION: {
                "movement": "FLUID",
                "animation": "BUILDING",
                "light_intensity": 0.5,
                "light_color": "GOLDEN"
            },
            RecoveryState.INTEGRATION: {
                "movement": "HARMONIC",
                "animation": "CONNECTING",
                "light_intensity": 0.6,
                "light_color": "VIOLET"
            },
            RecoveryState.PURPOSE: {
                "movement": "PURPOSEFUL",
                "animation": "GUIDING",
                "light_intensity": 0.7,
                "light_color": "SUNLIGHT"
            }
        }
        
        # Apply state-based adjustments
        if state in state_based:
            state_settings = state_based[state]
            movement = state_settings["movement"]
            animation = state_settings["animation"]
            light_intensity = state_settings["light_intensity"]
            light_color = state_settings["light_color"]
        
        # Intent-based overrides (higher priority than state)
        if fused.intent == Intent.BOUNDARY:
            animation = "PROTECTIVE"
            movement = "STEADY"
            light_intensity = 0.8
            light_color = "AMBER"
        elif fused.intent == Intent.CRISIS:
            animation = "STABILIZING"
            movement = "CALM"
            light_intensity = 0.3
            light_color = "DEEP_BLUE"
        elif fused.intent == Intent.ACTION:
            animation = "MOTIVATING"
            movement = "ENERGETIC"
            light_intensity = 0.6
        elif fused.intent == Intent.ANALYSIS:
            animation = "EXPLAINING"
            movement = "MEASURED"
            light_intensity = 0.5
        elif fused.intent == Intent.GROUNDING:
            animation = "GROUNDING"
            movement = "STILL"
            light_intensity = 0.4
            light_color = "EARTH"
        
        # Emotion-based adjustments
        if fused.emotion == Emotion.INTENSE:
            light_intensity = min(light_intensity + 0.2, 1.0)
            animation = "ATTENTIVE"
        elif fused.emotion == Emotion.CALM:
            movement = "SLOW"
            light_intensity = max(light_intensity - 0.1, 0.2)
        elif fused.emotion == Emotion.CURIOUS:
            animation = "INQUIRING"
            movement = "FLUID"
        
        # Shadow awareness (if shadow dimension has high confidence)
        shadow_out = dimension_outputs[2]
        if shadow_out.confidence > 0.7:
            light_intensity = light_intensity * 0.8  # Dim slightly for shadow work
            animation = "REFLECTING"
        
        return {
            "movement": movement,
            "target": target,
            "animation": animation,
            "light_intensity": round(light_intensity, 2),
            "light_color": light_color,
            "state": state.value,
            "intent": fused.intent.value,
            "emotion": fused.emotion.value
        }