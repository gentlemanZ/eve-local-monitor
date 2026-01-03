"""OCR module for reading EVE Online Local player list from screen."""

import pytesseract
from PIL import ImageGrab, Image
from typing import List, Tuple, Optional
import re


class LocalReader:
    """Reads player names from EVE Local window using OCR."""

    def __init__(self, region: Optional[Tuple[int, int, int, int]] = None):
        """
        Initialize OCR reader.

        Args:
            region: Screen region to capture (left, top, right, bottom).
                   If None, must be set via configure_region()
        """
        self.region = region

        # Configure pytesseract to use installed Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def configure_region(self, region: Tuple[int, int, int, int]):
        """
        Set the screen region to capture.

        Args:
            region: (left, top, right, bottom) coordinates
        """
        self.region = region

    def capture_screenshot(self) -> Optional[Image.Image]:
        """
        Capture screenshot of the configured region.

        Returns:
            PIL Image or None if region not configured
        """
        if not self.region:
            print("Error: Screen region not configured")
            return None

        try:
            screenshot = ImageGrab.grab(bbox=self.region)
            return screenshot
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None

    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from image using OCR.

        Args:
            image: PIL Image to process

        Returns:
            Extracted text
        """
        try:
            # Use Tesseract to extract text
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def parse_player_names(self, text: str) -> List[str]:
        """
        Parse player names from OCR text.

        EVE player names:
        - 3-37 characters long
        - Can contain letters, numbers, spaces, apostrophes
        - Usually one name per line in Local

        Args:
            text: Raw OCR text

        Returns:
            List of cleaned player names
        """
        lines = text.split('\n')
        player_names = []

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip lines that are clearly not player names
            # (timestamps, system messages, etc.)
            if any(keyword in line for keyword in ['EVE System', 'CONCORD', 'EDENCOM', 'Local', 'members']):
                continue

            # Skip lines with too many numbers (likely timestamps or stats)
            if sum(c.isdigit() for c in line) > len(line) // 2:
                continue

            # Skip very short or very long lines
            if len(line) < 3 or len(line) > 40:
                continue

            # Clean up OCR artifacts
            # Remove common misreads
            cleaned = line.replace('|', '').replace('0', 'O')

            # Remove leading/trailing whitespace and common OCR artifacts
            cleaned = cleaned.strip()

            # Remove leading 'I' or 'l' that comes from OCR misreading '|' character
            if cleaned.startswith('I ') or cleaned.startswith('l '):
                cleaned = cleaned[2:]

            # Only accept if it looks like a valid character name
            # Letters, numbers, spaces, apostrophes
            if re.match(r"^[A-Za-z0-9\s']+$", cleaned) and len(cleaned) >= 3:
                player_names.append(cleaned.strip())

        return player_names

    def read_local_players(self) -> List[str]:
        """
        Capture screenshot and extract player names.

        Returns:
            List of player names from Local
        """
        screenshot = self.capture_screenshot()
        if not screenshot:
            return []

        text = self.extract_text(screenshot)
        player_names = self.parse_player_names(text)

        return player_names

    def save_debug_screenshot(self, filepath: str = "debug_screenshot.png"):
        """
        Save a screenshot for debugging OCR region.

        Args:
            filepath: Where to save the screenshot
        """
        screenshot = self.capture_screenshot()
        if screenshot:
            screenshot.save(filepath)
            print(f"Debug screenshot saved to: {filepath}")
