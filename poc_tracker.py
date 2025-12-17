#!/usr/bin/env python3
"""
AirForceNone - Presidential Aircraft Tracker PoC
================================================
Proof of Concept script to verify ADSB.One API functionality
and track presidential/government VIP aircraft.

Data Source: https://api.adsb.one (FREE - 1 req/sec)
"""

import requests
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

# Try to import Rich for fancy output, fallback to plain text
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
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
    print("Note: Install 'reverse_geocoder' for location info: pip install reverse_geocoder")


# =============================================================================
# PRIORITY COUNTRIES (highlighted in output)
# =============================================================================

PRIORITY_COUNTRIES = {"USA", "Russia", "Czech Rep", "Ukraine", "China", "North Korea"}

# =============================================================================
# PRESIDENTIAL & GOVERNMENT VIP AIRCRAFT DATABASE
# =============================================================================

PRESIDENTIAL_AIRCRAFT = {
    # =========================================================================
    # PRIORITY COUNTRIES
    # =========================================================================

    # -------------------------------------------------------------------------
    # USA - Presidential & Executive Fleet
    # -------------------------------------------------------------------------
    "ae001f": {"country": "USA", "description": "Air Force One (VC-25A)", "registration": "82-8000", "type": "VC25"},
    "ae0020": {"country": "USA", "description": "Air Force One (VC-25A)", "registration": "92-9000", "type": "VC25"},
    "ae001c": {"country": "USA", "description": "Air Force Two (C-32A)", "registration": "98-0001", "type": "C32"},
    "ae001d": {"country": "USA", "description": "Air Force Two (C-32A)", "registration": "98-0002", "type": "C32"},
    "ae4a48": {"country": "USA", "description": "C-32A VIP Transport", "registration": "99-6143", "type": "C32"},
    "ae01fa": {"country": "USA", "description": "C-40B Executive Transport", "registration": "01-0040", "type": "C40"},
    "ae01fb": {"country": "USA", "description": "C-40B Executive Transport", "registration": "01-0041", "type": "C40"},
    "ae010c": {"country": "USA", "description": "C-37A Gulfstream VIP", "registration": "97-0400", "type": "C37A"},
    "ae010d": {"country": "USA", "description": "C-37A Gulfstream VIP", "registration": "97-0401", "type": "C37A"},
    "ae0100": {"country": "USA", "description": "C-37B Gulfstream VIP", "registration": "09-0525", "type": "C37B"},
    "ae0101": {"country": "USA", "description": "C-37B Gulfstream VIP", "registration": "09-0540", "type": "C37B"},
    # E-4B Nightwatch "Doomsday Planes" - Airborne Command Post
    "ae0414": {"country": "USA", "description": "E-4B Nightwatch NAOC", "registration": "73-1676", "type": "E4B"},
    "ae0415": {"country": "USA", "description": "E-4B Nightwatch NAOC", "registration": "74-0787", "type": "E4B"},
    "ae0416": {"country": "USA", "description": "E-4B Nightwatch NAOC", "registration": "75-0125", "type": "E4B"},
    "ae0417": {"country": "USA", "description": "E-4B Nightwatch NAOC", "registration": "75-0126", "type": "E4B"},
    # E-6B Mercury - Nuclear Command
    "ae0419": {"country": "USA", "description": "E-6B Mercury TACAMO", "registration": "162782", "type": "E6"},
    "ae041a": {"country": "USA", "description": "E-6B Mercury TACAMO", "registration": "162783", "type": "E6"},
    "ae041b": {"country": "USA", "description": "E-6B Mercury TACAMO", "registration": "163918", "type": "E6"},

    # -------------------------------------------------------------------------
    # RUSSIA - Presidential Fleet
    # -------------------------------------------------------------------------
    "155026": {"country": "Russia", "description": "IL-96-300PU Presidential", "registration": "RA-96016", "type": "IL96"},
    "155027": {"country": "Russia", "description": "IL-96-300PU Presidential", "registration": "RA-96017", "type": "IL96"},
    "155028": {"country": "Russia", "description": "IL-96-300PU Presidential", "registration": "RA-96018", "type": "IL96"},
    "155029": {"country": "Russia", "description": "IL-96-300PU Presidential", "registration": "RA-96019", "type": "IL96"},
    "15502a": {"country": "Russia", "description": "IL-96-300PU Presidential", "registration": "RA-96020", "type": "IL96"},
    "15502b": {"country": "Russia", "description": "IL-96-300PU Presidential", "registration": "RA-96021", "type": "IL96"},
    "15502c": {"country": "Russia", "description": "IL-96-300PU Presidential", "registration": "RA-96022", "type": "IL96"},
    "150d4e": {"country": "Russia", "description": "Tu-214PU Government", "registration": "RA-64517", "type": "T214"},
    "150d4f": {"country": "Russia", "description": "Tu-214PU Government", "registration": "RA-64520", "type": "T214"},
    "150125": {"country": "Russia", "description": "IL-96-400 Presidential", "registration": "RA-96102", "type": "IL96"},
    "155001": {"country": "Russia", "description": "Tu-214SR Government", "registration": "RA-64515", "type": "T214"},
    "155002": {"country": "Russia", "description": "Tu-214SR Government", "registration": "RA-64516", "type": "T214"},
    # Russian Air Force Command
    "145624": {"country": "Russia", "description": "Il-80 Doomsday Plane", "registration": "RA-86147", "type": "IL86"},
    "145625": {"country": "Russia", "description": "Il-80 Doomsday Plane", "registration": "RA-86148", "type": "IL86"},

    # -------------------------------------------------------------------------
    # CHINA - Government & Military
    # -------------------------------------------------------------------------
    "780a71": {"country": "China", "description": "B747-8i Presidential", "registration": "B-2479", "type": "B748"},
    "780a72": {"country": "China", "description": "B747-8i VIP", "registration": "B-2480", "type": "B748"},
    "780b71": {"country": "China", "description": "B737-800 Government", "registration": "B-4026", "type": "B738"},
    "780b72": {"country": "China", "description": "B737-800 Government", "registration": "B-4027", "type": "B738"},
    "780c01": {"country": "China", "description": "A319CJ Government", "registration": "B-4090", "type": "A319"},
    "780c02": {"country": "China", "description": "A319CJ Government", "registration": "B-4091", "type": "A319"},
    "781011": {"country": "China", "description": "PLAAF VIP Transport", "registration": "B-4025", "type": "B738"},

    # -------------------------------------------------------------------------
    # NORTH KOREA - Government (rarely visible)
    # -------------------------------------------------------------------------
    "720101": {"country": "North Korea", "description": "IL-62M Chammae-1", "registration": "P-618", "type": "IL62"},
    "720102": {"country": "North Korea", "description": "IL-62M Government", "registration": "P-885", "type": "IL62"},
    "720201": {"country": "North Korea", "description": "Tu-154 Government", "registration": "P-552", "type": "T154"},
    "720301": {"country": "North Korea", "description": "AN-148 Government", "registration": "P-671", "type": "A148"},
    "720302": {"country": "North Korea", "description": "AN-148 Government", "registration": "P-672", "type": "A148"},

    # -------------------------------------------------------------------------
    # UKRAINE - Government Fleet
    # -------------------------------------------------------------------------
    "508a28": {"country": "Ukraine", "description": "A319CJ Presidential", "registration": "UR-ABA", "type": "A319"},
    "508016": {"country": "Ukraine", "description": "IL-62M Government", "registration": "UR-86527", "type": "IL62"},
    "508017": {"country": "Ukraine", "description": "IL-62M Government", "registration": "UR-86528", "type": "IL62"},
    "508a01": {"country": "Ukraine", "description": "An-148 Government", "registration": "UR-UKR", "type": "A148"},

    # -------------------------------------------------------------------------
    # CZECH REPUBLIC - Government Fleet
    # -------------------------------------------------------------------------
    "498da4": {"country": "Czech Rep", "description": "A319CJ Government", "registration": "OK-GOV", "type": "A319"},
    "498d4a": {"country": "Czech Rep", "description": "CL-601 Challenger VIP", "registration": "OK-BYR", "type": "CL60"},
    "498012": {"country": "Czech Rep", "description": "A319 Air Force", "registration": "3085", "type": "A319"},
    "498001": {"country": "Czech Rep", "description": "CASA C-295M", "registration": "0452", "type": "C295"},
    "498002": {"country": "Czech Rep", "description": "CASA C-295M", "registration": "0453", "type": "C295"},

    # =========================================================================
    # EUROPEAN COUNTRIES
    # =========================================================================

    # -------------------------------------------------------------------------
    # UNITED KINGDOM - Royal/Government Fleet
    # -------------------------------------------------------------------------
    "43c6c4": {"country": "UK", "description": "RAF Voyager A330 MRTT", "registration": "ZZ330", "type": "A332"},
    "43c6c5": {"country": "UK", "description": "RAF Voyager A330 MRTT", "registration": "ZZ331", "type": "A332"},
    "43c6c6": {"country": "UK", "description": "RAF Voyager A330 MRTT", "registration": "ZZ332", "type": "A332"},
    "43c6c7": {"country": "UK", "description": "RAF Voyager A330 MRTT", "registration": "ZZ333", "type": "A332"},
    "43c6c8": {"country": "UK", "description": "RAF Voyager A330 MRTT", "registration": "ZZ334", "type": "A332"},
    "43c6c9": {"country": "UK", "description": "RAF Voyager A330 MRTT", "registration": "ZZ335", "type": "A332"},
    "43c6d0": {"country": "UK", "description": "RAF Voyager A330 MRTT", "registration": "ZZ336", "type": "A332"},
    "43c2f0": {"country": "UK", "description": "BAe 146 Royal Flight", "registration": "ZE700", "type": "B461"},
    "43c2f1": {"country": "UK", "description": "BAe 146 Royal Flight", "registration": "ZE701", "type": "B461"},

    # -------------------------------------------------------------------------
    # FRANCE - Government Fleet (Republique)
    # -------------------------------------------------------------------------
    "3b75a6": {"country": "France", "description": "A330-200 Cotam 001", "registration": "F-RARF", "type": "A332"},
    "3b75a5": {"country": "France", "description": "A330-200 Cotam 002", "registration": "F-RARE", "type": "A332"},
    "3b7541": {"country": "France", "description": "Falcon 7X VIP", "registration": "F-RAFB", "type": "FA7X"},
    "3b7542": {"country": "France", "description": "Falcon 7X VIP", "registration": "F-RAFC", "type": "FA7X"},
    "3b7543": {"country": "France", "description": "Falcon 900 VIP", "registration": "F-RAFD", "type": "F900"},
    "3b7544": {"country": "France", "description": "Falcon 2000 VIP", "registration": "F-RAFE", "type": "F2TH"},
    "3b7545": {"country": "France", "description": "A340-200 VIP", "registration": "F-RAJB", "type": "A342"},
    "3b7601": {"country": "France", "description": "A330 MRTT Phenix", "registration": "F-UJCA", "type": "A332"},
    "3b7602": {"country": "France", "description": "A330 MRTT Phenix", "registration": "F-UJCB", "type": "A332"},

    # -------------------------------------------------------------------------
    # GERMANY - Government Fleet (Flugbereitschaft)
    # -------------------------------------------------------------------------
    "3f4615": {"country": "Germany", "description": "A350-900 Konrad Adenauer", "registration": "10+01", "type": "A359"},
    "3f4616": {"country": "Germany", "description": "A350-900 Theodor Heuss", "registration": "10+02", "type": "A359"},
    "3f4617": {"country": "Germany", "description": "A350-900 Kurt Schumacher", "registration": "10+03", "type": "A359"},
    "3f4542": {"country": "Germany", "description": "A321-200 VIP", "registration": "15+01", "type": "A321"},
    "3f4543": {"country": "Germany", "description": "A321-200 VIP", "registration": "15+02", "type": "A321"},
    "3f4544": {"country": "Germany", "description": "A319CJ VIP", "registration": "15+03", "type": "A319"},
    "3f4545": {"country": "Germany", "description": "A319CJ VIP", "registration": "15+04", "type": "A319"},
    "3f457c": {"country": "Germany", "description": "Global 5000 VIP", "registration": "14+01", "type": "GL5T"},
    "3f457d": {"country": "Germany", "description": "Global 5000 VIP", "registration": "14+02", "type": "GL5T"},
    "3f457e": {"country": "Germany", "description": "Global 5000 VIP", "registration": "14+03", "type": "GL5T"},
    "3f457f": {"country": "Germany", "description": "Global 5000 VIP", "registration": "14+04", "type": "GL5T"},

    # -------------------------------------------------------------------------
    # ITALY - Government Fleet
    # -------------------------------------------------------------------------
    "33ff01": {"country": "Italy", "description": "A340-500 Presidential", "registration": "I-TALY", "type": "A345"},
    "33ff02": {"country": "Italy", "description": "A319CJ VIP", "registration": "MM62243", "type": "A319"},
    "33ff03": {"country": "Italy", "description": "A319CJ VIP", "registration": "MM62174", "type": "A319"},
    "33ff10": {"country": "Italy", "description": "Falcon 900EX VIP", "registration": "MM62210", "type": "F900"},
    "33ff11": {"country": "Italy", "description": "Falcon 900EX VIP", "registration": "MM62211", "type": "F900"},
    "33ff12": {"country": "Italy", "description": "Falcon 900EX VIP", "registration": "MM62244", "type": "F900"},

    # -------------------------------------------------------------------------
    # SPAIN - Government Fleet
    # -------------------------------------------------------------------------
    "34318c": {"country": "Spain", "description": "A310-300 VIP", "registration": "T.22-1", "type": "A310"},
    "34318d": {"country": "Spain", "description": "A310-300 VIP", "registration": "T.22-2", "type": "A310"},
    "343191": {"country": "Spain", "description": "Falcon 900 VIP", "registration": "T.18-1", "type": "F900"},
    "343192": {"country": "Spain", "description": "Falcon 900 VIP", "registration": "T.18-2", "type": "F900"},
    "343193": {"country": "Spain", "description": "Falcon 900 VIP", "registration": "T.18-3", "type": "F900"},
    "343194": {"country": "Spain", "description": "Falcon 900 VIP", "registration": "T.18-4", "type": "F900"},
    "343195": {"country": "Spain", "description": "Falcon 900 VIP", "registration": "T.18-5", "type": "F900"},
    "3431a0": {"country": "Spain", "description": "A400M Atlas", "registration": "T.23-01", "type": "A400"},

    # -------------------------------------------------------------------------
    # POLAND - Government Fleet
    # -------------------------------------------------------------------------
    "489702": {"country": "Poland", "description": "B737-800 Head of State", "registration": "SP-LIG", "type": "B738"},
    "489460": {"country": "Poland", "description": "Gulfstream G550 VIP", "registration": "0110", "type": "G550"},
    "489461": {"country": "Poland", "description": "Gulfstream G550 VIP", "registration": "0111", "type": "G550"},
    "48947e": {"country": "Poland", "description": "B737-800BBJ VIP", "registration": "0001", "type": "B738"},
    "48947f": {"country": "Poland", "description": "B737-800BBJ VIP", "registration": "0002", "type": "B738"},

    # -------------------------------------------------------------------------
    # NETHERLANDS - Government Fleet
    # -------------------------------------------------------------------------
    "484101": {"country": "Netherlands", "description": "B737-700BBJ Royal", "registration": "PH-GOV", "type": "B737"},
    "484102": {"country": "Netherlands", "description": "Gulfstream G650 VIP", "registration": "PH-GVI", "type": "G650"},
    "484110": {"country": "Netherlands", "description": "KDC-10 Tanker/VIP", "registration": "T-264", "type": "DC10"},

    # -------------------------------------------------------------------------
    # BELGIUM - Government Fleet
    # -------------------------------------------------------------------------
    "44d001": {"country": "Belgium", "description": "ERJ-135 VIP", "registration": "CE-01", "type": "E135"},
    "44d002": {"country": "Belgium", "description": "ERJ-145 VIP", "registration": "CE-02", "type": "E145"},
    "44d003": {"country": "Belgium", "description": "Falcon 7X VIP", "registration": "CD-01", "type": "FA7X"},
    "44d010": {"country": "Belgium", "description": "A321 Government", "registration": "CS-TRJ", "type": "A321"},

    # -------------------------------------------------------------------------
    # AUSTRIA - Government Fleet
    # -------------------------------------------------------------------------
    "440101": {"country": "Austria", "description": "PC-12 VIP", "registration": "OE-EPM", "type": "PC12"},
    "440102": {"country": "Austria", "description": "C-130K Hercules", "registration": "8T-CA", "type": "C130"},
    "440103": {"country": "Austria", "description": "C-130K Hercules", "registration": "8T-CB", "type": "C130"},
    "440104": {"country": "Austria", "description": "C-130K Hercules", "registration": "8T-CC", "type": "C130"},

    # -------------------------------------------------------------------------
    # SWITZERLAND - Government Fleet
    # -------------------------------------------------------------------------
    "4b0011": {"country": "Switzerland", "description": "Citation Excel VIP", "registration": "T-784", "type": "C56X"},
    "4b0012": {"country": "Switzerland", "description": "PC-24 VIP", "registration": "T-786", "type": "PC24"},
    "4b0013": {"country": "Switzerland", "description": "Falcon 900 VIP", "registration": "T-785", "type": "F900"},

    # -------------------------------------------------------------------------
    # SWEDEN - Government Fleet
    # -------------------------------------------------------------------------
    "4a8001": {"country": "Sweden", "description": "Gulfstream G550 VIP", "registration": "102001", "type": "G550"},
    "4a8002": {"country": "Sweden", "description": "Gulfstream G550 VIP", "registration": "102002", "type": "G550"},
    "4a8003": {"country": "Sweden", "description": "S102B Korpen SIGINT", "registration": "102003", "type": "G550"},

    # -------------------------------------------------------------------------
    # NORWAY - Government Fleet
    # -------------------------------------------------------------------------
    "478101": {"country": "Norway", "description": "Falcon 7X VIP", "registration": "053", "type": "FA7X"},
    "478102": {"country": "Norway", "description": "Falcon 7X VIP", "registration": "054", "type": "FA7X"},
    "478103": {"country": "Norway", "description": "Falcon 20 EW", "registration": "041", "type": "FA20"},

    # -------------------------------------------------------------------------
    # DENMARK - Government Fleet
    # -------------------------------------------------------------------------
    "459901": {"country": "Denmark", "description": "CL-604 Challenger VIP", "registration": "C-080", "type": "CL60"},
    "459902": {"country": "Denmark", "description": "CL-604 Challenger VIP", "registration": "C-168", "type": "CL60"},
    "459903": {"country": "Denmark", "description": "CL-604 Challenger VIP", "registration": "C-172", "type": "CL60"},

    # -------------------------------------------------------------------------
    # FINLAND - Government Fleet
    # -------------------------------------------------------------------------
    "461e01": {"country": "Finland", "description": "CL-604 Challenger VIP", "registration": "CC-1", "type": "CL60"},
    "461e02": {"country": "Finland", "description": "LJ-35 Learjet VIP", "registration": "LJ-1", "type": "LJ35"},
    "461e03": {"country": "Finland", "description": "LJ-35 Learjet VIP", "registration": "LJ-2", "type": "LJ35"},

    # -------------------------------------------------------------------------
    # PORTUGAL - Government Fleet
    # -------------------------------------------------------------------------
    "490501": {"country": "Portugal", "description": "Falcon 50 VIP", "registration": "17401", "type": "FA50"},
    "490502": {"country": "Portugal", "description": "Falcon 50 VIP", "registration": "17402", "type": "FA50"},
    "490503": {"country": "Portugal", "description": "Falcon 50 VIP", "registration": "17403", "type": "FA50"},

    # -------------------------------------------------------------------------
    # GREECE - Government Fleet
    # -------------------------------------------------------------------------
    "468c01": {"country": "Greece", "description": "ERJ-135 VIP", "registration": "145-208", "type": "E135"},
    "468c02": {"country": "Greece", "description": "ERJ-135 VIP", "registration": "145-209", "type": "E135"},
    "468c03": {"country": "Greece", "description": "Gulfstream V VIP", "registration": "678", "type": "GLF5"},

    # -------------------------------------------------------------------------
    # HUNGARY - Government Fleet
    # -------------------------------------------------------------------------
    "47a001": {"country": "Hungary", "description": "Falcon 7X VIP", "registration": "606", "type": "FA7X"},
    "47a002": {"country": "Hungary", "description": "Dassault 900LX VIP", "registration": "604", "type": "F900"},
    "47a003": {"country": "Hungary", "description": "A319CJ VIP", "registration": "605", "type": "A319"},

    # -------------------------------------------------------------------------
    # ROMANIA - Government Fleet
    # -------------------------------------------------------------------------
    "4a1001": {"country": "Romania", "description": "B737-700BBJ VIP", "registration": "YR-BBJ", "type": "B737"},
    "4a1002": {"country": "Romania", "description": "C-130H Hercules", "registration": "5930", "type": "C130"},

    # -------------------------------------------------------------------------
    # BULGARIA - Government Fleet
    # -------------------------------------------------------------------------
    "450501": {"country": "Bulgaria", "description": "Falcon 2000 VIP", "registration": "LZ-OOI", "type": "F2TH"},
    "450502": {"country": "Bulgaria", "description": "A319 Government", "registration": "LZ-AOB", "type": "A319"},

    # -------------------------------------------------------------------------
    # CROATIA - Government Fleet
    # -------------------------------------------------------------------------
    "501c01": {"country": "Croatia", "description": "CL-604 Challenger VIP", "registration": "9A-CRO", "type": "CL60"},

    # -------------------------------------------------------------------------
    # SLOVENIA - Government Fleet
    # -------------------------------------------------------------------------
    "4d0001": {"country": "Slovenia", "description": "Falcon 2000 VIP", "registration": "S5-BAV", "type": "F2TH"},

    # -------------------------------------------------------------------------
    # SLOVAKIA - Government Fleet
    # -------------------------------------------------------------------------
    "506c01": {"country": "Slovakia", "description": "Fokker 100 VIP", "registration": "OM-BYA", "type": "F100"},
    "506c02": {"country": "Slovakia", "description": "Fokker 100 VIP", "registration": "OM-BYB", "type": "F100"},

    # -------------------------------------------------------------------------
    # ESTONIA - Government Fleet
    # -------------------------------------------------------------------------
    "511017": {"country": "Estonia", "description": "CRJ-700 Government", "registration": "ES-PVG", "type": "CRJ7"},

    # -------------------------------------------------------------------------
    # LATVIA - Government Fleet
    # -------------------------------------------------------------------------
    "502c03": {"country": "Latvia", "description": "A220-300 Government", "registration": "YL-LFB", "type": "BCS3"},
    "502c17": {"country": "Latvia", "description": "L-410 Government", "registration": "YL-KAM", "type": "L410"},

    # -------------------------------------------------------------------------
    # LITHUANIA - Government Fleet
    # -------------------------------------------------------------------------
    "503c01": {"country": "Lithuania", "description": "L-410 Government", "registration": "01", "type": "L410"},
    "503c02": {"country": "Lithuania", "description": "C-27J Spartan", "registration": "02", "type": "C27J"},

    # -------------------------------------------------------------------------
    # IRELAND - Government Fleet
    # -------------------------------------------------------------------------
    "4c8001": {"country": "Ireland", "description": "LJ-45 Learjet VIP", "registration": "252", "type": "LJ45"},
    "4c8002": {"country": "Ireland", "description": "LJ-45 Learjet VIP", "registration": "253", "type": "LJ45"},
    "4c8003": {"country": "Ireland", "description": "G280 Government", "registration": "280", "type": "G280"},

    # -------------------------------------------------------------------------
    # TURKEY - Government Fleet
    # -------------------------------------------------------------------------
    "4b8001": {"country": "Turkey", "description": "A330-200 VIP", "registration": "TC-TUR", "type": "A332"},
    "4b8002": {"country": "Turkey", "description": "A319CJ VIP", "registration": "TC-ANA", "type": "A319"},
    "4b8003": {"country": "Turkey", "description": "Gulfstream 550 VIP", "registration": "TC-DAP", "type": "G550"},
    "4b8004": {"country": "Turkey", "description": "B737-800BBJ VIP", "registration": "TC-ATA", "type": "B738"},

    # -------------------------------------------------------------------------
    # BELARUS - Government Fleet
    # -------------------------------------------------------------------------
    "151db8": {"country": "Belarus", "description": "B737-800 Presidential", "registration": "EW-001PA", "type": "B738"},
    "151db9": {"country": "Belarus", "description": "B767 VIP", "registration": "EW-001PB", "type": "B767"},
    "151dc0": {"country": "Belarus", "description": "Tu-134 Government", "registration": "EW-65149", "type": "T134"},

    # -------------------------------------------------------------------------
    # SERBIA - Government Fleet
    # -------------------------------------------------------------------------
    "4d0101": {"country": "Serbia", "description": "Falcon 900 VIP", "registration": "YU-FSS", "type": "F900"},
    "4d0102": {"country": "Serbia", "description": "ERJ-135 VIP", "registration": "YU-SRB", "type": "E135"},

    # -------------------------------------------------------------------------
    # ALBANIA - Government Fleet
    # -------------------------------------------------------------------------
    "501901": {"country": "Albania", "description": "AS365 Dauphin VIP", "registration": "ZA-BDF", "type": "AS65"},

    # -------------------------------------------------------------------------
    # NORTH MACEDONIA - Government Fleet
    # -------------------------------------------------------------------------
    "4d0301": {"country": "N. Macedonia", "description": "LJ-60 Learjet VIP", "registration": "Z3-MKD", "type": "LJ60"},

    # -------------------------------------------------------------------------
    # MONTENEGRO - Government Fleet
    # -------------------------------------------------------------------------
    "4d0201": {"country": "Montenegro", "description": "Falcon 50 VIP", "registration": "4O-MNE", "type": "FA50"},

    # -------------------------------------------------------------------------
    # BOSNIA - Government Fleet
    # -------------------------------------------------------------------------
    "4d0401": {"country": "Bosnia", "description": "HUEY II VIP", "registration": "T9-HAD", "type": "HUEY"},

    # -------------------------------------------------------------------------
    # LUXEMBOURG - Government Fleet
    # -------------------------------------------------------------------------
    "4b0501": {"country": "Luxembourg", "description": "LJ-45 Learjet VIP", "registration": "NAT-01", "type": "LJ45"},

    # -------------------------------------------------------------------------
    # ICELAND - Government Fleet
    # -------------------------------------------------------------------------
    "4ccc01": {"country": "Iceland", "description": "DHC-8 Coast Guard", "registration": "TF-SIF", "type": "DH8D"},

    # -------------------------------------------------------------------------
    # CYPRUS - Government Fleet
    # -------------------------------------------------------------------------
    "4d8001": {"country": "Cyprus", "description": "A319CJ Government", "registration": "5B-CYP", "type": "A319"},

    # -------------------------------------------------------------------------
    # MALTA - Government Fleet
    # -------------------------------------------------------------------------
    "4d9001": {"country": "Malta", "description": "B200 King Air VIP", "registration": "AS1428", "type": "BE20"},
}

