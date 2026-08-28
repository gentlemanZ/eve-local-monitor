# EVE Local Threat Monitor - Technical Documentation

## Project Overview

EVE Online Local Threat Monitor is a real-time threat analysis tool that uses OCR to read player names from the EVE Online Local chat window, then queries ESI and zKillboard APIs to provide threat intelligence. Features both a CLI display and a web-based dashboard.

**Version:** 1.5.0
**Language:** Python 3.8+
**Primary Dependencies:** EasyOCR, Flask, Pillow, Requests

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Application                         │
│                  (eve_local_monitor/main.py)                 │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──► OCR Reader (ocr_reader.py)
             │    └──► EasyOCR for text extraction
             │
             ├──► ESI Client (esi_client.py)
             │    └──► Character/Corp/Alliance data
             │
             ├──► zKillboard Client (zkill_client.py)
             │    └──► PvP statistics & ship data
             │
             ├──► Threat Analyzer (threat_analyzer.py)
             │    └──► Danger calculation & caching
             │
             ├──► CLI Display (display.py)
             │    └──► Terminal output with emoji indicators
             │
             └──► Web Server (web_server.py)
                  └──► Flask REST API + Dashboard
                       ├──► HTML Templates (templates/)
                       └──► Static Assets (static/)
```

### Data Flow

```
1. Screen Capture (every 10s)
   ↓
2. OCR Text Extraction (EasyOCR)
   ↓
3. Player Name Parsing & Filtering
   ↓
4. Check Cache (1 hour TTL)
   ↓
5. API Queries (ESI → zKillboard)
   ↓
6. Threat Analysis & Ranking
   ↓
