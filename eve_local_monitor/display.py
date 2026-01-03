"""Display module for threat monitor output."""

import os
import sys
from typing import List, Dict


class ThreatDisplay:
    """Displays threat information in terminal."""

    def __init__(self):
        """Initialize display."""
        # Fix Windows console encoding for emoji support
        if sys.platform == 'win32':
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except AttributeError:
                # Python < 3.7
                import codecs
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

    def clear_screen(self):
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def format_ships(self, top_ships: List[Dict]) -> str:
        """
        Format top ships list for display.

        Args:
            top_ships: List of ship dicts

        Returns:
            Formatted string
        """
        if not top_ships:
            return "No killboard data"

        ship_names = [ship['ship_name'] for ship in top_ships[:3]]  # Top 3
        return ", ".join(ship_names)

    def display_threats(self, threats: List[Dict], total_in_local: int):
        """
        Display ranked threats.

        Args:
            threats: List of threat dicts sorted by danger
            total_in_local: Total number of players in Local
        """
        self.clear_screen()

        print("="*80)
        print(f"  EVE ONLINE LOCAL THREAT MONITOR - {total_in_local} players in Local")
        print("="*80)
        print()

        if not threats:
            print("  No threat data available yet. Scanning...")
            print()
            print("="*80)
            return

        # Header
        print(f"{'':2} {'Player':<20} {'Corp/Alliance':<25} {'Danger':<8} {'K/D':<8} {'Ships':<20}")
        print("-"*80)

        # Display each threat
        for i, threat in enumerate(threats[:20], 1):  # Top 20
            emoji = self._get_emoji(threat['danger_ratio'])
            name = threat['name'][:19]  # Truncate if needed
            corp = threat['corporation'][:24]

            # Alliance if available
            if threat['alliance'] != 'None':
                alliance = f" [{threat['alliance'][:10]}]"
                corp = corp[:14] + alliance

            danger = f"{threat['danger_ratio']:.0f}%"

            # Kill/Death ratio
            kills = threat['kills']
            losses = threat['losses']
            if losses > 0:
                kd_ratio = kills / losses
                kd = f"{kills}/{losses}"
            else:
                kd = f"{kills}/0"

            # Solo vs gang
            solo = threat['solo_ratio']
            if solo >= 60:
                play_style = "(Solo)"
            elif solo >= 30:
                play_style = "(Mixed)"
            else:
                play_style = "(Gang)"

            # Top ships
            ships = self.format_ships(threat['top_ships'])[:19]

            print(f"{emoji} {name:<20} {corp:<25} {danger:<8} {kd:<8} {ships}")

        print("-"*80)
        print(f"Legend: 🔴 High Threat (70%+)  🟡 Medium (40-70%)  🟢 Low (10-40%)  ⚪ Minimal (<10%)")
        print("="*80)

    def _get_emoji(self, danger_ratio: float) -> str:
        """Get threat emoji."""
        if danger_ratio >= 70:
            return "🔴"
        elif danger_ratio >= 40:
            return "🟡"
        elif danger_ratio >= 10:
            return "🟢"
        else:
            return "⚪"

    def print_status(self, message: str):
        """
        Print a status message without clearing screen.

        Args:
            message: Status message
        """
        print(f"[STATUS] {message}")

    def print_error(self, message: str):
        """
        Print an error message.

        Args:
            message: Error message
        """
        print(f"[ERROR] {message}")