# VIP callsign patterns to look for (pattern -> country mapping)
VIP_CALLSIGN_PATTERNS = {
    # Priority Countries
    "AF1": "USA", "AF2": "USA", "SAM": "USA", "EXEC": "USA", "VENUS": "USA",  # USA
    "RSD": "Russia", "ROSSIYA": "Russia", "RFF": "Russia", "RUSS": "Russia", "RFAF": "Russia",  # Russia (not RUS - causes false positives)
    "CZAF": "Czech Rep", "CEF": "Czech Rep", "CZA": "Czech Rep",  # Czech
    "UKR": "Ukraine", "UKRAINA": "Ukraine", "UKF": "Ukraine",  # Ukraine
    "CCA": "China", "CHN": "China", "CHINA": "China", "CXA": "China",  # China
    "KOR": "North Korea", "PRK": "North Korea",  # North Korea

    # European Countries
    "RRR": "UK", "RFR": "UK", "KRF": "UK", "KITTY": "UK", "ASCOT": "UK",  # UK Royal/RAF
    "COTAM": "France", "CTM": "France", "FAF": "France", "FRF": "France",  # France
    "GAF": "Germany", "GAFTT": "Germany", "GERM": "Germany",  # Germany
    "IAM": "Italy", "ITAF": "Italy",  # Italy
    "AME": "Spain", "SPANISH": "Spain", "SPA": "Spain",  # Spain
    "PLF": "Poland", "POLISH": "Poland", "POL": "Poland",  # Poland
    "NAF": "Netherlands", "NLD": "Netherlands",  # Netherlands
    "BAF": "Belgium", "BEL": "Belgium",  # Belgium
    "AUA": "Austria", "OST": "Austria",  # Austria
    "SUI": "Switzerland", "HEB": "Switzerland",  # Switzerland
    "SVF": "Sweden", "SWE": "Sweden",  # Sweden
    "NOW": "Norway", "NOR": "Norway",  # Norway
    "DAF": "Denmark", "DNK": "Denmark",  # Denmark
    "FAF": "Finland", "FIN": "Finland", "FINNAF": "Finland",  # Finland
    "PAF": "Portugal", "POR": "Portugal",  # Portugal
    "HAF": "Greece", "GRC": "Greece",  # Greece
    "HDF": "Hungary", "HUN": "Hungary",  # Hungary
    "ROF": "Romania", "ROU": "Romania",  # Romania
    "BUF": "Bulgaria", "BGR": "Bulgaria",  # Bulgaria
    "HRZ": "Croatia", "CRO": "Croatia",  # Croatia
    "SVN": "Slovenia", "SLO": "Slovenia",  # Slovenia
    "SLK": "Slovakia", "SVK": "Slovakia",  # Slovakia
    "EST": "Estonia", "EEF": "Estonia",  # Estonia
    "LAT": "Latvia", "LVA": "Latvia",  # Latvia
    "LYF": "Lithuania", "LTU": "Lithuania",  # Lithuania
    "IRL": "Ireland",  # Ireland
    "THK": "Turkey", "TUAF": "Turkey", "TCGF": "Turkey",  # Turkey (not TUR - causes false positives like TURBO)
    "BRU": "Belarus", "BLR": "Belarus",  # Belarus
    "SRB": "Serbia", "YUG": "Serbia",  # Serbia
    "ALB": "Albania",  # Albania
    "MKD": "N. Macedonia",  # North Macedonia
    "MNE": "Montenegro",  # Montenegro
    "BIH": "Bosnia",  # Bosnia
    "LUX": "Luxembourg",  # Luxembourg
    "ICE": "Iceland",  # Iceland
    "CYP": "Cyprus",  # Cyprus
    "MLT": "Malta",  # Malta
}

