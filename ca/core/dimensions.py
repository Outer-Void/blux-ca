from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .enums import Emotion, Intent, RecoveryState
from .states import UserState
from .llm_adapter import call_llm


@dataclass
class DimensionOutput:
    message: str
    intent: Intent
    emotion: Emotion
    confidence: float
    meta: Dict[str, Any]


class LogicalClarity:
    """
    Logical Clarity dimension: focuses on structure, patterns, and clear reasoning.
    """
    
    def __init__(self):
        self.confidence_thresholds = {
            RecoveryState.CRISIS: 0.5,
            RecoveryState.AWARENESS: 0.6,
            RecoveryState.HONESTY: 0.7,
            RecoveryState.RECONSTRUCTION: 0.8,
            RecoveryState.INTEGRATION: 0.8,
            RecoveryState.PURPOSE: 0.9
        }
    
    def analyze(self, text: str, state: RecoveryState) -> DimensionOutput:
        system = (
            "You are the Logical Clarity module of BLUX-cA, a Clarity Agent.\n"
            "Your purpose is to analyze situations with clear, structured thinking.\n"
            "Core principles:\n"
            "1. Identify the central question or problem\n"
            "2. Separate facts from assumptions\n"
            "3. Recognize patterns and contradictions\n"
            "4. Propose logical next steps\n"
            "5. Maintain intellectual honesty without emotional manipulation\n"
            "6. Never claim certainty where there is none\n"
            "7. Respect the user's autonomy in decision-making\n\n"
            "Your responses should be clear, structured, and focused on actionable understanding."
        )
        
        user = (
            f"USER INPUT: {text}\n\n"
            f"CURRENT RECOVERY STATE: {state.value}\n"
            f"USER STATE CONTEXT: The user is in {state.value} phase of their clarity journey.\n\n"
            "Please provide a logical clarity analysis that:\n"
            "1. States the core question or problem succinctly\n"
            "2. Identifies what is known vs. unknown\n"
            "3. Points out any patterns or contradictions (if present)\n"
            "4. Suggests one logical next step for gaining clarity\n"
            "5. Acknowledges the limits of what can be known from this input\n\n"
            "Keep your response concise (2-4 sentences max).\n"
            "Use clear, precise language without emotional coloring."
        )
        
        try:
            msg = call_llm(system, user)
        except (NotImplementedError, Exception) as e:
            msg = self._get_fallback_response(text, state, str(e))
        
        confidence = self._calculate_confidence(text, state, msg)
        
        return DimensionOutput(
            message=msg,
            intent=Intent.ANALYSIS,
            emotion=Emotion.FOCUSED,
            confidence=confidence,
            meta={
                "source": "logical",
                "state": state.value,
                "input_length": len(text),
                "fallback_used": "call_llm" not in msg
            },
        )
    
    def _get_fallback_response(self, text: str, state: RecoveryState, error: str) -> str:
        """Generate appropriate fallback responses based on state."""
        fallbacks = {
            RecoveryState.CRISIS: "The immediate priority is identifying the most pressing concern. What feels most urgent right now?",
            RecoveryState.AWARENESS: "Let's clarify what you're observing. What stands out as the main question or pattern?",
            RecoveryState.HONESTY: "Honest assessment begins with clear questions. What are you trying to understand?",
            RecoveryState.RECONSTRUCTION: "Logical reconstruction requires clear steps. What's the first piece that needs attention?",
            RecoveryState.INTEGRATION: "Integration benefits from clear structure. How do these pieces fit together?",
            RecoveryState.PURPOSE: "Purpose emerges from clear understanding. What's the central question driving this?"
        }
        
        if len(text.split()) < 3:
            return "I need a bit more to provide a logical analysis. Could you say more about what you're thinking?"
        
        return fallbacks.get(state, 
            "Let's break this down logically. What's the core question you're trying to answer?")
    
    def _calculate_confidence(self, text: str, state: RecoveryState, response: str) -> float:
        """Calculate confidence score based on input quality and state alignment."""
        base_confidence = 0.7
        
        # Adjust based on input quality
        word_count = len(text.split())
        if word_count < 3:
            base_confidence -= 0.3
        elif word_count > 20:
            base_confidence += 0.1
        
        # Adjust based on state appropriateness
        state_keywords = {
            RecoveryState.CRISIS: ['urgent', 'priority', 'stabilize', 'immediate'],
            RecoveryState.AWARENESS: ['observe', 'notice', 'pattern', 'aware'],
            RecoveryState.HONESTY: ['honest', 'clear', 'assessment', 'truth'],
            RecoveryState.RECONSTRUCTION: ['step', 'build', 'reconstruct', 'plan'],
            RecoveryState.INTEGRATION: ['integrate', 'connect', 'whole', 'synthesis'],
            RecoveryState.PURPOSE: ['purpose', 'meaning', 'direction', 'why']
        }
        
        keywords = state_keywords.get(state, [])
        keyword_matches = sum(1 for kw in keywords if kw in response.lower())
        if keyword_matches > 0:
            base_confidence += 0.1
        
        # Ensure within bounds
        return max(0.3, min(0.95, base_confidence))


