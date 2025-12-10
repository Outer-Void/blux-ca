from __future__ import annotations

"""
Comprehensive audit system for BLUX-cA.

Records all agent decisions, actions, and system events with structured metadata.
Supports multiple storage backends and provides query/analytics capabilities.
"""

import json
import logging
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Generator
from dataclasses import dataclass, asdict, field
from uuid import uuid4
import hashlib

from cryptography.fernet import Fernet  # Optional encryption


class AuditLevel(str, Enum):
    """Audit entry severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    DECISION = "DECISION"
    ACTION = "ACTION"


class AuditCategory(str, Enum):
    """Categories for audit entries."""
    SYSTEM = "SYSTEM"
    USER_INTERACTION = "USER_INTERACTION"
    AGENT_DECISION = "AGENT_DECISION"
    MEMORY_OPERATION = "MEMORY_OPERATION"
    CONSTITUTION_CHECK = "CONSTITUTION_CHECK"
    DIMENSION_ANALYSIS = "DIMENSION_ANALYSIS"
    STATE_TRANSITION = "STATE_TRANSITION"
    SAFETY_CHECK = "SAFETY_CHECK"
    PERFORMANCE = "PERFORMANCE"
    CONFIGURATION = "CONFIGURATION"


@dataclass
class AuditEntry:
    """
    Structured audit entry with comprehensive metadata.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    level: AuditLevel = AuditLevel.INFO
    category: AuditCategory = AuditCategory.SYSTEM
    component: str = "unknown"
    operation: str = ""
    description: str = ""
    
    # Contextual data
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    agent_name: Optional[str] = None
    input_hash: Optional[str] = None
    recovery_state: Optional[str] = None
    
    # Details
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        data['category'] = self.category.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AuditEntry:
        """Create from dictionary."""
        # Convert string enums back to enum values
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['level'] = AuditLevel(data['level'])
        data['category'] = AuditCategory(data['category'])
        return cls(**data)
    
    def get_hash(self) -> str:
        """Get content hash for deduplication."""
        content = f"{self.timestamp}{self.level}{self.category}{self.component}{self.operation}{self.description}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def summarize(self) -> str:
        """Get human-readable summary."""
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.level}: {self.category}/{self.component} - {self.description}"


