"""OCR module for reading EVE Online Local player list from screen."""

from PIL import ImageGrab, Image, ImageEnhance, ImageFilter
from typing import List, Tuple, Optional
import re
import numpy as np
import easyocr
import os


class LocalReader:
    """Reads player names from EVE Local window using OCR."""

    def __init__(self, region: Optional[Tuple[int, int, int, int]] = None,
                 filter_friendly: bool = True,
                 friendly_colors: Optional[List[str]] = None):
        """
        Initialize OCR reader.

        Args:
            region: Screen region to capture (left, top, right, bottom).
                   If None, must be set via configure_region()
            filter_friendly: Whether to filter out players with friendly standings
            friendly_colors: List of colors to consider friendly (default: blue, green, purple)
        """
        self.region = region
        self.screenshot_path = None  # Path to save last screenshot

        # Standing filter settings
        self.filter_friendly = filter_friendly
        self.friendly_colors = friendly_colors or ["blue", "green", "purple"]

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

    def classify_standing_color(self, r: int, g: int, b: int) -> str:
        """
        Classify a standing icon color based on RGB values.

        EVE Online standing colors:
        - Blue: Good standing (friendly)
        - Purple: Fleet member (friendly)
        - Green: Corp/Alliance mate (friendly)
        - White/Gray: Neutral
        - Orange: Bad standing
        - Yellow: Terrible standing
        - Red: War target/enemy

        Args:
            r, g, b: RGB color values (0-255)

        Returns:
            Color name string
        """
        # Blue (good standing): Cyan-ish blue, high blue, moderate green, low red
        if b > 150 and g > 100 and r < 120:
            return "blue"

        # Purple (fleet): High red and blue, low green
        if r > 100 and b > 100 and g < 80:
            return "purple"

        # Green (corp/alliance): High green, lower red and blue
        if g > 150 and r < 150 and b < 150:
            return "green"

        # Orange: High red, medium green, low blue
        if r > 180 and 50 < g < 180 and b < 100:
            return "orange"

        # Yellow: High red and green, low blue
        if r > 180 and g > 150 and b < 120:
            return "yellow"

        # Red: High red, low green and blue
        if r > 150 and g < 100 and b < 100:
            return "red"

        # White/Gray: Similar RGB values (neutral)
        if abs(r - g) < 50 and abs(g - b) < 50 and abs(r - b) < 50:
            return "white"

        return "unknown"

    def detect_standing_color(self, image: Image.Image, y_coord: int, sample_x: int = 10) -> str:
        """
        Detect standing icon color at given Y coordinate.

        Samples a small area near the left edge of the image where
        standing icons appear in EVE Local window.

        Args:
            image: Original color screenshot (not preprocessed)
            y_coord: Y coordinate to sample (center of player name row)
            sample_x: X coordinate to sample (default 10 pixels from left)

        Returns:
            Color classification string
        """
        pixels = []

        # Sample a 5x5 area around the icon position
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                try:
                    x = sample_x + dx
                    y = y_coord + dy
                    if 0 <= x < image.width and 0 <= y < image.height:
                        pixel = image.getpixel((x, y))
                        # Handle RGBA images
                        if len(pixel) == 4:
                            pixel = pixel[:3]
                        pixels.append(pixel)
                except (IndexError, TypeError):
                    pass

        if not pixels:
            return "unknown"

        # Average RGB values
        avg_r = sum(p[0] for p in pixels) // len(pixels)
        avg_g = sum(p[1] for p in pixels) // len(pixels)
        avg_b = sum(p[2] for p in pixels) // len(pixels)

        return self.classify_standing_color(avg_r, avg_g, avg_b)

    def is_friendly_standing(self, color: str) -> bool:
        """
        Check if standing color indicates a friendly player.

        Args:
            color: Color classification from detect_standing_color()

        Returns:
            True if player should be filtered out (friendly)
        """
        return color in self.friendly_colors

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

    def extract_text_with_positions(self, image: Image.Image) -> List[Tuple[str, Tuple[int, int, int, int]]]:
        """
        Extract text with bounding box positions from image using EasyOCR.

        Args:
            image: PIL Image to process

        Returns:
            List of (text, bbox) tuples where bbox is (left, top, right, bottom)
        """
        try:
            # Preprocess image
            processed = self.preprocess_image(image)

            # Convert PIL Image to numpy array
            img_array = np.array(processed)

            # Read text with EasyOCR with detail=1 for bounding boxes
            results = self.easyocr_reader.readtext(img_array, detail=1, paragraph=False)

            # Convert to (text, bbox) format
            # EasyOCR returns: [(bbox, text, confidence), ...]
            # bbox format: [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            text_with_positions = []
            for bbox, text, conf in results:
                # Convert polygon to rectangle (left, top, right, bottom)
                x_coords = [p[0] for p in bbox]
                y_coords = [p[1] for p in bbox]
                rect_bbox = (min(x_coords), min(y_coords), max(x_coords), max(y_coords))
                text_with_positions.append((text, rect_bbox))

            return text_with_positions
        except Exception as e:
            print(f"Error extracting text with positions: {e}")
            return []

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

    def set_screenshot_path(self, path: str):
        """
        Set the path where screenshots should be saved.

        Args:
            path: Full file path for saving screenshots
        """
        self.screenshot_path = path
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def read_local_players(self) -> List[str]:
        """
        Capture screenshot and extract player names.

        If filter_friendly is enabled, filters out players with
        friendly standings (blue, green, purple icons).

        Returns:
            List of player names from Local (filtered if enabled)
        """
        screenshot = self.capture_screenshot()
        if not screenshot:
            return []

        # Save screenshot to file if path is set
        if self.screenshot_path:
            try:
                screenshot.save(self.screenshot_path)
            except Exception as e:
                print(f"Warning: Could not save screenshot to {self.screenshot_path}: {e}")

        # If standing filter is disabled, use the simple text extraction
        if not self.filter_friendly:
            text = self.extract_text(screenshot)
            return self.parse_player_names(text)

        # Use position-aware extraction for standing filter
        text_with_positions = self.extract_text_with_positions(screenshot)

        if not text_with_positions:
            return []

        # Filter based on standing colors
        player_names = []
        for text, bbox in text_with_positions:
            # Get Y-center of the text bounding box
            y_center = (bbox[1] + bbox[3]) // 2

            # Detect standing color from original (color) screenshot
            standing_color = self.detect_standing_color(screenshot, y_center)

            # Skip friendly standings
            if self.is_friendly_standing(standing_color):
                continue

            # Parse this text as potential player name
            parsed = self.parse_player_names(text)
            player_names.extend(parsed)

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