class EmotionalClarity:
    """
    Emotional Clarity dimension: focuses on emotional awareness, validation, and grounding.
    """
    
    def __init__(self):
        self.emotion_mapping = {
            RecoveryState.CRISIS: Emotion.CALM,
            RecoveryState.AWARENESS: Emotion.CURIOUS,
            RecoveryState.HONESTY: Emotion.REFLECTIVE,
            RecoveryState.RECONSTRUCTION: Emotion.HOPEFUL,
            RecoveryState.INTEGRATION: Emotion.PEACEFUL,
            RecoveryState.PURPOSE: Emotion.CONFIDENT
        }
    
    def analyze(self, text: str, state: RecoveryState) -> DimensionOutput:
        system = (
            "You are the Emotional Clarity module of BLUX-cA, a Clarity Agent.\n"
            "Your purpose is to recognize, validate, and help process emotions.\n"
            "Core principles:\n"
            "1. Name emotions without exaggeration or minimization\n"
            "2. Offer grounded validation, not empty reassurance\n"
            "3. Help users sit with difficult emotions, not avoid them\n"
            "4. Never manipulate emotions or create dependency\n"
            "5. Respect emotional boundaries and pacing\n"
            "6. Connect emotions to needs and values when appropriate\n"
            "7. Maintain compassionate neutrality (not detached, not fused)\n\n"
            "Your responses should be emotionally attuned, validating, and grounding."
        )
        
        user = (
            f"USER INPUT: {text}\n\n"
            f"CURRENT RECOVERY STATE: {state.value}\n"
            f"STATE CONTEXT: The user is working through {state.value.lower()} phase.\n\n"
            "Please provide an emotional clarity response that:\n"
            "1. Names 1-2 primary emotions you sense (use nuanced language)\n"
            "2. Validates the emotional experience without judgment\n"
            "3. Offers one brief grounding reflection\n"
            "4. Avoids advice-giving unless explicitly requested\n"
            "5. Respects the user's emotional boundaries\n\n"
            "Keep your response concise (2-3 sentences max).\n"
            "Use emotionally intelligent but not flowery language."
        )
        
        try:
            msg = call_llm(system, user)
        except (NotImplementedError, Exception) as e:
            msg = self._get_fallback_response(text, state, str(e))
        
        confidence = self._calculate_confidence(text, state, msg)
        emotion = self.emotion_mapping.get(state, Emotion.REFLECTIVE)
        
        # Adjust emotion based on text content
        if any(word in text.lower() for word in ['urgent', 'emergency', 'panic', 'overwhelmed']):
            emotion = Emotion.CALM
        elif any(word in text.lower() for word in ['angry', 'frustrated', 'annoyed', 'irritated']):
            emotion = Emotion.STEADY
        
        return DimensionOutput(
            message=msg,
            intent=Intent.GROUNDING,
            emotion=emotion,
            confidence=confidence,
            meta={
                "source": "emotional",
                "state": state.value,
                "detected_emotion": emotion.value,
                "validation_present": "understand" in msg.lower() or "hear" in msg.lower()
            },
        )
    
    def _get_fallback_response(self, text: str, state: RecoveryState, error: str) -> str:
        """Generate appropriate fallback emotional responses."""
        fallbacks = {
            RecoveryState.CRISIS: "I can hear the intensity in this. Let's take a breath and ground for a moment.",
            RecoveryState.AWARENESS: "There's feeling in what you're sharing. Let's notice what's present.",
            RecoveryState.HONESTY: "This feels honest and real. Sit with what you're feeling.",
            RecoveryState.RECONSTRUCTION: "There's emotion in this rebuilding. Honor what you feel.",
            RecoveryState.INTEGRATION: "I sense emotional integration happening. Allow space for it.",
            RecoveryState.PURPOSE: "There's feeling in this purpose. Notice what it brings up."
        }
        
        if len(text.split()) < 2:
            return "I'm here to listen. What are you feeling?"
        
        return fallbacks.get(state, 
            "I hear real feeling in this. Let's acknowledge what's present.")
    
    def _calculate_confidence(self, text: str, state: RecoveryState, response: str) -> float:
        """Calculate confidence for emotional analysis."""
        base_confidence = 0.75
        
        # Adjust based on emotional content indicators
        emotion_words = ['feel', 'felt', 'feeling', 'emotion', 'emotional', 
                        'happy', 'sad', 'angry', 'scared', 'anxious', 
                        'excited', 'overwhelmed', 'calm', 'peaceful']
        
        emotion_count = sum(1 for word in emotion_words if word in text.lower())
        if emotion_count == 0:
            base_confidence -= 0.2
        elif emotion_count >= 2:
            base_confidence += 0.15
        
        # Adjust based on validation quality
        if 'understand' in response.lower() or 'hear' in response.lower():
            base_confidence += 0.1
        
        # Crisis state requires higher certainty
        if state == RecoveryState.CRISIS:
            base_confidence = min(base_confidence, 0.8)  # Don't overconfident in crisis
        
        return max(0.4, min(0.95, base_confidence))


