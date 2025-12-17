#!/usr/bin/env python3
"""
AirForceNone - Presidential Aircraft Tracker PoC v2
====================================================
Uses plane-alert-db.csv for comprehensive aircraft database.
Includes Dictator Alert, Government, Military, and more categories.

Data Source: https://api.adsb.one (FREE - 1 req/sec)
Aircraft DB: plane-alert-db.csv (15,890 aircraft)
"""

import csv
import requests
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# Try to import Rich for fancy output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Note: Install 'rich' for better output: pip install rich")

# Try to import reverse_geocoder for location lookup
try:
    import reverse_geocoder as rg
    RG_AVAILABLE = True
except ImportError:
    RG_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================

# Table 1: TOP PRIORITY - Government & Dictators
TOP_PRIORITY_CATEGORIES = {
    "Dictator Alert",
    "Governments",
}

# Table 2: HIGH PRIORITY - Spy planes & Special ops
HIGH_PRIORITY_CATEGORIES = {
    "Oxcart",  # Spy planes
    "Special Forces",
    "Gunship",
}

# Table 3: MILITARY - Regular military aircraft
MILITARY_CATEGORIES = {
    "USAF",
    "RAF",
    "GAF",
    "United States Navy",
    "United States Marine Corps",
    "Royal Navy Fleet Air Arm",
    "Other Navies",
    "Other Air Forces",
    "Coastguard",
    "Toy Soldiers",
    "Zoomies",
}

# All categories we care about
ALL_TRACKED_CATEGORIES = TOP_PRIORITY_CATEGORIES | HIGH_PRIORITY_CATEGORIES | MILITARY_CATEGORIES | {
    "Joe Cool",
    "Big Hello",
    "Historic",
    "As Seen on TV",
    "Hired Gun",
    "Climate Crisis",
    "Police Forces",
    "Distinctive",
}

# CSV file path
CSV_PATH = Path(__file__).parent / "plane-alert-db.csv"


# =============================================================================
# AIRCRAFT DATABASE FROM CSV
# =============================================================================

@dataclass
class AircraftRecord:
    """Aircraft record from CSV database"""
    icao_hex: str
    registration: str
    operator: str
    aircraft_type: str
    icao_type: str
    cmpg: str  # Civ/Mil/Gov/Pol
    tag1: str
    tag2: str
    tag3: str
    category: str
    link: str


def load_aircraft_database(csv_path: Path) -> dict[str, AircraftRecord]:
    """Load aircraft database from CSV file"""
    database = {}

    if not csv_path.exists():
        print(f"Warning: CSV file not found at {csv_path}")
        return database

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            icao = row.get('$ICAO', '').lower().strip()
            if icao and len(icao) == 6:
                database[icao] = AircraftRecord(
                    icao_hex=icao,
                    registration=row.get('$Registration', ''),
                    operator=row.get('$Operator', ''),
                    aircraft_type=row.get('$Type', ''),
                    icao_type=row.get('$ICAO Type', ''),
                    cmpg=row.get('#CMPG', ''),
                    tag1=row.get('$Tag 1', ''),
                    tag2=row.get('$#Tag 2', ''),
                    tag3=row.get('$#Tag 3', ''),
                    category=row.get('Category', ''),
                    link=row.get('$#Link', ''),
                )

    return database


# =============================================================================
# API CLIENT
# =============================================================================

