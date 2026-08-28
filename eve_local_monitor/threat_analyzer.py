"""Threat analysis and player tracking."""

from typing import List, Dict
import time


class ThreatAnalyzer:
    """Analyzes and ranks player threats."""

    def __init__(self, exclude_character: str = "", cache_expiry: int = 3600):
        """
        Initialize threat analyzer.

        Args:
            exclude_character: Character name to exclude (your character)
        """
        self.exclude_character = self.normalize_name(exclude_character)
        self.known_players = {}  # char_name -> full data
        self.last_seen = {}  # char_name -> timestamp
        self.cache_expiry = max(0, cache_expiry)

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize OCR/API names while preserving EVE internal spaces."""
        return " ".join(str(name).strip().split())

    def filter_new_players(self, player_names: List[str]) -> List[str]:
        """Return unique, normalized names that are new or past the TTL."""
        current_time = time.time()
        new_players = []
        seen = set()

        for raw_name in player_names:
            name = self.normalize_name(raw_name)
            if not name or name in seen or name == self.exclude_character:
                continue
            seen.add(name)

            if name not in self.known_players:
                new_players.append(name)
            elif current_time - self.last_seen.get(name, 0) > self.cache_expiry:
                new_players.append(name)

        return new_players

    def update_player_data(self, player_name: str, esi_data: Dict, zkill_data: Dict):
        """
        Update stored data for a player.

        Args:
            player_name: Character name
            esi_data: Data from ESI (affiliations, etc)
            zkill_data: Data from zKillboard (stats, ships)
        """
        self.known_players[player_name] = {
            'name': player_name,
            'character_id': esi_data.get('character_id'),
            'corporation': esi_data.get('corporation_name', 'Unknown'),
            'alliance': esi_data.get('alliance_name', 'None'),
            'kills': zkill_data.get('kills', 0),
            'losses': zkill_data.get('losses', 0),
            'danger_ratio': zkill_data.get('danger_ratio', 0),
            'solo_ratio': zkill_data.get('solo_ratio', 0),
            'gang_ratio': zkill_data.get('gang_ratio', 0),
            'top_ships': zkill_data.get('top_ships', []),
            'last_updated': time.time()
        }
        self.last_seen[player_name] = time.time()

    def get_ranked_threats(self, current_players: List[str]) -> List[Dict]:
        """
        Get ranked list of current threats.

        Args:
            current_players: List of currently visible player names

        Returns:
            List of player dicts, sorted by danger (highest first)
        """
        threats = []

        for raw_name in current_players:
            name = self.normalize_name(raw_name)
            if name == self.exclude_character:
                continue

            if name in self.known_players and self.known_players[name] not in threats:
                threats.append(self.known_players[name])

        # Sort by danger ratio (highest first)
        threats.sort(key=lambda x: x['danger_ratio'], reverse=True)

        return threats

    def get_threat_level(self, danger_ratio: float) -> str:
        """
        Categorize threat level.

        Args:
            danger_ratio: Danger ratio from zkillboard (0-100)

        Returns:
            Threat level string
        """
        if danger_ratio >= 70:
            return "HIGH"
        elif danger_ratio >= 40:
            return "MEDIUM"
        elif danger_ratio > 0:
            return "LOW"
        else:
            return "UNKNOWN"

    def get_threat_emoji(self, danger_ratio: float) -> str:
        """
        Get emoji for threat level.

        Args:
            danger_ratio: Danger ratio (0-100)

        Returns:
            Emoji string
        """
        if danger_ratio >= 70:
            return "🔴"
        elif danger_ratio >= 40:
            return "🟡"
        elif danger_ratio > 0:
            return "🟢"
        else:
            return "⚪"

    def cleanup_offline_players(self, current_players: List[str]):
        """
        Remove players no longer in Local from active tracking.

        Args:
            current_players: List of currently visible players
        """
        # Mark players not in current list
        current_set = set(current_players)
        offline_players = []

        for name in list(self.last_seen.keys()):
            if name not in current_set:
                # Player left Local
                offline_players.append(name)

        # We keep their data in cache, but they're not "active"
        # This way, if they come back, we still have their info.
        return offline_players
