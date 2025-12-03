"""
Real-world Las Vegas services and agencies reference.
All information here is publicly available and non-sensitive.
"""

# Las Vegas Hotels (Real Brands)
LAS_VEGAS_HOTELS = {
    "mgm_grand": {
        "name": "MGM Grand Hotel & Casino",
        "address": "3799 Las Vegas Blvd South",
        "capacity": 500,
        "security_team": "MGM Resorts Security",
        "features": ["Athlete-only floors", "Keycard access", "24/7 concierge"]
    },
    "westgate": {
        "name": "Westgate Las Vegas Resort & Casino",
        "address": "3000 Paradise Road",
        "capacity": 400,
        "security_team": "Westgate Security",
        "features": ["Secured floors", "Escort services", "Medical support"]
    },
    "south_point": {
        "name": "South Point Hotel, Casino & Spa",
        "address": "9777 Las Vegas Blvd South",
        "capacity": 300,
        "security_team": "South Point Security",
        "features": ["Quiet zones", "Accessible rooms", "Dedicated staff"]
    },
    "venetian": {
        "name": "The Venetian Resort Las Vegas",
        "address": "3355 Las Vegas Blvd South",
        "capacity": 450,
        "security_team": "Venetian Security",
        "features": ["Premium accommodations", "Athlete floors", "24/7 support"]
    },
    "mandalay_bay": {
        "name": "Mandalay Bay Resort and Casino",
        "address": "3950 Las Vegas Blvd South",
        "capacity": 400,
        "security_team": "MGM Resorts Security",
        "features": ["Large capacity", "Event experience", "Security presence"]
    },
    "luxor": {
        "name": "Luxor Hotel & Casino",
        "address": "3900 Las Vegas Blvd South",
        "capacity": 350,
        "security_team": "MGM Resorts Security",
        "features": ["Iconic location", "Strip access", "Security coverage"]
    },
    "resorts_world": {
        "name": "Resorts World Las Vegas",
        "address": "3000 Las Vegas Blvd South",
        "capacity": 400,
        "security_team": "Resorts World Security",
        "features": ["Modern facilities", "Athlete support", "Medical access"]
    },
}

# Competition Venues (Real Locations)
COMPETITION_VENUES = {
    "unlv_cox": {
        "name": "UNLV Cox Pavilion",
        "address": "4505 S Maryland Parkway",
        "capacity": 2500,
        "type": "indoor_arena",
        "security": "UNLV Police + Event Security"
    },
    "thomas_mack": {
        "name": "Thomas & Mack Center",
        "address": "4505 S Maryland Parkway",
        "capacity": 19000,
        "type": "indoor_arena",
        "security": "UNLV Police + Event Security"
    },
    "lv_convention": {
        "name": "Las Vegas Convention Center",
        "address": "3150 Paradise Road",
        "capacity": 5000,
        "type": "convention_center",
        "security": "LVCC Security + LVMPD"
    },
    "t_mobile_arena": {
        "name": "T-Mobile Arena",
        "address": "3780 Las Vegas Blvd South",
        "capacity": 20000,
        "type": "indoor_arena",
        "security": "Arena Security + LVMPD"
    },
    "dollar_loan_center": {
        "name": "Dollar Loan Center Arena",
        "address": "2600 W Horizon Ridge Parkway",
        "capacity": 6000,
        "type": "indoor_arena",
        "security": "Arena Security + Henderson Police"
    },
    "lv_ballpark": {
        "name": "Las Vegas Ballpark",
        "address": "1650 S Pavilion Center Drive",
        "capacity": 10000,
        "type": "outdoor_stadium",
        "security": "Ballpark Security + LVMPD"
    },
}

