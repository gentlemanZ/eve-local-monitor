"""OCR module for reading EVE Online Local player lists from screen."""

from collections import OrderedDict
from typing import Any, Iterable, List, Optional, Sequence, Tuple
import os
import re

import easyocr
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab, ImageOps


BBox = Sequence[Sequence[float]]
Detection = Tuple[BBox, str, float]


class LocalReader:
    """Reads player names from EVE Local using row-aware OCR reconstruction."""

    MIN_CONFIDENCE = 0.20
    UPSCALE_FACTOR = 2
    ROW_TOLERANCE = 0.60

    def __init__(self, region: Optional[Tuple[int, int, int, int]] = None):
        self.region = region
        self.screenshot_path = None

        print("Initializing EasyOCR (this may take a moment on first run)...")
        self.easyocr_reader = easyocr.Reader(["en"], gpu=False)
        print("EasyOCR initialized successfully!")

    def configure_region(self, region: Tuple[int, int, int, int]):
        """Set the screen region to capture."""
        self.region = region

    def capture_screenshot(self) -> Optional[Image.Image]:
        """Capture the configured Local player-list region."""
        if not self.region:
            print("Error: Screen region not configured")
            return None

        try:
            return ImageGrab.grab(bbox=self.region)
        except Exception as exc:
            print(f"Error capturing screenshot: {exc}")
            return None

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Return the primary enlarged, contrast-enhanced OCR image."""
        gray = image.convert("L")
        width, height = gray.size
        enlarged = gray.resize(
            (width * self.UPSCALE_FACTOR, height * self.UPSCALE_FACTOR),
            Image.Resampling.LANCZOS,
        )
        enhanced = ImageOps.autocontrast(enlarged, cutoff=1)
        enhanced = ImageEnhance.Contrast(enhanced).enhance(1.35)
        enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.6)
        return enhanced

    def _preprocess_variants(self, image: Image.Image) -> Iterable[Image.Image]:
        """Yield complementary OCR inputs for dim or dense Local rows."""
        primary = self.preprocess_image(image)
        yield primary

        # A second pass helps when anti-aliased text blends into the EVE UI.
        threshold = primary.filter(ImageFilter.MedianFilter(size=3))
        threshold = threshold.point(lambda pixel: 255 if pixel >= 145 else 0)
        yield threshold

    def _read_detections(self, image: Image.Image) -> List[Detection]:
        """Read bounding boxes, text, and confidence from one OCR pass."""
        try:
            results = self.easyocr_reader.readtext(
                np.array(image),
                detail=1,
                paragraph=False,
                width_ths=0.35,
                ycenter_ths=0.5,
                height_ths=0.5,
                mag_ratio=1.0,
            )
        except Exception as exc:
            print(f"Error extracting text: {exc}")
            return []

        detections = []
        for result in results:
            if len(result) != 3:
                continue
            bbox, text, confidence = result
            if not str(text).strip():
                continue
            try:
                score = float(confidence)
            except (TypeError, ValueError):
                continue
            if score >= self.MIN_CONFIDENCE:
                detections.append((bbox, str(text), score))
        return detections

    @staticmethod
    def _box_geometry(bbox: BBox) -> Tuple[float, float, float]:
        xs = [float(point[0]) for point in bbox]
        ys = [float(point[1]) for point in bbox]
        return min(xs), (min(ys) + max(ys)) / 2.0, max(ys) - min(ys)

    def reconstruct_rows(
        self, detections: Sequence[Detection]
    ) -> List[Tuple[str, float]]:
        """
        Reconstruct visual rows from EasyOCR detections.

        EasyOCR does not guarantee stable reading order in a dense panel. Grouping
        by vertical center and then sorting by x-coordinate restores the Local
        list's visual order and also joins icon/name fragments on one row.
        """
        ordered = []
        for bbox, text, confidence in detections:
            left, center_y, height = self._box_geometry(bbox)
            if height <= 0:
                continue
            ordered.append((left, center_y, height, text, confidence))

        ordered.sort(key=lambda item: (item[1], item[0]))
        rows: List[dict[str, Any]] = []

        for left, center_y, height, text, confidence in ordered:
            matching_row = None
            best_distance = None
            for row in rows:
                tolerance = max(4.0, min(height, row["height"]) * self.ROW_TOLERANCE)
                distance = abs(center_y - row["center_y"])
                if distance <= tolerance and (
                    best_distance is None or distance < best_distance
                ):
                    matching_row = row
                    best_distance = distance

            if matching_row is None:
                rows.append(
                    {
                        "center_y": center_y,
                        "height": height,
                        "parts": [(left, text, confidence)],
                    }
                )
            else:
                matching_row["parts"].append((left, text, confidence))
                count = len(matching_row["parts"])
                matching_row["center_y"] = (
                    matching_row["center_y"] * (count - 1) + center_y
                ) / count
                matching_row["height"] = max(matching_row["height"], height)

        rows.sort(key=lambda row: row["center_y"])
        reconstructed = []
        for row in rows:
            parts = sorted(row["parts"], key=lambda part: part[0])
            text = " ".join(part[1].strip() for part in parts).strip()
            confidence = sum(part[2] for part in parts) / len(parts)
            reconstructed.append((text, confidence))
        return reconstructed

    def extract_text(self, image: Image.Image) -> str:
        """Extract row-reconstructed text for compatibility with callers."""
        rows = []
        for variant in self._preprocess_variants(image):
            detections = self._read_detections(variant)
            rows.extend(self.reconstruct_rows(detections))
        return "\n".join(text for text, _ in rows)

    @staticmethod
    def _clean_candidate(line: str) -> Optional[str]:
        """Clean one OCR row, returning None when it is not a player name."""
        cleaned = " ".join(line.strip().split())
        if not cleaned:
            return None

        folded = cleaned.casefold()
        if any(
            keyword in folded
            for keyword in ("eve system", "concord", "edencom", "local", "members")
        ):
            return None

        digit_count = sum(character.isdigit() for character in cleaned)
        if digit_count > len(cleaned) // 2:
            return None
        if len(cleaned) < 3 or len(cleaned) > 40:
            return None

        # Remove common EVE UI icon fragments without changing valid digits.
        if len(cleaned) > 2 and cleaned[0] in "IlBS" and cleaned[1] == " ":
            if cleaned[2].isupper():
                cleaned = cleaned[2:].strip()
        if len(cleaned) > 3 and cleaned[0] in "IlBS" and cleaned[1] in "IlBS":
            if cleaned[2] == " ":
                cleaned = cleaned[3:].strip()
        if (
            len(cleaned) > 2
            and cleaned[0] in "BS"
            and cleaned[1].isupper()
            and cleaned[2].islower()
        ):
            cleaned = cleaned[1:]
        if len(cleaned) > 2 and cleaned.endswith((" i", " l")):
            cleaned = cleaned[:-2].strip()

        if not re.fullmatch(r"[A-Za-z0-9\s']+", cleaned):
            return None
        if sum(character.isalpha() for character in cleaned) < len(cleaned) * 0.6:
            return None
        return cleaned

    def parse_player_names(self, text: str) -> List[str]:
        """Parse and de-duplicate player names from newline-separated OCR rows."""
        names = OrderedDict()
        for line in text.splitlines():
            candidate = self._clean_candidate(line)
            if candidate:
                names.setdefault(candidate, None)
        return list(names)

    def parse_rows(self, rows: Sequence[Tuple[str, float]]) -> List[str]:
        """Parse reconstructed rows while retaining first-seen visual order."""
        names = OrderedDict()
        for text, _confidence in rows:
            candidate = self._clean_candidate(text)
            if candidate:
                names.setdefault(candidate, None)
        return list(names)

    def read_local_players(self) -> List[str]:
        """
        Capture and OCR Local using two complementary passes.

        Candidates are merged by exact cleaned text, preserving visual order from
        the primary pass and adding names only found by the fallback pass.
        """
        screenshot = self.capture_screenshot()
        if screenshot is None:
            return []

        if self.screenshot_path:
            try:
                screenshot.save(self.screenshot_path)
            except Exception as exc:
                print(f"Warning: Could not save screenshot to {self.screenshot_path}: {exc}")

        names = OrderedDict()
        for variant in self._preprocess_variants(screenshot):
            rows = self.reconstruct_rows(self._read_detections(variant))
            for name in self.parse_rows(rows):
                names.setdefault(name, None)
        return list(names)

    def set_screenshot_path(self, path: str):
        """Set the path where the latest screenshot is saved."""
        self.screenshot_path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def save_debug_screenshot(self, filepath: str = "debug_screenshot.png"):
        """Save a screenshot for debugging OCR region selection."""
        screenshot = self.capture_screenshot()
        if screenshot:
            screenshot.save(filepath)
            print(f"Debug screenshot saved to: {filepath}")
