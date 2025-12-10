"""
Quantum Adapter for BLUX-cA - Integration with BLUX quantum CLI.

Provides CLI command definitions, help text, and entrypoint metadata
for the BLUX quantum command-line interface.
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

import typer
from typer.models import CommandInfo, TyperInfo

from ca.cli import get_app as get_ca_app
from ca.core.audit import AuditTrail, AuditLevel, AuditCategory
from ca.core.constitution import ConstitutionEngine
from ca.core.discernment import DiscernmentCompass
from ca.core.reflection import ReflectionEngine
from ca.core_agent import BLUXAgent, ProcessingContext

# Try to import optional components
try:
    from ca.bq_cli import BQCliAdapter, quick_reflect
    BQ_CLI_AVAILABLE = True
except ImportError:
    BQ_CLI_AVAILABLE = False
    BQCliAdapter = None
    quick_reflect = None

try:
    from ca.doctrine_adapter import DoctrineAdapter, create_doctrine_adapter
    DOCTRINE_AVAILABLE = True
except ImportError:
    DOCTRINE_AVAILABLE = False
    DoctrineAdapter = None
    create_doctrine_adapter = None

try:
    from ca.guard_adapter import GuardAdapter, create_guard_adapter
    GUARD_AVAILABLE = True
except ImportError:
    GUARD_AVAILABLE = False
    GuardAdapter = None
    create_guard_adapter = None

try:
    from ca.lite_adapter import LiteAdapter, create_lite_adapter
    LITE_AVAILABLE = True
except ImportError:
    LITE_AVAILABLE = False
    LiteAdapter = None
    create_lite_adapter = None


class CommandCategory(str, Enum):
    """Categories for CLI commands."""
    CORE = "CORE"              # Core BLUX-cA functionality
    ANALYSIS = "ANALYSIS"      # Analysis and reflection
    SAFETY = "SAFETY"          # Safety and guardrails
    ADMIN = "ADMIN"            # Administration and monitoring
    INTEGRATION = "INTEGRATION" # External integrations
    DEVELOPMENT = "DEVELOPMENT" # Development and debugging
    DATA = "DATA"              # Data management


@dataclass
class CommandMetadata:
    """Metadata for a CLI command."""
    name: str                    # Command name
    description: str             # Command description
    category: CommandCategory    # Command category
    aliases: List[str] = field(default_factory=list)  # Command aliases
    requires_auth: bool = False  # Whether command requires authentication
    hidden: bool = False         # Whether command is hidden from help
    experimental: bool = False   # Whether command is experimental
    version: str = "1.0"         # Command version
    dependencies: List[str] = field(default_factory=list)  # Required dependencies
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['category'] = self.category.value
        return data


@dataclass
class AdapterStatus:
    """Status of the quantum adapter."""
    initialized: bool = False
    app_loaded: bool = False
    commands_registered: int = 0
    components_available: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    initialized_at: Optional[str] = None


class QuantumAdapter:
    """
    Adapter for `bluxq ca` commands.
    
    Provides entrypoint metadata, command definitions, and integration
    with the BLUX quantum command-line interface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize quantum adapter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize Typer app
        self.app = typer.Typer(
            name="ca",
            help="BLUX-cA (Clarity Agent) - Logical, Emotional, and Shadow Clarity",
            add_completion=False,
            no_args_is_help=True,
            context_settings={"help_option_names": ["-h", "--help"]},
        )
        
        # Component availability
        self.components_available = {
            "bq_cli": BQ_CLI_AVAILABLE,
            "doctrine": DOCTRINE_AVAILABLE,
            "guard": GUARD_AVAILABLE,
            "lite": LITE_AVAILABLE,
        }
        
        # Command registry
        self.commands: Dict[str, CommandMetadata] = {}
        self.command_handlers: Dict[str, Callable] = {}
        
        # Initialize status
        self.status = AdapterStatus(
            components_available=self.components_available.copy(),
            initialized_at=datetime.now().isoformat(),
        )
        
        # Register commands
        self._register_commands()
        
        self.status.initialized = True
        self.status.app_loaded = True
        self.status.commands_registered = len(self.commands)
        
        self.logger.info("Quantum adapter initialized")
    
    def _register_commands(self) -> None:
        """Register all CLI commands."""
        # Core commands
        self._register_core_commands()
        
        # Analysis commands
        self._register_analysis_commands()
        
        # Safety commands
        self._register_safety_commands()
        
        # Admin commands
        self._register_admin_commands()
        
        # Integration commands (if available)
        if BQ_CLI_AVAILABLE:
            self._register_bq_commands()
        
        if DOCTRINE_AVAILABLE:
            self._register_doctrine_commands()
        
        if GUARD_AVAILABLE:
            self._register_guard_commands()
        
        if LITE_AVAILABLE:
            self._register_lite_commands()
        
        # Development commands
        self._register_development_commands()
        
        # Data commands
        self._register_data_commands()
    
    def _register_core_commands(self) -> None:
        """Register core BLUX-cA commands."""
        
        @self.app.command(
            name="process",
            help="Process text through BLUX-cA",
            rich_help_panel="Core Commands"
        )
        def process_command(
            text: str = typer.Argument(..., help="Text to process"),
            mode: str = typer.Option("standard", "--mode", "-m", 
                                    help="Processing mode (standard, fast, deep, crisis)"),
            session_id: Optional[str] = typer.Option(None, "--session", "-s", 
                                                   help="Session ID"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
            debug: bool = typer.Option(False, "--debug", help="Enable debug output"),
        ):
            """Process text through the full BLUX-cA pipeline."""
            try:
                # Initialize agent
                agent = BLUXAgent()
                
                # Create processing context
                context = ProcessingContext(
                    session_id=session_id or f"cli_{datetime.now().timestamp()}",
                    mode=mode.upper()
                )
                
                # Process text
                response = agent.process(text, context=context)
                
                # Format output
                if output_format == "json":
                    import json
                    result = {
                        "input": text,
                        "response": response.message,
                        "intent": response.intent,
                        "emotion": response.emotion,
                        "confidence": response.confidence,
                        "recovery_state": response.recovery_state,
                        "session_id": context.session_id,
                        "processing_time_ms": response.processing_time_ms,
                    }
                    if debug:
                        result["debug"] = {
                            "clarity_scores": response.clarity_scores,
                            "user_state_token": response.user_state_token,
                            "dimensional_insights": response.dimensional_insights,
                        }
                    typer.echo(json.dumps(result, indent=2))
                else:
                    # Text output
                    typer.echo(f"Input: {text}")
                    typer.echo(f"Response: {response.message}")
                    typer.echo(f"Intent: {response.intent} | Emotion: {response.emotion}")
                    typer.echo(f"Confidence: {response.confidence:.2f} | State: {response.recovery_state}")
                    
                    if debug:
                        typer.echo("\n" + "="*40)
                        typer.echo("DEBUG INFO:")
                        typer.echo(f"Session ID: {context.session_id}")
                        typer.echo(f"Processing time: {response.processing_time_ms:.1f}ms")
                        typer.echo(f"Clarity scores: {response.clarity_scores}")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                if debug:
                    import traceback
                    typer.echo(traceback.format_exc(), err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "process",
            "Process text through BLUX-cA",
            CommandCategory.CORE,
            aliases=["p", "run"]
        )
        
        @self.app.command(
            name="interactive",
            help="Start interactive BLUX-cA session",
            rich_help_panel="Core Commands"
        )
        def interactive_command(
            session_id: Optional[str] = typer.Option(None, "--session", "-s", 
                                                   help="Session ID"),
            debug: bool = typer.Option(False, "--debug", help="Enable debug output"),
        ):
            """Start an interactive BLUX-cA session."""
            try:
                from ca import clarity_interactive_mode
                clarity_interactive_mode()
            except ImportError:
                typer.echo("Interactive mode not available. Using fallback.", err=True)
                
                # Simple interactive fallback
                agent = BLUXAgent()
                session = session_id or f"interactive_{datetime.now().timestamp()}"
                
                typer.echo("BLUX-cA Interactive Mode (Fallback)")
                typer.echo("Type 'exit' to quit, 'debug' to toggle debug mode")
                typer.echo("="*40)
                
                debug_mode = False
                context = ProcessingContext(session_id=session)
                
                while True:
                    try:
                        user_input = typer.prompt("> ").strip()
                        
                        if user_input.lower() in ["exit", "quit"]:
                            typer.echo("Goodbye!")
                            break
                        
                        if user_input.lower() == "debug":
                            debug_mode = not debug_mode
                            typer.echo(f"Debug mode {'enabled' if debug_mode else 'disabled'}")
                            continue
                        
                        if not user_input:
                            continue
                        
                        response = agent.process(user_input, context=context)
                        typer.echo(f"\nBLUX-cA: {response.message}")
                        
                        if debug_mode:
                            typer.echo(f"[Debug: {response.intent}/{response.emotion}, "
                                     f"Confidence: {response.confidence:.2f}, "
                                     f"State: {response.recovery_state}]")
                        
                        typer.echo()
                        
                    except (KeyboardInterrupt, EOFError):
                        typer.echo("\n\nSession ended.")
                        break
                    except Exception as e:
                        typer.echo(f"Error: {e}", err=True)
                        if debug:
                            import traceback
                            typer.echo(traceback.format_exc(), err=True)
            
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "interactive",
            "Start interactive BLUX-cA session",
            CommandCategory.CORE,
            aliases=["chat", "repl"]
        )
    
    def _register_analysis_commands(self) -> None:
        """Register analysis and reflection commands."""
        
        @self.app.command(
            name="reflect",
            help="Reflect on text using reflection engine",
            rich_help_panel="Analysis Commands"
        )
        def reflect_command(
            text: str = typer.Argument(..., help="Text to reflect on"),
            depth: int = typer.Option(3, "--depth", "-d", help="Reflection depth"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Reflect on text using the reflection engine."""
            try:
                reflection = ReflectionEngine(depth=depth)
                insight = reflection.reflect(text)
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps(asdict(insight), indent=2))
                else:
                    typer.echo(f"Reflection on: {text}")
                    typer.echo("="*40)
                    typer.echo(f"Summary: {insight.summary}")
                    typer.echo(f"Depth: {insight.depth}")
                    typer.echo(f"Confidence: {insight.confidence:.2f}")
                    typer.echo("\nWhy Chain:")
                    for i, step in enumerate(insight.why_chain, 1):
                        typer.echo(f"  {i}. {step}")
                    if insight.actionable:
                        typer.echo(f"\nActionable: {insight.actionable}")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "reflect",
            "Reflect on text using reflection engine",
            CommandCategory.ANALYSIS
        )
        
        @self.app.command(
            name="discern",
            help="Discern intent and user type from text",
            rich_help_panel="Analysis Commands"
        )
        def discern_command(
            text: str = typer.Argument(..., help="Text to analyze"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Discern intent and user type from text."""
            try:
                compass = DiscernmentCompass()
                result = compass.classify(text)
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps(asdict(result), indent=2))
                else:
                    typer.echo(f"Text: {text}")
                    typer.echo("="*40)
                    typer.echo(f"User Type: {result.user_type.value}")
                    typer.echo(f"Intent: {result.intent.value}")
                    typer.echo(f"Confidence: {result.confidence:.2f}")
                    if result.metadata:
                        typer.echo("\nMetadata:")
                        for key, value in result.metadata.items():
                            typer.echo(f"  {key}: {value}")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "discern",
            "Discern intent and user type from text",
            CommandCategory.ANALYSIS
        )
        
        @self.app.command(
            name="analyze-dimensions",
            help="Analyze text through all clarity dimensions",
            rich_help_panel="Analysis Commands"
        )
        def analyze_dimensions_command(
            text: str = typer.Argument(..., help="Text to analyze"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Analyze text through logical, emotional, and shadow dimensions."""
            try:
                from ca.core.dimensions import LogicalClarity, EmotionalClarity, ShadowClarity
                from ca.core.states import RecoveryState
                
                # Initialize dimensions
                logical = LogicalClarity()
                emotional = EmotionalClarity()
                shadow = ShadowClarity()
                
                # Analyze with each dimension
                state = RecoveryState.AWARENESS  # Default state
                
                logical_out = logical.analyze(text, state)
                emotional_out = emotional.analyze(text, state)
                shadow_out = shadow.analyze(text, state)
                
                if output_format == "json":
                    import json
                    result = {
                        "logical": asdict(logical_out),
                        "emotional": asdict(emotional_out),
                        "shadow": asdict(shadow_out),
                    }
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Analysis of: {text}")
                    typer.echo("="*40)
                    
                    typer.echo("\n📊 LOGICAL CLARITY:")
                    typer.echo(f"  {logical_out.message}")
                    typer.echo(f"  Intent: {logical_out.intent.value} | "
                             f"Emotion: {logical_out.emotion.value} | "
                             f"Confidence: {logical_out.confidence:.2f}")
                    
                    typer.echo("\n💖 EMOTIONAL CLARITY:")
                    typer.echo(f"  {emotional_out.message}")
                    typer.echo(f"  Intent: {emotional_out.intent.value} | "
                             f"Emotion: {emotional_out.emotion.value} | "
                             f"Confidence: {emotional_out.confidence:.2f}")
                    
                    typer.echo("\n🌑 SHADOW CLARITY:")
                    typer.echo(f"  {shadow_out.message}")
                    typer.echo(f"  Intent: {shadow_out.intent.value} | "
                             f"Emotion: {shadow_out.emotion.value} | "
                             f"Confidence: {shadow_out.confidence:.2f}")
                
            except ImportError as e:
                typer.echo(f"Dimensions not available: {e}", err=True)
                raise typer.Exit(code=1)
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "analyze-dimensions",
            "Analyze text through all clarity dimensions",
            CommandCategory.ANALYSIS,
            aliases=["dimensions", "analyze"]
        )
    
    def _register_safety_commands(self) -> None:
        """Register safety and guardrail commands."""
        
        @self.app.command(
            name="check-constitution",
            help="Check text against constitutional rules",
            rich_help_panel="Safety Commands"
        )
        def check_constitution_command(
            text: str = typer.Argument(..., help="Text to check"),
            mode: str = typer.Option("strict", "--mode", "-m", 
                                   help="Constitution mode (strict, balanced, permissive)"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Check text against constitutional rules."""
            try:
                from ca.core.discernment import DiscernmentCompass
                
                compass = DiscernmentCompass()
                constitution = ConstitutionEngine(mode=mode)
                
                discernment = compass.classify(text)
                
                context = {
                    "user_input": text,
                    "user_type": discernment.user_type.value,
                    "intent": discernment.intent.value,
                    "recovery_state": "UNKNOWN",
                }
                
                action = {
                    "type": "constitution_check",
                    "text": text,
                    "user_type": discernment.user_type.value,
                }
                
                verdict = constitution.evaluate(action, context)
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps(verdict, indent=2))
                else:
                    typer.echo(f"Constitutional Check: {text}")
                    typer.echo("="*40)
                    typer.echo(f"Decision: {verdict.get('decision', 'UNKNOWN')}")
                    typer.echo(f"Allowed: {verdict.get('allowed', False)}")
                    
                    violations = verdict.get('violations', [])
                    if violations:
                        typer.echo(f"\nViolations ({len(violations)}):")
                        for v in violations[:3]:  # Show first 3
                            typer.echo(f"  • {v.get('rule_name', 'Unknown')}: "
                                     f"{v.get('description', 'No description')}")
                    
                    warnings = verdict.get('warnings', [])
                    if warnings:
                        typer.echo(f"\nWarnings ({len(warnings)}):")
                        for w in warnings[:3]:
                            typer.echo(f"  • {w.get('rule_name', 'Unknown')}")
                    
                    if not violations and not warnings:
                        typer.echo("\n✓ No constitutional violations detected")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "check-constitution",
            "Check text against constitutional rules",
            CommandCategory.SAFETY,
            aliases=["constitution", "check"]
        )
    
    def _register_admin_commands(self) -> None:
        """Register administration and monitoring commands."""
        
        @self.app.command(
            name="status",
            help="Get BLUX-cA system status",
            rich_help_panel="Admin Commands"
        )
        def status_command(
            detailed: bool = typer.Option(False, "--detailed", "-d", 
                                        help="Show detailed status"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Get BLUX-cA system status."""
            try:
                from ca.core_agent import BLUXAgent
                
                agent = BLUXAgent()
                status = agent.get_status()
                health = agent.get_health()
                metrics = agent.get_metrics()
                
                if output_format == "json":
                    import json
                    result = {
                        "status": status,
                        "health": health,
                        "metrics": asdict(metrics),
                        "quantum_adapter": self.status,
                    }
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo("BLUX-cA System Status")
                    typer.echo("="*40)
                    
                    typer.echo(f"Agent: {status.get('name', 'Unknown')}")
                    typer.echo(f"Status: {status.get('status', 'Unknown')}")
                    typer.echo(f"Uptime: {status.get('uptime_seconds', 0):.0f} seconds")
                    typer.echo(f"Active Sessions: {status.get('active_sessions', 0)}")
                    typer.echo(f"Processing Count: {status.get('processing_count', 0)}")
                    
                    if detailed:
                        typer.echo("\nHealth Check:")
                        health_status = health.get('status', {})
                        for component, healthy in health_status.items():
                            status_icon = "✓" if healthy else "✗"
                            typer.echo(f"  {status_icon} {component}")
                        
                        typer.echo(f"\nMetrics:")
                        typer.echo(f"  Total Interactions: {metrics.interactions_total}")
                        typer.echo(f"  Avg Processing Time: {metrics.avg_processing_time_ms:.1f}ms")
                        
                        if metrics.dimension_usage:
                            typer.echo(f"  Dimension Usage:")
                            for dim, count in metrics.dimension_usage.items():
                                typer.echo(f"    • {dim}: {count}")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "status",
            "Get BLUX-cA system status",
            CommandCategory.ADMIN,
            aliases=["info", "health"]
        )
        
        @self.app.command(
            name="audit",
            help="View audit trail",
            rich_help_panel="Admin Commands"
        )
        def audit_command(
            recent: int = typer.Option(10, "--recent", "-r", help="Number of recent entries"),
            level: Optional[str] = typer.Option(None, "--level", "-l", 
                                              help="Filter by level (DEBUG, INFO, WARNING, ERROR)"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """View audit trail entries."""
            try:
                audit = AuditTrail()
                
                if level:
                    from ca.core.audit import AuditLevel
                    entries = audit.get_entries_by_level(AuditLevel(level), limit=recent)
                else:
                    entries = audit.get_recent_entries(limit=recent)
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps([e.to_dict() for e in entries], indent=2))
                else:
                    if not entries:
                        typer.echo("No audit entries found.")
                        return
                    
                    typer.echo(f"Audit Trail (Last {len(entries)} entries)")
                    typer.echo("="*60)
                    
                    for entry in entries:
                        timestamp = entry.timestamp.split('T')[1].split('.')[0]  # Just time
                        typer.echo(f"[{timestamp}] {entry.level}: {entry.component}/{entry.operation}")
                        typer.echo(f"  {entry.description[:80]}...")
                        typer.echo()
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "audit",
            "View audit trail",
            CommandCategory.ADMIN,
            aliases=["logs", "history"]
        )
    
    def _register_bq_commands(self) -> None:
        """Register BQ CLI integration commands."""
        if not BQ_CLI_AVAILABLE:
            return
        
        @self.app.command(
            name="bq-reflect",
            help="Reflect using bq-cli integration",
            rich_help_panel="Integration Commands"
        )
        def bq_reflect_command(
            text: str = typer.Argument(..., help="Text to reflect on"),
            koans: Optional[str] = typer.Option(None, "--koans", "-k", 
                                              help="Comma-separated list of koans"),
            mode: str = typer.Option("standard", "--mode", "-m", 
                                   help="Reflection mode (standard, deep, koan)"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Reflect on text using bq-cli integration."""
            try:
                adapter = BQCliAdapter()
                
                koan_list = None
                if koans:
                    koan_list = [k.strip() for k in koans.split(",")]
                
                from ca.bq_cli import ReflectionMode
                reflection_mode = ReflectionMode(mode.lower())
                
                result = adapter.run_reflection(
                    prompt=text,
                    koans=koan_list,
                    mode=reflection_mode
                )
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps(result.to_dict(), indent=2))
                else:
                    typer.echo(f"BQ Reflection: {text}")
                    typer.echo("="*40)
                    typer.echo(result.reflection_text)
                    typer.echo(f"\nMode: {result.mode.value} | "
                             f"Confidence: {result.confidence:.2f}")
                    
                    if result.insights:
                        typer.echo(f"\nKey Insights ({len(result.insights)}):")
                        for i, insight in enumerate(result.insights[:3], 1):
                            insight_text = insight.get('text', str(insight))[:100]
                            typer.echo(f"  {i}. {insight_text}...")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "bq-reflect",
            "Reflect using bq-cli integration",
            CommandCategory.INTEGRATION,
            dependencies=["bq_cli"]
        )
    
    def _register_doctrine_commands(self) -> None:
        """Register doctrine integration commands."""
        if not DOCTRINE_AVAILABLE:
            return
        
        @self.app.command(
            name="doctrine",
            help="Fetch and apply doctrine policies",
            rich_help_panel="Integration Commands"
        )
        def doctrine_command(
            policy_id: Optional[str] = typer.Option(None, "--policy", "-p", 
                                                  help="Specific policy ID to fetch"),
            sync: bool = typer.Option(False, "--sync", "-s", 
                                    help="Sync with doctrine server"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Fetch and apply doctrine policies."""
            try:
                adapter = create_doctrine_adapter()
                
                if sync:
                    success = adapter.sync_policies(force=True)
                    if success:
                        typer.echo("✓ Doctrine policies synced successfully")
                    else:
                        typer.echo("✗ Failed to sync doctrine policies", err=True)
                    return
                
                if policy_id:
                    policy = adapter.fetch_policy(policy_id)
                    if not policy:
                        typer.echo(f"Policy not found: {policy_id}", err=True)
                        raise typer.Exit(code=1)
                    
                    policies = [policy]
                else:
                    # Fetch all active policies
                    from ca.doctrine_adapter import DoctrineQuery
                    query = DoctrineQuery(active_only=True)
                    policies = adapter.fetch_policies(query)
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps([p.to_dict() for p in policies], indent=2))
                else:
                    typer.echo(f"Doctrine Policies ({len(policies)})")
                    typer.echo("="*60)
                    
                    for policy in policies[:10]:  # Show first 10
                        typer.echo(f"\n{policy.name} ({policy.category.value})")
                        typer.echo(f"  {policy.description}")
                        typer.echo(f"  Priority: {policy.priority} | "
                                 f"Enforcement: {policy.enforcement_level}")
                        if policy.content:
                            typer.echo(f"  Content: {policy.content[:80]}...")
                
                if len(policies) > 10:
                    typer.echo(f"\n... and {len(policies) - 10} more policies")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "doctrine",
            "Fetch and apply doctrine policies",
            CommandCategory.INTEGRATION,
            dependencies=["doctrine_adapter"]
        )
    
    def _register_guard_commands(self) -> None:
        """Register guard integration commands."""
        if not GUARD_AVAILABLE:
            return
        
        @self.app.command(
            name="guard-check",
            help="Check content against guardrails",
            rich_help_panel="Integration Commands"
        )
        def guard_check_command(
            text: str = typer.Argument(..., help="Text to check"),
            scope: str = typer.Option("input", "--scope", "-s", 
                                    help="Check scope (input, output, processing)"),
            notify: bool = typer.Option(False, "--notify", "-n", 
                                      help="Notify BLUX-Guard of violations"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Check content against guardrails."""
            try:
                from ca.guard_adapter import GuardScope, create_guard_adapter
                
                adapter = create_guard_adapter()
                scope_enum = GuardScope(scope.upper())
                
                result = adapter.check_and_notify(
                    content=text,
                    scope=scope_enum,
                    notify_guard=notify,
                )
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Guard Check: {text}")
                    typer.echo("="*40)
                    typer.echo(f"Allowed: {result.get('allowed', False)}")
                    typer.echo(f"Action: {result.get('action', 'UNKNOWN')}")
                    
                    violations = result.get('violations', [])
                    if violations:
                        typer.echo(f"\nViolations ({len(violations)}):")
                        for v in violations:
                            typer.echo(f"  • {v.get('guardrail_name', 'Unknown')}: "
                                     f"{v.get('severity', 'MEDIUM')} - "
                                     f"{v.get('description', 'No description')}")
                    
                    warnings = result.get('warnings', [])
                    if warnings:
                        typer.echo(f"\nWarnings ({len(warnings)}):")
                        for w in warnings:
                            typer.echo(f"  • {w.get('guardrail_name', 'Unknown')}")
                    
                    if not violations and not warnings:
                        typer.echo("\n✓ No guardrail violations detected")
                    
                    if notify:
                        typer.echo(f"\n✓ Notified BLUX-Guard: {result.get('guard_notified', False)}")
                
            except Exception as e:
                typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(code=1)
        
        self._register_command_metadata(
            "guard-check",
            "Check content against guardrails",
            CommandCategory.INTEGRATION,
            dependencies=["guard_adapter"],
            aliases=["guard"]
        )
    
    def _register_lite_commands(self) -> None:
        """Register lite adapter commands."""
        if not LITE_AVAILABLE:
            return
        
        @self.app.command(
            name="lite-evaluate",
            help="Evaluate text using Lite adapter",
            rich_help_panel="Integration Commands"
        )
        def lite_evaluate_command(
            text: str = typer.Argument(..., help="Text to evaluate"),
            mode: str = typer.Option("standard", "--mode", "-m", 
                                   help="Evaluation mode (fast, standard, deep, crisis)"),
            output_format: str = typer.Option("text", "--format", "-f", 
                                            help="Output format (text, json)"),
        ):
            """Evaluate text using Lite adapter."""
            try:
                from ca.lite_adapter import EvaluationMode, create_lite_adapter
                
                adapter = create_lite_adapter()
                eval_mode = EvaluationMode(mode.upper())
                
                result = adapter.evaluate(text, mode=eval_mode)
                
                if output_format == "json":
                    import json
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Lite Evaluation ({mode} mode): {text}")
                    typer.echo("="*40)
                    
                    if "summary" in result:
                        typer.echo(f"Summary: {result['summary']}")
                    
                    if "discernment" in result:
                        disc = result["discernment"]
                        typer.echo(f"\nDiscernment: {disc.get('user_type', 'Unknown')} "
                                 f"with {disc.get('intent', 'Unknown')} intent "
                                 f"(confidence: {disc.get('confidence', 0):.2f})")
                    
                    if "constitutional_verdict" in result:
                        verdict = result["constitutional_verdict"]
                        typer.echo(f"\nConstitutional Verdict: {verdict.get('decision', 'Unknown')}")
                        
                        violations = verdict.get('violations', [])
                        if violations:
                            typer.echo(f"  Violations: {len(violations)}")
                        
                        recommendations = verdict.get('recommendations', [])
                        if recommendations:
                            typer.echo(f"  Recommendations: {len(recommendations)}")
                    
                    if "confidence" in result:
                        typer.echo(f"\nOverall Confidence: {result