7. Display Updates (CLI + Web Dashboard)
```

## Core Components

### 1. OCR Reader (`ocr_reader.py`)

**Purpose:** Captures screen region and extracts player names from EVE Local window.

**Key Features:**
- Screen region configuration (left, top, right, bottom)
- Image preprocessing (grayscale, contrast enhancement, sharpness)
- EasyOCR neural network-based text recognition
- Smart artifact removal (removes UI icons: B, S, I, l characters with specific patterns)
- Debug screenshot capability
- Auto-save last screenshot to `static/screenshots/last_scan.png` for web display

**Image Preprocessing Pipeline:**
```python
1. PIL ImageGrab → capture region
2. Convert to grayscale
3. Enhance contrast (factor: 2.0)
4. Enhance sharpness (factor: 1.5)
5. Convert to numpy array for EasyOCR
```

**Artifact Removal Logic:**
- Remove leading 'I ' or 'l ' (from | symbol in EVE UI)
- Smart removal of 'B' and 'S' only when followed by space or uppercase+lowercase pattern
- Prevents breaking names like "BIGBUSSYFEMBOY"

**Important:** Uses EasyOCR only (Tesseract was removed in v1.0.0 for better accuracy).

### 2. ESI Client (`esi_client.py`)

**Purpose:** Interface with EVE Online ESI API for character data.

**Endpoints Used:**
- `/search/?categories=character&search={name}` - Character ID lookup
- `/characters/{id}/` - Character info
- `/corporations/{id}/` - Corporation info
- `/alliances/{id}/` - Alliance info

**Features:**
- Batch processing for multiple characters
- Error handling with retries
- Rate limiting compliance
- Response caching

**Data Structure:**
```python
{
    'character_id': int,
    'character_name': str,
    'corporation': str,
    'corporation_id': int,
    'alliance': str,
    'alliance_id': int
}
```

### 3. zKillboard Client (`zkill_client.py`)

**Purpose:** Fetch PvP statistics from zKillboard API.

**Endpoints Used:**
- `/api/stats/characterID/{id}/` - Player statistics

**Features:**
- Batch statistics retrieval
- Top ships extraction (max 10)
- Kill/loss aggregation
- Danger ratio calculation

**Data Structure:**
```python
{
    'kills': int,
    'losses': int,
    'danger_ratio': float,  # 0-100
    'solo_kills': int,
    'top_ships': [
        {
            'ship_id': int,
            'ship_name': str,
            'kills': int
        }
    ]
}
```

**Danger Ratio Formula:**
```
If kills + losses == 0: return 0
danger_ratio = (kills / (kills + losses)) * 100
```

### 4. Threat Analyzer (`threat_analyzer.py`)

**Purpose:** Aggregate data and calculate threat rankings.

**Key Features:**
- Player data caching (1 hour TTL)
- Character name filtering (exclude self)
- Threat ranking by danger ratio
- Data aggregation from ESI + zKill

**Cache Structure:**
```python
player_cache = {
    'player_name': {
        'timestamp': float,
        'data': {
            # Combined ESI + zKill data
        }
    }
}
```

**Threat Levels:**
- 🔴 High: 70%+ danger ratio
- 🟡 Medium: 40-70% danger ratio
- 🟢 Low: <40% danger ratio
- ⚪ Unknown: No data available

### 5. Web Server (`web_server.py`)

**Purpose:** Flask-based REST API and web dashboard.

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve dashboard HTML |
| `/api/threats` | GET | Get current threat data (JSON) |
| `/api/stream` | GET | SSE stream for real-time updates |
| `/api/status` | GET | Get monitor running status |
| `/api/screenshot` | GET | Get latest OCR screenshot (PNG image) |
| `/api/stop` | POST | Stop monitor (web server stays running) |
| `/api/start` | POST | Start monitor |
| `/api/restart` | POST | Restart monitor (clear cache) |
| `/api/reconfigure` | POST | Launch region selector |
| `/api/exit` | POST | Exit entire application (monitor + web server) |

**Response Format (`/api/threats`):**
```json
{
    "threats": [
        {
            "name": "PlayerName",
            "corporation": "Corp Name",
            "alliance": "Alliance Name",
            "danger_ratio": 75.5,
            "kills": 1234,
            "losses": 456,
            "top_ships": [
                {"ship_id": 123, "ship_name": "Vagabond", "kills": 234}
            ]
        }
    ],
    "player_count": 42,
    "last_update": 1704326400.0
}
```

**Thread Safety:**
- Uses `threading.Lock` for data updates
- Background thread for Flask server
- Main thread handles monitoring loop

**Control Signal Flow (v1.2.0 - Persistent Web Server):**
```
Stop Monitor Button:
  Web UI → POST /api/stop → Set should_shutdown flag → Main loop stops → Wait for should_start
    ↓
  Monitor status = "Stopped", Web server stays running, Dashboard remains accessible
    ↓
  User clicks Start → POST /api/start → Set should_start flag → Main loop resumes

Exit Application Button:
  Web UI → POST /api/exit → Set should_exit flag → Main loop exits completely → sys.exit(0)

Key Change: Web server persists independently of monitor state, allowing restart without losing UI access
```

### 6. Region Selector (`region_selector.py`)

**Purpose:** GUI tool for selecting OCR region.

**Features:**
- Fullscreen tkinter overlay
- Click-and-drag rectangle selection
- Screenshot preview
- Automatic config.ini update

**Workflow:**
1. Capture full screen
2. Display fullscreen overlay with screenshot
3. User drags to select region
4. Save coordinates to config.ini
5. Close overlay

### 7. Display (`display.py`)

**Purpose:** Terminal-based threat display.

**Features:**
- UTF-8 emoji support (🔴🟡🟢⚪)
- Ranked threat list
- Player count and status messages
- Windows console UTF-8 configuration

## Configuration

### config.ini Structure

```ini
[General]
character_name = T zhong  # Your character (excluded from analysis)

[OCR]
region_left = 1746     # Screen region coordinates
region_top = 249
region_right = 1949
region_bottom = 895

