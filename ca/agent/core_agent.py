from __future__ import annotations

"""
BLUX-cA Core Agent - Clarity Agent Implementation.

Coordinates all components to provide clarity through logical, emotional, 
and shadow dimensions with ethical guardrails and state-aware processing.
"""

import asyncio
import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from uuid import uuid4

# Core components
from .memory import Memory, MemoryEntry
from .discernment import DiscernmentCompass, DiscernmentResult
from .constitution import ConstitutionEngine, ConstitutionalRule, RulePriority
from .audit import AuditTrail, AuditLevel, AuditCategory

# Optional components (handle missing imports gracefully)
try:
    from .dimensions import LogicalClarity, EmotionalClarity, ShadowClarity, DimensionOutput
    DIMENSIONS_AVAILABLE = True
except ImportError:
    DIMENSIONS_AVAILABLE = False
    LogicalClarity = EmotionalClarity = ShadowClarity = DimensionOutput = None

try:
    from .states import UserState, RecoveryStateMachine, RecoveryState
    STATES_AVAILABLE = True
except ImportError:
    STATES_AVAILABLE = False
    UserState = RecoveryStateMachine = RecoveryState = None

try:
    from .llm_adapter import call_llm, LLMAdapter
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    call_llm = LLMAdapter = None


class AgentStatus(str, Enum):
    """Agent operational status."""
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    PROCESSING = "PROCESSING"
    ERROR = "ERROR"
    SHUTTING_DOWN = "SHUTTING_DOWN"
    MAINTENANCE = "MAINTENANCE"


class ProcessingMode(str, Enum):
    """Processing modes for the agent."""
    STANDARD = "STANDARD"          # Full 3D clarity processing
    FAST = "FAST"                  # Quick response mode
    DEEP = "DEEP"                  # Extended reflection mode
    CRISIS = "CRISIS"              # Crisis handling mode
    SHADOW_ONLY = "SHADOW_ONLY"    # Focus on shadow dimension
    LOGICAL_ONLY = "LOGICAL_ONLY"  # Focus on logical dimension
    EMOTIONAL_ONLY = "EMOTIONAL_ONLY"  # Focus on emotional dimension