class ADSBOneClient:
    """Client for ADSB.One API"""

    BASE_URL = "https://api.adsb.one"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AirForceNone-PoC/2.0",
            "Accept": "application/json"
        })
        self.last_request_time = 0
        self.min_request_interval = 1.0

    def _rate_limit(self):
        """Ensure we don't exceed 1 request per second"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def get_military_aircraft(self) -> dict:
        """Get all military aircraft from /v2/mil endpoint"""
        self._rate_limit()
        try:
            response = self.session.get(f"{self.BASE_URL}/v2/mil", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return {"ac": [], "msg": str(e)}


# =============================================================================
# LOCATION LOOKUP
# =============================================================================

_location_cache = {}

def get_location(lat: float, lon: float) -> str:
    """Get country from coordinates using reverse geocoding"""
    if not RG_AVAILABLE or lat is None or lon is None:
        return ""

    cache_key = f"{lat:.2f},{lon:.2f}"
    if cache_key in _location_cache:
        return _location_cache[cache_key]

    try:
        results = rg.search([(lat, lon)], mode=1, verbose=False)
        if results:
            cc = results[0].get('cc', '')
            country_names = {
                'US': 'USA', 'GB': 'UK', 'DE': 'Germany', 'FR': 'France',
                'IT': 'Italy', 'ES': 'Spain', 'PL': 'Poland', 'CZ': 'Czechia',
                'UA': 'Ukraine', 'RU': 'Russia', 'CN': 'China', 'KP': 'N.Korea',
                'NL': 'Netherlands', 'BE': 'Belgium', 'AT': 'Austria', 'CH': 'Switzerland',
                'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland',
                'EG': 'Egypt', 'SA': 'Saudi', 'AE': 'UAE', 'IL': 'Israel',
                'TR': 'Turkey', 'JP': 'Japan', 'KR': 'S.Korea', 'AU': 'Australia',
                'CA': 'Canada', 'MX': 'Mexico', 'BR': 'Brazil', 'ZA': 'S.Africa',
                'ZW': 'Zimbabwe', 'BY': 'Belarus', 'SY': 'Syria', 'IR': 'Iran',
                'KZ': 'Kazakhstan', 'UZ': 'Uzbekistan', 'TM': 'Turkmenistan',
            }
            location = country_names.get(cc, cc)
            _location_cache[cache_key] = location
            return location
    except Exception:
        pass

    return ""


# =============================================================================
# DISPLAY STRUCTURES
# =============================================================================

@dataclass
class TrackedAircraft:
    """Aircraft being tracked with all info"""
    icao_hex: str
    callsign: str
    registration: str
    operator: str
    aircraft_type: str
    icao_type: str
    category: str
    cmpg: str
    tag1: str
    tag2: str
    tag3: str
    link: str
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[int]
    ground_speed: Optional[int]
    heading: Optional[int]
    squawk: str
    on_ground: bool
    over_country: str
    is_priority: bool = False
    is_high_interest: bool = False


def parse_tracked_aircraft(ac_data: dict, db: dict[str, AircraftRecord]) -> Optional[TrackedAircraft]:
    """Parse API data and match against database"""
    hex_code = ac_data.get("hex", "").lower()

    # Look up in database
    record = db.get(hex_code)
    if not record:
        return None  # Not in our database

    lat = ac_data.get("lat")
    lon = ac_data.get("lon")
    over_country = get_location(lat, lon) if lat and lon else ""

    # Determine priority
    is_priority = record.category in TOP_PRIORITY_CATEGORIES
    is_high_interest = record.category in HIGH_PRIORITY_CATEGORIES

    return TrackedAircraft(
        icao_hex=hex_code.upper(),
        callsign=ac_data.get("flight", "").strip() or "N/A",
        registration=record.registration,
        operator=record.operator[:35] if record.operator else "Unknown",
        aircraft_type=record.aircraft_type[:25] if record.aircraft_type else "",
        icao_type=ac_data.get("t", "") or record.icao_type,
        category=record.category,
        cmpg=record.cmpg,
        tag1=record.tag1,
        tag2=record.tag2,
        tag3=record.tag3,
        link=record.link,
        latitude=lat,
        longitude=lon,
        altitude=ac_data.get("alt_baro") if ac_data.get("alt_baro") != "ground" else 0,
        ground_speed=ac_data.get("gs"),
        heading=ac_data.get("track"),
        squawk=ac_data.get("squawk", ""),
        on_ground=ac_data.get("alt_baro") == "ground",
        over_country=over_country,
        is_priority=is_priority,
        is_high_interest=is_high_interest,
    )


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

def display_table(aircraft_list: list[TrackedAircraft], title: str, title_style: str = "white", border_style: str = "blue", show_link: bool = False):
    """Display a table of aircraft"""
    console = Console()

    if not aircraft_list:
        return

    # Sort by operator
    aircraft_list.sort(key=lambda x: (x.category, x.operator))

    table = Table(
        title=f"[bold {title_style}]{title}[/bold {title_style}]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style=border_style,
        title_justify="center",
        expand=False,
        padding=(0, 1),
    )

    table.add_column("Operator", style="white", no_wrap=True, max_width=32)
    table.add_column("Callsign", style="green", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("Alt (ft)", justify="right", no_wrap=True)
    table.add_column("Spd", justify="right", no_wrap=True)
    table.add_column("Hdg", justify="right", no_wrap=True)
    table.add_column("Over", style="bold cyan", no_wrap=True)
    table.add_column("Tag", style="dim", no_wrap=True, max_width=18)
    if show_link:
        table.add_column("Link", style="dim blue", no_wrap=True, max_width=30)

    for ac in aircraft_list:
        # Format altitude
        if ac.on_ground:
            alt_str = "[dim]GND[/dim]"
        elif ac.altitude:
            alt_str = f"{ac.altitude:,}"
        else:
            alt_str = "[dim]-[/dim]"

        # Format speed
        speed_str = f"{ac.ground_speed:.0f}" if ac.ground_speed else "[dim]-[/dim]"

        # Format heading
        hdg_str = f"{ac.heading:.0f}°" if ac.heading else "[dim]-[/dim]"

        # Tag info
        tag_str = ac.tag2[:18] if ac.tag2 else (ac.tag1[:18] if ac.tag1 else "")

        # Over country - highlight if interesting
        over_str = ac.over_country if ac.over_country else "[dim]-[/dim]"

        row = [
            ac.operator[:32],
            ac.callsign,
            ac.icao_type or "?",
            alt_str,
            speed_str,
            hdg_str,
            over_str,
            tag_str,
        ]

        if show_link:
            link_str = ac.link.split("/")[-1][:30] if ac.link else ""
            row.append(link_str)

        table.add_row(*row)

    console.print()
    console.print(table)


def display_government_dictators(aircraft_list: list[TrackedAircraft]):
    """Display Government & Dictator Alert aircraft with detailed panels"""
    console = Console()

    govt = [ac for ac in aircraft_list if ac.category in TOP_PRIORITY_CATEGORIES]
    if not govt:
        console.print()
        console.print(Panel(
            "[dim]No Government or Dictator aircraft currently detected.[/dim]",
            title="[bold red]★ GOVERNMENTS & DICTATORS[/bold red]",
            border_style="red"
        ))
        return

    console.print()
    console.print(f"[bold red]{'='*70}[/bold red]")
    console.print(f"[bold red]★ GOVERNMENTS & DICTATOR ALERT ({len(govt)} aircraft)[/bold red]")
    console.print(f"[bold red]{'='*70}[/bold red]")

    for ac in govt:
        # Determine border color based on category
        if ac.category == "Dictator Alert":
            border = "red"
            icon = "🚨"
        else:
            border = "yellow"
            icon = "🏛️"

        # Build detailed info
        info_lines = []

        # Main info line
        info_lines.append(f"[bold white]{ac.operator}[/bold white]")
        info_lines.append("")

        # Aircraft details
        info_lines.append(f"[cyan]Callsign:[/cyan] {ac.callsign}   [cyan]Registration:[/cyan] {ac.registration}   [cyan]Type:[/cyan] {ac.aircraft_type}")

        # Position and flight info
        if ac.latitude and ac.longitude:
            over_highlight = f"[bold yellow]{ac.over_country}[/bold yellow]" if ac.over_country else "Unknown"
            info_lines.append(f"[cyan]Flying Over:[/cyan] {over_highlight}   [cyan]Position:[/cyan] {ac.latitude:.3f}, {ac.longitude:.3f}")

        if ac.altitude or ac.ground_speed:
            alt_str = "Ground" if ac.on_ground else f"{ac.altitude:,} ft" if ac.altitude else "N/A"
            spd_str = f"{ac.ground_speed:.0f} kts" if ac.ground_speed else "N/A"
            hdg_str = f"{ac.heading:.0f}°" if ac.heading else "N/A"
            info_lines.append(f"[cyan]Altitude:[/cyan] {alt_str}   [cyan]Speed:[/cyan] {spd_str}   [cyan]Heading:[/cyan] {hdg_str}")

        # Tags
        if ac.tag1 or ac.tag2 or ac.tag3:
            tags = " | ".join(filter(None, [ac.tag1, ac.tag2, ac.tag3]))
            info_lines.append(f"[cyan]Tags:[/cyan] {tags}")

        # Link
        if ac.link:
            info_lines.append(f"[cyan]More Info:[/cyan] {ac.link}")

        panel = Panel(
            "\n".join(info_lines),
            title=f"[bold]{icon} {ac.category}[/bold]",
            border_style=border,
            padding=(0, 1),
        )
        console.print()
        console.print(panel)


def display_spy_special_forces(aircraft_list: list[TrackedAircraft]):
    """Display Oxcart (spy planes) and Special Forces"""
    console = Console()

    spy_sf = [ac for ac in aircraft_list if ac.category in HIGH_PRIORITY_CATEGORIES]
    if not spy_sf:
        return

    console.print()
    console.print(f"[bold magenta]{'='*70}[/bold magenta]")
    console.print(f"[bold magenta]🛩️  SPY PLANES & SPECIAL FORCES ({len(spy_sf)} aircraft)[/bold magenta]")
    console.print(f"[bold magenta]{'='*70}[/bold magenta]")

    display_table(spy_sf, "", title_style="magenta", border_style="magenta", show_link=False)


def display_military(aircraft_list: list[TrackedAircraft]):
    """Display regular military aircraft"""
    console = Console()

    military = [ac for ac in aircraft_list if ac.category in MILITARY_CATEGORIES]
    if not military:
        return

    console.print()
    console.print(f"[bold blue]{'='*70}[/bold blue]")
    console.print(f"[bold blue]✈️  MILITARY AIRCRAFT ({len(military)} aircraft)[/bold blue]")
    console.print(f"[bold blue]{'='*70}[/bold blue]")

    display_table(military, "", title_style="blue", border_style="blue")


def display_summary(aircraft_list: list[TrackedAircraft], total_scanned: int, db_size: int):
    """Display summary statistics"""
    console = Console()

    # Count by category
    category_counts = {}
    for ac in aircraft_list:
        category_counts[ac.category] = category_counts.get(ac.category, 0) + 1

    priority_count = len([ac for ac in aircraft_list if ac.is_priority])
    high_interest_count = len([ac for ac in aircraft_list if ac.is_high_interest])

    console.print()
    console.rule("[bold]Summary[/bold]", style="blue")
    console.print()

    # Database info
    console.print(f"[bold cyan]Aircraft Database:[/bold cyan] {db_size:,} aircraft loaded from CSV")
    all_priority = TOP_PRIORITY_CATEGORIES | HIGH_PRIORITY_CATEGORIES
    console.print(f"[bold cyan]Priority Categories:[/bold cyan] {', '.join(sorted(all_priority))}")
    console.print()

    # Results
    console.rule("[dim]Detection Results[/dim]", style="dim")
    console.print(f"[dim]Military aircraft scanned:[/dim] {total_scanned}")
    console.print(f"[dim]Matched in database:[/dim] {len(aircraft_list)}")
    console.print()

    # Priority alerts
    if priority_count > 0:
        priority_cats = set(ac.category for ac in aircraft_list if ac.is_priority)
        console.print(f"[bold red]★ PRIORITY ALERT:[/bold red] {priority_count} aircraft in: [bold]{', '.join(sorted(priority_cats))}[/bold]")
    else:
        console.print("[dim]★ No priority aircraft currently detected[/dim]")

    if high_interest_count > 0:
        console.print(f"[yellow]◆ High Interest:[/yellow] {high_interest_count} aircraft")

    console.print()

    # Breakdown by category
    if category_counts:
        console.print("[bold]Aircraft by Category:[/bold]")
        for cat in sorted(category_counts.keys(), key=lambda c: (c not in TOP_PRIORITY_CATEGORIES, c)):
            count = category_counts[cat]
            if cat in TOP_PRIORITY_CATEGORIES:
                console.print(f"   [bold red]★ {cat}:[/bold red] {count}")
            elif cat in HIGH_PRIORITY_CATEGORIES:
                console.print(f"   [yellow]◆ {cat}:[/yellow] {count}")
            else:
                console.print(f"   [dim]{cat}:[/dim] {count}")

    console.print()


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point"""
    console = Console() if RICH_AVAILABLE else None

    # Header
    if RICH_AVAILABLE:
        console.print()
        console.print(Panel.fit(
            "[bold white]AirForceNone v2[/bold white]\n"
            "[dim]Presidential & VIP Aircraft Tracker[/dim]\n\n"
            "[cyan]Data Source:[/cyan] ADSB.One API (FREE)\n"
            "[cyan]Aircraft DB:[/cyan] plane-alert-db.csv",
            border_style="blue",
        ))
        console.print()
    else:
        print("\n" + "="*60)
        print(" AirForceNone v2 - Aircraft Tracker")
        print("="*60 + "\n")

    # Load database
    if RICH_AVAILABLE:
        console.print("[dim]Loading aircraft database from CSV...[/dim]")

    database = load_aircraft_database(CSV_PATH)

    if not database:
        print("Error: Could not load aircraft database!")
        return

    if RICH_AVAILABLE:
        console.print(f"[green]✓[/green] Loaded {len(database):,} aircraft from database")
        console.print()

    # Initialize API client
    client = ADSBOneClient()

    # Fetch military aircraft
    if RICH_AVAILABLE:
        console.print("[dim]Fetching military aircraft from ADSB.One...[/dim]")

    response = client.get_military_aircraft()

    total_military = len(response.get("ac", []))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    if RICH_AVAILABLE:
        console.print(f"[green]✓[/green] Received {total_military} military aircraft at {timestamp}")
        console.print()

    # Match against database
    tracked = []
    for ac_data in response.get("ac", []):
        aircraft = parse_tracked_aircraft(ac_data, database)
        if aircraft:
            tracked.append(aircraft)

    # Display results
    if RICH_AVAILABLE:
        if tracked:
            console.print(f"[bold green]Found {len(tracked)} aircraft from database![/bold green]")

            # Table 1: Government & Dictator Alert (detailed panels)
            display_government_dictators(tracked)

            # Table 2: Spy planes & Special Forces
            display_spy_special_forces(tracked)

            # Table 3: Military aircraft
            display_military(tracked)

        else:
            console.print("[yellow]No database aircraft currently detected.[/yellow]")

        # Summary
        display_summary(tracked, total_military, len(database))
    else:
        print(f"Found {len(tracked)} tracked aircraft")
        for ac in tracked:
            print(f"  [{ac.category}] {ac.operator}: {ac.callsign} ({ac.icao_type})")


if __name__ == "__main__":
    main()
