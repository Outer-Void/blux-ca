"""
BLUX-cA Core Agent Package.

This package contains the core components of the BLUX-cA (Clarity Agent) system.
The agent provides clarity through three dimensions: logical, emotional, and shadow clarity.
"""

__version__ = "1.0.0"
__author__ = "BLUX-cA Team"
__description__ = "Clarity Agent for logical, emotional, and shadow clarity"

from typing import Optional, Dict, Any, List

# Core components
from .core_agent import BLUXAgent
from .memory import Memory, MemoryEntry
from .discernment import DiscernmentCompass, DiscernmentResult
from .constitution import Constitution, ConstitutionRule
from .audit import AuditTrail, AuditEntry

# Clarity dimensions (if available)
try:
    from .dimensions import LogicalClarity, EmotionalClarity, ShadowClarity
    DIMENSIONS_AVAILABLE = True
except ImportError:
    DIMENSIONS_AVAILABLE = False

# State management (if available)
try:
    from .states import UserState, RecoveryStateMachine
    STATES_AVAILABLE = True
except ImportError:
    STATES_AVAILABLE = False


class ClarityAgentFactory:
    """
    Factory for creating and configuring BLUX-cA agent instances.
    """
    
    @staticmethod
    def create_agent(
        name: str = "BLUX-cA",
        config: Optional[Dict[str, Any]] = None,
        enable_memory: bool = True,
        enable_discernment: bool = True,
        enable_constitution: bool = True,
        enable_audit: bool = True,
        memory_config: Optional[Dict[str, Any]] = None,
        constitution_rules: Optional[List[ConstitutionRule]] = None
    ) -> BLUXAgent:
        """
        Create a configured BLUX-cA agent instance.
        
        Args:
            name: Agent name
            config: Agent configuration
            enable_memory: Enable memory system
            enable_discernment: Enable discernment compass
            enable_constitution: Enable constitution rules
            enable_audit: Enable audit trail
            memory_config: Memory system configuration
            constitution_rules: Custom constitution rules
            
        Returns:
            Configured BLUXAgent instance
        """
        # Initialize components
        memory = None
        if enable_memory:
            memory = Memory(**(memory_config or {}))
        
        discernment = None
        if enable_discernment:
            discernment = DiscernmentCompass()
        
        constitution = None
        if enable_constitution:
            constitution = Constitution(rules=constitution_rules)
        
        audit = None
        if enable_audit:
            audit = AuditTrail()
        
        # Create agent
        agent = BLUXAgent(
            name=name,
            memory=memory,
            discernment=discernment,
            constitution=constitution,
            audit=audit,
            config=config or {}
        )
        
        return agent
    
    @staticmethod
    def create_default_agent(name: str = "BLUX-cA") -> BLUXAgent:
        """
        Create a default configured BLUX-cA agent.
        
        Args:
            name: Agent name
            
        Returns:
            Default configured BLUXAgent instance
        """
        return ClarityAgentFactory.create_agent(
            name=name,
            enable_memory=True,
            enable_discernment=True,
            enable_constitution=True,
            enable_audit=True
        )


def create_agent(
    name: str = "BLUX-cA",
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> BLUXAgent:
    """
    Convenience function to create a BLUX-cA agent.
    
    Args:
        name: Agent name
        config: Agent configuration
        **kwargs: Additional arguments passed to factory
        
    Returns:
        BLUXAgent instance
    """
    return ClarityAgentFactory.create_agent(name=name, config=config, **kwargs)


# Package exports
__all__ = [
    # Core components
    "BLUXAgent",
    "Memory",
    "MemoryEntry",
    "DiscernmentCompass",
    "DiscernmentResult",
    "Constitution",
    "ConstitutionRule",
    "AuditTrail",
    "AuditEntry",
    
    # Factory and convenience
    "ClarityAgentFactory",
    "create_agent",
    
    # Availability flags
    "DIMENSIONS_AVAILABLE",
    "STATES_AVAILABLE",
    
    # Package metadata
    "__version__",
    "__author__",
    "__description__",
]

# Add dimension exports if available
if DIMENSIONS_AVAILABLE:
    __all__.extend([
        "LogicalClarity",
        "EmotionalClarity",
        "ShadowClarity",
    ])

# Add state exports if available
if STATES_AVAILABLE:
    __all__.extend([
        "UserState",
        "RecoveryStateMachine",
    ])


def get_package_info() -> Dict[str, Any]:
    """
    Get package information and capabilities.
    
    Returns:
        Dictionary with package metadata and capabilities
    """
    return {
        "version": __version__,
        "author": __author__,
        "description": __description__,
        "capabilities": {
            "dimensions": DIMENSIONS_AVAILABLE,
            "state_management": STATES_AVAILABLE,
            "memory": True,
            "discernment": True,
            "constitution": True,
            "audit": True,
        },
        "components": {
            "core": ["BLUXAgent"],
            "memory": ["Memory", "MemoryEntry"],
            "discernment": ["DiscernmentCompass", "DiscernmentResult"],
            "constitution": ["Constitution", "ConstitutionRule"],
            "audit": ["AuditTrail", "AuditEntry"],
        }
    }


# Initialize package logging
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())