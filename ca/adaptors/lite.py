"""
Lite Adapter for BLUX-cA - Bridging interface for BLUX-Lite orchestrator.

Provides a simplified, high-level API for BLUX-Lite to interact with BLUX-cA,
exposing core functionality while handling complexity internally.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ca.core.constitution import ConstitutionEngine, ConstitutionalRule
from ca.core.discernment import DiscernmentCompass, DiscernmentResult
from ca.core.reflection import ReflectionEngine, ReflectionInsight

# Optional imports for full functionality
try:
    from ca.core_agent import BLUXAgent, ProcessingContext, ProcessingMode
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False
    BLUXAgent = None
    ProcessingContext = None
    ProcessingMode = None

try:
    from ca.core.memory import Memory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    Memory = None

try:
    from ca.core.states import RecoveryStateMachine, RecoveryState
    STATES_AVAILABLE = True
except ImportError:
    STATES_AVAILABLE = False
    RecoveryStateMachine = None
    RecoveryState = None

try:
    from ca.core.dimensions import LogicalClarity, EmotionalClarity, ShadowClarity
    DIMENSIONS_AVAILABLE = True
except ImportError:
    DIMENSIONS_AVAILABLE = False
    LogicalClarity = EmotionalClarity = ShadowClarity = None


class EvaluationMode(str, Enum):
    """Modes for evaluation processing."""
    FAST = "FAST"          # Quick evaluation with minimal processing
    STANDARD = "STANDARD"  # Standard evaluation with full processing
    DEEP = "DEEP"          # Deep evaluation with extended reflection
    CRISIS = "CRISIS"      # Crisis mode with safety prioritization
    CUSTOM = "CUSTOM"      # Custom evaluation configuration


@dataclass
class EvaluationRequest:
    """Request for evaluation."""
    text: str                                     # Text to evaluate
    mode: EvaluationMode = EvaluationMode.STANDARD
    session_id: Optional[str] = None              # Session identifier
    user_id: Optional[str] = None                 # User identifier
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)  # Request metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['mode'] = self.mode.value
        return data


@dataclass
class EvaluationResult:
    """Result of an evaluation."""
    id: str = field(default_factory=lambda: str(uuid4()))
    request: Optional[EvaluationRequest] = None
    processing_time_ms: float = 0.0
    
    # Core components
    discernment: Optional[DiscernmentResult] = None
    reflection: Optional[ReflectionInsight] = None
    constitutional_verdict: Optional[Dict[str, Any]] = None
    
    # Extended components (if available)
    dimensional_insights: Dict[str, Any] = field(default_factory=dict)
    recovery_state: Optional[str] = None
    memory_references: List[Dict[str, Any]] = field(default_factory=list)
    agent_response: Optional[Dict[str, Any]] = None
    
    # Summary and metadata
    summary: str = ""
    confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    component_versions: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = {
            "id": self.id,
            "processing_time_ms": self.processing_time_ms,
            "summary": self.summary,
            "confidence": self.confidence,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "errors": self.errors,
            "timestamp": self.timestamp,
            "component_versions": self.component_versions,
            "metadata": self.metadata,
        }
        
        if self.request:
            data["request"] = self.request.to_dict()
        
        if self.discernment:
            data["discernment"] = asdict(self.discernment)
        
        if self.reflection:
            data["reflection"] = asdict(self.reflection)
        
        if self.constitutional_verdict:
            data["constitutional_verdict"] = self.constitutional_verdict
        
        if self.dimensional_insights:
            data["dimensional_insights"] = self.dimensional_insights
        
        if self.recovery_state:
            data["recovery_state"] = self.recovery_state
        
        if self.memory_references:
            data["memory_references"] = self.memory_references
        
        if self.agent_response:
            data["agent_response"] = self.agent_response
        
        return data
    
    def get_summary_text(self, max_length: int = 500) -> str:
        """Get a summary text of the evaluation."""
        if self.summary:
            if len(self.summary) <= max_length:
                return self.summary
            return self.summary[:max_length] + "..."
        
        # Generate summary from components
        parts = []
        
        if self.discernment:
            parts.append(f"Intent: {self.discernment.intent.value}")
            parts.append(f"User type: {self.discernment.user_type.value}")
        
        if self.reflection:
            parts.append(f"Reflection: {self.reflection.summary[:100]}...")
        
        if self.constitutional_verdict:
            verdict = self.constitutional_verdict.get("decision", "unknown")
            parts.append(f"Constitutional verdict: {verdict}")
        
        if self.recovery_state:
            parts.append(f"Recovery state: {self.recovery_state}")
        
        summary = ". ".join(parts)
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    def is_safe(self) -> bool:
        """Check if evaluation result indicates safe operation."""
        if self.errors:
            return False
        
        if self.constitutional_verdict:
            decision = self.constitutional_verdict.get("decision", "")
            if decision in ["REJECT", "BLOCK"]:
                return False
            
            violations = self.constitutional_verdict.get("violations", [])
            if any(v.get("priority", 0) >= 75 for v in violations):  # High priority violations
                return False
        
        return True
    
    def get_primary_recommendation(self) -> Optional[str]:
        """Get the primary recommendation."""
        if self.recommendations:
            return self.recommendations[0]
        
        if self.constitutional_verdict:
            recommendations = self.constitutional_verdict.get("recommendations", [])
            if recommendations:
                return recommendations[0].get("guidance")
        
        return None


class LiteAdapter:
    """
    Adapter bridging BLUX-Lite orchestrator with BLUX-cA.
    
    Provides a high-level, simplified interface for BLUX-Lite to access
    BLUX-cA's capabilities while handling complexity internally.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        enable_full_pipeline: bool = AGENT_AVAILABLE,
        enable_memory: bool = MEMORY_AVAILABLE,
        enable_states: bool = STATES_AVAILABLE,
        enable_dimensions: bool = DIMENSIONS_AVAILABLE,
        cache_results: bool = True,
        max_cache_size: int = 1000,
    ) -> None:
        """
        Initialize Lite adapter.
        
        Args:
            config: Configuration dictionary
            enable_full_pipeline: Enable full agent pipeline if available
            enable_memory: Enable memory system if available
            enable_states: Enable state management if available
            enable_dimensions: Enable clarity dimensions if available
            cache_results: Cache evaluation results
            max_cache_size: Maximum number of results to cache
        """
        self.config = config or {}
        self.enable_full_pipeline = enable_full_pipeline and AGENT_AVAILABLE
        self.enable_memory = enable_memory and MEMORY_AVAILABLE
        self.enable_states = enable_states and STATES_AVAILABLE
        self.enable_dimensions = enable_dimensions and DIMENSIONS_AVAILABLE
        self.cache_results = cache_results
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize core components
        self.reflection = ReflectionEngine()
        self.compass = DiscernmentCompass()
        self.constitution = ConstitutionEngine()
        
        # Initialize extended components if available
        self.agent = None
        self.memory = None
        self.state_machine = None
        self.dimensions = {}
        
        if self.enable_full_pipeline and AGENT_AVAILABLE:
            try:
                self.agent = BLUXAgent(name="BLUX-Lite-Adapter")
                self.logger.info("Full agent pipeline enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize agent: {e}")
                self.enable_full_pipeline = False
        
        if self.enable_memory and MEMORY_AVAILABLE:
            try:
                self.memory = Memory()
                self.logger.info("Memory system enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize memory: {e}")
                self.enable_memory = False
        
        if self.enable_states and STATES_AVAILABLE:
            try:
                self.state_machine = RecoveryStateMachine()
                self.logger.info("State management enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize state machine: {e}")
                self.enable_states = False
        
        if self.enable_dimensions and DIMENSIONS_AVAILABLE:
            try:
                self.dimensions = {
                    "logical": LogicalClarity(),
                    "emotional": EmotionalClarity(),
                    "shadow": ShadowClarity(),
                }
                self.logger.info("Clarity dimensions enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize dimensions: {e}")
                self.enable_dimensions = False
        
        # Initialize cache
        self.result_cache: Dict[str, EvaluationResult] = {}
        self.max_cache_size = max_cache_size
        
        # Metrics
        self.metrics = {
            "evaluations_total": 0,
            "evaluations_today": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_processing_time_ms": 0.0,
            "errors": 0,
            "last_evaluation": None,
        }
        
        # Component versions
        self.component_versions = {
            "lite_adapter": "1.0.0",
            "reflection": getattr(self.reflection, '__version__', 'unknown'),
            "discernment": getattr(self.compass, '__version__', 'unknown'),
            "constitution": getattr(self.constitution, '__version__', 'unknown'),
        }
        
        self.logger.info("Lite adapter initialized")
    
    def evaluate(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        High-level evaluate entrypoint used by BLUX-Lite.
        
        Args:
            text: Text to evaluate
            **kwargs: Additional parameters (mode, session_id, etc.)
            
        Returns:
            Evaluation result as dictionary
        """
        # Create evaluation request
        mode = kwargs.get('mode', EvaluationMode.STANDARD)
        request = EvaluationRequest(
            text=text,
            mode=mode,
            session_id=kwargs.get('session_id'),
            user_id=kwargs.get('user_id'),
            context=kwargs.get('context', {}),
            metadata=kwargs.get('metadata', {}),
        )
        
        # Perform evaluation
        result = self._evaluate_request(request)
        
        # Return as dictionary
        return result.to_dict()
    
    def evaluate_request(self, request: EvaluationRequest) -> EvaluationResult:
        """
        Evaluate a structured request.
        
        Args:
            request: Evaluation request
            
        Returns:
            Evaluation result
        """
        return self._evaluate_request(request)
    
    def _evaluate_request(self, request: EvaluationRequest) -> EvaluationResult:
        """Internal method to evaluate a request."""
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        if self.cache_results and cache_key in self.result_cache:
            self.metrics["cache_hits"] += 1
            cached = self.result_cache[cache_key]
            cached.metadata["cached"] = True
            self.logger.debug(f"Cache hit for evaluation: {request.text[:50]}...")
            return cached
        
        self.metrics["cache_misses"] += 1
        
        # Create result object
        result = EvaluationResult(request=request)
        result.component_versions = self.component_versions.copy()
        
        try:
            # Determine evaluation pipeline based on mode
            if request.mode == EvaluationMode.FAST:
                result = self._evaluate_fast(request, result)
            elif request.mode == EvaluationMode.CRISIS:
                result = self._evaluate_crisis(request, result)
            elif request.mode == EvaluationMode.DEEP:
                result = self._evaluate_deep(request, result)
            elif self.enable_full_pipeline and self.agent:
                result = self._evaluate_full_pipeline(request, result)
            else:
                result = self._evaluate_standard(request, result)
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            
            self.metrics["evaluations_total"] += 1
            self.metrics["last_evaluation"] = datetime.now().isoformat()
            
            # Update average processing time
            if self.metrics["avg_processing_time_ms"] == 0:
                self.metrics["avg_processing_time_ms"] = processing_time
            else:
                self.metrics["avg_processing_time_ms"] = (
                    0.9 * self.metrics["avg_processing_time_ms"] + 0.1 * processing_time
                )
            
            # Cache result
            if self.cache_results and result.is_safe():
                if len(self.result_cache) >= self.max_cache_size:
                    # Remove oldest entry
                    oldest_key = next(iter(self.result_cache))
                    del self.result_cache[oldest_key]
                
                self.result_cache[cache_key] = result
            
            self.logger.info(f"Evaluation completed in {processing_time:.1f}ms")
            
        except Exception as e:
            self.metrics["errors"] += 1
            self.logger.error(f"Evaluation error: {e}", exc_info=True)
            
            # Create error result
            result.errors.append(f"Evaluation failed: {str(e)}")
            result.summary = f"Evaluation error: {str(e)[:100]}"
            result.confidence = 0.0
            result.processing_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _evaluate_standard(self, request: EvaluationRequest, result: EvaluationResult) -> EvaluationResult:
        """Standard evaluation pipeline."""
        text = request.text
        
        # 1. Discernment
        try:
            result.discernment = self.compass.classify(text)
            result.summary += f"Discerned as: {result.discernment.user_type.value} with intent: {result.discernment.intent.value}. "
        except Exception as e:
            result.errors.append(f"Discernment failed: {e}")
            result.discernment = DiscernmentResult(
                user_type="UNKNOWN",
                intent="UNKNOWN",
                confidence=0.0
            )
        
        # 2. Reflection
        try:
            result.reflection = self.reflection.reflect(text)
            result.summary += f"Reflection: {result.reflection.summary[:100]}... "
            result.confidence = max(result.confidence, result.reflection.confidence)
        except Exception as e:
            result.errors.append(f"Reflection failed: {e}")
        
        # 3. Constitutional evaluation
        try:
            insights = [result.reflection.summary] if result.reflection else [text]
            intent_value = result.discernment.intent.value if result.discernment else "UNKNOWN"
            
            # Prepare context
            context = {
                "user_input": text,
                "user_type": result.discernment.user_type.value if result.discernment else "UNKNOWN",
                "intent": intent_value,
                "session_id": request.session_id,
                "user_id": request.user_id,
                **request.context
            }
            
            # Simple action for evaluation
            action = {
                "type": "evaluation",
                "text": text,
                "intent": intent_value,
            }
            
            result.constitutional_verdict = self.constitution.evaluate(action, context)
            
            # Add verdict to summary
            if result.constitutional_verdict:
                decision = result.constitutional_verdict.get("decision", "UNKNOWN")
                result.summary += f"Constitutional verdict: {decision}. "
                
                # Add warnings from violations
                violations = result.constitutional_verdict.get("violations", [])
                if violations:
                    result.warnings.extend([v.get("description", "") for v in violations[:2]])
                
                # Add recommendations
                recommendations = result.constitutional_verdict.get("recommendations", [])
                if recommendations:
                    result.recommendations.extend([r.get("guidance", "") for r in recommendations[:2]])
        except Exception as e:
            result.errors.append(f"Constitutional evaluation failed: {e}")
        
        # 4. Dimensional insights (if available)
        if self.enable_dimensions and result.discernment:
            try:
                dimensional_insights = self._get_dimensional_insights(text, request)
                result.dimensional_insights = dimensional_insights
                
                # Add to summary if significant
                if dimensional_insights.get("confidence", 0) > 0.6:
                    result.summary += "Dimensional analysis available. "
            except Exception as e:
                self.logger.debug(f"Dimensional insights failed: {e}")
        
        # 5. Memory references (if available)
        if self.enable_memory and self.memory:
            try:
                memory_refs = self._get_memory_references(text, request)
                result.memory_references = memory_refs
                
                if memory_refs:
                    result.summary += f"Found {len(memory_refs)} relevant memory references. "
            except Exception as e:
                self.logger.debug(f"Memory reference failed: {e}")
        
        # 6. Update recovery state (if available)
        if self.enable_states and self.state_machine:
            try:
                self.state_machine.update_from_input(text)
                result.recovery_state = self.state_machine.state.recovery_state.value
                result.summary += f"Recovery state: {result.recovery_state}. "
            except Exception as e:
                self.logger.debug(f"State update failed: {e}")
        
        # Finalize summary
        if not result.summary:
            result.summary = f"Evaluated: {text[:100]}..."
        
        # Calculate overall confidence
        result.confidence = self._calculate_overall_confidence(result)
        
        return result
    
    def _evaluate_fast(self, request: EvaluationRequest, result: EvaluationResult) -> EvaluationResult:
        """Fast evaluation pipeline (minimal processing)."""
        text = request.text
        
        # Only do discernment
        try:
            result.discernment = self.compass.classify(text)
            result.summary = f"Fast evaluation: {result.discernment.user_type.value} with {result.discernment.intent.value} intent."
            result.confidence = result.discernment.confidence
        except Exception as e:
            result.errors.append(f"Fast evaluation failed: {e}")
            result.summary = f"Fast evaluation failed for: {text[:100]}..."
        
        result.metadata["pipeline"] = "fast"
        return result
    
    def _evaluate_crisis(self, request: EvaluationRequest, result: EvaluationResult) -> EvaluationResult:
        """Crisis mode evaluation (safety first)."""
        text = request.text
        
        # 1. Quick safety check
        crisis_keywords = ["help", "emergency", "crisis", "urgent", "now", "immediately", "can't", "cannot"]
        text_lower = text.lower()
        is_crisis = any(keyword in text_lower for keyword in crisis_keywords)
        
        if is_crisis:
            result.summary = "Crisis mode activated. Prioritizing safety and stabilization."
            result.recommendations = [
                "Focus on immediate safety and stabilization",
                "Provide grounding and reassurance",
                "Avoid deep analysis in crisis situations",
                "Consider connecting with appropriate support resources"
            ]
            result.warnings = ["Crisis situation detected - handle with care"]
        
        # 2. Run standard evaluation but with safety focus
        result = self._evaluate_standard(request, result)
        
        # 3. Override with crisis recommendations if needed
        if is_crisis:
            # Ensure constitutional verdict prioritizes safety
            if result.constitutional_verdict:
                result.constitutional_verdict["decision"] = "SAFETY_FIRST"
                result.constitutional_verdict["priority"] = "SAFETY"
            
            result.metadata["crisis_detected"] = True
        
        result.metadata["pipeline"] = "crisis"
        return result
    
    def _evaluate_deep(self, request: EvaluationRequest, result: EvaluationResult) -> EvaluationResult:
        """Deep evaluation pipeline (extended processing)."""
        # Start with standard evaluation
        result = self._evaluate_standard(request, result)
        
        # Add extended reflection
        try:
            if result.reflection:
                # Run additional reflection cycles
                extended_text = f"{request.text}\n\nInitial reflection: {result.reflection.summary}"
                extended_reflection = self.reflection.reflect(extended_text, depth=5)
                
                # Update result
                result.reflection = extended_reflection
                result.summary += f" Deep reflection completed with {extended_reflection.depth} levels."
                result.confidence = max(result.confidence, extended_reflection.confidence)
        except Exception as e:
            self.logger.debug(f"Extended reflection failed: {e}")
        
        # Add dimensional analysis if available
        if self.enable_dimensions:
            try:
                # Run all three dimensions
                dimensional_results = {}
                
                if "logical" in self.dimensions:
                    logical = self.dimensions["logical"].analyze(request.text, None)
                    dimensional_results["logical"] = asdict(logical) if hasattr(logical, '__dict__') else str(logical)
                
                if "emotional" in self.dimensions:
                    emotional = self.dimensions["emotional"].analyze(request.text, None)
                    dimensional_results["emotional"] = asdict(emotional) if hasattr(emotional, '__dict__') else str(emotional)
                
                if "shadow" in self.dimensions:
                    shadow = self.dimensions["shadow"].analyze(request.text, None)
                    dimensional_results["shadow"] = asdict(shadow) if hasattr(shadow, '__dict__') else str(shadow)
                
                result.dimensional_insights = dimensional_results
                result.summary += " Comprehensive dimensional analysis completed."
                
            except Exception as e:
                self.logger.debug(f"Deep dimensional analysis failed: {e}")
        
        result.metadata["pipeline"] = "deep"
        return result
    
    def _evaluate_full_pipeline(self, request: EvaluationRequest, result: EvaluationResult) -> EvaluationResult:
        """Full agent pipeline evaluation."""
        if not self.agent:
            return self._evaluate_standard(request, result)
        
        try:
            # Create processing context
            context_kwargs = {}
            if request.session_id:
                context_kwargs["session_id"] = request.session_id
            if request.user_id:
                context_kwargs["user_id"] = request.user_id
            
            # Map evaluation mode to processing mode
            mode_map = {
                EvaluationMode.FAST: ProcessingMode.FAST if ProcessingMode else "FAST",
                EvaluationMode.STANDARD: ProcessingMode.STANDARD if ProcessingMode else "STANDARD",
                EvaluationMode.DEEP: ProcessingMode.DEEP if ProcessingMode else "DEEP",
                EvaluationMode.CRISIS: ProcessingMode.CRISIS if ProcessingMode else "CRISIS",
            }
            
            processing_mode = mode_map.get(request.mode, ProcessingMode.STANDARD if ProcessingMode else "STANDARD")
            
            # Process through agent
            agent_response = self.agent.process(
                user_input=request.text,
                context=ProcessingContext(**context_kwargs) if ProcessingContext else None,
                mode=processing_mode if isinstance(processing_mode, ProcessingMode) else None
            )
            
            # Convert agent response to result
            result.agent_response = asdict(agent_response) if hasattr(agent_response, '__dict__') else agent_response
            
            # Extract components from agent response
            if hasattr(agent_response, 'discernment_result'):
                result.discernment = agent_response.discernment_result
            
            if hasattr(agent_response, 'clarity_scores'):
                result.dimensional_insights["clarity_scores"] = agent_response.clarity_scores
            
            if hasattr(agent_response, 'recovery_state'):
                result.recovery_state = agent_response.recovery_state
            
            if hasattr(agent_response, 'constitutional_check'):
                result.constitutional_verdict = agent_response.constitutional_check
            
            # Create summary from agent response
            if hasattr(agent_response, 'message'):
                result.summary = f"Agent response: {agent_response.message}"
                result.confidence = getattr(agent_response, 'confidence', 0.7)
            else:
                result.summary = "Full agent pipeline completed."
            
            result.metadata["pipeline"] = "full_agent"
            
        except Exception as e:
            self.logger.error(f"Full pipeline evaluation failed: {e}")
            # Fall back to standard evaluation
            result = self._evaluate_standard(request, result)
            result.errors.append(f"Full pipeline failed, using standard: {str(e)[:100]}")
        
        return result
    
    def _get_dimensional_insights(self, text: str, request: EvaluationRequest) -> Dict[str, Any]:
        """Get dimensional insights for text."""
        insights = {}
        
        if not self.enable_dimensions:
            return insights
        
        # Determine recovery state for dimensional analysis
        recovery_state = None
        if self.enable_states and self.state_machine:
            recovery_state = self.state_machine.state
        
        # Analyze with each dimension
        for dim_name, dimension in self.dimensions.items():
            try:
                output = dimension.analyze(text, recovery_state)
                if hasattr(output, '__dict__'):
                    insights[dim_name] = asdict(output)
                else:
                    insights[dim_name] = str(output)
            except Exception as e:
                self.logger.debug(f"Dimension {dim_name} analysis failed: {e}")
                insights[dim_name] = {"error": str(e)}
        
        # Calculate overall dimensional confidence
        if insights:
            confidences = []
            for dim_data in insights.values():
                if isinstance(dim_data, dict) and "confidence" in dim_data:
                    confidences.append(dim_data["confidence"])
            
            if confidences:
                insights["overall_confidence"] = sum(confidences) / len(confidences)
        
        return insights
    
    def _get_memory_references(self, text: str, request: EvaluationRequest) -> List[Dict[str, Any]]:
        """Get relevant memory references for text."""
        references = []
        
        if not self.enable_memory or not self.memory:
            return references
        
        try:
            # Search memory for similar entries
            memory_entries = self.memory.search(
                query=text,
                limit=3,
                threshold=0.5
            )
            
            for entry in memory_entries:
                references.append({
                    "id": getattr(entry, 'id', 'unknown'),
                    "input": getattr(entry, 'input_text', '')[:100],
                    "decision": getattr(entry, 'decision', 'unknown'),
                    "timestamp": getattr(entry, 'timestamp', 'unknown'),
                    "similarity": getattr(entry, 'similarity_score', 0.0),
                })
        
        except Exception as e:
            self.logger.debug(f"Memory search failed: {e}")
        
        return references
    
    def _calculate_overall_confidence(self, result: EvaluationResult) -> float:
        """Calculate overall confidence score."""
        confidences = []
        
        if result.discernment and hasattr(result.discernment, 'confidence'):
            confidences.append(result.discernment.confidence)
        
        if result.reflection and hasattr(result.reflection, 'confidence'):
            confidences.append(result.reflection.confidence)
        
        if result.constitutional_verdict and 'confidence' in result.constitutional_verdict:
            # Constitutional verdict might not have confidence
            pass
        
        if result.dimensional_insights and 'overall_confidence' in result.dimensional_insights:
            confidences.append(result.dimensional_insights['overall_confidence'])
        
        if confidences:
            return sum(confidences) / len(confidences)
        
        return 0.7  # Default confidence
    
    def _generate_cache_key(self, request: EvaluationRequest) -> str:
        """Generate cache key for request."""
        import hashlib
        
        key_parts = [
            request.text,
            request.mode.value,
            request.session_id or "",
            json.dumps(request.context, sort_keys=True),
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    # Public API methods
    
    def batch_evaluate(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        Evaluate multiple texts.
        
        Args:
            texts: List of texts to evaluate
            **kwargs: Additional parameters
            
        Returns:
            List of evaluation results
        """
        results = []
        mode = kwargs.get('mode', EvaluationMode.STANDARD)
        
        for text in texts:
            try:
                request = EvaluationRequest(
                    text=text,
                    mode=mode,
                    session_id=kwargs.get('session_id'),
                    user_id=kwargs.get('user_id'),
                    context=kwargs.get('context', {}),
                )
                
                result = self._evaluate_request(request)
                results.append(result.to_dict())
                
            except Exception as e:
                self.logger.error(f"Batch evaluation failed for text: {e}")
                # Create error result
                error_result = EvaluationResult(
                    request=EvaluationRequest(text=text, mode=mode),
                    errors=[f"Evaluation failed: {str(e)}"],
                    summary=f"Error: {str(e)[:100]}",
                    confidence=0.0,
                )
                results.append(error_result.to_dict())
        
        return results
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get adapter capabilities."""
        return {
            "full_pipeline": self.enable_full_pipeline,
            "memory": self.enable_memory,
            "states": self.enable_states,
            "dimensions": self.enable_dimensions,
            "cache_enabled": self.cache_results,
            "max_cache_size": self.max_cache_size,
            "component_versions": self.component_versions,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            "metrics": self.metrics.copy(),
            "cache_size": len(self.result_cache),
            "capabilities": self.get_capabilities(),
            "config": self.config,
        }
    
    def clear_cache(self) -> int:
        """Clear evaluation cache."""
        count = len(self.result_cache)
        self.result_cache.clear()
        self.logger.info(f"Cleared {count} cached evaluations")
        return count
    
    def export_results(self, filepath: str, format: str = "json") -> bool:
        """
        Export cached results to file.
        
        Args:
            filepath: Path to export file
            format: Export format ("json" or "jsonl")
            
        Returns:
            True if export successful
        """
        try:
            results = [result.to_dict() for result in self.result_cache.values()]
            
            if format == "json":
                data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "count": len(results),
                    "results": results,
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format == "jsonl":
                with open(filepath, 'w', encoding='utf-8') as f:
                    for result in results:
                        f.write(json.dumps(result) + "\n")
            
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.logger.info(f"Exported {len(results)} results to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export results: {e}")
            return False


# Convenience functions

def create_lite_adapter(
    config: Optional[Dict[str, Any]] = None,
    enable_full_pipeline: bool = True,
) -> LiteAdapter:
    """
    Create a Lite adapter with sensible defaults.
    
    Args:
        config: Configuration dictionary
        enable_full_pipeline: Enable full agent pipeline if available
        
    Returns:
        Configured LiteAdapter instance
    """
    return LiteAdapter(
        config=config,
        enable_full_pipeline=enable_full_pipeline,
        enable_memory=True,
        enable_states=True,
        enable_dimensions=True,
        cache_results=True,
    )


def quick_evaluate(text: str) -> Dict[str, Any]:
    """
    Quick evaluation utility function.
    
    Args:
        text: Text to evaluate
        
    Returns:
        Evaluation result
    """
    adapter = LiteAdapter(enable_full_pipeline=False)
    return adapter.evaluate(text, mode=EvaluationMode.FAST)


__all__ = [
    "LiteAdapter",
    "EvaluationRequest",
    "EvaluationResult",
    "EvaluationMode",
    "create_lite_adapter",
    "quick_evaluate",
]