# VIP aircraft types commonly used for government transport
VIP_AIRCRAFT_TYPES = [
    "VC25", "C32", "C40", "C37A", "C37B",  # USA military VIP
    "E4B", "E6",  # Command & Control
    "A319", "A320", "A321",  # Common government configs
    "A332", "A333", "A359",  # Wide-body VIP
    "B738", "B739", "B77L", "B788",  # Boeing government
    "IL96", "T204", "T214",  # Russian government
    "FA7X", "F900", "F2TH",  # Falcon jets
    "G550", "G650", "GLEX", "GL5T", "GL7T",  # Gulfstream/Global
    "CL60", "CL35",  # Challenger
]


# =============================================================================
# API CLIENT
# =============================================================================

class ADSBOneClient:
    """Client for ADSB.One API"""

    BASE_URL = "https://api.adsb.one"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AirForceNone-PoC/1.0",
            "Accept": "application/json"
        })
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 request per second limit

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

    def get_aircraft_by_hex(self, hex_codes: list) -> dict:
        """Get specific aircraft by ICAO hex codes"""
        self._rate_limit()
        hex_str = ",".join(hex_codes)
        try:
            response = self.session.get(f"{self.BASE_URL}/v2/hex/{hex_str}", timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"API Error: {e}")
            return {"ac": [], "msg": str(e)}


# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

@dataclass
class AircraftInfo:
    """Structured aircraft information"""
    hex_code: str
    callsign: str
    registration: str
    aircraft_type: str
    country: str
    description: str
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[int]
    ground_speed: Optional[int]
    heading: Optional[int]
    vertical_rate: Optional[int]
    squawk: str
    on_ground: bool
    last_seen: float
    over_country: str = ""  # Country the aircraft is flying over


# Cache for reverse geocoding results
_location_cache = {}


def get_location(lat: float, lon: float) -> str:
    """Get country/city from coordinates using reverse geocoding"""
    if not RG_AVAILABLE or lat is None or lon is None:
        return ""

    cache_key = f"{lat:.2f},{lon:.2f}"
    if cache_key in _location_cache:
        return _location_cache[cache_key]

    try:
        results = rg.search([(lat, lon)], mode=1, verbose=False)
        if results:
            result = results[0]
            # Return "City, Country" or just "Country"
            city = result.get('name', '')
            country = result.get('cc', '')  # Country code

            # Map country codes to names for common ones
            country_names = {
                'US': 'USA', 'GB': 'UK', 'DE': 'Germany', 'FR': 'France',
                'IT': 'Italy', 'ES': 'Spain', 'PL': 'Poland', 'CZ': 'Czechia',
                'UA': 'Ukraine', 'RU': 'Russia', 'CN': 'China', 'KP': 'N.Korea',
                'NL': 'Netherlands', 'BE': 'Belgium', 'AT': 'Austria', 'CH': 'Switzerland',
                'SE': 'Sweden', 'NO': 'Norway', 'DK': 'Denmark', 'FI': 'Finland',
                'PT': 'Portugal', 'GR': 'Greece', 'HU': 'Hungary', 'RO': 'Romania',
                'BG': 'Bulgaria', 'HR': 'Croatia', 'SI': 'Slovenia', 'SK': 'Slovakia',
                'EE': 'Estonia', 'LV': 'Latvia', 'LT': 'Lithuania', 'IE': 'Ireland',
                'TR': 'Turkey', 'BY': 'Belarus', 'RS': 'Serbia', 'AL': 'Albania',
                'MK': 'N.Macedonia', 'ME': 'Montenegro', 'BA': 'Bosnia', 'LU': 'Luxembourg',
                'IS': 'Iceland', 'CY': 'Cyprus', 'MT': 'Malta', 'CA': 'Canada',
                'MX': 'Mexico', 'JP': 'Japan', 'KR': 'S.Korea', 'AU': 'Australia',
                'NZ': 'New Zealand', 'BR': 'Brazil', 'AR': 'Argentina', 'IN': 'India',
                'SA': 'Saudi Arabia', 'AE': 'UAE', 'IL': 'Israel', 'EG': 'Egypt',
            }
            country_name = country_names.get(country, country)

            location = f"{country_name}"
            _location_cache[cache_key] = location
            return location
    except Exception:
        pass

    return ""


