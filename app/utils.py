from pathlib import Path
from datetime import datetime
from dash import html
import dash_leaflet as dl

DATA_VERSION_FILE = Path("data/processed/DATA_VERSION")
VERSION_FILE = Path("VERSION")

def get_data_version():
    """Return dataset version from DATA_VERSION as DD-MMM-YYYY, or 'unknown'."""
    if DATA_VERSION_FILE.exists():
        raw = DATA_VERSION_FILE.read_text().strip()
        try:
            # Parse YYMMDD
            dt = datetime.strptime(raw, "%y%m%d")
            return dt.strftime("%d-%b-%Y")  # e.g., 22-Sep-2025
        except Exception:
            return raw
    return "unknown"

def get_app_version():
    """Return the app version from VERSION file"""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "unknown"

def make_gpx_tooltip(feature):
    """Return styled HTML string for a GPX feature tooltip."""
    row = feature["properties"]

    # Parse and format date
    try:
        date_str = datetime.fromisoformat(row['track_date']).strftime("%Y-%m-%d")
    except Exception:
        # fallback if it's already clean
        date_str = row['track_date'][:10]

    html_string = f"""
    <div style="line-height:1.4">
        <span style="color:#999; font-size:14px;">Track </span>
        <span style="color:#000; font-size:16px; font-weight:bold;">{row['track_name']}</span>
        <br><br>
        <span style="color:#999; font-size:11px;">Date: </span>
        <span style="color:#000; font-size:11px; font-weight:bold;">{date_str}</span><br>
        <span style="color:#999; font-size:11px;">Distance: </span>
        <span style="color:#000; font-size:11px; font-weight:bold;">{row['track_length']:.2f} km</span><br>
        <span style="color:#999; font-size:11px;">File: </span>
        <span style="color:#000; font-size:11px; font-weight:bold;">{row['gpx_name']}</span>
        <br><br>
        <i style="color:#999; font-size:14px;">Click to zoom in on this track</i>
    </div>
    """
    return html_string
