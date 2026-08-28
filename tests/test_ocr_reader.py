import unittest

from eve_local_monitor.ocr_reader import LocalReader


def box(left, top, right, bottom):
    return [[left, top], [right, top], [right, bottom], [left, bottom]]


class LocalReaderTests(unittest.TestCase):
    def setUp(self):
        # Avoid loading the EasyOCR model for pure parser tests.
        self.reader = LocalReader.__new__(LocalReader)

    def test_reconstructs_rows_in_visual_order(self):
        detections = [
            (box(10, 42, 120, 56), "Second Pilot", 0.9),
            (box(10, 10, 100, 24), "First Pilot", 0.9),
            (box(10, 74, 110, 88), "Third Pilot", 0.9),
        ]
        rows = self.reader.reconstruct_rows(detections)
        self.assertEqual([text for text, _ in rows], [
            "First Pilot",
            "Second Pilot",
            "Third Pilot",
        ])

    def test_joins_icon_and_name_fragments(self):
        detections = [
            (box(10, 10, 18, 24), "B", 0.8),
            (box(22, 10, 120, 24), "Pilot Name", 0.9),
        ]
        rows = self.reader.reconstruct_rows(detections)
        self.assertEqual(self.reader.parse_rows(rows), ["Pilot Name"])

    def test_parser_deduplicates_and_preserves_valid_digits(self):
        text = "  Pilot  7\nPilot 7\nB Enemy Name\n12\n"
        self.assertEqual(
            self.reader.parse_player_names(text),
            ["Pilot 7", "Enemy Name"],
        )


if __name__ == "__main__":
    unittest.main()
