# EVE Online Local Threat Monitor (OCR + Real-time)

Real-time threat monitoring for EVE Online Local channel using OCR and direct API queries.

## Features

- **Real-time monitoring**: Continuously reads Local player list via OCR
- **Automatic threat analysis**: Queries ESI + zKillboard APIs directly
- **Ship intel**: Shows top ships for each player
- **Danger ratings**: Kill stats, danger ratio, solo vs gang
- **No manual interaction**: Fully automated once configured

## Requirements

- Python 3.10+
- Tesseract OCR installed on system
- EVE Online Local window positioned consistently

## Installation

### 1. Install Tesseract OCR

Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

Make sure to add it to PATH during installation.

### 2. Install Python dependencies

```bash
cd "C:\Users\tiany\Claude Project\eve-local-monitor"
pip install -r requirements.txt
```

## Configuration

1. Position your EVE Local window at a consistent location on screen
2. Edit `config.ini` to set the screen region for OCR
3. Set your character name to filter yourself out

## Usage

```bash
python -m eve_local_monitor.main
```

The monitor will:
1. Continuously screenshot the Local player list region
2. OCR to extract player names
3. Query ESI/zKillboard for each new player
4. Display threat intel in terminal/overlay

Press Ctrl+C to stop.

## How It Works

1. **OCR**: Screenshots Local window → Tesseract extracts text
2. **ESI API**: Get character IDs, affiliations (corp/alliance)
3. **zKillboard API**: Get PvP stats, danger ratio, top ships
4. **Display**: Show ranked threat list with ship intel

No website needed - all data processing happens locally!
