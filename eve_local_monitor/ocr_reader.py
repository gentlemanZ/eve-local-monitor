"""OCR module for reading EVE Online Local player list from screen."""

from PIL import ImageGrab, Image, ImageEnhance, ImageFilter
from typing import List, Tuple, Optional
import re
import numpy as np
import easyocr


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

        # Initialize EasyOCR
        print("Initializing EasyOCR (this may take a moment on first run)...")
        self.easyocr_reader = easyocr.Reader(['en'], gpu=False)
        print("EasyOCR initialized successfully!")

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

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.

        Args:
            image: Original PIL Image

        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        image = image.convert('L')

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)

        # Apply slight blur to reduce noise (optional)
        # image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    def extract_text(self, image: Image.Image) -> str:
        """
        Extract text from image using EasyOCR with preprocessing.

        Args:
            image: PIL Image to process

        Returns:
            Extracted text
        """
        try:
            # Preprocess image
            processed = self.preprocess_image(image)

            # Convert PIL Image to numpy array
            img_array = np.array(processed)

            # Read text with EasyOCR
            results = self.easyocr_reader.readtext(img_array, detail=0, paragraph=False)

            # Join all detected text with newlines
            text = '\n'.join(results)
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

            # Smarter removal of UI icon artifacts
            # Pattern 1: Single char + space + name (e.g., "B BIGBUSSY" or "S Billy")
            if len(cleaned) > 2 and cleaned[0] in 'IlBS' and cleaned[1] == ' ' and cleaned[2].isupper():
                cleaned = cleaned[2:].strip()

            # Pattern 2: Double artifacts (e.g., "SB Billy")
            if len(cleaned) > 3 and cleaned[0] in 'IlBS' and cleaned[1] in 'IlBS' and cleaned[2] == ' ':
                cleaned = cleaned[3:].strip()

            # Pattern 3: Merged artifacts - "B" or "S" stuck to name with no space
            # Only remove if followed by uppercase + lowercase (e.g., "BAtlugh" -> "Atlugh")
            # Don't remove if all caps (e.g., "BIGBUSSY" stays as-is)
            if (len(cleaned) > 2 and
                cleaned[0] in 'BS' and
                cleaned[1].isupper() and
                len(cleaned) > 2 and
                cleaned[2].islower()):
                cleaned = cleaned[1:]

            # Remove trailing 'i' or 'l' followed by space (e.g., "Name i")
            if len(cleaned) > 2 and cleaned[-2:].strip() and cleaned[-2] == ' ' and cleaned[-1] in 'il':
                cleaned = cleaned[:-2].strip()

            # Only accept if it looks like a valid character name
            # Letters, numbers, spaces, apostrophes
            if re.match(r"^[A-Za-z0-9\s']+$", cleaned) and len(cleaned) >= 3:
                # Final validation: check if it's mostly letters (not just numbers)
                letter_count = sum(c.isalpha() for c in cleaned)
                if letter_count >= len(cleaned) * 0.6:  # At least 60% letters
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
