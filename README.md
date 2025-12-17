# AirForceNone

Presidential & Military Aircraft Tracker

## Overview

Real-time tracking of government, military, and VIP aircraft using the free ADSB.One API. Detects presidential planes, dictator aircraft, spy planes, and military flights worldwide.

## Data Source

- **API**: [ADSB.One](https://api.adsb.one) - FREE, 1 request/second, unfiltered military data
- **Endpoint**: `/v2/mil` - Returns all military aircraft globally

## Proof of Concept Scripts

### poc_tracker.py

Basic PoC with a hardcoded database of ~170 known VIP aircraft.

**Features:**
- Tracks presidential aircraft (Air Force One, SAM flights, etc.)
- Monitors VIP callsign patterns (AF1*, SAM*, EXEC*, etc.)
- Highlights priority countries: USA, Russia, Czech Republic, Ukraine, China, North Korea
- Shows aircraft location using reverse geocoding
- Rich console output with detailed flight panels

**Usage:**
```bash
source venv/bin/activate
python poc_tracker.py
```

### poc_tracker2.py

Enhanced PoC using the comprehensive `plane-alert-db.csv` database (15,887 aircraft).

**Features:**
- Three-tier priority display:
  1. **Governments & Dictator Alert** - VIP government planes with detailed panels
  2. **Spy Planes & Special Forces** - Oxcart, SIGINT, Special Ops aircraft
  3. **Military Aircraft** - Regular military (USAF, RAF, Navy, etc.)
- Category-based tracking: Dictator Alert, Governments, Oxcart, Special Forces, Gunship, and more
- Shows "flying over" country for each aircraft
- Links to more info for tracked aircraft
- Summary breakdown by category

**Usage:**
```bash
source venv/bin/activate
python poc_tracker2.py
```

## Requirements

```
requests>=2.28.0
rich>=13.0.0
reverse_geocoder>=1.5.1
```

## Future Plans

See [BRAINSTORM.md](BRAINSTORM.md) for the full web application architecture including:
- Flask web server with real-time WebSocket updates
- PostgreSQL database for historical flight data
- Interactive map with Leaflet.js
- Slack alerts for VIP aircraft detection
- Flight trajectory visualization
