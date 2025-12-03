"""
Seed spatial data for Las Vegas venues.
Run this after database is initialized.
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# Real Las Vegas venue coordinates (lat, lon)
VENUES = [
    # Airport
    {
        "name": "Harry Reid International Airport (LAS)",
        "venue_type": "airport",
        "capacity": 1000,
        "lat": 36.084,
        "lon": -115.153,
    },
    # Hotels
    {
        "name": "MGM Grand Hotel & Casino",
        "venue_type": "hotel",
        "capacity": 500,
        "lat": 36.1027,
        "lon": -115.171,
    },
    {
        "name": "Westgate Las Vegas Resort & Casino",
        "venue_type": "hotel",
        "capacity": 400,
        "lat": 36.1144,
        "lon": -115.1689,
    },
    {
        "name": "South Point Hotel, Casino & Spa",
        "venue_type": "hotel",
        "capacity": 300,
        "lat": 36.0125,
        "lon": -115.1753,
    },
    {
        "name": "The Venetian Resort Las Vegas",
        "venue_type": "hotel",
        "capacity": 450,
        "lat": 36.1214,
        "lon": -115.1694,
    },
    {
        "name": "Mandalay Bay Resort and Casino",
        "venue_type": "hotel",
        "capacity": 400,
        "lat": 36.0929,
        "lon": -115.1767,
    },
    {
        "name": "Luxor Hotel & Casino",
        "venue_type": "hotel",
        "capacity": 350,
        "lat": 36.0955,
        "lon": -115.1761,
    },
    {
        "name": "Resorts World Las Vegas",
        "venue_type": "hotel",
        "capacity": 400,
        "lat": 36.1189,
        "lon": -115.1681,
    },
    # Competition Venues
    {
        "name": "UNLV Cox Pavilion",
        "venue_type": "venue",
        "capacity": 2500,
        "lat": 36.102,
        "lon": -115.150,
    },
    {
        "name": "Thomas & Mack Center",
        "venue_type": "venue",
        "capacity": 19000,
        "lat": 36.104,
        "lon": -115.152,
    },
    {
        "name": "Las Vegas Convention Center",
        "venue_type": "venue",
        "capacity": 5000,
        "lat": 36.125,
        "lon": -115.165,
    },
    {
        "name": "T-Mobile Arena",
        "venue_type": "venue",
        "capacity": 20000,
        "lat": 36.1028,
        "lon": -115.1783,
    },
    {
        "name": "Dollar Loan Center Arena",
        "venue_type": "venue",
        "capacity": 6000,
        "lat": 36.0811,
        "lon": -115.2406,
    },
    {
        "name": "Las Vegas Ballpark",
        "venue_type": "venue",
        "capacity": 10000,
        "lat": 36.1231,
        "lon": -115.1547,
    },
    # Hospitals
    {
        "name": "University Medical Center (UMC)",
        "venue_type": "hospital",
        "capacity": 100,
        "lat": 36.1447,
        "lon": -115.1481,
    },
    {
        "name": "Sunrise Hospital & Medical Center",
        "venue_type": "hospital",
        "capacity": 100,
        "lat": 36.1694,
        "lon": -115.1231,
    },
    # Transportation Hubs
    {
        "name": "MGM Grand Monorail Station",
        "venue_type": "transportation",
        "capacity": 200,
        "lat": 36.1027,
        "lon": -115.171,
    },
    {
        "name": "Convention Center Monorail Station",
        "venue_type": "transportation",
        "capacity": 200,
        "lat": 36.125,
        "lon": -115.165,
    },
]


def seed_venues():
    """Insert venues into database."""
    conn = psycopg2.connect(
        host="localhost",
        database="special_olympics",
        user="postgres",
        password="postgres",
        port=5432,
    )
    
    cur = conn.cursor()
    
    try:
        # Clear existing venues (optional - comment out if you want to keep existing)
        cur.execute("DELETE FROM venues")
        
        # Insert venues
        for venue in VENUES:
            # Create PostGIS Point geometry (lon, lat)
            cur.execute(
                """
                INSERT INTO venues (name, venue_type, capacity, geom)
                VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                """,
                (
                    venue["name"],
                    venue["venue_type"],
                    venue["capacity"],
                    venue["lon"],
                    venue["lat"],
                ),
            )
        
        conn.commit()
        print(f"Successfully inserted {len(VENUES)} venues")
        
    except Exception as e:
        conn.rollback()
        print(f"Error seeding venues: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed_venues()

