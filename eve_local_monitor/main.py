"""Main application for EVE Online Local Threat Monitor."""

import time
import signal
import sys
import configparser
import os
from .ocr_reader import LocalReader
from .esi_client import ESIClient
from .zkill_client import ZKillClient
from .threat_analyzer import ThreatAnalyzer
from .display import ThreatDisplay
from .web_server import ThreatWebServer


class LocalThreatMonitor:
    """Main threat monitoring application."""

    def __init__(self, screen_region=None, character_name="T zhong", enable_web=True):
        """
        Initialize monitor.

        Args:
            screen_region: (left, top, right, bottom) for Local window
            character_name: Your character name to exclude
            enable_web: Enable web dashboard (default: True)
        """
        self.screen_region = screen_region
        self.character_name = character_name
        self.enable_web = enable_web

        # Initialize components
        self.ocr = LocalReader(region=screen_region)
        self.esi = ESIClient()
        self.zkill = ZKillClient()
        self.analyzer = ThreatAnalyzer(exclude_character=character_name)
        self.display = ThreatDisplay()

        # Initialize web server if enabled
        self.web_server = None
        if self.enable_web:
            self.web_server = ThreatWebServer(monitor=self)

        self.running = False
        self.scan_interval = 10  # Scan every 10 seconds

        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print("\n\nShutting down...")
        self.stop()
        if self.web_server:
            print("Stopping web server...")
            # Give time for graceful shutdown
            import time
            time.sleep(1)
        sys.exit(0)

    def configure_region(self):
        """Interactive region configuration using GUI selector."""
        print("="*60)
        print("EVE ONLINE LOCAL THREAT MONITOR - Setup")
        print("="*60)
        print()
        print("Opening region selector...")
        print("Click and drag to select your EVE Local player list area")
        print()

        try:
            from .region_selector import RegionSelector, update_config_with_region

            selector = RegionSelector()
            region = selector.select_region()

            if region:
                self.screen_region = region
                self.ocr.configure_region(self.screen_region)

                # Update config file
                update_config_with_region(region)

                print(f"\nRegion configured: {self.screen_region}")
                print("\nTaking test screenshot...")

                self.ocr.save_debug_screenshot("test_screenshot.png")
                print("Test screenshot saved to: test_screenshot.png")

                return True
            else:
                print("\nSetup cancelled.")
                return False

        except Exception as e:
            print(f"Error during region selection: {e}")
            print("Falling back to manual entry...")
            return self._configure_region_manual()

    def _configure_region_manual(self):
        """Manual region configuration (fallback)."""
        print("\nEnter coordinates manually:")
        print("(You can use find_coordinates.py to get these values)")

        try:
            left = int(input("Left X coordinate: "))
            top = int(input("Top Y coordinate: "))
            right = int(input("Right X coordinate: "))
            bottom = int(input("Bottom Y coordinate: "))

            self.screen_region = (left, top, right, bottom)
            self.ocr.configure_region(self.screen_region)

            print(f"\nRegion configured: {self.screen_region}")
            return True

        except ValueError:
            print("Invalid input. Please enter numbers only.")
            return False

    def start(self):
        """Start the monitoring loop."""
        print("\n" + "="*60)
        print("EVE ONLINE LOCAL THREAT MONITOR")
        print("="*60)
        print(f"Character: {self.character_name}")
        print(f"Scan interval: {self.scan_interval} seconds")
        if self.enable_web:
            print(f"Web Dashboard: http://127.0.0.1:5000")
        print("="*60)
        print("\nStarting monitor... Press Ctrl+C to stop.")
        print()

        # Start web server in background if enabled
        if self.web_server:
            self.web_server.start_background()

        self.running = True
        last_scan_time = 0

        while self.running:
            current_time = time.time()

            # Check for web server control signals
            if self.web_server:
                if self.web_server.should_shutdown:
                    print("\nStop signal received from web dashboard...")
                    self.web_server.should_shutdown = False
                    self.web_server.monitor_running = False
                    self.running = False
                    print("Monitor stopped. Web server still running.")
                    print("Use the web dashboard to restart the monitor.")
                    # Wait for start signal
                    while not self.web_server.should_start and not self.web_server.should_exit:
                        time.sleep(1)

                    if self.web_server.should_exit:
                        print("\nExit signal received. Shutting down completely...")
                        sys.exit(0)

                    if self.web_server.should_start:
                        print("\nStart signal received from web dashboard...")
                        self.web_server.should_start = False
                        self.web_server.monitor_running = True
                        self.running = True
                        last_scan_time = 0
                        print("Monitor restarted successfully.")

                if self.web_server.should_restart:
                    print("\nRestart signal received from web dashboard...")
                    self.web_server.should_restart = False
                    print("Restarting monitor...")
                    # Just clear the cache and continue
                    self.analyzer.player_cache.clear()
                    print("Monitor restarted successfully.")

                if self.web_server.should_reconfigure:
                    print("\nReconfigure signal received from web dashboard...")
                    self.web_server.should_reconfigure = False
                    self.running = False
                    if self.configure_region():
                        print("Region reconfigured. Restarting monitor...")
                        self.running = True
                        last_scan_time = 0  # Force immediate scan
                    else:
                        print("Reconfiguration cancelled.")
                        continue

            # Check if it's time to scan
            if current_time - last_scan_time >= self.scan_interval:
                self.scan_and_update()
                last_scan_time = current_time

            time.sleep(1)  # Check every second

    def scan_and_update(self):
        """Perform one scan cycle."""
        # Step 1: OCR to get player names
        player_names = self.ocr.read_local_players()

        if not player_names:
            self.display.print_status("No players detected. Check OCR region configuration.")
            return

        # Step 2: Filter to new/updated players
        new_players = self.analyzer.filter_new_players(player_names)

        # Step 3: Query APIs for new players
        if new_players:
            self.display.print_status(f"Analyzing {len(new_players)} new player(s)...")

            # Get ESI data
            esi_data_batch = self.esi.get_character_info(new_players)

            # Get zKillboard data
            char_ids = [data['character_id'] for data in esi_data_batch.values() if 'character_id' in data]
            zkill_data_batch = self.zkill.get_batch_stats(char_ids)

            # Update analyzer with new data
            for player_name in new_players:
                if player_name in esi_data_batch:
                    esi_data = esi_data_batch[player_name]
                    char_id = esi_data.get('character_id')

                    if char_id and char_id in zkill_data_batch:
                        zkill_data = zkill_data_batch[char_id]
                    else:
                        zkill_data = {}

                    self.analyzer.update_player_data(player_name, esi_data, zkill_data)

        # Step 4: Get ranked threats for current players
        threats = self.analyzer.get_ranked_threats(player_names)

        # Step 5: Display
        self.display.display_threats(threats, len(player_names))

        # Step 6: Update web dashboard if enabled
        if self.web_server:
            self.web_server.update_threats(threats, len(player_names))

    def stop(self):
        """Stop monitoring."""
        self.running = False
        print("\nMonitor stopped.")