def parse_aircraft(ac_data: dict, known_aircraft: dict) -> AircraftInfo:
    """Parse raw API data into structured AircraftInfo"""
    hex_code = ac_data.get("hex", "").lower()

    # Check if this is a known presidential aircraft
    known = known_aircraft.get(hex_code, {})

    lat = ac_data.get("lat")
    lon = ac_data.get("lon")

    # Get location (which country they're flying over)
    over_country = get_location(lat, lon) if lat and lon else ""

    return AircraftInfo(
        hex_code=hex_code.upper(),
        callsign=ac_data.get("flight", "").strip() or "N/A",
        registration=ac_data.get("r", "") or known.get("registration", "N/A"),
        aircraft_type=ac_data.get("t", "") or known.get("type", "N/A"),
        country=known.get("country", "Unknown"),
        description=known.get("description", "Military Aircraft"),
        latitude=lat,
        longitude=lon,
        altitude=ac_data.get("alt_baro") if ac_data.get("alt_baro") != "ground" else 0,
        ground_speed=ac_data.get("gs"),
        heading=ac_data.get("track"),
        vertical_rate=ac_data.get("baro_rate"),
        squawk=ac_data.get("squawk", "N/A"),
        on_ground=ac_data.get("alt_baro") == "ground",
        last_seen=ac_data.get("seen", 0),
        over_country=over_country,
    )


