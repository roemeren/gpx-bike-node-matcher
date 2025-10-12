import math
import random
import zipfile
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
import gpxpy
import gpxpy.gpx

# =============================================================================
# Configuration
# =============================================================================
# ⚠️ Replace with your own key from https://openrouteservice.org/dev/#/signup
ORS_API_KEY = "YOUR_ORS_API_KEY"
PROFILE = "cycling-regular"
USE_FIXED_SEED = True
FIXED_SEED = 42
N_RIDES = 50
DIST_RANGE_KM = (25, 100)
OUTPUT_DIR = Path("data/sample")
ZIP_NAME = "sample_rides_ors.zip"

# Triangle roughly covering Belgium
A = (2.500598113784781, 51.38374433155327)  # (lon, lat)
B = (6.287612556287783, 51.522101934243)
C = (6.304094137687353, 49.34180026957003)

# =============================================================================
# Helpers
# =============================================================================
def set_random_seed():
    """Set and log random seed."""
    if USE_FIXED_SEED:
        random.seed(FIXED_SEED)
        seed_used = FIXED_SEED
    else:
        seed_used = random.randint(0, 999999)
        random.seed(seed_used)
    print(f"🧩 Using random seed: {seed_used} (USE_FIXED_SEED={USE_FIXED_SEED})")
    return seed_used


def haversine(lat1, lon1, lat2, lon2):
    """Return great-circle distance (meters)."""
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def random_point_be():
    """
    Generate a random point within the triangle ABC (approx Belgium).
    Uses barycentric coordinates to ensure uniform distribution inside the triangle.
    """
    r1, r2 = random.random(), random.random()
    if r1 + r2 > 1:
        r1, r2 = 1 - r1, 1 - r2
    lon = A[0] + r1 * (B[0] - A[0]) + r2 * (C[0] - A[0])
    lat = A[1] + r1 * (B[1] - A[1]) + r2 * (C[1] - A[1])
    return (lon, lat)


def random_point_nearby(start, distance_km, bearing_deg):
    """Return (lon, lat) at distance_km and bearing_deg from start."""
    R = 6371.0  # Earth radius (km)
    lat1 = math.radians(start[1])
    lon1 = math.radians(start[0])
    d = distance_km / R
    brng = math.radians(bearing_deg)

    lat2 = math.asin(math.sin(lat1) * math.cos(d) +
                     math.cos(lat1) * math.sin(d) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(d) * math.cos(lat1),
                             math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return (math.degrees(lon2), math.degrees(lat2))


def random_route_within_range():
    """Return a start and end point within a random distance range."""
    start = random_point_be()
    distance = random.uniform(*DIST_RANGE_KM)
    bearing = random.uniform(0, 360)
    end = random_point_nearby(start, distance, bearing)
    return start, end


def route_ors(start, end, retries=3, delay=1.0):
    """Fetch ORS route (cycling-regular) between two lon/lat points."""
    url = f"https://api.openrouteservice.org/v2/directions/{PROFILE}"
    params = {
        "api_key": ORS_API_KEY,
        "start": f"{start[0]},{start[1]}",
        "end": f"{end[0]},{end[1]}",
        "geometry_format": "geojson"
    }

    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()["features"][0]["geometry"]["coordinates"]
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise


def save_coords_to_gpx(coords, filename, track_name="ORS Route", avg_speed_kmh=20):
    """Save coords to GPX with artificial timestamps (≈ avg_speed_kmh)."""
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack(name=track_name)
    gpx.tracks.append(gpx_track)
    seg = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(seg)

    # Random start date between 2010 and now
    start_date = datetime(
        random.randint(2010, datetime.now().year),
        random.randint(1, 12),
        random.randint(1, 28),
        random.randint(6, 18),
        random.randint(0, 59)
    )

    sec_per_meter = 3600 / (avg_speed_kmh * 1000)
    t = start_date
    prev = None
    for lon, lat in coords:
        if prev:
            dist = haversine(prev[1], prev[0], lat, lon)
            t += timedelta(seconds=dist * sec_per_meter)
        seg.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, time=t))
        prev = (lon, lat)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(gpx.to_xml())


# =============================================================================
# Main
# =============================================================================
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    seed_used = set_random_seed()

    success_count = 0

    for i in range(1, N_RIDES + 1):
        start, end = random_route_within_range()
        time.sleep(1.0)  # ✅ polite delay between API calls to avoid 429s

        try:
            coords = route_ors(start, end)
        except Exception as e:
            print(f"⚠️ Ride {i} failed ({e}), skipping.")
            continue

        fname = OUTPUT_DIR / f"ride_{i:03d}.gpx"
        save_coords_to_gpx(coords, fname)
        dist_est_km = haversine(start[1], start[0], end[1], end[0]) / 1000
        print(f"✅ Saved {fname.name} (~{dist_est_km:.1f} km, {len(coords)} pts)")
        success_count += 1

    # Zip all GPX
    zip_path = OUTPUT_DIR / ZIP_NAME
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for file in OUTPUT_DIR.glob("*.gpx"):
            z.write(file, arcname=file.name)

    print(f"\n📦 Created {zip_path.resolve()} with {success_count} rides (out of max {N_RIDES}).")

    # Clean up GPX files
    for file in OUTPUT_DIR.glob("*.gpx"):
        try:
            file.unlink()
        except Exception as e:
            print(f"⚠️ Could not delete {file.name}: {e}")
    
    print("✅ Cleanup complete — only ZIP and README remain.")

    # Folder README
    readme = f"""# Sample GPX Data (ORS)

Generated {success_count} synthetic bike rides (out of max. {N_RIDES})
using OpenRouteService '{PROFILE}' profile.
All tracks include artificial timestamps (≈20 km/h avg speed).

Random seed used: {seed_used}
Distance range: {DIST_RANGE_KM[0]}–{DIST_RANGE_KM[1]} km
"""
    with open(OUTPUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