[Monitoring]
scan_interval = 10     # Seconds between scans
cache_expiry = 3600    # Player data cache TTL (seconds)
```

### Environment Variables

None required. All configuration via config.ini.

## Web Dashboard

### Frontend Architecture

**Technology Stack:**
- Vanilla JavaScript (ES6+)
- CSS3 with CSS Variables
- Server-side Jinja2 templates

**Key Files:**
- `templates/dashboard.html` - Main HTML structure
- `static/css/dashboard.css` - EVE Online dark theme
- `static/js/dashboard.js` - Dashboard logic
- `static/screenshots/last_scan.png` - Latest OCR screenshot (auto-updated)

### JavaScript Dashboard Class

```javascript
class ThreatDashboard {
    constructor() {
        this.apiUrl = '/api/threats';
        this.refreshInterval = 2000; // 2 seconds
    }

    // Methods:
    // - fetchThreats()
    // - updateUI(data)
    // - renderThreats(threats)
    // - shutdownMonitor()
    // - restartMonitor()
    // - reconfigureOCR()
}
```

### CSS Theme Variables

```css
:root {
    --bg-primary: #0a0a0a;      /* Main background */
    --bg-secondary: #1a1a1a;    /* Card background */
    --bg-tertiary: #2a2a2a;     /* Item background */
    --text-primary: #e0e0e0;    /* Main text */
    --text-secondary: #a0a0a0;  /* Secondary text */
    --border-color: #333;       /* Borders */
    --danger-high: #ff4444;     /* High threat */
    --danger-medium: #ffaa00;   /* Medium threat */
    --danger-low: #44ff44;      /* Low threat */
    --danger-unknown: #888888;  /* Unknown */
    --accent: #00d4ff;          /* Accent color */
}
```

### Compact Row Design

**Design Goals:**
- Display ~30 players without scrolling
- Minimal padding/margins
- Small but readable fonts

**Specifications:**
- Row padding: 8px 12px
- Row margin: 4px
- Player name font: 14px bold
- Detail labels: 9px uppercase
- Detail values: 11px
- Danger rating: 14px bold

## Data Mapping (Backend ↔ Frontend)

**Critical Field Mappings:**

| Backend (Python) | Frontend (JavaScript) | Notes |
|------------------|----------------------|-------|
| `name` | `threat.name` | Player name |
| `danger_ratio` | `threat.danger_ratio` | 0-100 percentage |
| `losses` | `threat.losses` | Death count |
| `top_ships` | Array of objects | `{ship_id, ship_name, kills}` |

**Important:** Frontend must use `.map(ship => ship.ship_name)` to extract ship names from objects.

## Launcher Scripts

### start_monitor.bat (Windows)

```batch
@echo off
echo Starting EVE Local Threat Monitor...
echo.
python -m eve_local_monitor.main
pause
```

**Features:**
- Shows console window
- Pauses on exit to show errors
- Simple double-click launch

### start_monitor_background.vbs (Windows)

```vbs
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & """ && python -m eve_local_monitor.main", 1, False
```

**Features:**
- Runs in background (minimized)
- No blocking pause
- Silent operation

## API Rate Limiting & Caching

### ESI API
- No explicit rate limit enforced by code
- Uses ESI's built-in rate limiting
- Respects HTTP 429 responses

### zKillboard API
- 1-hour cache per player
- Reduces API load significantly
- Cache stored in-memory (cleared on restart)

### Caching Strategy

```python
# Check cache before API call
if player in cache and (current_time - cache_time) < 3600:
    return cached_data
else:
    fetch_from_api()
    update_cache()
```

## Error Handling

### OCR Errors
- Graceful fallback if region not configured
- Debug screenshots for troubleshooting
- Artifact removal for UI elements

### API Errors
- ESI: Return empty dict on failure, log error
- zKillboard: Return empty stats, continue
- Network errors logged but don't crash app

### Web Server Errors
- Thread-safe data access with locks
- Graceful 404/500 handling
- CORS enabled for development

## Development Guidelines

### Code Style
- PEP 8 compliance
- Type hints for function signatures
- Docstrings for all classes/methods
- Clear variable names

### Testing Workflow
1. Configure OCR region with GUI selector
2. Test with real EVE Local window
3. Verify API responses in console
4. Check web dashboard display
5. Test control buttons (shutdown, restart, reconfigure)

### Adding New Features

**Example: Add new API endpoint**

1. Add route in `web_server.py`:
```python
@self.app.route('/api/new-endpoint')
def new_endpoint():
    return jsonify({'data': 'value'})
```

2. Add frontend handler in `dashboard.js`:
```javascript
async fetchNewData() {
    const response = await fetch('/api/new-endpoint');
    const data = await response.json();
    // Process data
}
```

3. Update HTML template if needed

## Version History

### v1.3.0 (2026-01-07)
- Added OCR screenshot display in web dashboard
- Collapsible screenshot viewer at bottom of dashboard
- `/api/screenshot` endpoint for serving latest OCR capture
- Auto-refresh of screenshot every 2 seconds
- Screenshot timestamp display

### v1.2.0 (2026-01-06)
- Persistent web server (stays running when monitor stopped)
- Start/Stop monitor controls
- Monitor status indicator

### v1.1.0 (2026-01-03)
- Added web-based dashboard
- Flask REST API with control endpoints
- Real-time auto-refresh (2s interval)
- EVE Online dark theme styling
- Compact row design for 30+ players
- Danger rating legend
- Control buttons (shutdown, restart, reconfigure)
- Launcher scripts (.bat and .vbs)

### v1.0.0 (2026-01-03)
- Initial release
- OCR-based player detection (EasyOCR)
- ESI and zKillboard integration
- Threat analysis with danger ratings
- CLI display with emoji indicators
- GUI region selector
- Player data caching (1 hour)

## Known Issues & Limitations

### OCR Accuracy
- Requires clear, visible Local window
- Performance varies with screen resolution
- May miss names if UI elements overlap
- Best with windowed/borderless windowed mode

### API Limitations
- zKillboard data may be outdated
- ESI occasionally unavailable
- Player with no killboard data shows as unknown
- Alliance-less corps show "None"

### Performance
- EasyOCR initialization takes ~5-10 seconds
- OCR processing takes ~1-2 seconds per scan
- Memory usage ~500MB (EasyOCR models)

### Platform Support
- Windows-only launcher scripts
- Linux/Mac require manual `python -m eve_local_monitor.main`
- Screen capture may vary by OS

## Future Considerations

### Potential Enhancements
- Sound alerts for high-threat players
- Historical threat tracking
- System/region intel integration
- Discord webhook notifications
- Custom threat rules/filters
- Multiple Local window support
- Docker containerization

### Performance Optimizations
- GPU acceleration for EasyOCR
- Redis for distributed caching
- WebSocket for real-time updates (replace polling)
- Lazy loading for large player lists

### UI Improvements
- Sorting/filtering options
- Player detail popup/modal
- zKillboard link integration
- Corporation/Alliance grouping
- Dark/light theme toggle

## Troubleshooting Guide

### Problem: No players detected
**Solutions:**
1. Check OCR region coordinates in config.ini
2. Use "Reconfigure OCR" button in web dashboard
3. Ensure EVE is in windowed mode (not fullscreen)
4. Verify Local window is visible (not minimized)
5. Check debug screenshot in project root

### Problem: Web dashboard shows "Waiting for threat data"
**Solutions:**
1. Verify monitor is running (check console)
2. Check that port 5000 is not blocked
3. Ensure at least one scan has completed
4. Check for errors in console output

### Problem: API errors in console
**Solutions:**
1. Verify internet connection
2. Check ESI status: https://esi.evetech.net/ui/
3. Check zKillboard status: https://zkillboard.com/
4. Wait for next scan cycle (APIs may be temporarily down)

### Problem: High memory usage
**Solutions:**
1. Restart monitor to clear cache
2. EasyOCR models are large (~200MB)
3. Reduce scan frequency in config.ini
4. Normal memory usage: 400-600MB

## Contact & Support

- GitHub: https://github.com/gentlemanZ/eve-local-monitor
- Issues: https://github.com/gentlemanZ/eve-local-monitor/issues
- License: MIT

## Technical Notes for Claude

### When Working on This Project:

1. **OCR Engine:** Only EasyOCR is used. Tesseract was removed.
2. **Field Naming:** Backend uses `danger_ratio`, `losses`, `name` (not `danger_percent`, `deaths`, `player_name`)
3. **Top Ships:** Always an array of dicts with `ship_name` key, must extract in frontend
4. **Web Server:** Pass `monitor=self` when creating ThreatWebServer instance
5. **Control Flow:** Flags set by web API, checked in main loop (not direct calls)
6. **CSS:** Use compact design (8px 12px padding, 4px margin, 11px fonts)
7. **Version Bumps:** Update `__version__.py`, `CHANGELOG.md`, and commit message
8. **Git Workflow:** Feature branches → merge to main → tag releases

### Key Design Decisions:

- **Why EasyOCR?** Better accuracy than Tesseract for EVE UI
- **Why Flask?** Lightweight, simple REST API, easy templating
- **Why in-memory cache?** Fast, simple, sufficient for single-user tool
- **Why 10s scan interval?** Balance between responsiveness and API load
- **Why compact UI?** Users want to see many players at once (PvP intel)

### Testing Checklist:

- [ ] OCR region selector works
- [ ] Player names extracted correctly
- [ ] ESI API returns character data
- [ ] zKillboard stats display correctly
- [ ] Web dashboard loads and auto-refreshes
- [ ] Control buttons work (shutdown, restart, reconfigure)
- [ ] Top ships display ship names (not [object Object])
- [ ] Danger ratings display correctly (not undefined)
- [ ] Deaths/losses display correctly (not always 0)
- [ ] OCR screenshot displays in web dashboard
- [ ] Screenshot updates with each scan
- [ ] Screenshot section expands/collapses correctly
- [ ] Launcher scripts work

---

**Last Updated:** 2026-08-28
**Document Version:** 1.2


## 1.5.0 OCR Parsing Hardening

The OCR reader now uses EasyOCR detections with bounding boxes rather than treating the returned strings as ordered lines. It upscales the capture, runs a primary enhancement pass plus a thresholded fallback pass, reconstructs visual rows by y-position, and sorts fragments left-to-right within each row. Candidates are then cleaned and de-duplicated without converting valid digits.

This improves recall when the Local panel contains many tightly spaced names. It does not overcome a capture region that clips the list or a list that has scrolled names outside the screenshot. Those are capture/layout constraints and should be addressed by selecting a taller region or changing the EVE UI layout.

Regression coverage is in `tests/test_ocr_reader.py`; it avoids loading the EasyOCR model and tests row geometry and cleanup in isolation.

## 1.4.0 Spec Alignment and Hardening

This branch makes the following contract changes:

- `config.ini` is the source of truth for both `scan_interval` and `cache_expiry`; runtime values are applied in `main.py`.
- OCR names are normalized for surrounding/repeated whitespace and de-duplicated before API enrichment.
- Threat policy is unified across analyzer, CLI, and dashboard: High `>=70`, Medium `>=40`, Low `>0` and `<40`, Unknown `0` or unavailable.
- The dashboard treats a zero danger ratio as Unknown and tolerates an absent optional connection-status element.
- `ARCHITECTURE.md` is the concise implementation contract; this document remains the detailed historical reference.
- `tests/test_threat_analyzer.py` covers normalization, filtering, TTL behavior, and policy boundaries.

The next lifecycle hardening step should replace the web server's independent control booleans with an explicit state machine. That is intentionally documented as a follow-up rather than mixed into this compatibility-focused branch.
