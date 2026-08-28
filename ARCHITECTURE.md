# Architecture and Specification Contract

This document is the implementation contract for the EVE Local Threat Monitor. It records the behavior that the code, CLI, dashboard, and future changes should preserve.

## Purpose

Read the visible EVE Online Local player list, enrich detected character names with ESI and zKillboard data, and present a ranked threat snapshot locally. The application is informational: it does not control the EVE client.

## Runtime pipeline

```
screen capture
  -> OCR extraction
  -> name cleanup and de-duplication
  -> cache lookup
  -> ESI identity/affiliation enrichment
  -> zKillboard combat enrichment
  -> threat snapshot and ranking
  -> CLI + dashboard publication
```

A scan must tolerate an empty OCR result or an individual API failure. Existing cached data remains usable when a player is temporarily unavailable upstream.

## Component boundaries

- `ocr_reader.py`: capture, preprocessing, OCR, and player-name parsing.
- `esi_client.py`: character ID and affiliation lookups.
- `zkill_client.py`: combat statistics and ship parsing.
- `threat_analyzer.py`: normalized names, TTL decisions, data aggregation, and ranking.
- `main.py`: orchestration, configuration, and lifecycle control.
- `display.py`: terminal presentation only.
- `web_server.py`: local HTTP transport and control signals.
- dashboard assets: presentation only; they must not recalculate backend policy.

## Configuration contract

`config.ini` is the source of truth for:

- `General.character_name`: excluded character name.
- `OCR.region_left/top/right/bottom`: capture rectangle.
- `Monitoring.scan_interval`: minimum seconds between scans; values below one second are clamped to one.
- `Monitoring.cache_expiry`: player enrichment TTL in seconds; zero means refresh on every scan.

## Threat policy

The danger ratio is a percentage from 0 to 100:

- High: `>= 70` (red)
- Medium: `>= 40` and `< 70` (yellow)
- Low: `> 0` and `< 40` (green)
- Unknown: `0` or unavailable (white)

This policy must be identical in the analyzer, CLI, and dashboard.

## Lifecycle contract

The web server is persistent while the process is alive. Monitor controls signal the main loop:

- Stop pauses scanning but leaves the dashboard available.
- Start resumes scanning and forces an immediate scan.
- Restart clears cached player data and continues scanning.
- Reconfigure pauses scanning, updates the OCR region, then resumes with an immediate scan.
- Exit terminates the process.

Future lifecycle changes should use an explicit state machine rather than adding independent boolean flags.

## Reliability and security expectations

- External requests use timeouts and must fail closed to an empty/stale result.
- Enrichment should remain bounded by upstream rate limits.
- Dashboard control routes are intended for localhost only; if the server ever binds beyond loopback, add authentication and CSRF protection before exposing mutating routes.
- Logs should identify scan failures without logging credentials or sensitive local configuration.

## Testing contract

The minimum regression suite should cover:

- OCR cleanup using representative captured-text fixtures.
- Name normalization, self-filtering, de-duplication, and cache expiry.
- Threat policy boundary values: 0, 1, 39.99, 40, 69.99, and 70.
- ESI/zKillboard response parsing with empty and malformed upstream data.
- Dashboard control responses and lifecycle transitions using fake dependencies.

## OCR design for dense Local lists

EasyOCR returns text detections with bounding boxes, not guaranteed visual order. The reader therefore:

1. Captures the configured region and saves the raw image for diagnostics.
2. Upscales the image before recognition to preserve small Local text.
3. Runs a contrast/sharpness pass and a thresholded fallback pass.
4. Groups detections by vertical center into visual rows.
5. Sorts fragments left-to-right within each row, so UI icons and names can be joined.
6. Cleans and de-duplicates candidates while preserving row order.
7. Leaves valid digits unchanged; cleanup must not silently mutate a character name.

The fallback pass is merged by cleaned text. This improves recall in dense lists without changing the downstream ESI/zKillboard identity contract. A configured capture region still limits the maximum names visible to OCR; if the Local panel is clipped or scrolled, no parser can recover names that are outside the screenshot.

## Changes in this branch

- Made `cache_expiry` from `config.ini` active at runtime.
- Normalized whitespace and removed duplicate OCR names before enrichment.
- Unified zero/low/medium/high rendering across all surfaces.
- Added defensive handling for an optional dashboard connection indicator.
- Updated setup/version documentation to describe EasyOCR and the active configuration.