def load_config():
    """Load configuration from config.ini file."""
    config = configparser.ConfigParser()

    # Try to find config.ini in the project root
    # This script is in eve_local_monitor/, so go up one level
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(script_dir), 'config.ini')

    if os.path.exists(config_path):
        config.read(config_path)

        # Load character name
        character_name = config.get('General', 'character_name', fallback='T zhong')

        # Load region coordinates
        region = None
        try:
            left = config.getint('OCR', 'region_left')
            top = config.getint('OCR', 'region_top')
            right = config.getint('OCR', 'region_right')
            bottom = config.getint('OCR', 'region_bottom')

            if all([left, top, right, bottom]):
                region = (left, top, right, bottom)
        except (ValueError, configparser.NoOptionError):
            pass

        # Load scan interval
        scan_interval = config.getint('Monitoring', 'scan_interval', fallback=10)

        return character_name, region, scan_interval

    # Default values if no config file
    return "T zhong", None, 10


def main():
    """Main entry point."""
    # Load configuration
    character_name, region, scan_interval = load_config()

    monitor = LocalThreatMonitor(
        screen_region=region,
        character_name=character_name
    )

    # Set scan interval
    monitor.scan_interval = scan_interval

    # Interactive setup if no region configured
    if not monitor.screen_region:
        if not monitor.configure_region():
            print("Setup cancelled.")
            return

    # Start monitoring
    monitor.start()


if __name__ == "__main__":
    main()
