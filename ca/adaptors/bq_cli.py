"""
BQ CLI Adapter for BLUX-cA - Integration with bq-cli for advanced reflection.

Provides integration with external reflection tools through bq-cli,
enhancing BLUX-cA's reflection capabilities with external wisdom sources.
"""

from __future__ import annotations

import json
import logging
import shlex
import shutil
import subprocess
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Union
from uuid import uuid4

# Try to import BLUX-cA reflection engine, but make it optional
try:
    from ca.core.reflection import ReflectionEngine, ReflectionInsight
    REFLECTION_ENGINE_AVAILABLE = True
except ImportError:
    REFLECTION_ENGINE_AVAILABLE = False
    ReflectionEngine = None
    ReflectionInsight = None


class ReflectionMode(str, Enum):
    """Modes for reflection processing."""
    STANDARD = "standard"          # Basic reflection
    DEEP = "deep"                  # Extended reflection
    KOAN = "koan"                  # Koan-based reflection
    INTEGRATED = "integrated"      # Integrated with BLUX-cA dimensions
    CUSTOM = "custom"             # Custom reflection configuration


class BQTaskStatus(str, Enum):
    """Status of BQ CLI task."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DRY_RUN = "DRY_RUN"


@dataclass
class BQTask:
    """Represents a bq-cli task."""
    id: str = field(default_factory=lambda: str(uuid4()))
    command: List[str] = field(default_factory=list)
    status: BQTaskStatus = BQTaskStatus.PENDING
    executed: bool = False
    output: str = ""
    error: Optional[str] = None
    return_code: Optional[int] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BQTask:
        """Create from dictionary."""
        data = data.copy()
        data['status'] = BQTaskStatus(data['status'])
        return cls(**data)


@dataclass
class ReflectionResult:
    """Result of a reflection process."""
    id: str = field(default_factory=lambda: str(uuid4()))
    original_prompt: str = ""
    reflection_text: str = ""
    insights: List[Dict[str, Any]] = field(default_factory=list)
    koans_used: List[str] = field(default_factory=list)
    mode: ReflectionMode = ReflectionMode.STANDARD
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    bq_task: Optional[BQTask] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['mode'] = self.mode.value
        if self.bq_task:
            data['bq_task'] = self.bq_task.to_dict()
        return data
    
    def get_summary(self, max_length: int = 200) -> str:
        """Get a summary of the reflection result."""
        if len(self.reflection_text) <= max_length:
            return self.reflection_text
        
        # Try to find a good breaking point
        if "." in self.reflection_text[:max_length]:
            last_period = self.reflection_text[:max_length].rfind(".")
            if last_period > max_length // 2:
                return self.reflection_text[:last_period + 1] + ".."
        
        return self.reflection_text[:max_length] + "..."
    
    def get_primary_insight(self) -> Optional[str]:
        """Get the primary insight from the reflection."""
        if not self.insights:
            return None
        
        # Try to find the most significant insight
        for insight in self.insights:
            if insight.get("type") in ["statement", "key_value"]:
                return insight.get("text", "")
        
        # Return the first insight
        return self.insights[0].get("text", "") if self.insights else None


class BQCliAdapter:
    """
    Enhanced adapter for bq-cli integration with BLUX-cA.
    
    Provides advanced reflection capabilities by leveraging external
    wisdom sources and koan databases through bq-cli.
    """
    
    # Default koans for reflection
    DEFAULT_KOANS = [
        "The obstacle is the path.",
        "What you resist persists.",
        "The map is not the territory.",
        "Know thyself.",
        "The unexamined life is not worth living.",
        "This too shall pass.",
        "The only constant is change.",
        "Where attention goes, energy flows.",
    ]
    
    def __init__(
        self,
        executable: str | None = None,
        runner: Callable[[List[str]], subprocess.CompletedProcess[str]] | None = None,
        config: Optional[Dict[str, Any]] = None,
        enable_integration: bool = True,
    ) -> None:
        """
        Initialize BQ CLI adapter.
        
        Args:
            executable: Path to bq-cli executable (default: searches in PATH)
            runner: Function to run commands (default: subprocess.run)
            config: Configuration dictionary
            enable_integration: Enable integration with BLUX-cA reflection engine
        """
        self.config = config or {}
        self.executable = executable or shutil.which("bq") or "bq"
        self.runner = runner or self._default_runner
        self.enable_integration = enable_integration and REFLECTION_ENGINE_AVAILABLE
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize reflection engine if integration enabled
        self.reflection_engine = None
        if self.enable_integration:
            try:
                self.reflection_engine = ReflectionEngine()
                self.logger.debug("Reflection engine integrated")
            except Exception as e:
                self.logger.warning(f"Failed to initialize reflection engine: {e}")
                self.reflection_engine = None
                self.enable_integration = False
        
        # Load koans from config or use defaults
        self.koans = self.config.get("koans", self.DEFAULT_KOANS)
        
        # Cache for reflection results
        self.result_cache: Dict[str, ReflectionResult] = {}
        self.task_history: List[BQTask] = []
        
        self.logger.info(f"BQ CLI adapter initialized (executable: {self.executable})")
    
    def _default_runner(self, cmd: List[str]) -> subprocess.CompletedProcess[str]:
        """Default command runner with enhanced error handling."""
        try:
            # Add timeout from config or default
            timeout = self.config.get("timeout", 30)
            
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,  # Don't raise exception on non-zero exit
                encoding='utf-8',
                errors='replace'
            )
        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Command timeout: {e}")
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=124,  # Standard timeout exit code
                stdout="",
                stderr=f"Command timeout after {timeout} seconds"
            )
        except Exception as e:
            self.logger.error(f"Command execution error: {e}")
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=1,
                stdout="",
                stderr=str(e)
            )
    
    def available(self) -> bool:
        """Check if bq-cli is available."""
        try:
            result = shutil.which(self.executable)
            if result:
                # Test with version command
                test_cmd = [self.executable, "--version"]
                test_result = self.runner(test_cmd)
                return test_result.returncode == 0
            return False
        except Exception as e:
            self.logger.debug(f"Availability check failed: {e}")
            return False
    
    def plan_reflection(
        self,
        prompt: str,
        *,
        koans: Optional[Sequence[str]] = None,
        mode: ReflectionMode = ReflectionMode.STANDARD,
        depth: int = 3,
        output_format: str = "text"
    ) -> List[str]:
        """
        Plan a reflection command.
        
        Args:
            prompt: Reflection prompt
            koans: List of koans to use (default: uses configured koans)
            mode: Reflection mode
            depth: Reflection depth
            output_format: Output format (text, json, markdown)
            
        Returns:
            List of command arguments
        """
        koans_to_use = koans or self.koans
        
        # Base command
        command = [self.executable, "reflect"]
        
        # Add prompt
        command.extend(["--prompt", prompt])
        
        # Add koans
        for koan in koans_to_use[:5]:  # Limit number of koans
            command.extend(["--koan", koan])
        
        # Add mode-specific options
        if mode == ReflectionMode.DEEP:
            command.extend(["--depth", str(depth * 2)])
            command.extend(["--iterations", "5"])
        elif mode == ReflectionMode.KOAN:
            command.extend(["--koan-only"])
        elif mode == ReflectionMode.INTEGRATED:
            command.extend(["--integrate"])
        
        # Add output format
        if output_format != "text":
            command.extend(["--format", output_format])
        
        # Add any additional config options
        if "additional_args" in self.config:
            command.extend(self.config["additional_args"])
        
        return command
    
    def run_reflection(
        self,
        prompt: str,
        *,
        koans: Optional[Sequence[str]] = None,
        mode: ReflectionMode = ReflectionMode.STANDARD,
        depth: int = 3,
        dry_run: bool = False,
        cache_result: bool = True
    ) -> ReflectionResult:
        """
        Run a reflection process.
        
        Args:
            prompt: Reflection prompt
            koans: List of koans to use
            mode: Reflection mode
            depth: Reflection depth
            dry_run: If True, only plan command without execution
            cache_result: Cache the result for future use
            
        Returns:
            ReflectionResult object
        """
        import time
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(prompt, koans, mode, depth)
        
        # Check cache
        if cache_result and cache_key in self.result_cache:
            self.logger.debug(f"Using cached reflection result for: {prompt[:50]}...")
            cached = self.result_cache[cache_key]
            cached.metadata["cached"] = True
            return cached
        
        # Plan command
        command = self.plan_reflection(
            prompt=prompt,
            koans=koans,
            mode=mode,
            depth=depth
        )
        
        # Create task
        task = BQTask(command=command)
        
        if dry_run or not self.available():
            # Dry run or bq-cli not available
            task.status = BQTaskStatus.DRY_RUN
            task.executed = False
            task.output = f"dry-run: {' '.join(shlex.quote(part) for part in command)}"
            
            # Create fallback result
            result = self._create_fallback_result(prompt, mode)
            result.bq_task = task
            result.processing_time_ms = (time.time() - start_time) * 1000
            
            if cache_result:
                self.result_cache[cache_key] = result
            
            return result
        
        # Execute command
        task.status = BQTaskStatus.RUNNING
        self.logger.info(f"Running reflection: {prompt[:50]}...")
        
        try:
            exec_start = time.time()
            process_result = self.runner(command)
            exec_time = (time.time() - exec_start) * 1000
            
            # Update task
            task.status = BQTaskStatus.COMPLETED if process_result.returncode == 0 else BQTaskStatus.FAILED
            task.executed = True
            task.output = (process_result.stdout or "") + (process_result.stderr or "")
            task.return_code = process_result.returncode
            task.execution_time_ms = exec_time
            
            if process_result.returncode != 0:
                task.error = f"Command failed with return code {process_result.returncode}"
                self.logger.warning(f"Reflection command failed: {task.error}")
            
        except Exception as e:
            task.status = BQTaskStatus.FAILED
            task.error = str(e)
            task.output = str(e)
            self.logger.error(f"Reflection execution error: {e}")
        
        # Record task
        self.task_history.append(task)
        if len(self.task_history) > 100:  # Keep last 100 tasks
            self.task_history = self.task_history[-100:]
        
        # Process result
        result = self._process_reflection_result(
            prompt=prompt,
            task=task,
            mode=mode,
            koans=koans
        )
        
        # Integrate with BLUX-cA reflection engine if available
        if (self.enable_integration and self.reflection_engine and 
            task.status == BQTaskStatus.COMPLETED):
            try:
                enhanced_result = self._integrate_with_reflection_engine(result, prompt)
                if enhanced_result:
                    result = enhanced_result
            except Exception as e:
                self.logger.warning(f"Failed to integrate with reflection engine: {e}")
        
        result.processing_time_ms = (time.time() - start_time) * 1000
        result.bq_task = task
        
        # Cache result
        if cache_result and task.status == BQTaskStatus.COMPLETED:
            self.result_cache[cache_key] = result
            if len(self.result_cache) > 1000:  # Limit cache size
                # Remove oldest entry (first key)
                oldest_key = next(iter(self.result_cache))
                del self.result_cache[oldest_key]
        
        self.logger.info(f"Reflection completed in {result.processing_time_ms:.1f}ms")
        
        return result
    
    def _generate_cache_key(
        self,
        prompt: str,
        koans: Optional[Sequence[str]],
        mode: ReflectionMode,
        depth: int
    ) -> str:
        """Generate cache key for reflection parameters."""
        import hashlib
        
        key_parts = [
            prompt,
            mode.value,
            str(depth),
            str(sorted(koans) if koans else [])
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _create_fallback_result(self, prompt: str, mode: ReflectionMode) -> ReflectionResult:
        """Create fallback reflection result when bq-cli is not available."""
        # Use integrated reflection engine if available
        if self.reflection_engine:
            try:
                insight = self.reflection_engine.reflect(prompt)
                return ReflectionResult(
                    original_prompt=prompt,
                    reflection_text=insight.summary,
                    insights=[{"source": "reflection_engine", "summary": insight.summary}],
                    mode=mode,
                    confidence=0.7,
                    metadata={"source": "integrated_reflection_engine"}
                )
            except Exception as e:
                self.logger.debug(f"Fallback reflection failed: {e}")
        
        # Basic fallback
        reflection_text = (
            f"Reflection on: {prompt}\n\n"
            f"This is a placeholder reflection. "
            f"For deeper insights, ensure bq-cli is installed and available."
        )
        
        return ReflectionResult(
            original_prompt=prompt,
            reflection_text=reflection_text,
            insights=[{"level": "info", "message": "Fallback reflection used"}],
            mode=mode,
            confidence=0.3,
            metadata={"source": "fallback", "bq_cli_available": False}
        )
    
    def _process_reflection_result(
        self,
        prompt: str,
        task: BQTask,
        mode: ReflectionMode,
        koans: Optional[Sequence[str]]
    ) -> ReflectionResult:
        """Process the output from bq-cli into a structured result."""
        if task.status != BQTaskStatus.COMPLETED:
            # Failed execution
            return ReflectionResult(
                original_prompt=prompt,
                reflection_text=f"Reflection failed: {task.error}",
                insights=[{"level": "error", "message": task.error or "Unknown error"}],
                mode=mode,
                confidence=0.0,
                metadata={"error": True, "task_status": task.status.value}
            )
        
        output = task.output.strip()
        
        # Try to parse JSON output
        if output.startswith("{") or output.startswith("["):
            try:
                parsed = json.loads(output)
                if isinstance(parsed, dict):
                    # Handle structured output
                    reflection_text = parsed.get("reflection", parsed.get("output", output))
                    insights = parsed.get("insights", [])
                    confidence = float(parsed.get("confidence", 0.7))
                    
                    return ReflectionResult(
                        original_prompt=prompt,
                        reflection_text=str(reflection_text),
                        insights=insights if isinstance(insights, list) else [insights],
                        koans_used=list(koans or []),
                        mode=mode,
                        confidence=confidence,
                        metadata={"parsed": True, "format": "json"}
                    )
            except json.JSONDecodeError:
                pass  # Not valid JSON, fall through to text processing
        
        # Process as text
        lines = output.split('\n')
        insights = []
        
        # Simple insight extraction
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:
                # Classify lines as insights
                if line.startswith(("- ", "* ", "• ")):
                    insight_type = "bullet"
                elif ":" in line and len(line.split(":")[0]) < 20:
                    insight_type = "key_value"
                elif len(line) > 50 and line[0].isupper():
                    insight_type = "statement"
                else:
                    insight_type = "text"
                
                insights.append({
                    "type": insight_type,
                    "text": line,
                    "length": len(line)
                })
        
        # Calculate confidence based on output quality
        confidence = min(0.3 + (len(output) / 1000), 0.9)  # More text = higher confidence
        if len(insights) > 0:
            confidence = min(confidence + 0.2, 0.95)
        
        return ReflectionResult(
            original_prompt=prompt,
            reflection_text=output,
            insights=insights[:10],  # Limit number of insights
            koans_used=list(koans or []),
            mode=mode,
            confidence=confidence,
            metadata={"parsed": True, "format": "text", "line_count": len(lines)}
        )
    
    def _integrate_with_reflection_engine(
        self,
        result: ReflectionResult,
        original_prompt: str
    ) -> Optional[ReflectionResult]:
        """Integrate bq-cli result with BLUX-cA reflection engine."""
        if not self.reflection_engine:
            return None
        
        try:
            # Create combined prompt
            combined_prompt = f"{original_prompt}\n\nExternal reflection:\n{result.reflection_text}"
            
            # Get insight from reflection engine
            insight = self.reflection_engine.reflect(combined_prompt)
            
            # Enhance the result
            enhanced_insights = result.insights.copy()
            enhanced_insights.append({
                "source": "blux_ca_integration",
                "summary": insight.summary,
                "depth": insight.depth,
                "confidence": insight.confidence
            })
            
            # Update confidence
            enhanced_confidence = (result.confidence + insight.confidence) / 2
            
            # Create enhanced result
            enhanced_result = ReflectionResult(
                id=result.id,
                original_prompt=result.original_prompt,
                reflection_text=f"{result.reflection_text}\n\n---\n\nBLUX-cA Integration:\n{insight.summary}",
                insights=enhanced_insights,
                koans_used=result.koans_used,
                mode=ReflectionMode.INTEGRATED,
                confidence=enhanced_confidence,
                processing_time_ms=result.processing_time_ms,
                bq_task=result.bq_task,
                metadata={
                    **result.metadata,
                    "integrated": True,
                    "blux_ca_confidence": insight.confidence
                }
            )
            
            return enhanced_result
            
        except Exception as e:
            self.logger.debug(f"Integration failed: {e}")
            return None
    
    def batch_reflection(
        self,
        prompts: List[str],
        *,
        koans: Optional[Sequence[str]] = None,
        mode: ReflectionMode = ReflectionMode.STANDARD,
        parallel: bool = False,
        max_workers: int = 3
    ) -> List[ReflectionResult]:
        """
        Run reflection on multiple prompts.
        
        Args:
            prompts: List of prompts to reflect on
            koans: List of koans to use
            mode: Reflection mode
            parallel: Run in parallel (requires threading)
            max_workers: Maximum number of parallel workers
            
        Returns:
            List of ReflectionResult objects
        """
        results = []
        
        if parallel and len(prompts) > 1:
            # Parallel execution
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_prompt = {
                    executor.submit(
                        self.run_reflection,
                        prompt=prompt,
                        koans=koans,
                        mode=mode,
                        cache_result=False  # Don't cache individual results in batch
                    ): prompt
                    for prompt in prompts
                }
                
                for future in concurrent.futures.as_completed(future_to_prompt):
                    prompt = future_to_prompt[future]
                    try:
                        result = future.result()
                        results.append(result)
                        self.logger.debug(f"Completed reflection for: {prompt[:30]}...")
                    except Exception as e:
                        self.logger.error(f"Failed reflection for {prompt[:30]}...: {e}")
                        # Create error result
                        error_result = ReflectionResult(
                            original_prompt=prompt,
                            reflection_text=f"Error: {str(e)[:100]}",
                            insights=[{"level": "error", "message": str(e)}],
                            mode=mode,
                            confidence=0.0,
                            metadata={"error": True, "exception": str(e)}
                        )
                        results.append(error_result)
        else:
            # Sequential execution
            for prompt in prompts:
                try:
                    result = self.run_reflection(
                        prompt=prompt,
                        koans=koans,
                        mode=mode,
                        cache_result=False
                    )
                    results.append(result)
                    self.logger.debug(f"Completed reflection for: {prompt[:30]}...")
                except Exception as e:
                    self.logger.error(f"Failed reflection for {prompt[:30]}...: {e}")
                    error_result = ReflectionResult(
                        original_prompt=prompt,
                        reflection_text=f"Error: {str(e)[:100]}",
                        insights=[{"level": "error", "message": str(e)}],
                        mode=mode,
                        confidence=0.0,
                        metadata={"error": True, "exception": str(e)}
                    )
                    results.append(error_result)
        
        return results
    
    def save_result(self, result: ReflectionResult, filepath: Union[str, Path]) -> bool:
        """Save reflection result to file."""
        try:
            filepath = Path(filepath)
            data = result.to_dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved reflection result to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save result: {e}")
            return False
    
    def load_result(self, filepath: Union[str, Path]) -> Optional[ReflectionResult]:
        """Load reflection result from file."""
        try:
            filepath = Path(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct BQTask if present
            if 'bq_task' in data and data['bq_task']:
                data['bq_task'] = BQTask.from_dict(data['bq_task'])
            
            result = ReflectionResult(**data)
            self.logger.debug(f"Loaded reflection result from {filepath}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to load result: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter status."""
        return {
            "available": self.available(),
            "executable": self.executable,
            "enable_integration": self.enable_integration,
            "koan_count": len(self.koans),
            "cache_size": len(self.result_cache),
            "task_history_count": len(self.task_history),
            "reflection_engine_available": self.reflection_engine is not None,
            "config": self.config,
        }
    
    def clear_cache(self) -> int:
        """Clear reflection cache and return number of cleared items."""
        count = len(self.result_cache)
        self.result_cache.clear()
        self.logger.info(f"Cleared {count} cached reflection results")
        return count
    
    def get_recent_tasks(self, limit: int = 10) -> List[BQTask]:
        """Get recent tasks."""
        return self.task_history[-limit:] if self.task_history else []
    
    def add_koan(self, koan: str) -> None:
        """Add a koan to the koan list."""
        if koan not in self.koans:
            self.koans.append(koan)
            self.logger.debug(f"Added koan: {koan[:50]}...")
    
    def remove_koan(self, koan: str) -> bool:
        """Remove a koan from the koan list."""
        if koan in self.koans:
            self.koans.remove(koan)
            self.logger.debug(f"Removed koan: {koan[:50]}...")
            return True
        return False
    
    def load_koans_from_file(self, filepath: Union[str, Path]) -> int:
        """Load koans from a file (one per line)."""
        try:
            filepath = Path(filepath)
            with open(filepath, 'r', encoding='utf-8') as f:
                new_koans = [line.strip() for line in f if line.strip()]
            
            added = 0
            for koan in new_koans:
                if koan not in self.koans:
                    self.koans.append(koan)
                    added += 1
            
            self.logger.info(f"Loaded {added} new koans from {filepath}")
            return added
        except Exception as e:
            self.logger.error(f"Failed to load koans: {e}")
            return 0
    
    def export_results(self, filepath: Union[str, Path], format: str = "json") -> bool:
        """Export all cached results to file."""
        try:
            filepath = Path(filepath)
            
            if format == "json":
                data = {
                    "results": [result.to_dict() for result in self.result_cache.values()],
                    "export_timestamp": self._get_timestamp(),
                    "count": len(self.result_cache)
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format == "jsonl":
                with open(filepath, 'w', encoding='utf-8') as f:
                    for result in self.result_cache.values():
                        f.write(json.dumps(result.to_dict()) + "\n")
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.logger.info(f"Exported {len(self.result_cache)} results to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export results: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about reflection operations."""
        total_tasks = len(self.task_history)
        completed_tasks = len([t for t in self.task_history if t.status == BQTaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.task_history if t.status == BQTaskStatus.FAILED])
        
        if completed_tasks > 0:
            avg_execution_time = sum(
                t.execution_time_ms for t in self.task_history 
                if t.status == BQTaskStatus.COMPLETED
            ) / completed_tasks
        else:
            avg_execution_time = 0.0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
            "avg_execution_time_ms": avg_execution_time,
            "cached_results": len(self.result_cache),
            "koan_count": len(self.koans),
            "bq_cli_available": self.available(),
        }


# Utility functions

def create_bq_adapter(
    config: Optional[Dict[str, Any]] = None,
    enable_integration: bool = True
) -> BQCliAdapter:
    """
    Convenience function to create a BQ CLI adapter.
    
    Args:
        config: Configuration dictionary
        enable_integration: Enable integration with BLUX-cA reflection
        
    Returns:
        BQCliAdapter instance
    """
    return BQCliAdapter(config=config, enable_integration=enable_integration)


def quick_reflect(
    prompt: str,
    koans: Optional[List[str]] = None,
    mode: ReflectionMode = ReflectionMode.STANDARD
) -> str:
    """
    Quick reflection utility function.
    
    Args:
        prompt: Reflection prompt
        koans: Optional list of koans
        mode: Reflection mode
        
    Returns:
        Reflection text
    """
    adapter = BQCliAdapter()
    result = adapter.run_reflection(prompt, koans=koans, mode=mode)
    return result.reflection_text


def reflect_with_fallback(
    prompt: str,
    koans: Optional[List[str]] = None,
    mode: ReflectionMode = ReflectionMode.STANDARD
) -> ReflectionResult:
    """
    Run reflection with automatic fallback to integrated engine.
    
    Args:
        prompt: Reflection prompt
        koans: Optional list of koans
        mode: Reflection mode
        
    Returns:
        ReflectionResult with best available reflection
    """
    adapter = BQCliAdapter(enable_integration=True)
    result = adapter.run_reflection(prompt, koans=koans, mode=mode)
    
    # If bq-cli failed but we have integration, ensure we have some result
    if result.confidence < 0.5 and adapter.reflection_engine:
        try:
            insight = adapter.reflection_engine.reflect(prompt)
            result.reflection_text = insight.summary
            result.confidence = insight.confidence
            result.metadata["fallback_used"] = True
        except Exception:
            pass
    
    return result


__all__ = [
    "BQCliAdapter",
    "BQTask",
    "BQTaskStatus",
    "ReflectionResult",
    "ReflectionMode",
    "create_bq_adapter",
    "quick_reflect",
    "reflect_with_fallback",
]