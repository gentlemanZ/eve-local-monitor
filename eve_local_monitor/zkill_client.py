"""zKillboard API client for PvP stats and ship data."""

import requests
from typing import Dict, List, Optional
import time


class ZKillClient:
    """Client for zKillboard API."""

    BASE_URL = "https://zkillboard.com/api"

    def __init__(self):
        """Initialize zKillboard client."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EVE-Local-Monitor/1.0"
        })
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests (rate limiting)

    def _rate_limit(self):
        """Ensure we don't exceed zkillboard rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def get_character_stats(self, character_id: int) -> Optional[Dict]:
        """
        Get PvP statistics for a character.

        Args:
            character_id: EVE character ID

        Returns:
            Stats dict or None if error/not found
        """
        self._rate_limit()

        try:
            response = self.session.get(
                f"{self.BASE_URL}/stats/characterID/{character_id}/",
                timeout=10
            )

            if response.status_code == 404:
                # Character has no killboard activity
                return None

            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting zkill stats for {character_id}: {e}")
            return None

    def parse_stats(self, stats: Optional[Dict]) -> Dict:
        """
        Parse zkillboard stats into usable format.

        Args:
            stats: Raw zkillboard stats

        Returns:
            Parsed stats dict with danger info
        """
        if not stats:
            return {
                'kills': 0,
                'losses': 0,
                'danger_ratio': 0,
                'gang_ratio': 0,
                'solo_ratio': 0,
                'top_ships': []
            }

        # Extract key metrics
        kills = stats.get('shipsDestroyed', 0)
        losses = stats.get('shipsLost', 0)

        # Danger ratio (0-100, higher = more dangerous)
        danger_ratio = stats.get('dangerRatio', 0)

        # Gang ratio (0-100, higher = flies with gangs more)
        gang_ratio = stats.get('gangRatio', 0)
        solo_ratio = 100 - gang_ratio

        # Top ships
        top_ships = self._extract_top_ships(stats)

        return {
            'kills': kills,
            'losses': losses,
            'danger_ratio': danger_ratio,
            'gang_ratio': gang_ratio,
            'solo_ratio': solo_ratio,
            'top_ships': top_ships
        }

    def _extract_top_ships(self, stats: Dict) -> List[Dict[str, any]]:
        """
        Extract top ships from zkillboard stats.

        Args:
            stats: Raw zkillboard stats

        Returns:
            List of top ship dicts with {ship_id, ship_name, kills}
        """
        top_ships = []

        # zkillboard returns topLists with ship data
        if 'topLists' not in stats:
            return []

        top_lists = stats['topLists']

        # Look for ship kills
        for top_list in top_lists:
            if top_list.get('type') == 'shipType' and top_list.get('title') == 'Top Ships':
                values = top_list.get('values', [])

                for ship in values[:5]:  # Top 5 ships
                    top_ships.append({
                        'ship_id': ship.get('id'),
                        'ship_name': ship.get('name', 'Unknown'),
                        'kills': ship.get('kills', 0)
                    })
                break

        return top_ships

    def get_batch_stats(self, character_ids: List[int]) -> Dict[int, Dict]:
        """
        Get stats for multiple characters.

        Args:
            character_ids: List of character IDs

        Returns:
            Dict mapping character_id -> parsed stats
        """
        results = {}

        for char_id in character_ids:
            raw_stats = self.get_character_stats(char_id)
            parsed_stats = self.parse_stats(raw_stats)
            results[char_id] = parsed_stats

        return results
