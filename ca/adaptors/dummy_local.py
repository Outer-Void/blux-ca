"""
Dummy Local Adaptor for BLUX-cA.

Provides simulated local input/output for testing and development.
Can be configured with various input sources and output formats.
"""

import json
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

from . import BaseAdaptor


class DummyLocalAdaptor(BaseAdaptor):
    """
    Local adaptor that simulates user interaction for testing.
    
    Supports multiple input modes:
    - Static: Fixed input text
    - Random: Random selection from predefined prompts
    - File: Read inputs from a file
    - Scripted: Predefined conversation sequence
    - Interactive: Manual input during testing
    """
    
    # Predefined prompts for different testing scenarios
    TEST_PROMPTS = {
        "crisis": [
            "I can't handle this anymore. Everything is falling apart.",
            "I'm in crisis and don't know what to do.",
            "It feels like there's no way out of this situation.",
            "I'm overwhelmed and need immediate help.",
            "This is an emergency. I don't know where to turn.",
        ],
        "awareness": [
            "I've been noticing a pattern in my relationships.",
            "Something feels off about how I'm approaching this.",
            "I'm becoming aware of some recurring thoughts.",
            "There's something I keep avoiding but I can't ignore it anymore.",
            "I'm starting to see connections I didn't see before.",
        ],
        "honesty": [
            "I need to be honest about my role in this situation.",
            "I've been lying to myself about how I feel.",
            "The truth is, I've been avoiding facing this.",
            "I need to admit that I was wrong about this.",
            "I haven't been completely truthful about what happened.",
        ],
        "reconstruction": [
            "I want to rebuild my daily routine from scratch.",
            "How can I create better habits around this?",
            "I need a plan to move forward from here.",
            "What steps should I take to reconstruct my approach?",
            "I'm ready to build a new structure for dealing with this.",
        ],
        "integration": [
            "How do I integrate what I've learned into my daily life?",
            "I'm seeing how different pieces fit together now.",
            "This understanding needs to become part of who I am.",
            "How can I bring these insights into my everyday decisions?",
            "I want to make this new perspective part of my identity.",
        ],
        "purpose": [
            "I feel called to help others with similar struggles.",
            "This experience has given me a sense of purpose.",
            "I want to use what I've learned to make a difference.",
            "My mission is becoming clearer to me now.",
            "I feel a sense of direction and purpose emerging.",
        ],
        "general": [
            "Hello BLUX-cA, I need help with a problem.",
            "I'm feeling stuck and could use some clarity.",
            "Can you help me understand what's going on?",
            "I need to talk through something that's been bothering me.",
            "I'm looking for some perspective on a situation.",
            "What does clarity look like in this context?",
            "I'm trying to make sense of my feelings about this.",
            "Could you help me see this from a different angle?",
        ]
    }
    
    def __init__(self, name: str = "dummy_local", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the dummy local adaptor.
        
        Args:
            name: Adaptor instance name
            config: Configuration dictionary with keys:
                - mode: Input mode ("static", "random", "file", "scripted", "interactive")
                - input_text: For static mode
                - prompt_category: For random mode ("crisis", "awareness", etc.)
                - input_file: Path to input file for file mode
                - script: List of inputs for scripted mode
                - output_format: How to display output ("simple", "detailed", "json")
                - include_timestamp: Whether to include timestamps in output
                - simulate_typing: Whether to simulate typing delay
                - conversation_length: Max number of exchanges for scripted mode
        """
        super().__init__(name, config)
        
        # Default configuration
        self.default_config = {
            "mode": "random",
            "prompt_category": "general",
            "output_format": "detailed",
            "include_timestamp": True,
            "simulate_typing": False,
            "conversation_length": 10,
            "auto_connect": True,
        }
        
        # Merge provided config with defaults
        if config:
            self.default_config.update(config)
        self.config = self.default_config
        
        # State tracking
        self.input_history: List[Dict[str, Any]] = []
        self.output_history: List[Dict[str, Any]] = []
        self.script_position = 0
        self.conversation_count = 0
        
        # Initialize based on mode
        self._initialize_mode()
        
    def _initialize_mode(self) -> None:
        """Initialize adaptor based on configured mode."""
        mode = self.config.get("mode", "random")
        
        if mode == "static":
            self.input_text = self.config.get("input_text", "Hello BLUX-cA")
            self.logger.info(f"Initialized in static mode with text: {self.input_text[:50]}...")
            
        elif mode == "random":
            category = self.config.get("prompt_category", "general")
            self.prompts = self.TEST_PROMPTS.get(category, self.TEST_PROMPTS["general"])
            self.logger.info(f"Initialized in random mode with category: {category}")
            
        elif mode == "file":
            input_file = self.config.get("input_file", "test_inputs.txt")
            self.file_path = Path(input_file)
            if not self.file_path.exists():
                self.logger.warning(f"Input file not found: {input_file}. Will use random mode.")
                self.config["mode"] = "random"
                self._initialize_mode()
                return
            self.logger.info(f"Initialized in file mode with file: {input_file}")
            
        elif mode == "scripted":
            self.script = self.config.get("script", [])
            if not self.script:
                # Generate a sample script
                self.script = self._generate_sample_script()
            self.logger.info(f"Initialized in scripted mode with {len(self.script)} scripted inputs")
            
        elif mode == "interactive":
            self.logger.info("Initialized in interactive mode (user will provide input)")
            
        else:
            self.logger.warning(f"Unknown mode: {mode}. Defaulting to random.")
            self.config["mode"] = "random"
            self._initialize_mode()
    
    def _generate_sample_script(self) -> List[str]:
        """Generate a sample conversation script."""
        return [
            "I'm feeling really overwhelmed with work.",
            "It feels like I can't keep up with everything.",
            "I think part of it is that I'm not setting good boundaries.",
            "How can I start setting better boundaries?",
            "I want to rebuild my work habits from the ground up.",
            "This is giving me a new sense of direction.",
        ]
    
    def connect(self) -> bool:
        """Simulate connection (always succeeds for dummy adaptor)."""
        self.is_connected = True
        self.logger.info(f"Dummy adaptor '{self.name}' connected")
        return True
    
    def disconnect(self) -> bool:
        """Simulate disconnection."""
        self.is_connected = False
        self.logger.info(f"Dummy adaptor '{self.name}' disconnected")
        
        # Log conversation summary
        if self.input_history:
            self.logger.info(f"Conversation summary: {len(self.input_history)} exchanges")
        return True
    
    def get_input(self) -> str:
        """
        Get simulated user input based on configured mode.
        
        Returns:
            str: Simulated user input
        """
        if not self.is_connected and self.config.get("auto_connect", True):
            self.connect()
        
        mode = self.config.get("mode", "random")
        input_text = ""
        
        try:
            if mode == "static":
                input_text = self.input_text
                
            elif mode == "random":
                category = self.config.get("prompt_category", "general")
                prompts = self.TEST_PROMPTS.get(category, self.TEST_PROMPTS["general"])
                input_text = random.choice(prompts)
                
            elif mode == "file":
                with open(self.file_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                    if lines:
                        # Cycle through lines
                        line_index = self.conversation_count % len(lines)
                        input_text = lines[line_index]
                    else:
                        input_text = "No input available in file."
                        
            elif mode == "scripted":
                if self.script_position < len(self.script):
                    input_text = self.script[self.script_position]
                    self.script_position += 1
                else:
                    # Loop back to start
                    self.script_position = 0
                    input_text = self.script[self.script_position]
                    self.script_position += 1
                    
            elif mode == "interactive":
                input_text = input(f"[{self.name} INPUT] > ")
                
            else:
                input_text = "Test input from dummy adaptor."
        
        except Exception as e:
            self.logger.error(f"Error getting input: {e}")
            input_text = f"Error: {str(e)[:50]}"
        
        # Simulate typing delay if configured
        if self.config.get("simulate_typing", False):
            typing_delay = min(len(input_text) * 0.01, 2.0)  # Max 2 seconds
            time.sleep(typing_delay)
        
        # Record input history
        self.input_history.append({
            "timestamp": datetime.now().isoformat(),
            "text": input_text,
            "mode": mode,
            "exchange_number": self.conversation_count
        })
        
        self.conversation_count += 1
        return input_text
    
    def send_output(self, output: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Receive and display output from BLUX-cA.
        
        Args:
            output: The output text to display
            metadata: Additional metadata about the output
            
        Returns:
            bool: Always returns True for dummy adaptor
        """
        output_format = self.config.get("output_format", "detailed")
        include_timestamp = self.config.get("include_timestamp", True)
        
        # Record output history
        output_record = {
            "timestamp": datetime.now().isoformat(),
            "text": output,
            "metadata": metadata or {},
            "exchange_number": self.conversation_count - 1  # Match with last input
        }
        self.output_history.append(output_record)
        
        # Format and display output
        if output_format == "simple":
            self._display_simple(output, include_timestamp)
        elif output_format == "json":
            self._display_json(output, metadata, include_timestamp)
        else:  # detailed (default)
            self._display_detailed(output, metadata, include_timestamp)
        
        return True
    
    def _display_simple(self, output: str, include_timestamp: bool) -> None:
        """Display output in simple format."""
        timestamp = f"[{datetime.now().strftime('%H:%M:%S')}] " if include_timestamp else ""
        print(f"{timestamp}[{self.name} OUTPUT]: {output}")
    
    def _display_detailed(self, output: str, metadata: Optional[Dict[str, Any]], include_timestamp: bool) -> None:
        """Display output in detailed format."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print("\n" + "=" * 60)
        if include_timestamp:
            print(f"Timestamp: {timestamp}")
        print(f"Adaptor: {self.name}")
        print("-" * 60)
        print(f"OUTPUT:\n{output}")
        
        if metadata:
            print("-" * 60)
            print("METADATA:")
            for key, value in metadata.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for subkey, subvalue in value.items():
                        print(f"    {subkey}: {subvalue}")
                else:
                    print(f"  {key}: {value}")
        
        print("=" * 60 + "\n")
    
    def _display_json(self, output: str, metadata: Optional[Dict[str, Any]], include_timestamp: bool) -> None:
        """Display output as JSON."""
        display_data = {
            "adaptor": self.name,
            "output": output,
        }
        
        if include_timestamp:
            display_data["timestamp"] = datetime.now().isoformat()
        
        if metadata:
            display_data["metadata"] = metadata
        
        print(json.dumps(display_data, indent=2))
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history with inputs and outputs paired.
        
        Args:
            limit: Maximum number of exchanges to return
            
        Returns:
            List of conversation exchanges
        """
        history = []
        min_length = min(len(self.input_history), len(self.output_history))
        
        for i in range(min_length):
            exchange = {
                "exchange_number": i,
                "input": self.input_history[i],
                "output": self.output_history[i]
            }
            history.append(exchange)
        
        if limit:
            history = history[-limit:]
            
        return history
    
    def clear_history(self) -> None:
        """Clear input and output history."""
        self.input_history.clear()
        self.output_history.clear()
        self.script_position = 0
        self.conversation_count = 0
        self.logger.info("Conversation history cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get adaptor status with conversation statistics."""
        base_status = super().get_status()
        
        # Add adaptor-specific status
        base_status.update({
            "mode": self.config.get("mode", "unknown"),
            "conversation_count": self.conversation_count,
            "input_history_size": len(self.input_history),
            "output_history_size": len(self.output_history),
            "script_position": self.script_position if self.config.get("mode") == "scripted" else None,
        })
        
        return base_status
    
    def set_mode(self, mode: str, **kwargs) -> bool:
        """
        Change the adaptor's input mode.
        
        Args:
            mode: New mode ("static", "random", "file", "scripted", "interactive")
            **kwargs: Additional configuration for the mode
            
        Returns:
            bool: True if mode changed successfully
        """
        valid_modes = ["static", "random", "file", "scripted", "interactive"]
        if mode not in valid_modes:
            self.logger.error(f"Invalid mode: {mode}. Valid modes: {valid_modes}")
            return False
        
        self.config["mode"] = mode
        self.config.update(kwargs)
        self._initialize_mode()
        
        self.logger.info(f"Mode changed to: {mode}")
        return True
    
    def save_conversation(self, filepath: str, format: str = "json") -> bool:
        """
        Save conversation history to a file.
        
        Args:
            filepath: Path to save file
            format: Output format ("json", "text")
            
        Returns:
            bool: True if saved successfully
        """
        try:
            history = self.get_conversation_history()
            
            if format == "json":
                with open(filepath, 'w') as f:
                    json.dump(history, f, indent=2)
            else:  # text format
                with open(filepath, 'w') as f:
                    for exchange in history:
                        f.write(f"Exchange #{exchange['exchange_number']}\n")
                        f.write(f"Input: {exchange['input']['text']}\n")
                        f.write(f"Output: {exchange['output']['text']}\n")
                        f.write("-" * 40 + "\n")
            
            self.logger.info(f"Conversation saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save conversation: {e}")
            return False