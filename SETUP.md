# Setup Guide - EVE Local Threat Monitor

## Prerequisites

### 1. Install Tesseract OCR

Tesseract is required for reading text from screenshots.

**Download**: https://github.com/UB-Mannheim/tesseract/wiki

1. Download the Windows installer (tesseract-ocr-w64-setup-v5.x.x.exe)
2. Run the installer
3. **IMPORTANT**: During installation, check "Add to PATH"
4. Default installation path: `C:\Program Files\Tesseract-OCR\`

### 2. Install Python Dependencies

```bash
cd "C:\Users\tiany\Claude Project\eve-local-monitor"
pip install -r requirements.txt
```

This installs:
- **Pillow**: Screenshot capture
- **pytesseract**: OCR text extraction
- **requests**: API calls to ESI and zKillboard

## Configuration

### Step 1: Position EVE Local Window

1. Launch EVE Online
2. Position your Local chat window at a **consistent location** on screen
3. Make sure the player list is visible
4. **Recommended**: Place it on the right side of your screen for easy OCR

### Step 2: Run Interactive Setup

```bash
python -m eve_local_monitor.main
```

The app will ask you to configure the screen region:

```
Position your EVE Local window on screen, then enter coordinates:
(You can find coordinates by hovering over corners with mouse)

Left X coordinate: 1500
Top Y coordinate: 200
Right X coordinate: 1900
Bottom Y coordinate: 800
```

**How to find coordinates**:
- Use Windows built-in "Steps Recorder" (search for "psr" in Start menu)
- Or use PowerShell: `[System.Windows.Forms.Cursor]::Position`
- Or hover over Local window corners and estimate

The app will take a test screenshot (`test_screenshot.png`) for you to verify.

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