def display_rich(aircraft_list: list[AircraftInfo], title: str = "Presidential Aircraft Detected"):
    """Display aircraft using Rich library"""
    console = Console()

    if not aircraft_list:
        console.print(Panel(
            "[yellow]No presidential aircraft currently detected in airspace.[/yellow]\n"
            "[dim]They may be on the ground, transponders off, or outside coverage.[/dim]",
            title="[bold]No Aircraft Found[/bold]",
            border_style="yellow"
        ))
        return

    # Sort: Priority countries first, then alphabetically
    aircraft_list.sort(key=lambda x: (
        0 if x.country in PRIORITY_COUNTRIES else 1,  # Priority first
        x.country,
        x.description
    ))

    table = Table(
        title=f"[bold white]{title}[/bold white]",
        box=box.SIMPLE_HEAD,
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_justify="center",
        expand=False,
        padding=(0, 1),
    )

    table.add_column("Owner", style="bold yellow", no_wrap=True)
    table.add_column("Callsign", style="green", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("Alt (ft)", justify="right", no_wrap=True)
    table.add_column("Spd", justify="right", no_wrap=True)
    table.add_column("Hdg", justify="right", no_wrap=True)
    table.add_column("Over", style="cyan", no_wrap=True)
    table.add_column("Lat", justify="right", no_wrap=True, style="dim")
    table.add_column("Lon", justify="right", no_wrap=True, style="dim")

    for ac in aircraft_list:
        # Check if priority country
        is_priority = ac.country in PRIORITY_COUNTRIES

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

        # Format position
        lat_str = f"{ac.latitude:.2f}" if ac.latitude else "-"
        lon_str = f"{ac.longitude:.2f}" if ac.longitude else "-"

        # Format over country
        over_str = ac.over_country if ac.over_country else "[dim]-[/dim]"

        # Highlight priority countries
        if is_priority:
            country_str = f"[bold red]★ {ac.country}[/bold red]"
            callsign_str = f"[bold white]{ac.callsign}[/bold white]"
            style = "on grey23"
        else:
            country_str = ac.country
            callsign_str = ac.callsign
            style = None

        table.add_row(
            country_str,
            callsign_str,
            ac.aircraft_type or "?",
            alt_str,
            speed_str,
            hdg_str,
            over_str,
            lat_str,
            lon_str,
            style=style,
        )

    console.print()
    console.print(table)
    console.print()


def display_detailed_rich(aircraft: AircraftInfo):
    """Display detailed info for a single aircraft using Rich"""
    console = Console()

    # Status indicator
    if aircraft.on_ground:
        status = "[yellow]ON GROUND[/yellow]"
    elif aircraft.altitude and aircraft.altitude > 0:
        status = "[green]AIRBORNE[/green]"
    else:
        status = "[dim]UNKNOWN[/dim]"

    # Build detail text
    details = Text()
    details.append(f"ICAO: {aircraft.hex_code}", style="bold")
    details.append(f"  │  Callsign: {aircraft.callsign}", style="green")
    details.append(f"  │  Type: {aircraft.aircraft_type}\n", style="magenta")

    if aircraft.latitude and aircraft.longitude:
        details.append(f"Position: {aircraft.latitude:.4f}° N, {aircraft.longitude:.4f}° W", style="cyan")
        details.append(f"  │  Alt: {aircraft.altitude:,} ft\n" if aircraft.altitude else "  │  Alt: N/A\n")

    if aircraft.ground_speed:
        details.append(f"Speed: {aircraft.ground_speed} kts", style="white")
        details.append(f"  │  Heading: {aircraft.heading}°" if aircraft.heading else "  │  Heading: N/A")
        if aircraft.vertical_rate:
            vr_style = "green" if aircraft.vertical_rate > 0 else "red" if aircraft.vertical_rate < 0 else "white"
            details.append(f"  │  V/S: {aircraft.vertical_rate:+} fpm\n", style=vr_style)
        else:
            details.append("\n")

    details.append(f"Status: ", style="white")
    details.append(status)
    details.append(f"  │  Squawk: {aircraft.squawk}\n", style="dim")

    panel = Panel(
        details,
        title=f"[bold white]{aircraft.country}: {aircraft.description}[/bold white]",
        border_style="green" if not aircraft.on_ground else "yellow",
        padding=(0, 1),
    )

    console.print(panel)


def display_plain(aircraft_list: list[AircraftInfo], title: str = "Presidential Aircraft Detected"):
    """Display aircraft using plain text (fallback)"""
    if not aircraft_list:
        print(f"\n{'='*70}")
        print(f" {title}")
        print(f"{'='*70}")
        print(" No presidential aircraft currently detected in airspace.")
        print(" They may be on the ground, transponders off, or outside coverage.")
        print(f"{'='*70}\n")
        return

    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")

    for ac in aircraft_list:
        print(f"\n [{ac.country}] {ac.description}")
        print(f"   ICAO: {ac.hex_code}  |  Callsign: {ac.callsign}  |  Type: {ac.aircraft_type}")

        if ac.latitude and ac.longitude:
            print(f"   Position: {ac.latitude:.4f}, {ac.longitude:.4f}  |  Alt: {ac.altitude or 'N/A'} ft")

        if ac.ground_speed:
            print(f"   Speed: {ac.ground_speed} kts  |  Heading: {ac.heading}°  |  V/S: {ac.vertical_rate or 0} fpm")

        status = "ON GROUND" if ac.on_ground else "AIRBORNE" if ac.altitude else "UNKNOWN"
        print(f"   Status: {status}  |  Squawk: {ac.squawk}")

    print(f"\n{'='*70}\n")


# =============================================================================
# MAIN TRACKER LOGIC
# =============================================================================

def find_presidential_aircraft(api_response: dict) -> list[AircraftInfo]:
    """Filter API response for presidential/VIP aircraft"""
    presidential = []
    seen_hex = set()  # Avoid duplicates

    aircraft_list = api_response.get("ac", [])

    for ac in aircraft_list:
        hex_code = ac.get("hex", "").lower()
        callsign = ac.get("flight", "").strip().upper()
        ac_type = ac.get("t", "").upper()

        if hex_code in seen_hex:
            continue

        # Check 1: Known ICAO hex codes
        if hex_code in PRESIDENTIAL_AIRCRAFT:
            info = parse_aircraft(ac, PRESIDENTIAL_AIRCRAFT)
            presidential.append(info)
            seen_hex.add(hex_code)
            continue

        # Check 2: VIP callsign patterns
        matched_country = None
        for pattern, country in VIP_CALLSIGN_PATTERNS.items():
            if callsign.startswith(pattern):
                matched_country = country
                break

        if matched_country:
            info = parse_aircraft(ac, PRESIDENTIAL_AIRCRAFT)
            info.country = matched_country
            info.description = f"VIP Flight ({callsign})"
            presidential.append(info)
            seen_hex.add(hex_code)

    return presidential


def main():
    """Main entry point"""
    console = Console() if RICH_AVAILABLE else None

    # Header
    if RICH_AVAILABLE:
        console.print()
        console.print(Panel.fit(
            "[bold white]AirForceNone[/bold white]\n"
            "[dim]Presidential Aircraft Tracker - Proof of Concept[/dim]\n\n"
            "[cyan]Data Source:[/cyan] ADSB.One API (FREE)\n"
            "[cyan]Rate Limit:[/cyan] 1 request/second",
            border_style="blue",
        ))
        console.print()
    else:
        print("\n" + "="*50)
        print(" AirForceNone - Presidential Aircraft Tracker PoC")
        print(" Data Source: ADSB.One API (FREE)")
        print("="*50 + "\n")

    # Initialize API client
    client = ADSBOneClient()

    # Fetch military aircraft
    if RICH_AVAILABLE:
        console.print("[dim]Fetching military aircraft from ADSB.One...[/dim]")
    else:
        print("Fetching military aircraft from ADSB.One...")

    response = client.get_military_aircraft()

    total_military = len(response.get("ac", []))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    if RICH_AVAILABLE:
        console.print(f"[green]✓[/green] Received {total_military} military aircraft at {timestamp}")
        console.print()
    else:
        print(f"✓ Received {total_military} military aircraft at {timestamp}\n")

    # Find presidential aircraft
    presidential = find_presidential_aircraft(response)

    # Display results
    if RICH_AVAILABLE:
        # Show summary
        if presidential:
            console.print(f"[bold green]Found {len(presidential)} presidential/VIP aircraft![/bold green]\n")

            # Show ALL aircraft - priority countries first
            display_rich(presidential, f"All {len(presidential)} Presidential/VIP Aircraft Detected")

        else:
            display_rich([], "Presidential Aircraft Scan")

            # Show some interesting military aircraft instead
            console.print("\n[yellow]Showing sample of active military aircraft instead:[/yellow]\n")

            sample_military = []
            for ac in response.get("ac", [])[:15]:
                info = parse_aircraft(ac, PRESIDENTIAL_AIRCRAFT)
                sample_military.append(info)

            if sample_military:
                display_rich(sample_military, "Sample Military Aircraft (for reference)")
    else:
        display_plain(presidential, f"All {len(presidential)} Presidential/VIP Aircraft")

    # Summary stats
    if RICH_AVAILABLE:
        priority_count = len([a for a in presidential if a.country in PRIORITY_COUNTRIES])
        countries_found = set(a.country for a in presidential)
        priority_countries_found = countries_found & PRIORITY_COUNTRIES
        priority_countries_not_found = PRIORITY_COUNTRIES - countries_found

        # Count aircraft by country
        country_counts = {}
        for a in presidential:
            country_counts[a.country] = country_counts.get(a.country, 0) + 1

        console.print()
        console.rule("[bold]Summary[/bold]", style="blue")
        console.print()

        # What we're monitoring
        console.print(f"[bold cyan]Monitoring Priority Countries:[/bold cyan] {', '.join(sorted(PRIORITY_COUNTRIES))}")
        console.print(f"[dim]Known aircraft in database:[/dim] {len(PRESIDENTIAL_AIRCRAFT)} aircraft from {len(set(a['country'] for a in PRESIDENTIAL_AIRCRAFT.values()))} countries")
        console.print(f"[dim]Callsign patterns tracked:[/dim] {len(VIP_CALLSIGN_PATTERNS)} patterns")
        console.print()

        # What we found
        console.rule("[dim]Detection Results[/dim]", style="dim")
        console.print(f"[dim]Total military aircraft scanned:[/dim] {total_military}")
        console.print(f"[dim]Presidential/VIP aircraft found:[/dim] {len(presidential)}")
        console.print()

        # Priority countries status
        if priority_count > 0:
            console.print(f"[bold red]★ PRIORITY ALERT:[/bold red] {priority_count} aircraft detected from: [bold]{', '.join(sorted(priority_countries_found))}[/bold]")
        else:
            console.print(f"[yellow]★ No priority country aircraft currently airborne[/yellow]")

        if priority_countries_not_found:
            console.print(f"[dim]   Not currently detected: {', '.join(sorted(priority_countries_not_found))}[/dim]")
        console.print()

        # Breakdown by country
        if country_counts:
            console.print("[bold]Aircraft by Owner Country:[/bold]")
            for country in sorted(country_counts.keys(), key=lambda c: (c not in PRIORITY_COUNTRIES, c)):
                count = country_counts[country]
                if country in PRIORITY_COUNTRIES:
                    console.print(f"   [bold red]★ {country}:[/bold red] {count} aircraft")
                else:
                    console.print(f"   [dim]{country}:[/dim] {count} aircraft")

        console.print()
    else:
        print("-" * 50)
        print(f"Total military aircraft tracked: {total_military}")
        print(f"Presidential/VIP aircraft found: {len(presidential)}")
        print("-" * 50 + "\n")


if __name__ == "__main__":
    main()
