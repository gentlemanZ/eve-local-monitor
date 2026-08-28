# Setup Guide - EVE Local Threat Monitor

## Prerequisites

### 1. Install Python dependencies

Python 3.8 or higher is required. The monitor uses EasyOCR for text recognition; Tesseract is not required.

```bash
pip install -r requirements.txt
```

This installs:
- **Pillow**: Screenshot capture and image preprocessing
- **EasyOCR**: Player-name recognition
- **requests**: ESI and zKillboard API clients
- **Flask / Flask-CORS**: Local dashboard

## Configuration

### Step 1: Create Configuration File

Copy the example configuration:

```bash
copy config.ini.example config.ini
```

### Step 2: Configure Screen Region (GUI Method - Recommended)

1. Launch EVE Online and position your Local chat window where you want it
2. Run the region selector:
   ```bash
   python -m eve_local_monitor.region_selector
   ```
3. A fullscreen overlay will appear showing your screen
4. **Click and drag** to select the area containing your Local player list
5. Release the mouse to confirm - you'll see a dialog with coordinates
6. Click "Yes" to save the region to `config.ini`

**Tips for selecting the region**:
- Make sure to capture the entire player name list area
- Exclude the Local chat text area (we only need names)
- The selection should be at least 50x50 pixels
- You can press ESC to cancel and try again

### Step 3: Set Your Character Name

Edit `config.ini` and set your character name to filter yourself out:

```ini
[General]
character_name = Your Character Name
```

### Alternative: Manual Configuration

If you prefer to manually set coordinates, edit `config.ini`:

```ini
[OCR]
region_left = 1500
region_top = 200
region_right = 1900
region_bottom = 800
```

**How to find coordinates manually**:
- Use PowerShell: `[System.Windows.Forms.Cursor]::Position`
- Or use Windows built-in "Steps Recorder" (search for "psr" in Start menu)
- Or hover over corners and estimate based on screen resolution

## Usage

### Running the Monitor

```bash
cd "C:\Users\tiany\Claude Project\eve-local-monitor"
python -m eve_local_monitor.main
```

### What Happens

1. **Every 10 seconds**, the app:
   - Screenshots your Local window region
   - OCR extracts player names
   - Queries ESI API for character/corp/alliance info
   - Queries zKillboard for PvP stats and top ships
   - Displays ranked threat list

2. **Display shows**:
   - Player name
   - Corp/Alliance
   - Danger ratio (0-100%)
   - Kill/Death stats
   - Top 3 ships they fly
   - Emoji threat indicator (🔴🟡🟢⚪)

### Example Output

```
================================================================================
  EVE ONLINE LOCAL THREAT MONITOR - 15 players in Local
================================================================================

   Player               Corp/Alliance             Danger   K/D      Ships
--------------------------------------------------------------------------------
🔴 Veteran PvPer       Elite Corp [ELITE]        89%      234/45   Vagabond, Orthrus, Cerberus
🔴 Scary Hunter        Null Alliance [NULL]      78%      156/32   Sabre, Stiletto, Jackdaw
🟡 Fleet Member        Big Alliance [BIG]        45%      89/67    Drake, Caracal, Osprey
🟢 Occasional PvP      Small Corp                23%      15/8     Atron, Tristan
⚪ Carebear Miner       Mining Corp               5%       2/12     Venture, Procurer
```

### Stopping the Monitor

Press `Ctrl+C` to stop.

## Troubleshooting

### "No players detected"

- Check your screen region configuration
- Make sure Local window is visible and not minimized
- Verify `test_screenshot.png` shows the player list clearly
- Try adjusting the coordinates

### Tesseract not found

- Make sure Tesseract is installed
- Verify it's in PATH: run `tesseract --version` in command prompt
- If not in PATH, edit `ocr_reader.py` and uncomment:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

### OCR reading garbage text

- Local window may be too small - make it larger
- Font might be unclear - try adjusting EVE UI scaling
- Ensure good contrast (dark mode vs light mode)

### API rate limiting

- zKillboard has rate limits (10 requests/second)
- App automatically throttles to 100ms between requests
- If you get rate limited, the app will slow down automatically

## Tips

- **Keep Local window visible** - OCR needs to see it
- **Consistent positioning** - Don't move Local window after setup
- **Adjust scan interval** - Edit `scan_interval` in main.py if 10 seconds is too fast/slow
- **Cache works** - Players are cached for 1 hour, so re-scans are fast

## Advanced

### Manual Region Configuration

Edit `config.ini` instead of using interactive setup:

```ini
[OCR]
region_left = 1500
region_top = 200
region_right = 1900
region_bottom = 800
```

### Change Your Character Name

Edit `config.ini`:

```ini
[General]
character_name = Your Character Name
```

Or edit `main.py`:

```python
monitor = LocalThreatMonitor(character_name="Your Character Name")
```
