# EVE Online Local Threat Monitor

Real-time threat monitoring for EVE Online using OCR and player intelligence data.

## Features

- **OCR-based Player Detection** - Reads dense Local lists with row-aware, multi-pass OCR
- **Threat Analysis** - Analyzes players using ESI API and zKillboard statistics
- **Danger Ratings** - Calculates threat levels (0-100%) based on PvP activity
- **Web Dashboard** - Real-time web interface with auto-refresh
- **CLI Display** - Terminal-based display with color-coded indicators
- **Smart Caching** - Configurable TTL reduces API calls while preserving fresh data

## Quick Start

### Installation

1. Install Python 3.8 or higher
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Configuration

1. **First Run Setup:**
   - Double-click `start_monitor.bat`
   - The GUI region selector will launch
   - Click and drag to select your EVE Local player list area
   - Configuration is saved automatically

2. **Manual Configuration:**
   - Copy `config.ini.example` to `config.ini`
   - Edit the values as needed

### Running the Monitor

**Option 1: Double-click launcher (Recommended)**
- Double-click `start_monitor.bat` - Shows console window
- OR double-click `start_monitor_background.vbs` - Runs in background

**Option 2: Command line**
```bash
python -m eve_local_monitor.main
```

### Accessing the Web Dashboard

Once running, open your browser to: **http://127.0.0.1:5000**

The dashboard features:
- Real-time threat display with color-coded danger levels
- Player corporation, alliance, and ship information
- Threat level legend (🔴 High, 🟡 Medium, 🟢 Low, ⚪ Unknown)
- Control buttons: Shutdown, Restart, Reconfigure OCR

## Configuration

Edit `config.ini`:

```ini
[General]
character_name = Your Character Name

[OCR]
region_left = 1746
region_top = 249
region_right = 1949
region_bottom = 895

[Monitoring]
scan_interval = 10
cache_expiry = 3600
```

## Threat Levels

- 🔴 **High (70%+)** - Dangerous PvP player with high kill count
- 🟡 **Medium (40-70%)** - Moderate threat, some PvP activity
- 🟢 **Low (<40%)** - Low threat, minimal PvP activity
- ⚪ **Unknown** - No PvP data available

## How It Works

1. **OCR Scanning** - Captures your EVE Local window region every 10 seconds
2. **Text Recognition** - Upscales the image, runs complementary OCR passes, and reconstructs visual rows
3. **API Queries** - Fetches character, corporation, and alliance data from ESI
4. **Threat Analysis** - Retrieves PvP statistics from zKillboard
5. **Danger Calculation** - Calculates threat rating based on kills, deaths, and activity
6. **Display** - Updates both CLI and web dashboard in real-time

## Requirements

- Python 3.8+
- EVE Online running in windowed or borderless windowed mode
- Internet connection for API access

## Dependencies

- Pillow - Image processing
- EasyOCR - Optical character recognition
- Requests - HTTP API client
- Flask - Web server
- Flask-CORS - Cross-origin resource sharing

## Project Structure

```
eve-local-monitor/
├── eve_local_monitor/
│   ├── main.py              # Main application
│   ├── ocr_reader.py        # OCR functionality
│   ├── esi_client.py        # EVE ESI API client
│   ├── zkill_client.py      # zKillboard API client
│   ├── threat_analyzer.py   # Threat calculation logic
│   ├── display.py           # CLI display
│   ├── web_server.py        # Flask web server
│   ├── region_selector.py   # GUI coordinate selector
│   ├── templates/           # HTML templates
│   └── static/              # CSS and JavaScript
├── config.ini               # Configuration file
├── start_monitor.bat        # Windows launcher (with console)
├── start_monitor_background.vbs  # Windows launcher (background)
└── requirements.txt         # Python dependencies
```

## Troubleshooting

**No players detected:**
- Reconfigure the OCR region using the "Reconfigure OCR" button in the web dashboard
- Ensure EVE Online is in windowed or borderless windowed mode
- Check that the Local window is visible and not minimized

**API errors:**
- Check your internet connection
- ESI API and zKillboard may occasionally be unavailable
- The monitor will retry on the next scan cycle

**Web dashboard not loading:**
- Ensure port 5000 is not in use by another application
- Check the console for error messages
- Try accessing http://127.0.0.1:5000 directly

## License

MIT License - See LICENSE file for details

## Credits

- EVE Online ESI API - https://esi.evetech.net/
- zKillboard API - https://zkillboard.com/
- EasyOCR - https://github.com/JaidedAI/EasyOCR

## Version

Current version: 1.5.0

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design contract and [CHANGELOG.md](CHANGELOG.md) for version history.
