"""Web server for EVE Local Threat Monitor dashboard."""

from flask import Flask, render_template, jsonify, Response
from flask_cors import CORS
import json
import time
from threading import Lock
from typing import Dict, List, Any
import os


class ThreatWebServer:
    """Web server for displaying threat data in browser."""

    def __init__(self, host='127.0.0.1', port=5000, monitor=None):
        """
        Initialize web server.

        Args:
            host: Host to bind to
            port: Port to bind to
            monitor: Reference to parent LocalThreatMonitor instance
        """
        self.host = host
        self.port = port
        self.monitor = monitor
        self.app = Flask(__name__,
                        template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
                        static_folder=os.path.join(os.path.dirname(__file__), 'static'))
        CORS(self.app)

        # Thread-safe data storage
        self.data_lock = Lock()
        self.current_threats: List[Dict[str, Any]] = []
        self.player_count = 0
        self.last_update = time.time()
        self.monitor_running = True
        self.should_shutdown = False
        self.should_start = False
        self.should_restart = False
        self.should_reconfigure = False
        self.should_exit = False

        # SSE clients
        self.sse_clients = []

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            """Serve main dashboard page."""
            return render_template('dashboard.html')

        @self.app.route('/api/threats')
        def get_threats():
            """Get current threat data."""
            with self.data_lock:
                return jsonify({
                    'threats': self.current_threats,
                    'player_count': self.player_count,
                    'last_update': self.last_update
                })

        @self.app.route('/api/stream')
        def stream():
            """Server-Sent Events stream for real-time updates."""
            def event_stream():
                # Send initial data
                with self.data_lock:
                    yield f"data: {json.dumps({'threats': self.current_threats, 'player_count': self.player_count})}\n\n"

                # Keep connection alive and send updates
                while True:
                    time.sleep(1)
                    # Client will poll /api/threats for updates
                    yield f"data: {json.dumps({'heartbeat': True})}\n\n"

            return Response(event_stream(), mimetype='text/event-stream')

        @self.app.route('/api/status')
        def get_status():
            """Get monitor status."""
            return jsonify({
                'monitor_running': self.monitor_running
            })

        @self.app.route('/api/stop', methods=['POST'])
        def stop_monitor():
            """Stop the monitor (web server stays running)."""
            print("\nStop requested from web dashboard...")
            self.should_shutdown = True
            return jsonify({'status': 'stop initiated'})

        @self.app.route('/api/start', methods=['POST'])
        def start_monitor():
            """Start the monitor."""
            print("\nStart requested from web dashboard...")
            self.should_start = True
            return jsonify({'status': 'start initiated'})

        @self.app.route('/api/exit', methods=['POST'])
        def exit_completely():
            """Exit the entire application."""
            print("\nExit requested from web dashboard...")
            self.should_exit = True
            return jsonify({'status': 'exit initiated'})

        @self.app.route('/api/restart', methods=['POST'])
        def restart():
            """Restart the monitor (clear cache)."""
            print("\nRestart requested from web dashboard...")
            self.should_restart = True
            return jsonify({'status': 'restart initiated'})

        @self.app.route('/api/reconfigure', methods=['POST'])
        def reconfigure():
            """Reconfigure OCR region."""
            print("\nReconfigure requested from web dashboard...")
            self.should_reconfigure = True
            return jsonify({'status': 'reconfigure initiated'})

    def update_threats(self, threats: List[Dict[str, Any]], player_count: int):
        """
        Update threat data (called by main monitor).

        Args:
            threats: List of threat dictionaries
            player_count: Total number of players in local
        """
        with self.data_lock:
            self.current_threats = threats
            self.player_count = player_count
            self.last_update = time.time()

    def run(self):
        """Run the web server."""
        print(f"\n{'='*60}")
        print(f"Web Dashboard: http://{self.host}:{self.port}")
        print(f"{'='*60}\n")
        self.app.run(host=self.host, port=self.port, threaded=True, debug=False)

    def start_background(self):
        """Start web server in background thread."""
        from threading import Thread
        thread = Thread(target=self.run, daemon=True)
        thread.start()
        print(f"Web dashboard started at http://{self.host}:{self.port}")