class AuditStorage(ABC):
    """Abstract base class for audit storage backends."""
    
    @abstractmethod
    def store(self, entry: AuditEntry) -> bool:
        """Store an audit entry."""
        pass
    
    @abstractmethod
    def retrieve(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[AuditEntry]:
        """Retrieve audit entries matching criteria."""
        pass
    
    @abstractmethod
    def count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        component: Optional[str] = None
    ) -> int:
        """Count audit entries matching criteria."""
        pass
    
    @abstractmethod
    def cleanup(self, older_than_days: int = 30) -> int:
        """Clean up old audit entries."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        pass


class MemoryAuditStorage(AuditStorage):
    """In-memory audit storage (default, for testing/small deployments)."""
    
    def __init__(self, max_entries: int = 10000):
        self.entries: List[AuditEntry] = []
        self.max_entries = max_entries
        self.logger = logging.getLogger(__name__)
    
    def store(self, entry: AuditEntry) -> bool:
        try:
            self.entries.append(entry)
            
            # Enforce size limit (FIFO)
            if len(self.entries) > self.max_entries:
                removed = len(self.entries) - self.max_entries
                self.entries = self.entries[removed:]
                self.logger.debug(f"Trimmed {removed} old audit entries")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store audit entry: {e}")
            return False
    
    def retrieve(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[AuditEntry]:
        filtered = []
        
        for entry in reversed(self.entries):  # Most recent first
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if level and entry.level != level:
                continue
            if category and entry.category != category:
                continue
            if component and entry.component != component:
                continue
            
            filtered.append(entry)
            
            if limit and len(filtered) >= limit:
                break
        
        return filtered
    
    def count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        component: Optional[str] = None
    ) -> int:
        return len(self.retrieve(start_time, end_time, level, category, component, limit=None))
    
    def cleanup(self, older_than_days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=older_than_days)
        initial_count = len(self.entries)
        self.entries = [e for e in self.entries if e.timestamp >= cutoff]
        removed = initial_count - len(self.entries)
        
        if removed > 0:
            self.logger.info(f"Cleaned up {removed} audit entries older than {older_than_days} days")
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "storage_type": "memory",
            "total_entries": len(self.entries),
            "max_entries": self.max_entries,
            "levels": {level.value: self.count(level=level) for level in AuditLevel},
            "categories": {cat.value: self.count(category=cat) for cat in AuditCategory},
        }


class FileAuditStorage(AuditStorage):
    """File-based audit storage (JSON lines format)."""
    
    def __init__(self, filepath: Union[str, Path], encrypt: bool = False):
        self.filepath = Path(filepath)
        self.encrypt = encrypt
        self.encryption_key = None
        
        if encrypt:
            # Generate or load encryption key
            key_file = self.filepath.parent / f"{self.filepath.name}.key"
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    self.encryption_key = f.read()
            else:
                self.encryption_key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(self.encryption_key)
        
        self.logger = logging.getLogger(__name__)
        
        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
    
    def store(self, entry: AuditEntry) -> bool:
        try:
            entry_dict = entry.to_dict()
            line = json.dumps(entry_dict, ensure_ascii=False)
            
            if self.encrypt and self.encryption_key:
                fernet = Fernet(self.encryption_key)
                line = fernet.encrypt(line.encode()).decode()
            
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store audit entry to file: {e}")
            return False
    
    def _read_entries(self) -> Generator[AuditEntry, None, None]:
        """Read entries from file."""
        if not self.filepath.exists():
            return
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        if self.encrypt and self.encryption_key:
                            fernet = Fernet(self.encryption_key)
                            line = fernet.decrypt(line.encode()).decode()
                        
                        entry_dict = json.loads(line)
                        yield AuditEntry.from_dict(entry_dict)
                    except (json.JSONDecodeError, ValueError) as e:
                        self.logger.warning(f"Failed to parse audit entry: {e}")
                        continue
        except Exception as e:
            self.logger.error(f"Failed to read audit file: {e}")
    
    def retrieve(
        self, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[AuditEntry]:
        filtered = []
        
        for entry in self._read_entries():
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
            if level and entry.level != level:
                continue
            if category and entry.category != category:
                continue
            if component and entry.component != component:
                continue
            
            filtered.append(entry)
            
            if limit and len(filtered) >= limit:
                break
        
        return filtered
    
    def count(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        level: Optional[AuditLevel] = None,
        category: Optional[AuditCategory] = None,
        component: Optional[str] = None
    ) -> int:
        count = 0
        for _ in self.retrieve(start_time, end_time, level, category, component, limit=None):
            count += 1
        return count
    
    def cleanup(self, older_than_days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=older_than_days)
        temp_file = self.filepath.with_suffix('.tmp')
        removed = 0
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as out_f:
                for entry in self._read_entries():
                    if entry.timestamp >= cutoff:
                        entry_dict = entry.to_dict()
                        line = json.dumps(entry_dict, ensure_ascii=False)
                        
                        if self.encrypt and self.encryption_key:
                            fernet = Fernet(self.encryption_key)
                            line = fernet.encrypt(line.encode()).decode()
                        
                        out_f.write(line + '\n')
                    else:
                        removed += 1
            
            # Replace original file
            temp_file.replace(self.filepath)
            
            if removed > 0:
                self.logger.info(f"Cleaned up {removed} audit entries older than {older_than_days} days")
            
            return removed
        except Exception as e:
            self.logger.error(f"Failed to clean up audit file: {e}")
            if temp_file.exists():
                temp_file.unlink()
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {
            "storage_type": "file",
            "filepath": str(self.filepath),
            "encrypted": self.encrypt,
            "file_size": self.filepath.stat().st_size if self.filepath.exists() else 0,
        }
        
        # Count entries by level and category (sample-based for performance)
        level_counts = {level.value: 0 for level in AuditLevel}
        category_counts = {cat.value: 0 for cat in AuditCategory}
        
        # Sample up to 1000 entries for stats
        for entry in self.retrieve(limit=1000):
            level_counts[entry.level.value] += 1
            category_counts[entry.category.value] += 1
        
        stats["level_counts"] = level_counts
        stats["category_counts"] = category_counts
        
        return stats


class AuditTrail:
    """
    Comprehensive audit trail system for BLUX-cA.
    
    Records all system activities with structured metadata and provides
    query, analytics, and export capabilities.
    """
    
    def __init__(
        self,
        storage_backend: Optional[AuditStorage] = None,
        component_name: str = "BLUX-cA",
        enable_audit: bool = True,
        retention_days: int = 30
    ):
        """
        Initialize audit trail.
        
        Args:
            storage_backend: AuditStorage implementation (defaults to MemoryAuditStorage)
            component_name: Name of the component being audited
            enable_audit: Whether auditing is enabled
            retention_days: Days to retain audit entries before cleanup
        """
        self.storage = storage_backend or MemoryAuditStorage()
        self.component_name = component_name
        self.enable_audit = enable_audit
        self.retention_days = retention_days
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.performance_stats = {
            "entries_logged": 0,
            "queries_performed": 0,
            "last_cleanup": None,
            "errors": 0,
        }
    
    def log(
        self,
        level: AuditLevel,
        category: AuditCategory,
        operation: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        input_hash: Optional[str] = None,
        recovery_state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        component: Optional[str] = None
    ) -> Optional[AuditEntry]:
        """
        Log an audit entry.
        
        Returns:
            AuditEntry if logged, None if auditing disabled or failed
        """
        if not self.enable_audit:
            return None
        
        try:
            entry = AuditEntry(
                level=level,
                category=category,
                component=component or self.component_name,
                operation=operation,
                description=description,
                user_id=user_id,
                session_id=session_id,
                agent_name=agent_name,
                input_hash=input_hash,
                recovery_state=recovery_state,
                details=details or {},
                metadata=metadata or {},
            )
            
            if self.storage.store(entry):
                self.performance_stats["entries_logged"] += 1
                
                # Also log to application logs for important events
                if level in [AuditLevel.ERROR, AuditLevel.SECURITY, AuditLevel.WARNING]:
                    log_method = getattr(self.logger, level.value.lower())
                    log_method(f"Audit: {entry.summarize()}")
                
                return entry
            else:
                self.performance_stats["errors"] += 1
                return None
                
        except Exception as e:
            self.performance_stats["errors"] += 1
            self.logger.error(f"Failed to create audit entry: {e}")
            return None
    
    # Convenience methods for common audit operations
    
    def log_decision(
        self,
        decision: str,
        rationale: str,
        user_input: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[AuditEntry]:
        """Log an agent decision."""
        input_hash = None
        if user_input:
            input_hash = hashlib.sha256(user_input.encode()).hexdigest()
        
        return self.log(
            level=AuditLevel.DECISION,
            category=AuditCategory.AGENT_DECISION,
            operation="decision_making",
            description=f"Agent decision: {decision}",
            details={
                "decision": decision,
                "rationale": rationale,
                "input_preview": user_input[:100] if user_input else None,
                **(details or {})
            },
            user_id=user_id,
            session_id=session_id,
            agent_name=agent_name,
            input_hash=input_hash
        )
    
    def log_user_interaction(
        self,
        user_input: str,
        response: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        recovery_state: Optional[str] = None,
        clarity_scores: Optional[Dict[str, float]] = None
    ) -> Optional[AuditEntry]:
        """Log a user interaction."""
        input_hash = hashlib.sha256(user_input.encode()).hexdigest()
        
        return self.log(
            level=AuditLevel.INFO,
            category=AuditCategory.USER_INTERACTION,
            operation="user_interaction",
            description=f"User interaction processed",
            details={
                "input_preview": user_input[:200],
                "response_preview": response[:200],
                "input_length": len(user_input),
                "response_length": len(response),
                "clarity_scores": clarity_scores or {},
            },
            user_id=user_id,
            session_id=session_id,
            agent_name=agent_name,
            input_hash=input_hash,
            recovery_state=recovery_state
        )
    
    def log_state_transition(
        self,
        from_state: str,
        to_state: str,
        reason: str,
        confidence: float,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> Optional[AuditEntry]:
        """Log a recovery state transition."""
        return self.log(
            level=AuditLevel.INFO,
            category=AuditCategory.STATE_TRANSITION,
            operation="state_transition",
            description=f"Recovery state transition: {from_state} → {to_state}",
            details={
                "from_state": from_state,
                "to_state": to_state,
                "reason": reason,
                "confidence": confidence,
            },
            session_id=session_id,
            agent_name=agent_name,
            recovery_state=to_state
        )
    
    def log_safety_check(
        self,
        check_type: str,
        result: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> Optional[AuditEntry]:
        """Log a safety/guardrail check."""
        return self.log(
            level=AuditLevel.SECURITY if result == "violation" else AuditLevel.INFO,
            category=AuditCategory.SAFETY_CHECK,
            operation="safety_check",
            description=f"Safety check: {check_type} - {result}",
            details={
                "check_type": check_type,
                "result": result,
                **details,
            },
            user_id=user_id,
            session_id=session_id,
            agent_name=agent_name
        )
    
    # Query methods
    
    def get_recent_entries(self, limit: int = 100) -> List[AuditEntry]:
        """Get most recent audit entries."""
        self.performance_stats["queries_performed"] += 1
        return self.storage.retrieve(limit=limit)
    
    def get_entries_by_time(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[AuditEntry]:
        """Get entries within a time range."""
        self.performance_stats["queries_performed"] += 1
        return self.storage.retrieve(start_time=start_time, end_time=end_time)
    
    def get_entries_by_level(self, level: AuditLevel, limit: int = 100) -> List[AuditEntry]:
        """Get entries by severity level."""
        self.performance_stats["queries_performed"] += 1
        return self.storage.retrieve(level=level, limit=limit)
    
    def get_entries_by_category(self, category: AuditCategory, limit: int = 100) -> List[AuditEntry]:
        """Get entries by category."""
        self.performance_stats["queries_performed"] += 1
        return self.storage.retrieve(category=category, limit=limit)
    
    def search_entries(
        self,
        search_text: str,
        field: str = "description",
        limit: int = 100
    ) -> List[AuditEntry]:
        """Search entries by text content."""
        self.performance_stats["queries_performed"] += 1
        all_entries = self.storage.retrieve(limit=limit * 2)  # Get more for filtering
        
        filtered = []
        search_text_lower = search_text.lower()
        
        for entry in all_entries:
            if field == "description" and search_text_lower in entry.description.lower():
                filtered.append(entry)
            elif field == "component" and search_text_lower in entry.component.lower():
                filtered.append(entry)
            elif field == "operation" and search_text_lower in entry.operation.lower():
                filtered.append(entry)
            elif field == "all":
                if (search_text_lower in entry.description.lower() or
                    search_text_lower in entry.component.lower() or
                    search_text_lower in entry.operation.lower()):
                    filtered.append(entry)
            
            if len(filtered) >= limit:
                break
        
        return filtered
    
    # Analytics and reporting
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics."""
        stats = self.storage.get_stats()
        stats.update({
            "performance": self.performance_stats,
            "component": self.component_name,
            "enabled": self.enable_audit,
            "retention_days": self.retention_days,
        })
        return stats
    
    def export_entries(
        self,
        output_format: str = "json",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Union[str, List[Dict[str, Any]]]:
        """Export audit entries."""
        entries = self.storage.retrieve(start_time=start_time, end_time=end_time, limit=limit)
        
        if output_format == "json":
            return [entry.to_dict() for entry in entries]
        elif output_format == "csv":
            # Simple CSV format
            csv_lines = ["timestamp,level,category,component,operation,description"]
            for entry in entries:
                csv_lines.append(
                    f'"{entry.timestamp.isoformat()}","{entry.level.value}",'
                    f'"{entry.category.value}","{entry.component}","{entry.operation}",'
                    f'"{entry.description.replace('"', '""')}"'
                )
            return "\n".join(csv_lines)
        else:
            raise ValueError(f"Unsupported export format: {output_format}")
    
    # Maintenance
    
    def cleanup_old_entries(self) -> int:
        """Clean up entries older than retention period."""
        removed = self.storage.cleanup(self.retention_days)
        if removed > 0:
            self.performance_stats["last_cleanup"] = datetime.now().isoformat()
            self.logger.info(f"Cleaned up {removed} old audit entries")
        return removed
    
    def enable(self) -> None:
        """Enable auditing."""
        self.enable_audit = True
        self.logger.info("Audit trail enabled")
    
    def disable(self) -> None:
        """Disable auditing."""
        self.enable_audit = False
        self.logger.info("Audit trail disabled")
    
    def set_retention_days(self, days: int) -> None:
        """Set retention period in days."""
        self.retention_days = days
        self.logger.info(f"Audit retention set to {days} days")
    
    def get_status(self) -> Dict[str, Any]:
        """Get audit trail status."""
        return {
            "enabled": self.enable_audit,
            "storage_type": self.storage.__class__.__name__,
            "entries_logged": self.performance_stats["entries_logged"],
            "retention_days": self.retention_days,
            "last_cleanup": self.performance_stats["last_cleanup"],
        }


# Convenience function for creating audit trails
def create_audit_trail(
    storage_type: str = "memory",
    filepath: Optional[str] = None,
    encrypt: bool = False,
    component_name: str = "BLUX-cA",
    max_entries: int = 10000,
    retention_days: int = 30
) -> AuditTrail:
    """
    Create an audit trail with specified storage backend.
    
    Args:
        storage_type: "memory" or "file"
        filepath: Required for file storage
        encrypt: Encrypt file storage
        component_name: Name of component being audited
        max_entries: For memory storage
        retention_days: Days to retain entries
    
    Returns:
        Configured AuditTrail instance
    """
    storage = None
    
    if storage_type == "memory":
        storage = MemoryAuditStorage(max_entries=max_entries)
    elif storage_type == "file":
        if not filepath:
            raise ValueError("Filepath required for file storage")
        storage = FileAuditStorage(filepath=filepath, encrypt=encrypt)
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
    
    return AuditTrail(
        storage_backend=storage,
        component_name=component_name,
        retention_days=retention_days
    )