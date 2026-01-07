# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-06

### Added
- Persistent web server that keeps running even when monitor is stopped
- Start/Stop monitor controls (web server stays active)
- Monitor status indicator in web dashboard (Running/Stopped)

### Changed
- Shutdown button now stops the monitor but keeps web server running
- Restart button renamed to Start/Stop and works even when monitor is stopped
- Web dashboard remains accessible for control operations

### Fixed
- Web UI no longer becomes inaccessible when monitor is shut down
- Users can now restart the monitor from the web dashboard after shutdown

## [1.1.0] - 2026-01-03

### Added
- Web-based dashboard for threat monitoring
- Flask web server with REST API endpoints
- Real-time threat data display in browser
- Auto-refreshing web interface (2-second intervals)
- EVE Online dark theme styling
- Threat level indicators with color coding
- Player corporation, alliance, and ship information display
- Responsive web design for multiple screen sizes
- Compact row layout to display ~30 players without scrolling
- Threat level legend on dashboard (🔴🟡🟢⚪)
- Control buttons: Shutdown, Restart, Reconfigure OCR
- Windows launcher scripts (start_monitor.bat and start_monitor_background.vbs)
- Comprehensive technical documentation (claude.md)

### Changed
- Monitor now starts web server automatically on http://127.0.0.1:5000
- Threat data is now pushed to both CLI and web dashboard
- Reduced row padding and font sizes for compact display

### Fixed
- Top ships now display ship names correctly (was showing [object Object])
- Danger rating displays correctly (was showing undefined%)
- Deaths/losses display correctly (was always showing 0)

## [1.0.0] - 2026-01-03

### Added
- Initial release
- OCR-based player name detection from EVE Online Local window
- ESI API integration for character, corporation, and alliance data
- zKillboard integration for PvP statistics and threat analysis
- Real-time threat monitoring with danger ratings (0-100%)
- Configurable screen region for OCR capture
- CLI-based display with emoji threat indicators (🔴🟡🟢⚪)
- Kill/Death statistics and top ships for each player
- Player data caching (1 hour) to reduce API calls
- Configurable scan interval
- Character name filtering to exclude yourself from analysis

[1.0.0]: https://github.com/gentlemanZ/eve-local-monitor/releases/tag/v1.0.0
