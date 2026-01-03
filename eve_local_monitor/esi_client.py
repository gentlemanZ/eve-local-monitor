"""ESI API client for EVE Online character data."""

import requests
from typing import List, Dict, Optional
import time


class ESIClient:
    """Client for EVE Swagger Interface (ESI) API."""

    BASE_URL = "https://esi.evetech.net/latest"

    def __init__(self):
        """Initialize ESI client."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "EVE-Local-Monitor/1.0"
        })
        self.cache = {}  # Simple in-memory cache

    def get_character_ids(self, names: List[str]) -> Dict[str, int]:
        """
        Convert character names to IDs.

        Args:
            names: List of character names

        Returns:
            Dict mapping name -> character_id
        """
        if not names:
            return {}

        try:
            # ESI endpoint: POST /universe/ids/
            # Max 500 names per request
            response = self.session.post(
                f"{self.BASE_URL}/universe/ids/",
                json=names[:500],  # Limit to 500
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Build name -> ID mapping
            char_map = {}
            if 'characters' in data:
                for char in data['characters']:
                    char_map[char['name']] = char['id']

            return char_map

        except Exception as e:
            print(f"Error getting character IDs: {e}")
            return {}

    def get_character_affiliations(self, character_ids: List[int]) -> List[Dict]:
        """
        Get affiliations (corp, alliance, faction) for characters.

        Args:
            character_ids: List of character IDs

        Returns:
            List of affiliation dicts
        """
        if not character_ids:
            return []

        try:
            # ESI endpoint: POST /characters/affiliation/
            # Max 1000 IDs per request
            response = self.session.post(
                f"{self.BASE_URL}/characters/affiliation/",
                json=character_ids[:1000],
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"Error getting affiliations: {e}")
            return []

    def get_names_from_ids(self, ids: List[int]) -> Dict[int, str]:
        """
        Convert IDs to names (for corps, alliances, ships, etc).

        Args:
            ids: List of IDs to resolve

        Returns:
            Dict mapping ID -> name
        """
        if not ids:
            return {}

        try:
            # ESI endpoint: POST /universe/names/
            # Max 1000 IDs per request
            response = self.session.post(
                f"{self.BASE_URL}/universe/names/",
                json=ids[:1000],
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Build ID -> name mapping
            name_map = {}
            for item in data:
                name_map[item['id']] = item['name']

            return name_map

        except Exception as e:
            print(f"Error getting names from IDs: {e}")
            return {}

    def get_character_info(self, character_names: List[str]) -> Dict[str, Dict]:
        """
        Get full character info including affiliations.

        Args:
            character_names: List of character names

        Returns:
            Dict mapping character name -> info dict
        """
        # Step 1: Get character IDs
        char_ids = self.get_character_ids(character_names)

        if not char_ids:
            return {}

        # Step 2: Get affiliations
        affiliations = self.get_character_affiliations(list(char_ids.values()))

        # Step 3: Get corp/alliance names
        corp_ids = set()
        alliance_ids = set()

        for aff in affiliations:
            if 'corporation_id' in aff:
                corp_ids.add(aff['corporation_id'])
            if 'alliance_id' in aff:
                alliance_ids.add(aff['alliance_id'])

        all_ids = list(corp_ids | alliance_ids)
        id_to_name = self.get_names_from_ids(all_ids)

        # Step 4: Build result dict
        result = {}
        for aff in affiliations:
            char_id = aff['character_id']

            # Find character name
            char_name = None
            for name, cid in char_ids.items():
                if cid == char_id:
                    char_name = name
                    break

            if not char_name:
                continue

            result[char_name] = {
                'character_id': char_id,
                'corporation_id': aff.get('corporation_id'),
                'corporation_name': id_to_name.get(aff.get('corporation_id'), 'Unknown'),
                'alliance_id': aff.get('alliance_id'),
                'alliance_name': id_to_name.get(aff.get('alliance_id'), 'None'),
            }

        return result
