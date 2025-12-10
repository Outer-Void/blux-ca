"""
HTTP API Adaptor for BLUX-cA.

Provides REST API and WebSocket interfaces for external systems to interact with BLUX-cA.
Supports authentication, rate limiting, and comprehensive monitoring.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple, Callable
from uuid import uuid4

from flask import Flask, request, jsonify, Response, abort
from flask_cors import CORS
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

# Optional WebSocket support
try:
    from flask_socketio import SocketIO, emit, join_room, leave_room
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False
    SocketIO = None
    emit = join_room = leave_room = None

from . import BaseAdaptor


class HTTPAPIAdaptor(BaseAdaptor):
    """
    HTTP API adaptor providing REST and WebSocket interfaces for BLUX-cA.
    
    Features:
    - REST API for synchronous requests
    - WebSocket for real-time bidirectional communication
    - Authentication (JWT and API key)
    - Rate limiting
    - Request logging and analytics
    - Health checks and monitoring
    - Swagger/OpenAPI documentation (optional)
    """
    
    def __init__(self, name: str = "http_api", config: Optional[Dict[str, Any]] = None):
        """
        Initialize HTTP API adaptor.
        
        Args:
            name: Adaptor instance name
            config: Configuration dictionary with keys:
                - host: Server host (default: "0.0.0.0")
                - port: Server port (default: 5000)
                - debug: Enable debug mode (default: False)
                - cors_enabled: Enable CORS (default: True)
                - auth_enabled: Enable authentication (default: False)
                - jwt_secret: Secret for JWT tokens
                - api_keys: List of valid API keys
                - rate_limit_enabled: Enable rate limiting (default: True)
                - rate_limit_requests: Requests per minute per IP (default: 60)
                - websocket_enabled: Enable WebSocket (default: True)
                - ssl_enabled: Enable SSL (default: False)
                - ssl_cert: SSL certificate path
                - ssl_key: SSL key path
                - log_requests: Log all requests (default: True)
                - max_request_size: Max request size in bytes (default: 10MB)
        """
        super().__init__(name, config)
        
        # Default configuration
        self.default_config = {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False,
            "cors_enabled": True,
            "auth_enabled": False,
            "jwt_secret": "blux-ca-secret-key-change-in-production",
            "api_keys": [],
            "rate_limit_enabled": True,
            "rate_limit_requests": 60,
            "rate_limit_window": 60,  # seconds
            "websocket_enabled": WEBSOCKET_AVAILABLE,
            "ssl_enabled": False,
            "log_requests": True,
            "max_request_size": 10 * 1024 * 1024,  # 10MB
            "session_timeout": 3600,  # 1 hour
            "enable_metrics": True,
            "enable_swagger": False,
        }
        
        # Merge provided config with defaults
        if config:
            self.default_config.update(config)
        self.config = self.default_config
        
        # Initialize Flask app
        self.app = Flask(self.name)
        
        # Configure CORS if enabled
        if self.config.get("cors_enabled", True):
            CORS(self.app)
        
        # Configure request size limit
        self.app.config['MAX_CONTENT_LENGTH'] = self.config.get("max_request_size", 10 * 1024 * 1024)
        
        # Initialize WebSocket if enabled
        self.socketio = None
        if self.config.get("websocket_enabled", False) and WEBSOCKET_AVAILABLE:
            self.socketio = SocketIO(
                self.app, 
                cors_allowed_origins="*" if self.config.get("cors_enabled", True) else None,
                async_mode='threading'
            )
        
        # State tracking
        self.request_count = 0
        self.active_connections = set()
        self.rate_limit_store: Dict[str, List[float]] = {}  # IP -> timestamps
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_id -> session data
        self.metrics = {
            "requests_total": 0,
            "requests_by_endpoint": {},
            "requests_by_method": {},
            "errors_by_type": {},
            "response_times": [],
            "active_sessions": 0,
            "websocket_connections": 0,
        }
        
        # Initialize routes and middleware
        self._setup_middleware()
        self._setup_routes()
        
        self.logger.info(f"HTTP API adaptor initialized on {self.config['host']}:{self.config['port']}")
    
    def _setup_middleware(self) -> None:
        """Setup Flask middleware."""
        
        @self.app.before_request
        def before_request():
            """Process before each request."""
            request.start_time = time.time()
            request.request_id = str(uuid4())
            
            # Log request if enabled
            if self.config.get("log_requests", True):
                self.logger.info(
                    f"Request [{request.request_id}]: {request.method} {request.path} "
                    f"from {request.remote_addr}"
                )
            
            # Check rate limiting
            if self.config.get("rate_limit_enabled", True):
                if not self._check_rate_limit(request.remote_addr):
                    abort(429, description="Rate limit exceeded")
            
            # Check authentication for protected endpoints
            if self.config.get("auth_enabled", False):
                if request.endpoint and not request.endpoint.startswith(('auth_', 'health_', 'docs_')):
                    auth_result = self._authenticate_request(request)
                    if not auth_result[0]:
                        abort(401, description=auth_result[1])
                    request.user = auth_result[1]  # Store user info
        
        @self.app.after_request
        def after_request(response: Response) -> Response:
            """Process after each request."""
            # Calculate response time
            if hasattr(request, 'start_time'):
                response_time = time.time() - request.start_time
                self.metrics["response_times"].append(response_time)
                
                # Keep only last 1000 response times
                if len(self.metrics["response_times"]) > 1000:
                    self.metrics["response_times"] = self.metrics["response_times"][-1000:]
                
                # Add response time header
                response.headers['X-Response-Time'] = f'{response_time:.3f}s'
            
            # Add request ID header
            if hasattr(request, 'request_id'):
                response.headers['X-Request-ID'] = request.request_id
            
            # Update metrics
            self._update_metrics(request, response)
            
            # Log response
            if self.config.get("log_requests", True):
                self.logger.info(
                    f"Response [{getattr(request, 'request_id', 'unknown')}]: "
                    f"{response.status_code} in {response_time:.3f}s"
                )
            
            return response
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"error": "Not found", "message": str(error)}), 404
        
        @self.app.errorhandler(429)
        def rate_limit_exceeded(error):
            return jsonify({"error": "Rate limit exceeded", "message": str(error)}), 429
        
        @self.app.errorhandler(401)
        def unauthorized(error):
            return jsonify({"error": "Unauthorized", "message": str(error)}), 401
        
        @self.app.errorhandler(500)
        def internal_error(error):
            self.logger.error(f"Internal server error: {error}")
            return jsonify({"error": "Internal server error", "message": str(error)}), 500
    
    def _setup_routes(self) -> None:
        """Setup all API routes."""
        
        # Health and status endpoints
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "service": "blux-ca",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "adaptor": self.name
            })
        
        @self.app.route('/metrics', methods=['GET'])
        @self._require_auth
        def get_metrics():
            """Get adaptor metrics."""
            return jsonify(self._get_formatted_metrics())
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get adaptor status."""
            return jsonify(self.get_status())
        
        # Authentication endpoints
        @self.app.route('/auth/login', methods=['POST'])
        def auth_login():
            """Login endpoint (JWT token generation)."""
            if not self.config.get("auth_enabled", False):
                return jsonify({"error": "Authentication disabled"}), 400
            
            data = request.json or {}
            username = data.get("username")
            password = data.get("password")
            api_key = data.get("api_key")
            
            # Validate credentials
            if api_key and api_key in self.config.get("api_keys", []):
                # API key authentication
                token = self._generate_token({"type": "api_key", "key": api_key})
                return jsonify({"token": token, "token_type": "bearer"})
            
            elif username and password:
                # TODO: Implement proper user authentication
                # For now, accept any username/password
                token = self._generate_token({"username": username, "type": "user"})
                return jsonify({"token": token, "token_type": "bearer"})
            
            return jsonify({"error": "Invalid credentials"}), 401
        
        @self.app.route('/auth/validate', methods=['POST'])
        def auth_validate():
            """Validate JWT token."""
            token = request.json.get("token") if request.json else None
            if not token:
                return jsonify({"error": "Token required"}), 400
            
            try:
                payload = jwt.decode(
                    token, 
                    self.config.get("jwt_secret"), 
                    algorithms=["HS256"]
                )
                return jsonify({"valid": True, "payload": payload})
            except jwt.ExpiredSignatureError:
                return jsonify({"valid": False, "error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"valid": False, "error": "Invalid token"}), 401
        
        # Core BLUX-cA endpoints
        @self.app.route('/api/v1/process', methods=['POST'])
        @self._require_auth
        def process_input():
            """
            Process user input through BLUX-cA.
            
            Request body:
            {
                "input": "User input text",
                "agent_name": "BLUX-cA",  # Optional
                "session_id": "existing-session-id",  # Optional
                "context": {}  # Optional additional context
            }
            """
            data = request.json or {}
            
            # Validate request
            validation_errors = self._validate_process_request(data)
            if validation_errors:
                return jsonify({"errors": validation_errors}), 400
            
            user_input = data.get("input", "")
            agent_name = data.get("agent_name", "BLUX-cA")
            session_id = data.get("session_id")
            context = data.get("context", {})
            
            try:
                # Get or create session
                if session_id and session_id in self.sessions:
                    session = self.sessions[session_id]
                else:
                    session_id = str(uuid4())
                    session = {
                        "id": session_id,
                        "created": datetime.now().isoformat(),
                        "interactions": [],
                        "user_state": None
                    }
                    self.sessions[session_id] = session
                
                # Process through orchestrator if available
                if hasattr(self, 'orchestrator') and self.orchestrator:
                    result = self.orchestrator.process_task(
                        user_input, 
                        agent_name=agent_name,
                        context=context
                    )
                    
                    # Store interaction in session
                    interaction = {
                        "timestamp": datetime.now().isoformat(),
                        "input": user_input,
                        "output": result,
                        "agent": agent_name
                    }
                    session["interactions"].append(interaction)
                    
                    # Clean old sessions
                    self._cleanup_sessions()
                    
                    return jsonify({
                        "session_id": session_id,
                        "response": result,
                        "interaction_count": len(session["interactions"]),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    # Fallback response if no orchestrator
                    fallback_response = {
                        "message": f"Received: {user_input}",
                        "status": "processed",
                        "agent": agent_name
                    }
                    return jsonify({
                        "session_id": session_id,
                        "response": fallback_response,
                        "note": "Orchestrator not connected - using fallback"
                    })
                    
            except Exception as e:
                self.logger.error(f"Error processing request: {e}")
                return jsonify({
                    "error": "Processing failed",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/v1/sessions/<session_id>', methods=['GET'])
        @self._require_auth
        def get_session(session_id: str):
            """Get session information and history."""
            if session_id not in self.sessions:
                return jsonify({"error": "Session not found"}), 404
            
            session = self.sessions[session_id]
            return jsonify(session)
        
        @self.app.route('/api/v1/sessions/<session_id>/interactions', methods=['GET'])
        @self._require_auth
        def get_session_interactions(session_id: str):
            """Get interactions for a session."""
            if session_id not in self.sessions:
                return jsonify({"error": "Session not found"}), 404
            
            interactions = self.sessions[session_id].get("interactions", [])
            return jsonify({
                "session_id": session_id,
                "interactions": interactions,
                "count": len(interactions)
            })
        
        @self.app.route('/api/v1/sessions/<session_id>', methods=['DELETE'])
        @self._require_auth
        def delete_session(session_id: str):
            """Delete a session."""
            if session_id in self.sessions:
                del self.sessions[session_id]
                return jsonify({"message": "Session deleted"})
            return jsonify({"error": "Session not found"}), 404
        
        # Batch processing endpoint
        @self.app.route('/api/v1/batch', methods=['POST'])
        @self._require_auth
        def batch_process():
            """
            Process multiple inputs in batch.
            
            Request body:
            {
                "inputs": ["input1", "input2", ...],
                "agent_name": "BLUX-cA",  # Optional
                "parallel": false  # Process in parallel (if supported)
            }
            """
            data = request.json or {}
            inputs = data.get("inputs", [])
            agent_name = data.get("agent_name", "BLUX-cA")
            
            if not inputs or not isinstance(inputs, list):
                return jsonify({"error": "Inputs must be a non-empty list"}), 400
            
            results = []
            for i, user_input in enumerate(inputs):
                try:
                    if hasattr(self, 'orchestrator') and self.orchestrator:
                        result = self.orchestrator.process_task(
                            str(user_input), 
                            agent_name=agent_name
                        )
                        results.append({
                            "input": user_input,
                            "output": result,
                            "status": "success",
                            "index": i
                        })
                    else:
                        results.append({
                            "input": user_input,
                            "output": {"message": f"Received: {user_input}"},
                            "status": "fallback",
                            "index": i
                        })
                except Exception as e:
                    results.append({
                        "input": user_input,
                        "error": str(e),
                        "status": "error",
                        "index": i
                    })
            
            return jsonify({
                "total": len(inputs),
                "successful": sum(1 for r in results if r["status"] == "success"),
                "failed": sum(1 for r in results if r["status"] == "error"),
                "results": results
            })
        
        # WebSocket event handlers (if enabled)
        if self.socketio:
            self._setup_websocket_events()
    
    def _setup_websocket_events(self) -> None:
        """Setup WebSocket event handlers."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle WebSocket connection."""
            self.active_connections.add(request.sid)
            self.metrics["websocket_connections"] = len(self.active_connections)
            self.logger.info(f"WebSocket connected: {request.sid}")
            emit('connected', {'message': 'Connected to BLUX-cA', 'sid': request.sid})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle WebSocket disconnection."""
            if request.sid in self.active_connections:
                self.active_connections.remove(request.sid)
                self.metrics["websocket_connections"] = len(self.active_connections)
                self.logger.info(f"WebSocket disconnected: {request.sid}")
        
        @self.socketio.on('process')
        def handle_process(data):
            """Process input via WebSocket."""
            if not data or 'input' not in data:
                emit('error', {'error': 'Input required'})
                return
            
            user_input = data['input']
            agent_name = data.get('agent_name', 'BLUX-cA')
            
            try:
                if hasattr(self, 'orchestrator') and self.orchestrator:
                    result = self.orchestrator.process_task(user_input, agent_name=agent_name)
                    emit('response', {
                        'input': user_input,
                        'response': result,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    emit('response', {
                        'input': user_input,
                        'response': {'message': f"Received: {user_input}"},
                        'note': 'Orchestrator not connected'
                    })
            except Exception as e:
                self.logger.error(f"WebSocket processing error: {e}")
                emit('error', {'error': str(e)})
    
    def _require_auth(self, f: Callable) -> Callable:
        """Decorator to require authentication."""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not self.config.get("auth_enabled", False):
                return f(*args, **kwargs)
            
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                abort(401, description="Missing or invalid Authorization header")
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            try:
                payload = jwt.decode(
                    token, 
                    self.config.get("jwt_secret"), 
                    algorithms=["HS256"]
                )
                request.user = payload
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                abort(401, description="Token expired")
            except jwt.InvalidTokenError:
                abort(401, description="Invalid token")
        
        return decorated
    
    def _check_rate_limit(self, ip_address: str) -> bool:
        """Check if IP address is within rate limits."""
        if not self.config.get("rate_limit_enabled", True):
            return True
        
        window = self.config.get("rate_limit_window", 60)
        max_requests = self.config.get("rate_limit_requests", 60)
        now = time.time()
        
        # Clean old timestamps
        if ip_address in self.rate_limit_store:
            self.rate_limit_store[ip_address] = [
                ts for ts in self.rate_limit_store[ip_address]
                if now - ts < window
            ]
        else:
            self.rate_limit_store[ip_address] = []
        
        # Check if within limits
        if len(self.rate_limit_store[ip_address]) >= max_requests:
            return False
        
        # Add current request timestamp
        self.rate_limit_store[ip_address].append(now)
        return True
    
    def _authenticate_request(self, request) -> Tuple[bool, Optional[Dict]]:
        """Authenticate incoming request."""
        # Check API key in header
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key in self.config.get("api_keys", []):
            return True, {"type": "api_key", "key": api_key}
        
        # Check JWT token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token, 
                    self.config.get("jwt_secret"), 
                    algorithms=["HS256"]
                )
                return True, payload
            except jwt.ExpiredSignatureError:
                return False, "Token expired"
            except jwt.InvalidTokenError:
                return False, "Invalid token"
        
        return False, "No valid authentication provided"
    
    def _generate_token(self, payload: Dict[str, Any]) -> str:
        """Generate JWT token."""
        payload['exp'] = datetime.now() + timedelta(seconds=self.config.get("session_timeout", 3600))
        payload['iat'] = datetime.now()
        return jwt.encode(payload, self.config.get("jwt_secret"), algorithm="HS256")
    
    def _validate_process_request(self, data: Dict[str, Any]) -> List[str]:
        """Validate process request data."""
        errors = []
        
        if 'input' not in data or not data['input']:
            errors.append("Input field is required")
        elif not isinstance(data['input'], str):
            errors.append("Input must be a string")
        elif len(data['input']) > 10000:  # Max input length
            errors.append("Input too long (max 10000 characters)")
        
        if 'agent_name' in data and not isinstance(data['agent_name'], str):
            errors.append("Agent name must be a string")
        
        return errors
    
    def _cleanup_sessions(self) -> None:
        """Clean up old sessions."""
        timeout = self.config.get("session_timeout", 3600)
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            created = datetime.fromisoformat(session['created'])
            if (now - created).total_seconds() > timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def _update_metrics(self, request, response) -> None:
        """Update metrics based on request/response."""
        self.metrics["requests_total"] += 1
        
        # Update by endpoint
        endpoint = request.endpoint or "unknown"
        self.metrics["requests_by_endpoint"][endpoint] = \
            self.metrics["requests_by_endpoint"].get(endpoint, 0) + 1
        
        # Update by method
        method = request.method
        self.metrics["requests_by_method"][method] = \
            self.metrics["requests_by_method"].get(method, 0) + 1
        
        # Update errors
        if response.status_code >= 400:
            error_type = f"http_{response.status_code}"
            self.metrics["errors_by_type"][error_type] = \
                self.metrics["errors_by_type"].get(error_type, 0) + 1
    
    def _get_formatted_metrics(self) -> Dict[str, Any]:
        """Get formatted metrics for API response."""
        response_times = self.metrics.get("response_times", [])
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "requests": {
                "total": self.metrics["requests_total"],
                "by_endpoint": self.metrics["requests_by_endpoint"],
                "by_method": self.metrics["requests_by_method"],
            },
            "errors": self.metrics["errors_by_type"],
            "performance": {
                "avg_response_time": f"{avg_response_time:.3f}s",
                "response_time_samples": len(response_times),
                "active_sessions": len(self.sessions),
                "websocket_connections": self.metrics.get("websocket_connections", 0),
            },
            "rate_limits": {
                "enabled": self.config.get("rate_limit_enabled", False),
                "active_ips": len(self.rate_limit_store),
            }
        }
    
    def connect(self) -> bool:
        """Start the HTTP server."""
        try:
            # Note: Actual server start happens in run() method
            self.is_connected = True
            self.logger.info(f"HTTP API adaptor '{self.name}' ready to connect")
            return True
        except Exception as e:
            self.logger.error(f"Failed to prepare HTTP API adaptor: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Stop the HTTP server."""
        self.is_connected = False
        # In a real implementation, we would stop the Flask server here
        self.logger.info(f"HTTP API adaptor '{self.name}' disconnected")
        return True
    
    def get_input(self) -> str:
        """Not applicable for HTTP API adaptor (uses request/response)."""
        raise NotImplementedError("HTTP API adaptor uses request/response model, not get_input")
    
    def send_output(self, output: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Not applicable for HTTP API adaptor (uses request/response)."""
        raise NotImplementedError("HTTP API adaptor uses request/response model, not send_output")
    
    def run(self) -> None:
        """Run the HTTP server."""
        host = self.config.get("host", "0.0.0.0")
        port = self.config.get("port", 5000)
        debug = self.config.get("debug", False)
        
        self.logger.info(f"Starting HTTP API server on {host}:{port}")
        
        if self.socketio:
            # Run with WebSocket support
            ssl_context = None
            if self.config.get("ssl_enabled", False):
                ssl_context = (
                    self.config.get("ssl_cert"),
                    self.config.get("ssl_key")
                )
            
            self.socketio.run(
                self.app, 
                host=host, 
                port=port, 
                debug=debug,
                ssl_context=ssl_context
            )
        else:
            # Run standard Flask server
            ssl_context = None
            if self.config.get("ssl_enabled", False):
                ssl_context = (
                    self.config.get("ssl_cert"),
                    self.config.get("ssl_key")
                )
            
            self.app.run(
                host=host, 
                port=port, 
                debug=debug,
                ssl_context=ssl_context
            )
    
    def get_status(self) -> Dict[str, Any]:
        """Get adaptor status with server information."""
        base_status = super().get_status()
        
        # Add HTTP-specific status
        base_status.update({
            "server": {
                "host": self.config.get("host"),
                "port": self.config.get("port"),
                "running": self.is_connected,
                "websocket_enabled": self.socketio is not None,
                "auth_enabled": self.config.get("auth_enabled", False),
                "cors_enabled": self.config.get("cors_enabled", True),
            },
            "metrics": {
                "total_requests": self.metrics.get("requests_total", 0),
                "active_sessions": len(self.sessions),
                "active_websocket_connections": self.metrics.get("websocket_connections", 0),
                "rate_limited_ips": len(self.rate_limit_store),
            }
        })
        
        return base_status
    
    def set_orchestrator(self, orchestrator) -> None:
        """Set the orchestrator for processing requests."""
        self.orchestrator = orchestrator
        self.logger.info("Orchestrator set for HTTP API adaptor")