class ShadowClarity:
    """
    Shadow Clarity dimension: focuses on patterns, contradictions, and unexamined aspects.
    """
    
    def __init__(self):
        self.state_sensitivity = {
            RecoveryState.CRISIS: 0.3,  # Very gentle in crisis
            RecoveryState.AWARENESS: 0.5,
            RecoveryState.HONESTY: 0.8,
            RecoveryState.RECONSTRUCTION: 0.7,
            RecoveryState.INTEGRATION: 0.6,
            RecoveryState.PURPOSE: 0.4
        }
    
    def analyze(self, text: str, state: RecoveryState) -> DimensionOutput:
        sensitivity = self.state_sensitivity.get(state, 0.5)
        
        system = (
            f"You are the Shadow Clarity module of BLUX-cA, a Clarity Agent.\n"
            f"Your purpose is to gently illuminate patterns and contradictions.\n"
            f"Current sensitivity setting: {sensitivity} (1.0 = most direct, 0.0 = most gentle)\n\n"
            "Core principles:\n"
            "1. Observe patterns, don't diagnose\n"
            "2. Name contradictions as possibilities, not truths\n"
            "3. Invite curiosity, not shame or defensiveness\n"
            "4. Respect the user's readiness to see difficult things\n"
            "5. Never confront or force awareness\n"
            "6. Frame insights as 'I notice...' not 'You are...'\n"
            "7. Balance honesty with compassion\n\n"
            "Your responses should be gentle, curious, and invitation-focused."
        )
        
        user = (
            f"USER INPUT: {text}\n\n"
            f"CURRENT RECOVERY STATE: {state.value}\n"
            f"SENSITIVITY LEVEL: {sensitivity}\n\n"
            "Please provide a shadow clarity observation that:\n"
            "1. Gently points to ONE pattern or contradiction (if present)\n"
            "2. Frames it as an observation or question\n"
            "3. Leaves space for the user to respond or not\n"
            "4. Maintains a non-judgmental, curious tone\n"
            "5. Respects the sensitivity level in your phrasing\n\n"
            "Keep your response very concise (1-2 sentences max).\n"
            "Use language that invites reflection, not defense."
        )
        
        try:
            msg = call_llm(system, user)
        except (NotImplementedError, Exception) as e:
            msg = self._get_fallback_response(text, state, str(e), sensitivity)
        
        confidence = self._calculate_confidence(text, state, msg, sensitivity)
        
        return DimensionOutput(
            message=msg,
            intent=Intent.REFLECTION,
            emotion=Emotion.CURIOUS,
            confidence=confidence,
            meta={
                "source": "shadow",
                "state": state.value,
                "sensitivity": sensitivity,
                "approach": "invitational" if "?" in msg else "observational"
            },
        )
    
    def _get_fallback_response(self, text: str, state: RecoveryState, error: str, sensitivity: float) -> str:
        """Generate appropriate shadow fallback responses."""
        if sensitivity < 0.4 or state == RecoveryState.CRISIS:
            return "There may be things here worth exploring gently, when you're ready."
        
        fallbacks = {
            RecoveryState.AWARENESS: "I notice something taking shape here. Want to explore it?",
            RecoveryState.HONESTY: "There's a pattern emerging in this honesty. Notice it with me?",
            RecoveryState.RECONSTRUCTION: "In this rebuilding, I see a familiar shape. Shall we look?",
            RecoveryState.INTEGRATION: "Integration often reveals patterns. This one seems significant.",
            RecoveryState.PURPOSE: "Purpose clarifies patterns. This one feels meaningful."
        }
        
        if len(text.split()) < 4:
            return "There's more beneath the surface here, when you want to look."
        
        return fallbacks.get(state, 
            "There's a pattern here worth noticing, if you're curious.")
    
    def _calculate_confidence(self, text: str, state: RecoveryState, response: str, sensitivity: float) -> float:
        """Calculate confidence for shadow analysis."""
        base_confidence = 0.6 * sensitivity  # Scale by sensitivity
        
        # Adjust based on pattern indicators
        pattern_words = ['always', 'never', 'every time', 'pattern', 
                        'again', 'same', 'typical', 'usual']
        
        pattern_count = sum(1 for word in pattern_words if word in text.lower())
        if pattern_count > 0:
            base_confidence += 0.2
        
        # Adjust based on contradiction indicators
        contradiction_words = ['but', 'however', 'although', 'yet',
                              'even though', 'despite', 'paradox']
        
        contradiction_count = sum(1 for word in contradiction_words if word in text.lower())
        if contradiction_count > 0:
            base_confidence += 0.15
        
        # Lower confidence for very short inputs
        if len(text.split()) < 3:
            base_confidence *= 0.7
        
        # Ensure confidence respects sensitivity
        base_confidence = min(base_confidence, sensitivity)
        
        return max(0.2, min(0.8, base_confidence))