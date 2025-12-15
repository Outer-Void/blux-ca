#!/usr/bin/env python3
"""
BLUX-cA :: Unified CLI Entrypoint
Consolidates all CLI functionality into a single entrypoint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import typer

ROOT_DIR = Path(__file__).resolve().parent
for path in [ROOT_DIR, ROOT_DIR / "ca"]:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from ca.core.audit import AuditLog
from ca.core.clarity_engine import ClarityEngine
from ca.core.constitution import ConstitutionEngine
from ca.core.discernment import DiscernmentCompass
from ca.core.perception import PerceptionLayer
from ca.core.reflection import ReflectionEngine
from ca.adaptors.reg import RegistryValidator, RegistrationResult, Capability
from ca.config import load_config
from ca.evaluator.probe_runner import PROBE_SUITES, run_probe_evaluation


def _hash_text(text: str) -> str:
    """Generate SHA256 hash for text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _format_timestamp() -> str:
    """Format current timestamp for display."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clarity_interactive_mode(registration_key: Optional[str] = None) -> None:
    """Run the interactive clarity engine demo with optional registration."""
    engine = ClarityEngine()
    user_state_token: Optional[Dict] = None
    validator = RegistryValidator()
    
    # Validate registration if provided
    registration_status: Optional[RegistrationResult] = None
    if registration_key:
        registration_status = validator.validate(registration_key)
        if not registration_status.valid:
            print(f"Registration failed: {registration_status.reason}")
            print("Continuing with limited capabilities...")
    
    print("=" * 60)
    print("BLUX-cA :: Clarity Agent Interactive Mode")
    print(f"Session started: {_format_timestamp()}")
    
    if registration_status and registration_status.valid:
        print(f"Registration: {registration_status.key_type.upper()}")
        caps = [cap.value for cap in registration_status.capabilities]
        print(f"Capabilities: {len(caps)} available")
    else:
        print("Registration: Limited (unregistered mode)")
    
    print("\nCommands:")
    print("  'exit' or 'quit' - End session")
    print("  'debug' - Toggle debug mode")
    print("  'state' - Show current user state")
    print("  'capabilities' - List available capabilities")
    print("  'help' - Show this help")
    print("  'clear' - Clear screen (if supported)")
    print("-" * 40)

    debug_mode = False
    session_messages = []

    while True:
        try:
            text = input("\n[cA] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended by user.")
            break

        # Command handling
        if text.lower() in {"exit", "quit"}:
            print("Exiting interactive mode.")
            print(f"Session summary: {len(session_messages)} messages processed")
            break

        if text.lower() == "debug":
            debug_mode = not debug_mode
            print(f"Debug mode {'enabled' if debug_mode else 'disabled'}")
            continue

        if text.lower() == "state":
            if user_state_token:
                print("\n" + "=" * 40)
                print("Current User State Token:")
                for key, value in user_state_token.items():
                    print(f"  {key}: {str(value)[:50]}...")
                print("=" * 40)
            else:
                print("No user state token available.")
            continue

        if text.lower() == "capabilities":
            if registration_status and registration_status.valid:
                print("\nAvailable Capabilities:")
                for cap in sorted(registration_status.capabilities, key=lambda c: c.value):
                    print(f"  • {cap.value}")
            else:
                print("No capabilities available in unregistered mode.")
            continue

        if text.lower() == "help":
            print("\nCommands:")
            print("  'exit' or 'quit' - End session")
            print("  'debug' - Toggle debug mode")
            print("  'state' - Show current user state")
            print("  'capabilities' - List available capabilities")
            print("  'help' - Show this help")
            print("  'clear' - Clear screen (if supported)")
            continue

        if text.lower() == "clear":
            print("\n" * 100)  # Simple clear for terminals that support it
            continue

        if not text:
            continue

        # Check capabilities if registered
        if registration_status and registration_status.valid:
            # Check if any capabilities are expired
            if registration_status.is_expired():
                print("Registration has expired. Please renew your key.")
                continue
            
            # Check for shadow clarity capability if needed
            # (This is a simple heuristic - production would be more sophisticated)
            shadow_keywords = {"shadow", "dark", "hidden", "repressed", "unconscious"}
            if any(keyword in text.lower() for keyword in shadow_keywords):
                if not registration_status.has_capability(Capability.SHADOW_CLARITY):
                    print("Shadow clarity capability required for this query.")
                    print("Please upgrade your registration for full access.")
                    continue

        # Process the input
        try:
            resp = engine.process(text, user_state_token=user_state_token)
            user_state_token = resp.user_state_token
            
            # Format and display response
            print(f"\n[{resp.intent.value if hasattr(resp.intent, 'value') else resp.intent}/"
                  f"{resp.emotion.value if hasattr(resp.emotion, 'value') else resp.emotion}]")
            print(f"{resp.message}")
            
            # Add to session history
            session_messages.append({
                "input": text,
                "response": resp.message,
                "intent": resp.intent,
                "emotion": resp.emotion,
                "timestamp": datetime.now().isoformat()
            })
            
            # Debug information
            if debug_mode:
                print("\n" + "=" * 40)
                print("DEBUG - Full Response Details:")
                print(f"Avatar: {resp.avatar}")
                print(f"Confidence: {resp.confidence if hasattr(resp, 'confidence') else 'N/A'}")
                
                if resp.user_state_token:
                    print("\nUser State Token Keys:")
                    for key in resp.user_state_token.keys():
                        print(f"  - {key}")
                
                print("=" * 40)
                
        except Exception as e:
            print(f"\nError processing input: {str(e)}")
            if debug_mode:
                print("\nTraceback:")
                traceback.print_exc()


def process_single_task(task: str, debug: bool = False, registration_key: Optional[str] = None) -> None:
    """Process a single task through the clarity engine."""
    engine = ClarityEngine()
    validator = RegistryValidator()
    
    # Validate registration if provided
    registration_status: Optional[RegistrationResult] = None
    if registration_key:
        registration_status = validator.validate(registration_key)
        if not registration_status.valid:
            print(f"Registration failed: {registration_status.reason}")
            return
    
    try:
        resp = engine.process(task)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}]")
        print(f"Input: {task}")
        print(f"Response: {resp.message}")
        print(f"Intent: {resp.intent}")
        print(f"Emotion: {resp.emotion}")
        
        if debug:
            print("\n" + "-" * 40)
            print("Full response details:")
            debug_info = {
                "intent": resp.intent.value if hasattr(resp.intent, 'value') else resp.intent,
                "emotion": resp.emotion.value if hasattr(resp.emotion, 'value') else resp.emotion,
                "message": resp.message,
                "avatar": resp.avatar,
            }
            
            if hasattr(resp, 'confidence'):
                debug_info["confidence"] = resp.confidence
            
            if resp.user_state_token:
                debug_info["state_token_keys"] = list(resp.user_state_token.keys())
                debug_info["state_token_sample"] = {
                    k: str(v)[:100] + "..." if len(str(v)) > 100 else v
                    for k, v in list(resp.user_state_token.items())[:3]
                }
            
            print(json.dumps(debug_info, indent=2))
            
            if registration_status:
                print("\nRegistration Status:")
                print(json.dumps(registration_status.to_dict(), indent=2))
                
    except Exception as e:
        print(f"Error processing task: {str(e)}")
        if debug:
            traceback.print_exc()


def process_batch_file(batch_file: str, output_file: Optional[str] = None, 
                      registration_key: Optional[str] = None) -> None:
    """Process a batch of tasks from a file."""
    engine = ClarityEngine()
    validator = RegistryValidator()
    
    # Validate registration if provided
    registration_status: Optional[RegistrationResult] = None
    if registration_key:
        registration_status = validator.validate(registration_key)
        if not registration_status.valid:
            print(f"Registration failed: {registration_status.reason}")
            return
    
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            tasks = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Batch file '{batch_file}' not found.")
        return
    except Exception as e:
        print(f"Error reading batch file: {str(e)}")
        return
    
    if not tasks:
        print("No tasks found in batch file.")
        return
    
    print(f"Processing {len(tasks)} tasks...")
    if registration_status:
        print(f"Registration: {registration_status.key_type.upper()}")
    
    results = []
    successful = 0
    failed = 0
    
    for i, task in enumerate(tasks, 1):
        print(f"\rProcessing {i}/{len(tasks)}...", end="", flush=True)
        
        try:
            resp = engine.process(task)
            result = {
                "task": task,
                "response": resp.message,
                "intent": resp.intent.value if hasattr(resp.intent, 'value') else resp.intent,
                "emotion": resp.emotion.value if hasattr(resp.emotion, 'value') else resp.emotion,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            successful += 1
        except Exception as e:
            result = {
                "task": task,
                "response": f"Error: {str(e)}",
                "intent": "error",
                "emotion": "error",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            failed += 1
        
        results.append(result)
    
    print(f"\n\nProcessing complete: {successful} successful, {failed} failed")
    
    # Output results
    if output_file:
        try:
            output_path = Path(output_file)
            output_data = {
                "metadata": {
                    "source_file": batch_file,
                    "processed_at": datetime.now().isoformat(),
                    "total_tasks": len(tasks),
                    "successful": successful,
                    "failed": failed,
                    "registration": registration_status.to_dict() if registration_status else None
                },
                "results": results
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"Results saved to {output_file} ({output_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"Error saving output file: {str(e)}")
            # Fall back to console output
            output_file = None
    
    if not output_file:
        print("\n" + "=" * 60)
        print("Batch Processing Results:")
        print("=" * 60)
        
        for i, r in enumerate(results[:10], 1):  # Show first 10 results
            print(f"\n{i}. Task: {r['task'][:80]}...")
            print(f"   Response: {r['response'][:100]}...")
            print(f"   Intent: {r['intent']}, Emotion: {r['emotion']}")
        
        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more results")


# Typer CLI functions for advanced features
typer_app = typer.Typer(
    help="BLUX-cA conscious agent core",
    context_settings={"help_option_names": ["-h", "--help"]}
)

@typer_app.command()
def register(
    key: str = typer.Argument(..., help="Registration key to validate"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show detailed information"),
    check_capability: Optional[str] = typer.Option(None, "-c", "--capability", 
                                                   help="Check for specific capability")
) -> None:
    """Validate a registration key and show capabilities."""
    validator = RegistryValidator()
    
    try:
        if check_capability:
            # Try to convert string to Capability enum
            try:
                cap = Capability(check_capability)
                result = validator.validate_with_context(key, {cap})
            except ValueError:
                typer.echo(f"Error: Invalid capability '{check_capability}'")
                typer.echo(f"Valid capabilities: {[c.value for c in Capability]}")
                raise typer.Exit(code=1)
        else:
            result = validator.validate(key)
        
        if verbose:
            typer.echo(json.dumps(result.to_dict(), indent=2))
        else:
            if result.valid:
                typer.echo(f"✓ Registration valid: {result.key_type}")
                typer.echo(f"Capabilities: {len(result.capabilities)}")
                typer.echo(f"Expires: {result.get_remaining_seconds() // 86400:.0f} days remaining")
            else:
                typer.echo(f"✗ Registration invalid: {result.reason}")
        
    except Exception as e:
        typer.echo(f"Error during registration validation: {str(e)}")
        raise typer.Exit(code=1)


@typer_app.command()
def code_eval(
    language: str = typer.Argument(...),
    file: Optional[Path] = typer.Option(None, exists=True),
    snippet: str = typer.Option("", help="Inline code snippet"),
) -> None:
    """Evaluate code (placeholder for future implementation)."""
    typer.echo("Code evaluation feature is under development.")
    typer.echo(f"Language: {language}")
    if file:
        typer.echo(f"File: {file}")
    if snippet:
        typer.echo(f"Snippet: {snippet[:50]}...")


@typer_app.command()
def reflect(
    text: str,
    depth: int = typer.Option(3, help="Number of why-chain iterations.")
) -> None:
    """Run reflection on text."""
    try:
        perception = PerceptionLayer()
        reflection = ReflectionEngine(depth=depth)
        entry = perception.observe(text)
        insight = reflection.reflect(entry.text)
        typer.echo(json.dumps(insight.__dict__, indent=2, ensure_ascii=False))
    except Exception as e:
        typer.echo(f"Error during reflection: {str(e)}")
        raise typer.Exit(code=1)


@typer_app.command(name="eval")
def eval_suite(
    dataset_dir: Path = typer.Option(..., exists=True, file_okay=False, dir_okay=True, resolve_path=True,
                                     help="Path to BLUX-cA dataset directory (with eval/*.jsonl files)."),
    suite: str = typer.Option("all", help=f"Probe suite to run: {sorted(PROBE_SUITES)} or 'all'"),
    output: Optional[Path] = typer.Option(None, help="Optional output report path (defaults to runs/eval_<timestamp>.md).")
) -> None:
    """Run evaluation probes (identity, red_team, capability, doctrine)."""
    try:
        suite_name = suite.lower()
        valid = set(PROBE_SUITES.keys()) | {"all"}
        if suite_name not in valid:
            raise typer.BadParameter(f"Unknown suite '{suite}'. Valid options: {sorted(valid)}")
        report_path = run_probe_evaluation(dataset_dir, suite_name, output)
        typer.echo(f"Evaluation complete. Report written to {report_path}")
    except Exception as e:
        typer.echo(f"Error during evaluation: {str(e)}")
        raise typer.Exit(code=1)


@typer_app.command()
def explain(
    last: bool = typer.Option(False, help="Explain the most recent audit entry."),
    count: int = typer.Option(1, help="Number of recent entries to show.")
) -> None:
    """Explain audit entries."""
    audit = AuditLog()
    if not audit.path.exists():
        typer.echo("No audit history available.")
        raise typer.Exit(code=1)
    
    try:
        lines = audit.path.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            typer.echo("Audit log empty.")
            return
        
        if last:
            show_count = min(count, len(lines))
            typer.echo(f"Last {show_count} audit entries:")
            for i, line in enumerate(lines[-show_count:], 1):
                typer.echo(f"\n{i}. {line}")
        else:
            typer.echo(f"Audit log contains {len(lines)} entries.")
            typer.echo("Use --last to view recent entries.")
            
    except Exception as e:
        typer.echo(f"Error reading audit log: {str(e)}")
        raise typer.Exit(code=1)


@typer_app.command()
def audit_export(
    output: Optional[str] = typer.Option(None, help="Export path."),
    format: str = typer.Option("jsonl", help="Export format: jsonl or json.")
) -> None:
    """Export audit log."""
    audit = AuditLog()
    if not audit.path.exists():
        typer.echo("No audit history available.")
        return
    
    try:
        target = output or f"audit_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        audit_data = audit.path.read_text(encoding="utf-8")
        
        if format.lower() == "json":
            # Convert JSONL to JSON array
            lines = audit_data.strip().splitlines()
            json_data = [json.loads(line) for line in lines if line.strip()]
            with open(target, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        else:
            # Default JSONL format
            with open(target, 'w', encoding='utf-8') as f:
                f.write(audit_data)
        
        typer.echo(f"Audit log exported to {target}")
        
    except Exception as e:
        typer.echo(f"Error exporting audit log: {str(e)}")
        raise typer.Exit(code=1)


@typer_app.command()
def doctrine(text: str, mode: str = typer.Option("strict", help="Evaluation mode")) -> None:
    """Evaluate text against doctrine."""
    try:
        config = load_config()
        compass = DiscernmentCompass()
        constitution = ConstitutionEngine(mode=mode)
        
        insights = [text]
        decision = constitution.evaluate(
            insights=insights,
            intent=compass.classify(text).intent.value
        )
        
        audit = AuditLog()
        record = audit.create_record(
            input_hash=_hash_text(text),
            verdict=decision.decision,
            doctrine_refs=decision.doctrine_refs,
            rationale=decision.reason,
        )
        audit.append(record)
        
        typer.echo(json.dumps(decision.__dict__, indent=2, ensure_ascii=False))
        
    except Exception as e:
        typer.echo(f"Error during doctrine evaluation: {str(e)}")
        raise typer.Exit(code=1)


@typer_app.command()
def repl(
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Registration key")
) -> None:
    """Start interactive REPL."""
    clarity_interactive_mode(registration_key=key)


@typer_app.command()
def version() -> None:
    """Show version information."""
    try:
        import importlib.metadata
        version = importlib.metadata.version("blux-ca")
        typer.echo(f"BLUX-cA version {version}")
    except:
        typer.echo("BLUX-cA (version unknown)")
    
    typer.echo(f"Python {sys.version}")
    typer.echo(f"Platform: {sys.platform}")


def run_typer_command(args: List[str]) -> None:
    """Run Typer commands from argparse."""
    try:
        # Set sys.argv for Typer
        original_argv = sys.argv
        sys.argv = ["ca.py"] + args
        typer_app()
    except SystemExit as e:
        if e.code != 0:
            print(f"Command failed with exit code {e.code}")
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        traceback.print_exc()
    finally:
        sys.argv = original_argv


def main() -> None:
    """Main CLI entrypoint with argparse for backward compatibility."""
    parser = argparse.ArgumentParser(
        description="BLUX-cA Clarity Agent - Unified Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ca.py                        # Start interactive session
  ca.py --task "Hello"         # Process single task
  ca.py --batch tasks.txt      # Process batch file
  ca.py --debug --task "Test"  # Debug single task
  ca.py reflect "What is clarity?"  # Reflection command
  ca.py doctrine "Analyze this"     # Doctrine evaluation
  ca.py repl                   # Interactive REPL
  ca.py register KEY           # Validate registration key
  ca.py --help                 # Show this help
        """
    )
    
    # Main operation modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--task",
        type=str,
        help="Process a single task"
    )
    mode_group.add_argument(
        "--batch",
        type=str,
        help="Process tasks from a file (one per line)"
    )
    mode_group.add_argument(
        "--repl",
        action="store_true",
        help="Start interactive REPL (same as no arguments)"
    )
    
    # Registration support
    parser.add_argument(
        "--key",
        "-k",
        type=str,
        help="Registration key for enhanced capabilities"
    )
    
    # Typer command passthrough
    parser.add_argument(
        "typer_command",
        nargs="?",
        help="Typer command (register, reflect, explain, eval, audit-export, doctrine, repl, version)"
    )
    
    # Options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file for batch processing"
    )
    
    # Typer command arguments (collected as extra)
    parser.add_argument(
        "typer_args",
        nargs=argparse.REMAINDER,
        help=argparse.SUPPRESS
    )
    
    args = parser.parse_args()
    
    # Handle Typer commands
    if args.typer_command:
        typer_args = [args.typer_command] + args.typer_args
        run_typer_command(typer_args)
        return
    
    # Handle argparse modes
    try:
        if args.task:
            process_single_task(args.task, args.debug, args.key)
        elif args.batch:
            process_batch_file(args.batch, args.output, args.key)
        elif args.repl or (not args.task and not args.batch):
            clarity_interactive_mode(args.key)
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.debug:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()