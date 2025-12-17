# AirForceNone

Presidential & Military Aircraft Tracker

## Overview

Real-time tracking of government, military, and VIP aircraft using the free ADSB.One API. Detects presidential planes, dictator aircraft, spy planes, and military flights worldwide.

## Data Sources

- **API**: [ADSB.One](https://api.adsb.one) - FREE, 1 request/second, unfiltered military data
- **Endpoint**: `/v2/mil` - Returns all military aircraft globally
- **Aircraft Database**: [plane-alert-db](https://github.com/sdr-enthusiasts/plane-alert-db) - Community-maintained database of interesting aircraft (15,887 entries)

> **Note:** The plane-alert-db is maintained by the community and occasionally contains editorial comments about UK politics in the tags. Don't blame me for those. :)

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