# Transportation Services (Real Systems)
TRANSPORTATION_SERVICES = {
    "las_vegas_monorail": {
        "name": "Las Vegas Monorail",
        "operator": "Las Vegas Monorail Company",
        "stations": [
            "MGM Grand Station",
            "Bally's/Paris Station",
            "Flamingo/Caesars Station",
            "Harrah's/The LINQ Station",
            "Westgate Station",
            "Convention Center Station",
            "SAHARA Station"
        ],
        "features": ["Wheelchair accessible", "Event shuttles", "Dedicated athlete transport"]
    },
    "rtc_bus": {
        "name": "RTC of Southern Nevada",
        "operator": "Regional Transportation Commission",
        "routes": [
            "Strip & Downtown Express (SDX)",
            "Deuce on the Strip",
            "Event Shuttle Routes"
        ],
        "features": ["ADA compliant", "Real-time tracking", "Event coordination"]
    },
    "ride_share_zones": {
        "name": "Designated Ride-Share Zones",
        "operators": ["Uber", "Lyft"],
        "locations": [
            "Hotel pickup zones",
            "Venue drop-off zones",
            "Airport terminals"
        ],
        "features": ["Accessible vehicles", "Event coordination", "Priority zones"]
    },
}

# Public Safety Agencies (Real Organizations)
PUBLIC_SAFETY_AGENCIES = {
    "lvmpd": {
        "name": "Las Vegas Metropolitan Police Department",
        "role": "Public safety, traffic management, event security coordination",
        "area_commands": [
            "South Central Area Command",
            "Convention Center Area",
            "Strip Corridor"
        ],
        "services": [
            "Community policing presence",
            "Traffic direction",
            "Event crowd management",
            "Emergency response coordination"
        ]
    },
    "fire_rescue": {
        "name": "Las Vegas Fire & Rescue",
        "role": "Fire suppression, emergency medical services, rescue operations",
        "stations": [
            "Station 5 (Strip area)",
            "Station 18 (Convention Center area)"
        ],
        "services": [
            "Medical first response",
            "Fire safety",
            "Emergency medical transport",
            "Event medical support"
        ]
    },
    "clark_county_fire": {
        "name": "Clark County Fire Department",
        "role": "Fire and emergency medical services in Clark County",
        "services": [
            "Emergency response",
            "Medical support",
            "Event coverage"
        ]
    },
    "amr": {
        "name": "AMR Las Vegas (American Medical Response)",
        "role": "Emergency medical transportation",
        "services": [
            "Ambulance transport",
            "Medical emergency response",
            "Hospital transport coordination"
        ]
    },
}

# Medical Facilities (Real Hospitals)
MEDICAL_FACILITIES = {
    "umc": {
        "name": "University Medical Center (UMC)",
        "address": "1800 W Charleston Blvd",
        "type": "trauma_center",
        "services": [
            "Emergency care",
            "Trauma services",
            "Specialized medical care"
        ],
        "distance_from_strip": "5 miles"
    },
    "sunrise": {
        "name": "Sunrise Hospital & Medical Center",
        "address": "3186 S Maryland Parkway",
        "type": "full_service_hospital",
        "services": [
            "Emergency care",
            "Inpatient services",
            "Specialized care"
        ],
        "distance_from_strip": "3 miles"
    },
}

# Airport (Real Facility)
AIRPORT = {
    "harry_reid": {
        "name": "Harry Reid International Airport (LAS)",
        "icao": "KLAS",
        "terminals": ["Terminal 1", "Terminal 3"],
        "services": [
            "Athlete arrival coordination",
            "Shuttle pickup zones",
            "Accessibility services",
            "Volunteer greeting areas"
        ]
    }
}

# Volunteer Organizations (Real Groups)
VOLUNTEER_ORGANIZATIONS = {
    "special_olympics_nevada": {
        "name": "Special Olympics Nevada",
        "role": "Event coordination, athlete support, volunteer management"
    },
    "las_vegas_volunteers": {
        "name": "Las Vegas Community Volunteers",
        "role": "Local support, hospitality, event assistance"
    },
}

