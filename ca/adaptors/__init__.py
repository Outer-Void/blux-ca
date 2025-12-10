"""
Adaptors package for BLUX-cA.

Adaptors provide interface layers between BLUX-cA and external systems.
Each adaptor handles input/output in a specific context (local, HTTP, file, etc.).
"""

from abc import ABC, abstractmethod
from datetime import datetime
import json
import logging
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

logger = logging.getLogger(__name__)


class BaseAdaptor(ABC):
    """
    Abstract base class for all adaptors.
    
    Defines the common interface that all adaptors must implement.
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adaptor.
        
        Args:
            name: Unique name for this adaptor instance
            config: Configuration dictionary for adaptor-specific settings
        """
        self.name = name
        self.config = config or {}
        self.is_connected = False
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the external system.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the external system.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_input(self) -> str:
        """
        Get input from the external system.
        
        Returns:
            str: Input text from the external system
        """
        pass
    
    @abstractmethod
    def send_output(self, output: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send output to the external system.
        
        Args:
            output: The output text to send
            metadata: Additional metadata about the output
            
        Returns:
            bool: True if output sent successfully, False otherwise
        """
        pass
    
    def validate_config(self) -> List[str]:
        """
        Validate adaptor configuration.
        
        Returns:
            List[str]: List of validation errors, empty if valid
        """
        errors = []
        if not self.name:
            errors.append("Adaptor name is required")
        return errors
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get adaptor status information.
        
        Returns:
            Dict[str, Any]: Status information including connection state
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "connected": self.is_connected,
            "config_valid": len(self.validate_config()) == 0
        }


class FileAdaptor(BaseAdaptor):
    """
    File system adaptor for reading from and writing to files.
    
    Supports multiple file formats and modes of operation.
    """
    
    def __init__(self, name: str = "file_adaptor", config: Optional[Dict[str, Any]] = None):
        """
        Initialize file adaptor.
        
        Config options:
            - input_file: Path to input file (for reading)
            - output_file: Path to output file (for writing)
            - mode: "read", "write", "append", "read_write"
            - format: "text", "json", "jsonl"
            - encoding: File encoding (default: "utf-8")
            - create_if_missing: Create files if they don't exist (default: True)
        """
        super().__init__(name, config)
        self.input_file = None
        self.output_file = None
        self.mode = self.config.get("mode", "read_write")
        self.format = self.config.get("format", "text")
        self.encoding = self.config.get("encoding", "utf-8")
        self.create_if_missing = self.config.get("create_if_missing", True)
        
        # Initialize file paths
        if "input_file" in self.config:
            self.input_file = Path(self.config["input_file"])
        if "output_file" in self.config:
            self.output_file = Path(self.config["output_file"])
        
        # File handles
        self.input_handle = None
        self.output_handle = None
        self.current_line = 0
        
    def connect(self) -> bool:
        """Open file connections based on mode."""
        try:
            # Open input file if needed
            if self.mode in ["read", "read_write"] and self.input_file:
                if not self.input_file.exists():
                    if self.create_if_missing:
                        self.input_file.touch()
                    else:
                        raise FileNotFoundError(f"Input file not found: {self.input_file}")
                
                self.input_handle = open(self.input_file, 'r', encoding=self.encoding)
                self.logger.info(f"Opened input file: {self.input_file}")
            
            # Open output file if needed
            if self.mode in ["write", "append", "read_write"] and self.output_file:
                mode = 'a' if self.mode == "append" else 'w'
                self.output_handle = open(self.output_file, mode, encoding=self.encoding)
                self.logger.info(f"Opened output file: {self.output_file}")
            
            self.is_connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect file adaptor: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Close file handles."""
        try:
            if self.input_handle:
                self.input_handle.close()
                self.input_handle = None
            
            if self.output_handle:
                self.output_handle.close()
                self.output_handle = None
            
            self.is_connected = False
            self.logger.info("File adaptor disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting file adaptor: {e}")
            return False
    
    def get_input(self) -> str:
        """Read input from file."""
        if not self.is_connected:
            if not self.connect():
                return ""
        
        if not self.input_handle:
            self.logger.error("No input file configured")
            return ""
        
        try:
            if self.format == "text":
                # Read line by line
                line = self.input_handle.readline()
                if not line:  # End of file
                    if self.config.get("loop", False):
                        self.input_handle.seek(0)
                        line = self.input_handle.readline()
                    else:
                        return ""
                
                self.current_line += 1
                return line.strip()
                
            elif self.format == "json":
                # Read JSON file (assumes one JSON object per call)
                content = self.input_handle.read()
                if not content:
                    return ""
                
                data = json.loads(content)
                return json.dumps(data)
                
            elif self.format == "jsonl":
                # Read JSON Lines
                line = self.input_handle.readline()
                if not line:
                    return ""
                
                try:
                    data = json.loads(line.strip())
                    return json.dumps(data)
                except json.JSONDecodeError:
                    return line.strip()
                    
            else:
                self.logger.error(f"Unsupported format: {self.format}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error reading from file: {e}")
            return ""
    
    def send_output(self, output: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Write output to file."""
        if not self.is_connected:
            if not self.connect():
                return False
        
        if not self.output_handle:
            self.logger.error("No output file configured")
            return False
        
        try:
            timestamp = datetime.now().isoformat()
            
            if self.format == "text":
                # Write plain text
                if metadata:
                    self.output_handle.write(f"[{timestamp}] {output}\n")
                    self.output_handle.write(f"Metadata: {json.dumps(metadata)}\n\n")
                else:
                    self.output_handle.write(f"[{timestamp}] {output}\n\n")
                    
            elif self.format in ["json", "jsonl"]:
                # Write structured data
                data = {
                    "timestamp": timestamp,
                    "output": output,
                    "adaptor": self.name,
                }
                
                if metadata:
                    data["metadata"] = metadata
                
                if self.format == "jsonl":
                    self.output_handle.write(json.dumps(data) + "\n")
                else:
                    # JSON format - append to array or write as object
                    current_pos = self.output_handle.tell()
                    if current_pos == 0:
                        # Start new JSON array
                        self.output_handle.write(json.dumps([data], indent=2))
                    else:
                        # This is complex for JSON - better to use JSONL
                        self.logger.warning("Appending to JSON file not supported, using JSONL format")
                        self.output_handle.seek(0)
                        content = self.output_handle.read()
                        if content:
                            try:
                                existing = json.loads(content)
                                if isinstance(existing, list):
                                    existing.append(data)
                                    self.output_handle.seek(0)
                                    self.output_handle.truncate()
                                    self.output_handle.write(json.dumps(existing, indent=2))
                            except json.JSONDecodeError:
                                # Fall back to JSONL
                                self.output_handle.write(json.dumps(data) + "\n")
            
            self.output_handle.flush()
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing to file: {e}")
            return False
    
    def validate_config(self) -> List[str]:
        """Validate file adaptor configuration."""
        errors = super().validate_config()
        
        valid_modes = ["read", "write", "append", "read_write"]
        if self.mode not in valid_modes:
            errors.append(f"Invalid mode: {self.mode}. Valid modes: {valid_modes}")
        
        valid_formats = ["text", "json", "jsonl"]
        if self.format not in valid_formats:
            errors.append(f"Invalid format: {self.format}. Valid formats: {valid_formats}")
        
        if self.mode in ["read", "read_write"] and not self.input_file:
            errors.append("Input file required for read modes")
        
        if self.mode in ["write", "append", "read_write"] and not self.output_file:
            errors.append("Output file required for write modes")
        
        return errors
    
    def get_status(self) -> Dict[str, Any]:
        """Get file adaptor status."""
        status = super().get_status()
        status.update({
            "input_file": str(self.input_file) if self.input_file else None,
            "output_file": str(self.output_file) if self.output_file else None,
            "mode": self.mode,
            "format": self.format,
            "current_line": self.current_line,
            "input_handle_open": self.input_handle is not None,
            "output_handle_open": self.output_handle is not None,
        })
        return status


class CLIAdaptor(BaseAdaptor):
    """
    Command-line interface adaptor for terminal interaction.
    
    Supports interactive mode, script execution, and command processing.
    """
    
    def __init__(self, name: str = "cli_adaptor", config: Optional[Dict[str, Any]] = None):
        """
        Initialize CLI adaptor.
        
        Config options:
            - interactive: Run in interactive mode (default: True)
            - prompt: Custom prompt string
            - history_file: Path to command history file
            - max_history: Maximum history entries to keep
            - echo_input: Echo user input (default: True)
            - color_output: Use colored output (default: True)
            - clear_screen: Clear screen on start (default: False)
        """
        super().__init__(name, config)
        self.interactive = self.config.get("interactive", True)
        self.prompt = self.config.get("prompt", "> ")
        self.history_file = self.config.get("history_file")
        self.max_history = self.config.get("max_history", 1000)
        self.echo_input = self.config.get("echo_input", True)
        self.color_output = self.config.get("color_output", True)
        self.clear_screen = self.config.get("clear_screen", False)
        
        # Command history
        self.history: List[str] = []
        self.history_index = 0
        
        # Color codes
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
            "bg_blue": "\033[44m",
        }
    
    def connect(self) -> bool:
        """Initialize CLI interface."""
        try:
            # Load command history
            if self.history_file:
                self._load_history()
            
            # Clear screen if configured
            if self.clear_screen:
                self._clear_screen()
            
            # Print welcome message
            self._print_welcome()
            
            self.is_connected = True
            self.logger.info("CLI adaptor connected")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect CLI adaptor: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Clean up CLI interface."""
        try:
            # Save command history
            if self.history_file:
                self._save_history()
            
            # Print goodbye message
            if self.interactive:
                self._print_colored("\nGoodbye!\n", "green")
            
            self.is_connected = False
            self.logger.info("CLI adaptor disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting CLI adaptor: {e}")
            return False
    
    def get_input(self) -> str:
        """Get input from command line."""
        if not self.is_connected:
            if not self.connect():
                return ""
        
        try:
            if self.interactive:
                # Interactive mode with prompt
                self._print_prompt()
                
                # Read input with support for history
                import readline  # Optional for better CLI experience
                line = input()
                
                # Add to history
                if line.strip():
                    self.history.append(line.strip())
                    self.history_index = len(self.history)
                    
                    # Trim history if too long
                    if len(self.history) > self.max_history:
                        self.history = self.history[-self.max_history:]
                
                return line.strip()
            else:
                # Non-interactive mode (read from stdin)
                line = sys.stdin.readline()
                if not line:  # EOF
                    return ""
                return line.strip()
                
        except (EOFError, KeyboardInterrupt):
            # Handle Ctrl+D and Ctrl+C
            return "exit"
        except Exception as e:
            self.logger.error(f"Error reading CLI input: {e}")
            return ""
    
    def send_output(self, output: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Send output to command line."""
        try:
            # Format output with metadata if provided
            formatted_output = self._format_output(output, metadata)
            
            # Print to stdout
            print(formatted_output)
            
            # Also log if configured
            if self.config.get("log_output", False):
                self.logger.info(f"CLI output: {output[:100]}...")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending CLI output: {e}")
            return False
    
    def _print_welcome(self) -> None:
        """Print welcome message."""
        welcome = f"""
        ╔══════════════════════════════════════════════════╗
        ║            BLUX-cA Command Line Interface        ║
        ║            Adaptor: {self.name:<20}           ║
        ╚══════════════════════════════════════════════════╝
        
        Type 'help' for commands, 'exit' to quit.
        """
        
        self._print_colored(welcome, "cyan")
    
    def _print_prompt(self) -> None:
        """Print command prompt."""
        prompt = f"{self.prompt}"
        self._print_colored(prompt, "green", end="")
    
    def _print_colored(self, text: str, color: str, end: str = "\n") -> None:
        """Print colored text if enabled."""
        if self.color_output and color in self.colors:
            print(f"{self.colors[color]}{text}{self.colors['reset']}", end=end)
        else:
            print(text, end=end)
    
    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _format_output(self, output: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Format output for display."""
        lines = []
        
        # Add timestamp if configured
        if self.config.get("show_timestamps", False):
            timestamp = datetime.now().strftime("%H:%M:%S")
            lines.append(self._format_colored(f"[{timestamp}]", "dim"))
        
        # Add adaptor name if configured
        if self.config.get("show_adaptor", True):
            lines.append(self._format_colored(f"[{self.name}]", "blue"))
        
        # Add output
        lines.append(output)
        
        # Add metadata if provided
        if metadata and self.config.get("show_metadata", False):
            lines.append(self._format_colored("Metadata:", "dim"))
            for key, value in metadata.items():
                if isinstance(value, dict):
                    value_str = json.dumps(value, indent=2)
                else:
                    value_str = str(value)
                lines.append(f"  {key}: {value_str}")
        
        return "\n".join(lines)
    
    def _format_colored(self, text: str, color: str) -> str:
        """Format text with color if enabled."""
        if self.color_output and color in self.colors:
            return f"{self.colors[color]}{text}{self.colors['reset']}"
        return text
    
    def _load_history(self) -> None:
        """Load command history from file."""
        try:
            if self.history_file and os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = [line.strip() for line in f if line.strip()]
                self.logger.debug(f"Loaded {len(self.history)} history entries")
        except Exception as e:
            self.logger.warning(f"Failed to load history: {e}")
    
    def _save_history(self) -> None:
        """Save command history to file."""
        try:
            if self.history_file:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    for entry in self.history:
                        f.write(entry + "\n")
                self.logger.debug(f"Saved {len(self.history)} history entries")
        except Exception as e:
            self.logger.warning(f"Failed to save history: {e}")
    
    def validate_config(self) -> List[str]:
        """Validate CLI adaptor configuration."""
        errors = super().validate_config()
        
        if not isinstance(self.interactive, bool):
            errors.append("Interactive must be boolean")
        
        if self.history_file:
            hist_path = Path(self.history_file)
            if not hist_path.parent.exists():
                errors.append(f"History file directory does not exist: {hist_path.parent}")
        
        return errors
    
    def get_status(self) -> Dict[str, Any]:
        """Get CLI adaptor status."""
        status = super().get_status()
        status.update({
            "interactive": self.interactive,
            "history_size": len(self.history),
            "color_enabled": self.color_output,
            "prompt": self.prompt,
        })
        return status


class DatabaseAdaptor(BaseAdaptor):
    """
    Database adaptor for persistent storage of interactions.
    
    Supports SQLite (default) and can be extended for other databases.
    """
    
    def __init__(self, name: str = "database_adaptor", config: Optional[Dict[str, Any]] = None):
        """
        Initialize database adaptor.
        
        Config options:
            - database_url: Database connection URL
            - driver: Database driver ("sqlite", "postgresql", "mysql") - default: "sqlite"
            - table_name: Table name for storing interactions
            - auto_create_tables: Create tables if they don't exist (default: True)
            - max_connections: Maximum database connections
            - connection_timeout: Connection timeout in seconds
        """
        super().__init__(name, config)
        self.database_url = self.config.get("database_url", "blux_ca.db")
        self.driver = self.config.get("driver", "sqlite").lower()
        self.table_name = self.config.get("table_name", "interactions")
        self.auto_create_tables = self.config.get("auto_create_tables", True)
        self.max_connections = self.config.get("max_connections", 5)
        self.connection_timeout = self.config.get("connection_timeout", 30)
        
        # Database connection
        self.connection = None
        self.cursor = None
        
    def connect(self) -> bool:
        """Connect to database."""
        try:
            if self.driver == "sqlite":
                # SQLite connection
                self.connection = sqlite3.connect(
                    self.database_url,
                    timeout=self.connection_timeout
                )
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()
                
                # Enable foreign keys and other pragmas
                self.cursor.execute("PRAGMA foreign_keys = ON")
                self.cursor.execute("PRAGMA journal_mode = WAL")
                
            # Note: Other database drivers would be implemented here
            # elif self.driver == "postgresql":
            #     import psycopg2
            #     self.connection = psycopg2.connect(self.database_url)
            #     self.cursor = self.connection.cursor()
            
            else:
                raise ValueError(f"Unsupported database driver: {self.driver}")
            
            # Create tables if needed
            if self.auto_create_tables:
                self._create_tables()
            
            self.is_connected = True
            self.logger.info(f"Connected to database: {self.database_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from database."""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            
            if self.connection:
                self.connection.close()
                self.connection = None
            
            self.is_connected = False
            self.logger.info("Database adaptor disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting from database: {e}")
            return False
    
    def get_input(self) -> str:
        """
        Get input from database.
        
        Note: This adaptor is primarily for output storage.
        Input retrieval would be for replaying previous interactions.
        """
        if not self.is_connected:
            if not self.connect():
                return ""
        
        try:
            # Query for latest input (for testing/replay)
            query = f"""
            SELECT input_text FROM {self.table_name}
            ORDER BY timestamp DESC
            LIMIT 1
            """
            
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                return ""
                
        except Exception as e:
            self.logger.error(f"Error reading from database: {e}")
            return ""
    
    def send_output(self, output: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store output in database."""
        if not self.is_connected:
            if not self.connect():
                return False
        
        try:
            # Prepare data for insertion
            timestamp = datetime.now().isoformat()
            metadata_json = json.dumps(metadata or {})
            
            # Insert interaction
            query = f"""
            INSERT INTO {self.table_name} 
            (timestamp, output_text, metadata, adaptor_name)
            VALUES (?, ?, ?, ?)
            """
            
            self.cursor.execute(query, (timestamp, output, metadata_json, self.name))
            self.connection.commit()
            
            self.logger.debug(f"Stored interaction in database (ID: {self.cursor.lastrowid})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing to database: {e}")
            self.connection.rollback()
            return False
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            # Main interactions table
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                input_text TEXT,
                output_text TEXT NOT NULL,
                user_type TEXT,
                decision TEXT,
                metadata TEXT,
                adaptor_name TEXT,
                session_id TEXT,
                recovery_state TEXT,
                clarity_scores TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            self.cursor.execute(create_table_query)
            
            # Create indexes for faster queries
            index_queries = [
                f"CREATE INDEX IF NOT EXISTS idx_timestamp ON {self.table_name}(timestamp)",
                f"CREATE INDEX IF NOT EXISTS idx_session ON {self.table_name}(session_id)",
                f"CREATE INDEX IF NOT EXISTS idx_adaptor ON {self.table_name}(adaptor_name)",
                f"CREATE INDEX IF NOT EXISTS idx_recovery_state ON {self.table_name}(recovery_state)",
            ]
            
            for query in index_queries:
                self.cursor.execute(query)
            
            self.connection.commit()
            self.logger.info(f"Created/verified table: {self.table_name}")
            
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise
    
    def query_interactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adaptor_name: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query stored interactions.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            adaptor_name: Filter by adaptor name
            session_id: Filter by session ID
            limit: Maximum number of results
            
        Returns:
            List of interaction records
        """
        if not self.is_connected:
            if not self.connect():
                return []
        
        try:
            # Build WHERE clause
            conditions = []
            params = []
            
            if start_date:
                conditions.append("timestamp >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("timestamp <= ?")
                params.append(end_date)
            
            if adaptor_name:
                conditions.append("adaptor_name = ?")
                params.append(adaptor_name)
            
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Execute query
            query = f"""
            SELECT * FROM {self.table_name}
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
            """
            
            params.append(limit)
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            # Convert to dictionaries
            results = []
            for row in rows:
                result = dict(row)
                
                # Parse JSON fields
                if result.get("metadata"):
                    try:
                        result["metadata"] = json.loads(result["metadata"])
                    except json.JSONDecodeError:
                        pass
                
                if result.get("clarity_scores"):
                    try:
                        result["clarity_scores"] = json.loads(result["clarity_scores"])
                    except json.JSONDecodeError:
                        pass
                
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error querying interactions: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.is_connected:
            if not self.connect():
                return {"error": "Not connected"}
        
        try:
            stats = {}
            
            # Total interactions
            self.cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            stats["total_interactions"] = self.cursor.fetchone()[0]
            
            # Interactions by adaptor
            self.cursor.execute(f"""
                SELECT adaptor_name, COUNT(*) as count 
                FROM {self.table_name} 
                GROUP BY adaptor_name
            """)
            stats["by_adaptor"] = dict(self.cursor.fetchall())
            
            # Recent activity
            self.cursor.execute(f"""
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM {self.table_name}
                WHERE timestamp >= date('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """)
            stats["recent_activity"] = dict(self.cursor.fetchall())
            
            # Database size (SQLite specific)
            if self.driver == "sqlite":
                self.cursor.execute("PRAGMA page_size")
                page_size = self.cursor.fetchone()[0]
                
                self.cursor.execute("PRAGMA page_count")
                page_count = self.cursor.fetchone()[0]
                
                stats["database_size_mb"] = (page_size * page_count) / (1024 * 1024)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    def validate_config(self) -> List[str]:
        """Validate database adaptor configuration."""
        errors = super().validate_config()
        
        valid_drivers = ["sqlite", "postgresql", "mysql"]
        if self.driver not in valid_drivers:
            errors.append(f"Invalid driver: {self.driver}. Valid drivers: {valid_drivers}")
        
        if not self.table_name:
            errors.append("Table name is required")
        
        # Check SQLite file path if using SQLite
        if self.driver == "sqlite":
            db_path = Path(self.database_url)
            if db_path.parent and not db_path.parent.exists():
                errors.append(f"SQLite database directory does not exist: {db_path.parent}")
        
        return errors
    
    def get_status(self) -> Dict[str, Any]:
        """Get database adaptor status."""
        status = super().get_status()
        status.update({
            "driver": self.driver,
            "database_url": self.database_url,
            "table_name": self.table_name,
            "auto_create_tables": self.auto_create_tables,
        })
        
        # Add stats if connected
        if self.is_connected:
            try:
                stats = self.get_stats()
                status["stats"] = stats
            except Exception as e:
                status["stats_error"] = str(e)
        
        return status


# Import the previously defined dummy_local adaptor
from .dummy_local import DummyLocalAdaptor

# Optional adaptors (may have additional dependencies)
try:
    from .http_api_adaptor import HTTPAPIAdaptor
    HTTP_API_AVAILABLE = True
except ImportError:
    HTTPAPIAdaptor = None
    HTTP_API_AVAILABLE = False
    logger.debug("HTTPAPIAdaptor not available (optional dependency)")

try:
    from .webhook_adaptor import WebhookAdaptor
    WEBHOOK_AVAILABLE = True
except ImportError:
    WebhookAdaptor = None
    WEBHOOK_AVAILABLE = False
    logger.debug("WebhookAdaptor not available (optional dependency)")

try:
    from .websocket_adaptor import WebSocketAdaptor
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WebSocketAdaptor = None
    WEBSOCKET_AVAILABLE = False
    logger.debug("WebSocketAdaptor not available (optional dependency)")

try:
    from .slack_adaptor import SlackAdaptor
    SLACK_AVAILABLE = True
except ImportError:
    SlackAdaptor = None
    SLACK_AVAILABLE = False
    logger.debug("SlackAdaptor not available (optional dependency)")

try:
    from .discord_adaptor import DiscordAdaptor
    DISCORD_AVAILABLE = True
except ImportError:
    DiscordAdaptor = None
    DISCORD_AVAILABLE = False
    logger.debug("DiscordAdaptor not available (optional dependency)")


class AdaptorFactory:
    """
    Factory for creating adaptor instances.
    
    Simplifies adaptor creation and configuration.
    """
    
    # Registry of available adaptor types
    _adaptor_types: Dict[str, Any] = {
        "dummy": DummyLocalAdaptor,
        "file": FileAdaptor,
        "cli": CLIAdaptor,
        "database": DatabaseAdaptor,
    }
    
    @classmethod
    def register_adaptor(cls, name: str, adaptor_class: Any) -> None:
        """
        Register a new adaptor type.
        
        Args:
            name: Type name for the adaptor
            adaptor_class: The adaptor class to register
        """
        cls._adaptor_types[name] = adaptor_class
        logger.info(f"Registered adaptor type: {name}")
    
    @classmethod
    def create_adaptor(
        cls, 
        adaptor_type: str, 
        name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseAdaptor]:
        """
        Create an adaptor instance.
        
        Args:
            adaptor_type: Type of adaptor to create
            name: Name for the adaptor instance
            config: Configuration dictionary
            
        Returns:
            BaseAdaptor instance or None if creation failed
        """
        if adaptor_type not in cls._adaptor_types:
            logger.error(f"Unknown adaptor type: {adaptor_type}")
            return None
        
        try:
            # Add optional adaptors to registry if available
            if adaptor_type == "http" and HTTP_API_AVAILABLE and HTTPAPIAdaptor:
                cls._adaptor_types["http"] = HTTPAPIAdaptor
            elif adaptor_type == "webhook" and WEBHOOK_AVAILABLE and WebhookAdaptor:
                cls._adaptor_types["webhook"] = WebhookAdaptor
            elif adaptor_type == "websocket" and WEBSOCKET_AVAILABLE and WebSocketAdaptor:
                cls._adaptor_types["websocket"] = WebSocketAdaptor
            elif adaptor_type == "slack" and SLACK_AVAILABLE and SlackAdaptor:
                cls._adaptor_types["slack"] = SlackAdaptor
            elif adaptor_type == "discord" and DISCORD_AVAILABLE and DiscordAdaptor:
                cls._adaptor_types["discord"] = DiscordAdaptor
            
            adaptor_class = cls._adaptor_types[adaptor_type]
            instance = adaptor_class(name=name, config=config or {})
            
            # Validate configuration
            errors = instance.validate_config()
            if errors:
                logger.error(f"Adaptor configuration errors: {errors}")
                return None
            
            logger.info(f"Created adaptor: {name} ({adaptor_type})")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create adaptor {adaptor_type}: {e}")
            return None
    
    @classmethod
    def list_available_adaptors(cls) -> List[str]:
        """
        List all available adaptor types.
        
        Returns:
            List[str]: List of adaptor type names
        """
        types = list(cls._adaptor_types.keys())
        
        # Add optional adaptors if available
        if HTTP_API_AVAILABLE:
            types.append("http")
        if WEBHOOK_AVAILABLE:
            types.append("webhook")
        if WEBSOCKET_AVAILABLE:
            types.append("websocket")
        if SLACK_AVAILABLE:
            types.append("slack")
        if DISCORD_AVAILABLE:
            types.append("discord")
            
        return sorted(types)


def create_adaptor(
    adaptor_type: str, 
    name: str, 
    config: Optional[Dict[str, Any]] = None
) -> Optional[BaseAdaptor]:
    """
    Convenience function for creating adaptors.
    
    Args:
        adaptor_type: Type of adaptor to create
        name: Name for the adaptor instance
        config: Configuration dictionary
        
    Returns:
        BaseAdaptor instance or None if creation failed
    """
    return AdaptorFactory.create_adaptor(adaptor_type, name, config)


# Export public interface
__all__ = [
    # Base classes
    "BaseAdaptor",
    "AdaptorFactory",
    
    # Always available adaptors
    "DummyLocalAdaptor",
    "FileAdaptor",
    "CLIAdaptor",
    "DatabaseAdaptor",
    
    # Optional adaptors (may be None)
    "HTTPAPIAdaptor",
    "WebhookAdaptor",
    "WebSocketAdaptor",
    "SlackAdaptor",
    "DiscordAdaptor",
    
    # Factory function
    "create_adaptor",
    
    # Availability flags
    "HTTP_API_AVAILABLE",
    "WEBHOOK_AVAILABLE",
    "WEBSOCKET_AVAILABLE",
    "SLACK_AVAILABLE",
    "DISCORD_AVAILABLE",
]