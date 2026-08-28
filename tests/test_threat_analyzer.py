import time
import unittest

from eve_local_monitor.threat_analyzer import ThreatAnalyzer


class ThreatAnalyzerTests(unittest.TestCase):
    def test_normalizes_filters_and_deduplicates_names(self):
        analyzer = ThreatAnalyzer(exclude_character=" My Pilot ")
        names = analyzer.filter_new_players(["  My Pilot", "  Red   Pilot ", "Red Pilot", "Blue Pilot"])
        self.assertEqual(names, ["Red Pilot", "Blue Pilot"])

    def test_cache_expiry_is_configurable(self):
        analyzer = ThreatAnalyzer(cache_expiry=10)
        analyzer.update_player_data("Pilot", {"character_id": 1}, {})
        self.assertEqual(analyzer.filter_new_players(["Pilot"]), [])

        analyzer.last_seen["Pilot"] = time.time() - 11
        self.assertEqual(analyzer.filter_new_players(["Pilot"]), ["Pilot"])

    def test_threat_policy_boundaries(self):
        analyzer = ThreatAnalyzer()
        expected = {
            0: ("UNKNOWN", "⚪"),
            1: ("LOW", "🟢"),
            39.99: ("LOW", "🟢"),
            40: ("MEDIUM", "🟡"),
            69.99: ("MEDIUM", "🟡"),
            70: ("HIGH", "🔴"),
        }
        for ratio, result in expected.items():
            self.assertEqual((analyzer.get_threat_level(ratio), analyzer.get_threat_emoji(ratio)), result)


if __name__ == "__main__":
    unittest.main()
