from flask import Flask, request, jsonify

class HTTPAPIAdaptor:
    """
    HTTP API adaptor for external interaction with BLUX-cA.
    """
    def __init__(self, name="http_api_adaptor", orchestrator=None, host="0.0.0.0", port=5000):
        self.name = name
        self.orchestrator = orchestrator
        self.app = Flask(self.name)
        self.host = host
        self.port = port
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/process", methods=["POST"])
        def process_input():
            data = request.json
            user_input = data.get("input", "")
            agent_name = data.get("agent", None)
            if self.orchestrator:
                result = self.orchestrator.process_task(user_input, agent_name)
                return jsonify({"result": result})
            else:
                return jsonify({"error": "Orchestrator not connected."}), 500

    def run(self):
        self.app.run(host=self.host, port=self.port)