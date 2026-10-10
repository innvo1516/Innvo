import json
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Optional
from pathlib import Path

import config
from brain.orchestrator import InnvoOrchestrator
from security.shadow_vault import ShadowVault

logger = logging.getLogger("InnvoAPI")

class InnvoAPIHandler(BaseHTTPRequestHandler):
    orchestrator: Optional[InnvoOrchestrator] = None

    def _set_cors_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        if path in ["", "/", "/api/health"]:
            self._set_cors_headers(200)
            res = {
                "status": "online",
                "name": config.ASSISTANT_NAME,
                "user": config.USER_NAME,
                "platform": "termux" if config.IS_TERMUX else ("windows" if config.IS_WINDOWS else "linux"),
                "voice_enabled": self.orchestrator.audio.enabled if self.orchestrator else False,
                "idle_curiosity": self.orchestrator.idle_daemon.is_enabled() if self.orchestrator else False
            }
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif path == "/api/memories":
            self._set_cors_headers(200)
            mems = self.orchestrator.memory_store.list_all_active() if self.orchestrator else []
            self.wfile.write(json.dumps({"memories": mems}).encode("utf-8"))

        elif path == "/api/tools":
            self._set_cors_headers(200)
            tools = self.orchestrator.registry.list_skills() if self.orchestrator else []
            self.wfile.write(json.dumps({"tools": tools}).encode("utf-8"))

        elif path == "/api/rules":
            self._set_cors_headers(200)
            if config.CONSTITUTION_PATH.exists():
                data = json.loads(config.CONSTITUTION_PATH.read_text(encoding="utf-8"))
            else:
                data = {"laws": []}
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif path == "/api/kg":
            self._set_cors_headers(200)
            triples = self.orchestrator.knowledge_graph.list_all() if self.orchestrator else []
            self.wfile.write(json.dumps({"triples": triples}).encode("utf-8"))

        elif path == "/api/stats":
            self._set_cors_headers(200)
            stats = {
                "memory": self.orchestrator.memory_store.get_stats() if self.orchestrator else {},
                "bandit": self.orchestrator.bandit.get_status() if self.orchestrator else {},
                "idle": self.orchestrator.get_idle_status() if self.orchestrator else {}
            }
            self.wfile.write(json.dumps(stats).encode("utf-8"))

        elif path == "/api/vault":
            self._set_cors_headers(200)
            vault = ShadowVault()
            snaps = vault.list_snapshots()
            self.wfile.write(json.dumps({"snapshots": snaps}).encode("utf-8"))

        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": f"Endpoint '{self.path}' not found."}).encode("utf-8"))

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = {}

        if path == "/api/chat":
            user_text = payload.get("text", "").strip()
            if not user_text:
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"error": "Empty text provided"}).encode("utf-8"))
                return

            if not self.orchestrator:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": "Orchestrator not initialized"}).encode("utf-8"))
                return

            result = self.orchestrator.process_input(user_text)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))

        elif path == "/api/idle":
            enable = payload.get("enable", False)
            if self.orchestrator:
                status = self.orchestrator.toggle_idle_learning(enable)
                self._set_cors_headers(200)
                self.wfile.write(json.dumps({"idle_learning_enabled": status}).encode("utf-8"))
            else:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": "Orchestrator not initialized"}).encode("utf-8"))

        elif path == "/api/clear":
            if self.orchestrator:
                self.orchestrator.clear_context()
                self._set_cors_headers(200)
                self.wfile.write(json.dumps({"success": True, "message": "Context cleared"}).encode("utf-8"))
            else:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": "Orchestrator not initialized"}).encode("utf-8"))

        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": f"POST endpoint '{self.path}' not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean logging
        logger.info("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))

def run_server(port: int = 8000, host: str = "0.0.0.0", orchestrator: Optional[InnvoOrchestrator] = None):
    """Starts the Innvo HTTP API Bridge for Flutter and Web clients."""
    orch = orchestrator or InnvoOrchestrator(voice_enabled=True)
    InnvoAPIHandler.orchestrator = orch

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, InnvoAPIHandler)
    print(f"\n=======================================================")
    print(f"⚡ [Innvo API Bridge] Online at http://{host}:{port}")
    print(f"Flutter Client Endpoint: http://localhost:{port}/api")
    print(f"Endpoints: /api/health, /api/chat, /api/memories, /api/tools")
    print(f"=======================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Innvo API Bridge] Shutting down...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