@dataclass
class ProcessingContext:
    """Context for processing a single interaction."""
    session_id: str
    user_id: Optional[str] = None
    user_state_token: Optional[Dict[str, Any]] = None
    recovery_state: Optional[str] = None
    mode: ProcessingMode = ProcessingMode.STANDARD
    custom_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """Structured agent response."""
    message: str
    intent: str
    emotion: str
    confidence: float
    clarity_scores: Dict[str, float]
    recovery_state: str
    processing_time_ms: float
    session_id: str
    user_state_token: Dict[str, Any]
    dimension_insights: Dict[str, Any]
    constitutional_check: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Agent performance and operational metrics."""
    interactions_total: int = 0
    interactions_today: int = 0
    avg_processing_time_ms: float = 0.0
    error_rate: float = 0.0
    dimension_usage: Dict[str, int] = field(default_factory=lambda: {
        "logical": 0,
        "emotional": 0,
        "shadow": 0
    })
    state_distribution: Dict[str, int] = field(default_factory=dict)
    last_interaction: Optional[str] = None
    component_health: Dict[str, bool] = field(default_factory=dict)


class ComponentHealth:
    """Health status of agent components."""
    
    def __init__(self):
        self.status = {
            "core": True,
            "memory": True,
            "discernment": True,
            "constitution": True,
            "audit": True,
            "dimensions": DIMENSIONS_AVAILABLE,
            "states": STATES_AVAILABLE,
            "llm": LLM_AVAILABLE,
        }
        self.last_check = datetime.now()
        self.errors: List[Dict[str, Any]] = []
    
    def check_all(self, agent: 'BLUXAgent') -> Dict[str, bool]:
        """Check health of all components."""
        checks = {}
        
        # Check core components
        checks["core"] = agent.status == AgentStatus.READY
        
        # Check memory
        try:
            test_entry = agent.memory.store("health_check", "system", "test")
            checks["memory"] = test_entry is not None
        except Exception as e:
            checks["memory"] = False
            self.errors.append({"component": "memory", "error": str(e), "time": datetime.now()})
        
        # Check discernment
        try:
            result = agent.discernment.classify("health check")
            checks["discernment"] = result is not None
        except Exception as e:
            checks["discernment"] = False
            self.errors.append({"component": "discernment", "error": str(e), "time": datetime.now()})
        
        # Check constitution
        try:
            context = {"user_type": "system", "recovery_state": "UNKNOWN"}
            result = agent.constitution.evaluate({"type": "test"}, context)
            checks["constitution"] = result is not None
        except Exception as e:
            checks["constitution"] = False
            self.errors.append({"component": "constitution", "error": str(e), "time": datetime.now()})
        
        # Check dimensions if available
        if DIMENSIONS_AVAILABLE:
            try:
                # Quick test of each dimension
                if hasattr(agent, 'logical_dimension'):
                    _ = agent.logical_dimension.analyze("test", RecoveryState.AWARENESS if STATES_AVAILABLE else None)
                checks["dimensions"] = True
            except Exception as e:
                checks["dimensions"] = False
                self.errors.append({"component": "dimensions", "error": str(e), "time": datetime.now()})
        else:
            checks["dimensions"] = False
        
        # Update status
        self.status.update(checks)
        self.last_check = datetime.now()
        
        return checks
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        return {
            "status": self.status,
            "last_check": self.last_check.isoformat(),
            "error_count": len(self.errors),
            "recent_errors": self.errors[-5:] if self.errors else [],
            "component_count": len(self.status),
            "healthy_components": sum(1 for v in self.status.values() if v),
        }


class BLUXAgent:
    """
    BLUX-cA Core Agent - Main orchestrator of clarity dimensions.
    
    Coordinates logical, emotional, and shadow clarity analysis with
    ethical guardrails, memory, and state-aware processing.
    """
    
    def __init__(
        self,
        name: str = "BLUX-cA",
        config: Optional[Dict[str, Any]] = None,
        memory: Optional[Memory] = None,
        discernment: Optional[DiscernmentCompass] = None,
        constitution: Optional[ConstitutionEngine] = None,
        audit: Optional[AuditTrail] = None,
        enable_dimensions: bool = DIMENSIONS_AVAILABLE,
        enable_states: bool = STATES_AVAILABLE,
        enable_llm: bool = LLM_AVAILABLE,
        processing_mode: ProcessingMode = ProcessingMode.STANDARD,
        session_timeout_minutes: int = 60,
    ) -> None:
        """
        Initialize BLUX-cA agent.
        
        Args:
            name: Agent name
            config: Configuration dictionary
            memory: Memory system instance
            discernment: Discernment compass instance
            constitution: Constitution engine instance
            audit: Audit trail instance
            enable_dimensions: Enable clarity dimensions
            enable_states: Enable state management
            enable_llm: Enable LLM integration
            processing_mode: Default processing mode
            session_timeout_minutes: Session timeout in minutes
        """
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.INITIALIZING
        self.processing_mode = processing_mode
        self.session_timeout_minutes = session_timeout_minutes
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        # Initialize core components
        self.memory = memory or Memory()
        self.discernment = discernment or DiscernmentCompass()
        self.constitution = constitution or ConstitutionEngine()
        self.audit = audit or AuditTrail(component_name=self.name)
        
        # Initialize optional components
        self.enable_dimensions = enable_dimensions and DIMENSIONS_AVAILABLE
        self.enable_states = enable_states and STATES_AVAILABLE
        self.enable_llm = enable_llm and LLM_AVAILABLE
        
        if self.enable_dimensions:
            self.logical_dimension = LogicalClarity()
            self.emotional_dimension = EmotionalClarity()
            self.shadow_dimension = ShadowClarity()
        
        if self.enable_states:
            self.state_machines: Dict[str, RecoveryStateMachine] = {}
        
        if self.enable_llm:
            self.llm_adapter = LLMAdapter(config.get("llm", {})) if LLM_AVAILABLE else None
        
        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.active_sessions: Dict[str, datetime] = {}
        
        # Processing pipeline
        self.pre_processors: List[Callable] = []
        self.post_processors: List[Callable] = []
        
        # Metrics and monitoring
        self.metrics = AgentMetrics()
        self.health = ComponentHealth()
        self.start_time = datetime.now()
        
        # Thread safety
        self._lock = threading.RLock()
        self._processing_count = 0
        
        # Initialize agent
        self._initialize_agent()
        
        self.logger.info(f"BLUX-cA agent '{name}' initialized successfully")
    
    def _initialize_agent(self) -> None:
        """Initialize agent components and validate configuration."""
        try:
            # Validate configuration
            self._validate_config()
            
            # Initialize sessions cleanup thread
            self._start_session_cleanup()
            
            # Run health check
            health_report = self.health.check_all(self)
            
            if all(health_report.values()):
                self.status = AgentStatus.READY
                self.logger.info("Agent initialized and ready")
            else:
                failed = [k for k, v in health_report.items() if not v]
                self.logger.warning(f"Agent initialized with failed components: {failed}")
                self.status = AgentStatus.READY  # Still ready, but with warnings
            
            # Log initialization
            self.audit.log(
                level=AuditLevel.INFO,
                category=AuditCategory.SYSTEM,
                operation="agent_initialization",
                description=f"Agent '{self.name}' initialized",
                details={
                    "status": self.status.value,
                    "components_enabled": {
                        "dimensions": self.enable_dimensions,
                        "states": self.enable_states,
                        "llm": self.enable_llm,
                    },
                    "health_report": health_report,
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def _validate_config(self) -> None:
        """Validate agent configuration."""
        if not self.name:
            raise ValueError("Agent name is required")
        
        # Validate processing mode
        try:
            _ = ProcessingMode(self.processing_mode.value)
        except ValueError:
            self.logger.warning(f"Invalid processing mode: {self.processing_mode}. Using STANDARD.")
            self.processing_mode = ProcessingMode.STANDARD
    
    def _start_session_cleanup(self) -> None:
        """Start background thread for session cleanup."""
        def cleanup_worker():
            while self.status != AgentStatus.SHUTTING_DOWN:
                try:
                    self._cleanup_expired_sessions()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    self.logger.error(f"Session cleanup error: {e}")
                    time.sleep(60)
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        self.logger.debug("Session cleanup thread started")
    
    def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions."""
        with self._lock:
            now = datetime.now()
            expired = []
            
            for session_id, last_active in self.active_sessions.items():
                if (now - last_active).total_seconds() > self.session_timeout_minutes * 60:
                    expired.append(session_id)
            
            for session_id in expired:
                del self.active_sessions[session_id]
                if session_id in self.sessions:
                    del self.sessions[session_id]
                
                if self.enable_states and session_id in self.state_machines:
                    del self.state_machines[session_id]
            
            if expired:
                self.logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def _get_or_create_session(self, context: ProcessingContext) -> Dict[str, Any]:
        """Get existing session or create new one."""
        session_id = context.session_id
        
        with self._lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "id": session_id,
                    "created": datetime.now().isoformat(),
                    "interaction_count": 0,
                    "user_id": context.user_id,
                    "recovery_state_history": [],
                    "clarity_scores_history": [],
                    "custom_data": {},
                }
                
                # Initialize state machine for session if enabled
                if self.enable_states:
                    state_token = context.user_state_token or {}
                    self.state_machines[session_id] = RecoveryStateMachine.from_token(state_token)
            
            # Update last active time
            self.active_sessions[session_id] = datetime.now()
            
            return self.sessions[session_id]
    
    def add_pre_processor(self, processor: Callable) -> None:
        """Add pre-processor to pipeline."""
        self.pre_processors.append(processor)
        self.logger.info(f"Added pre-processor: {processor.__name__}")
    
    def add_post_processor(self, processor: Callable) -> None:
        """Add post-processor to pipeline."""
        self.post_processors.append(processor)
        self.logger.info(f"Added post-processor: {processor.__name__}")
    
    def process(
        self,
        user_input: str,
        context: Optional[ProcessingContext] = None,
        mode: Optional[ProcessingMode] = None
    ) -> AgentResponse:
        """
        Process user input through full agent pipeline.
        
        Args:
            user_input: User input text
            context: Processing context (creates new session if not provided)
            mode: Processing mode override
            
        Returns:
            Structured agent response
        """
        start_time = time.time()
        
        # Validate agent status
        if self.status != AgentStatus.READY:
            raise RuntimeError(f"Agent not ready. Current status: {self.status.value}")
        
        # Create context if not provided
        if context is None:
            context = ProcessingContext(session_id=str(uuid4()))
        
        # Use provided mode or default
        processing_mode = mode or context.mode or self.processing_mode
        
        # Get or create session
        session = self._get_or_create_session(context)
        session_id = context.session_id
        
        # Update session metrics
        session["interaction_count"] += 1
        session["last_interaction"] = datetime.now().isoformat()
        
        self.logger.info(
            f"Processing input for session {session_id[:8]}... "
            f"(mode: {processing_mode.value}, length: {len(user_input)})"
        )
        
        try:
            # Run pre-processors
            processed_input = user_input
            for pre_processor in self.pre_processors:
                processed_input = pre_processor(processed_input, context)
            
            # Run core processing pipeline
            with self._lock:
                self._processing_count += 1
                self.status = AgentStatus.PROCESSING
            
            try:
                # Step 1: Discernment
                discernment_result = self._run_discernment(processed_input, context)
                
                # Step 2: State update (if enabled)
                recovery_state = self._update_state(processed_input, session_id, context)
                
                # Step 3: Constitutional check
                constitutional_result = self._run_constitutional_check(
                    processed_input, discernment_result, recovery_state, context
                )
                
                # Step 4: Dimensional analysis (if enabled)
                dimension_insights = self._run_dimensional_analysis(
                    processed_input, recovery_state, processing_mode, context
                )
                
                # Step 5: Generate response
                response = self._generate_response(
                    processed_input,
                    discernment_result,
                    constitutional_result,
                    dimension_insights,
                    recovery_state,
                    processing_mode,
                    context
                )
                
                # Step 6: Memory storage
                memory_entry = self._store_in_memory(
                    processed_input, response, discernment_result, recovery_state, context
                )
                
                # Step 7: Audit logging
                self._log_to_audit(
                    processed_input, response, discernment_result, constitutional_result, context
                )
                
                # Update session with recovery state
                if recovery_state:
                    session["recovery_state_history"].append({
                        "state": recovery_state,
                        "timestamp": datetime.now().isoformat()
                    })
                
                # Update metrics
                self._update_metrics(response, processing_time_ms=(time.time() - start_time) * 1000)
                
            finally:
                with self._lock:
                    self._processing_count -= 1
                    if self._processing_count == 0:
                        self.status = AgentStatus.READY
            
            # Run post-processors
            for post_processor in self.post_processors:
                response = post_processor(response, context)
            
            processing_time_ms = (time.time() - start_time) * 1000
            self.logger.info(f"Processing completed in {processing_time_ms:.1f}ms")
            
            return response
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Processing error: {e}", exc_info=True)
            
            # Log error to audit
            self.audit.log(
                level=AuditLevel.ERROR,
                category=AuditCategory.SYSTEM,
                operation="processing_error",
                description=f"Error processing input: {str(e)[:100]}",
                details={"error": str(e), "input_preview": user_input[:100]},
                session_id=session_id,
                agent_name=self.name
            )
            
            # Return error response
            return self._create_error_response(e, session_id, context)
    
    def _run_discernment(self, user_input: str, context: ProcessingContext) -> DiscernmentResult:
        """Run discernment classification."""
        result = self.discernment.classify(user_input)
        
        # Log discernment result
        self.audit.log(
            level=AuditLevel.INFO,
            category=AuditCategory.DIMENSION_ANALYSIS,
            operation="discernment_classification",
            description=f"Discernment result: {result.intent.value}",
            details=asdict(result),
            session_id=context.session_id,
            agent_name=self.name
        )
        
        return result
    
    def _update_state(
        self, 
        user_input: str, 
        session_id: str,
        context: ProcessingContext
    ) -> Optional[str]:
        """Update recovery state for session."""
        if not self.enable_states:
            return None
        
        if session_id not in self.state_machines:
            return None
        
        state_machine = self.state_machines[session_id]
        
        # Update state based on input
        state_machine.update_from_input(user_input)
        current_state = state_machine.state.recovery_state.value
        
        # Log state transition if changed
        if (context.user_state_token and 
            context.user_state_token.get("recovery_state") != current_state):
            
            self.audit.log(
                level=AuditLevel.INFO,
                category=AuditCategory.STATE_TRANSITION,
                operation="state_transition",
                description=f"Recovery state: {current_state}",
                details={
                    "previous_state": context.user_state_token.get("recovery_state"),
                    "current_state": current_state,
                    "input_preview": user_input[:100]
                },
                session_id=session_id,
                agent_name=self.name,
                recovery_state=current_state
            )
        
        return current_state
    
    def _run_constitutional_check(
        self,
        user_input: str,
        discernment_result: DiscernmentResult,
        recovery_state: Optional[str],
        context: ProcessingContext
    ) -> Dict[str, Any]:
        """Run constitutional rules check."""
        # Prepare context for constitution
        constitution_context = {
            "user_input": user_input,
            "user_type": discernment_result.user_type.value,
            "intent": discernment_result.intent.value,
            "recovery_state": recovery_state or "UNKNOWN",
            "session_id": context.session_id,
            "agent_name": self.name,
            **context.custom_context
        }
        
        # Prepare action to evaluate
        action = {
            "type": "response_generation",
            "user_input": user_input,
            "user_type": discernment_result.user_type.value,
            "intent": discernment_result.intent.value,
        }
        
        # Evaluate against constitution
        result = self.constitution.evaluate(action, constitution_context, self.name)
        
        # Log constitutional check
        self.audit.log(
            level=AuditLevel.INFO if result["allowed"] else AuditLevel.WARNING,
            category=AuditCategory.CONSTITUTION_CHECK,
            operation="constitutional_evaluation",
            description=f"Constitutional check: {result['decision']}",
            details=result,
            session_id=context.session_id,
            agent_name=self.name,
            recovery_state=recovery_state
        )
        
        return result
    
    def _run_dimensional_analysis(
        self,
        user_input: str,
        recovery_state: Optional[str],
        mode: ProcessingMode,
        context: ProcessingContext
    ) -> Dict[str, Any]:
        """Run clarity dimension analysis."""
        if not self.enable_dimensions:
            return {}
        
        insights = {
            "logical": None,
            "emotional": None,
            "shadow": None,
            "fused": None,
        }
        
        try:
            # Convert recovery state string to enum if available
            state_enum = None
            if recovery_state and STATES_AVAILABLE:
                try:
                    state_enum = RecoveryState(recovery_state)
                except ValueError:
                    state_enum = RecoveryState.AWARENESS
            
            # Run dimensional analysis based on mode
            if mode in [ProcessingMode.STANDARD, ProcessingMode.DEEP, ProcessingMode.LOGICAL_ONLY]:
                logical_out = self.logical_dimension.analyze(user_input, state_enum)
                insights["logical"] = asdict(logical_out) if logical_out else None
            
            if mode in [ProcessingMode.STANDARD, ProcessingMode.DEEP, ProcessingMode.EMOTIONAL_ONLY]:
                emotional_out = self.emotional_dimension.analyze(user_input, state_enum)
                insights["emotional"] = asdict(emotional_out) if emotional_out else None
            
            if mode in [ProcessingMode.STANDARD, ProcessingMode.DEEP, ProcessingMode.SHADOW_ONLY]:
                shadow_out = self.shadow_dimension.analyze(user_input, state_enum)
                insights["shadow"] = asdict(shadow_out) if shadow_out else None
            
            # Log dimensional analysis
            self.audit.log(
                level=AuditLevel.INFO,
                category=AuditCategory.DIMENSION_ANALYSIS,
                operation="dimensional_analysis",
                description=f"Dimensional analysis completed (mode: {mode.value})",
                details={"mode": mode.value, "recovery_state": recovery_state},
                session_id=context.session_id,
                agent_name=self.name,
                recovery_state=recovery_state
            )
            
        except Exception as e:
            self.logger.error(f"Dimensional analysis error: {e}")
            insights["error"] = str(e)
        
        return insights
    
    def _generate_response(
        self,
        user_input: str,
        discernment_result: DiscernmentResult,
        constitutional_result: Dict[str, Any],
        dimension_insights: Dict[str, Any],
        recovery_state: Optional[str],
        mode: ProcessingMode,
        context: ProcessingContext
    ) -> AgentResponse:
        """Generate final agent response."""
        # Get state token for session
        state_token = None
        if self.enable_states and context.session_id in self.state_machines:
            state_token = self.state_machines[context.session_id].to_token()
        
        # Extract clarity scores from dimension insights
        clarity_scores = {
            "logical": dimension_insights.get("logical", {}).get("confidence", 0.0) 
                      if dimension_insights.get("logical") else 0.0,
            "emotional": dimension_insights.get("emotional", {}).get("confidence", 0.0) 
                        if dimension_insights.get("emotional") else 0.0,
            "shadow": dimension_insights.get("shadow", {}).get("confidence", 0.0) 
                     if dimension_insights.get("shadow") else 0.0,
            "overall": 0.7,  # Default overall confidence
        }
        
        # Calculate overall confidence
        if clarity_scores["logical"] or clarity_scores["emotional"] or clarity_scores["shadow"]:
            non_zero_scores = [s for s in [clarity_scores["logical"], clarity_scores["emotional"], 
                                         clarity_scores["shadow"]] if s > 0]
            if non_zero_scores:
                clarity_scores["overall"] = sum(non_zero_scores) / len(non_zero_scores)
        
        # Generate response message
        if not constitutional_result["allowed"]:
            message = self._generate_boundary_response(constitutional_result)
            intent = "BOUNDARY"
            emotion = "CAUTIOUS"
        elif mode == ProcessingMode.CRISIS:
            message = self._generate_crisis_response(user_input, recovery_state)
            intent = "GROUNDING"
            emotion = "CALM"
        else:
            # Generate appropriate response based on dimensions
            message = self._generate_clarity_response(
                user_input, dimension_insights, recovery_state, mode
            )
            intent = discernment_result.intent.value
            emotion = self._determine_emotion(intent, recovery_state, clarity_scores)
        
        # Create response object
        response = AgentResponse(
            message=message,
            intent=intent,
            emotion=emotion,
            confidence=clarity_scores["overall"],
            clarity_scores=clarity_scores,
            recovery_state=recovery_state or "UNKNOWN",
            processing_time_ms=0.0,  # Will be updated by caller
            session_id=context.session_id,
            user_state_token=state_token or {},
            dimension_insights=dimension_insights,
            constitutional_check=constitutional_result,
            metadata={
                "processing_mode": mode.value,
                "discernment_result": asdict(discernment_result),
                "input_preview": user_input[:100],
                "response_generated": datetime.now().isoformat(),
            }
        )
        
        return response
    
    def _generate_boundary_response(self, constitutional_result: Dict[str, Any]) -> str:
        """Generate response when constitutional boundaries are triggered."""
        violations = constitutional_result.get("violations", [])
        if violations:
            rule_names = [v.get("rule_name", "boundary") for v in violations[:2]]
            return (
                f"I need to maintain some boundaries here. "
                f"This touches on principles like {', '.join(rule_names)}. "
                f"Let's approach this from a different angle that respects those boundaries."
            )
        
        return (
            "I need to apply some boundaries here to ensure we're working safely and ethically. "
            "Let's reframe this in a way that aligns with ethical guidelines."
        )
    
    def _generate_crisis_response(self, user_input: str, recovery_state: Optional[str]) -> str:
        """Generate response for crisis mode."""
        return (
            "I hear this feels overwhelming. Let's focus on grounding first. "
            "Take a deep breath. We can work through this step by step. "
            "The most important thing right now is stabilization."
        )
    
    def _generate_clarity_response(
        self,
        user_input: str,
        dimension_insights: Dict[str, Any],
        recovery_state: Optional[str],
        mode: ProcessingMode
    ) -> str:
        """Generate clarity-focused response."""
        # Extract messages from dimensions
        messages = []
        
        if dimension_insights.get("emotional") and dimension_insights["emotional"].get("message"):
            messages.append(dimension_insights["emotional"]["message"])
        
        if dimension_insights.get("logical") and dimension_insights["logical"].get("message"):
            messages.append(dimension_insights["logical"]["message"])
        
        if dimension_insights.get("shadow") and dimension_insights["shadow"].get("message"):
            messages.append(f"On a deeper level: {dimension_insights['shadow']['message']}")
        
        if messages:
            # Combine messages intelligently
            if len(messages) == 1:
                return messages[0]
            elif len(messages) >= 2:
                return f"{messages[0]} {messages[1]}"
        
        # Fallback response
        recovery_phrases = {
            "CRISIS": "This feels urgent. Let's focus on what's most important right now.",
            "AWARENESS": "I notice you're becoming aware of something significant.",
            "HONESTY": "There's courage in this honesty. Let's sit with what's true.",
            "RECONSTRUCTION": "This seems like a rebuilding moment. What's one small step?",
            "INTEGRATION": "I see integration happening. How does this fit together?",
            "PURPOSE": "This feels purposeful. What direction is emerging?",
        }
        
        if recovery_state and recovery_state in recovery_phrases:
            return recovery_phrases[recovery_state]
        
        return "I hear you. Let's explore this together to find clarity."
    
    def _determine_emotion(
        self, 
        intent: str, 
        recovery_state: Optional[str], 
        clarity_scores: Dict[str, float]
    ) -> str:
        """Determine appropriate emotional tone for response."""
        if intent == "BOUNDARY" or intent == "CRISIS":
            return "CALM"
        elif intent == "GROUNDING":
            return "STEADY"
        elif recovery_state == "CRISIS":
            return "CALM"
        elif recovery_state == "PURPOSE":
            return "CONFIDENT"
        elif clarity_scores.get("shadow", 0) > 0.7:
            return "REFLECTIVE"
        elif clarity_scores.get("emotional", 0) > 0.7:
            return "EMPATHETIC"
        else:
            return "FOCUSED"
    
    def _store_in_memory(
        self,
        user_input: str,
        response: AgentResponse,
        discernment_result: DiscernmentResult,
        recovery_state: Optional[str],
        context: ProcessingContext
    ) -> Optional[MemoryEntry]:
        """Store interaction in memory."""
        try:
            entry = self.memory.store(
                input_text=user_input,
                user_type=discernment_result.user_type.value,
                decision=response.intent,
                metadata={
                    "response": response.message,
                    "recovery_state": recovery_state,
                    "clarity_scores": response.clarity_scores,
                    "session_id": context.session_id,
                    "processing_mode": context.mode.value if context.mode else "STANDARD",
                }
            )
            return entry
        except Exception as e:
            self.logger.error(f"Memory storage error: {e}")
            return None
    
    def _log_to_audit(
        self,
        user_input: str,
        response: AgentResponse,
        discernment_result: DiscernmentResult,
        constitutional_result: Dict[str, Any],
        context: ProcessingContext
    ) -> None:
        """Log interaction to audit trail."""
        self.audit.log_user_interaction(
            user_input=user_input,
            response=response.message,
            user_id=context.user_id,
            session_id=context.session_id,
            agent_name=self.name,
            recovery_state=response.recovery_state,
            clarity_scores=response.clarity_scores
        )
    
    def _update_metrics(self, response: AgentResponse, processing_time_ms: float) -> None:
        """Update agent metrics."""
        with self._lock:
            self.metrics.interactions_total += 1
            
            # Reset daily counter if new day
            today = datetime.now().date()
            if self.metrics.last_interaction:
                last_date = datetime.fromisoformat(self.metrics.last_interaction).date()
                if today != last_date:
                    self.metrics.interactions_today = 0
            
            self.metrics.interactions_today += 1
            self.metrics.last_interaction = datetime.now().isoformat()
            
            # Update average processing time
            if self.metrics.avg_processing_time_ms == 0:
                self.metrics.avg_processing_time_ms = processing_time_ms
            else:
                # Exponential moving average
                self.metrics.avg_processing_time_ms = (
                    0.9 * self.metrics.avg_processing_time_ms + 0.1 * processing_time_ms
                )
            
            # Update dimension usage
            for dim, score in response.clarity_scores.items():
                if dim in ["logical", "emotional", "shadow"] and score > 0:
                    self.metrics.dimension_usage[dim] += 1
            
            # Update state distribution
            state = response.recovery_state
            if state:
                self.metrics.state_distribution[state] = (
                    self.metrics.state_distribution.get(state, 0) + 1
                )
    
    def _create_error_response(
        self, 
        error: Exception, 
        session_id: str,
        context: ProcessingContext
    ) -> AgentResponse:
        """Create error response when processing fails."""
        return AgentResponse(
            message=(
                "I encountered an error processing your request. "
                "Please try again or rephrase your input."
            ),
            intent="ERROR",
            emotion="NEUTRAL",
            confidence=0.0,
            clarity_scores={"overall": 0.0},
            recovery_state="UNKNOWN",
            processing_time_ms=0.0,
            session_id=session_id,
            user_state_token={},
            dimension_insights={"error": str(error)},
            constitutional_check={"allowed": False, "decision": "ERROR"},
            metadata={
                "error": str(error),
                "error_type": error.__class__.__name__,
                "timestamp": datetime.now().isoformat(),
            }
        )
    
    # Public API methods
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status information."""
        with self._lock:
            return {
                "name": self.name,
                "status": self.status.value,
                "processing_count": self._processing_count,
                "active_sessions": len(self.active_sessions),
                "total_sessions": len(self.sessions),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "components": {
                    "dimensions": self.enable_dimensions,
                    "states": self.enable_states,
                    "llm": self.enable_llm,
                },
                "processing_mode": self.processing_mode.value,
                "start_time": self.start_time.isoformat(),
            }
    
    def get_metrics(self) -> AgentMetrics:
        """Get agent metrics."""
        with self._lock:
            return self.metrics
    
    def get_health(self) -> Dict[str, Any]:
        """Get agent health report."""
        return self.health.get_health_report()
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific session."""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id].copy()
                
                # Add state information if available
                if self.enable_states and session_id in self.state_machines:
                    session["state"] = self.state_machines[session_id].get_state_summary()
                
                # Add memory entries for this session
                memory_entries = self.memory.retrieve(
                    filters={"metadata.session_id": session_id},
                    limit=10
                )
                session["recent_memory"] = [
                    {"input": e.input_text[:100], "decision": e.decision, "timestamp": e.timestamp}
                    for e in memory_entries
                ]
                
                return session
            return None
    
    def end_session(self, session_id: str) -> bool:
        """End a specific session."""
        with self._lock:
            if session_id in self.sessions:
                # Log session end
                self.audit.log(
                    level=AuditLevel.INFO,
                    category=AuditCategory.SYSTEM,
                    operation="session_end",
                    description=f"Session ended: {session_id[:8]}...",
                    details={
                        "session_id": session_id,
                        "interaction_count": self.sessions[session_id].get("interaction_count", 0),
                        "duration_seconds": (
                            datetime.now() - datetime.fromisoformat(
                                self.sessions[session_id]["created"]
                            )
                        ).total_seconds(),
                    },
                    session_id=session_id,
                    agent_name=self.name
                )
                
                # Clean up session
                del self.sessions[session_id]
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                if self.enable_states and session_id in self.state_machines:
                    del self.state_machines[session_id]
                
                self.logger.info(f"Session ended: {session_id[:8]}...")
                return True
            
            return False
    
    def shutdown(self) -> None:
        """Gracefully shutdown the agent."""
        self.status = AgentStatus.SHUTTING_DOWN
        self.logger.info("Agent shutdown initiated")
        
        # Log shutdown
        self.audit.log(
            level=AuditLevel.INFO,
            category=AuditCategory.SYSTEM,
            operation="agent_shutdown",
            description=f"Agent '{self.name}' shutting down",
            details={
                "total_interactions": self.metrics.interactions_total,
                "active_sessions": len(self.active_sessions),
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            },
            agent_name=self.name
        )
        
        # Perform cleanup
        self._cleanup_expired_sessions()
        
        self.logger.info("Agent shutdown complete")
    
    # Legacy method for backward compatibility
    def process_input(self, user_input: str) -> str:
        """
        Legacy method for backward compatibility.
        
        Args:
            user_input: User input text
            
        Returns:
            Simple response string
        """
        context = ProcessingContext(session_id="legacy_" + str(uuid4()))
        response = self.process(user_input, context)
        return response.message