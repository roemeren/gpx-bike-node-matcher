from app.constants import *
from pathlib import Path
import datetime
import re
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

DATA_VERSION_FILE = Path("data/processed/DATA_VERSION")
VERSION_FILE = Path("VERSION")

# --- change plotly settings ---
pio.templates.default = "plotly_white"
pio.templates["plotly_white"].layout.font.family = FONT_MAIN
pio.templates["plotly_white"].layout.font.size = 13

def get_data_version():
    """Return dataset version from DATA_VERSION as DD-MMM-YYYY, or 'unknown'."""
    if DATA_VERSION_FILE.exists():
        raw = DATA_VERSION_FILE.read_text().strip()
        try:
            # Parse YYMMDD
            dt = datetime.datetime.strptime(raw, "%y%m%d")
            return dt.strftime("%d-%b-%Y")  # e.g., 22-Sep-2025
        except Exception:
            return raw
    return "unknown"

def get_app_version():
    """Return the app version from VERSION file"""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "unknown"

def make_track_tooltip(feature):
    """Return styled HTML string for a GPX feature tooltip."""
    row = feature["properties"]

    # Parse and format date
    try:
        date_str = datetime.fromisoformat(row['track_date']).strftime("%Y-%m-%d")
    except Exception:
        # fallback if it's already clean
        date_str = row['track_date'][:10]

    # Get matched counts (default to 0 if missing)
    matched_segments = int(row.get("matched_segments_count", 0))
    matched_nodes = int(row.get("matched_nodes_count", 0))

    html_string = f"""
    <div style="line-height:1.4">
        <span style="color:#999; font-size:14px;">Track </span>
        <span style="color:#000; font-size:16px; font-weight:bold;">{row['track_name']}</span>
        <br><br>
        <span style="color:#999; font-size:12px;">Date: </span>
        <span style="color:#000; font-size:12px; font-weight:bold;">{date_str}</span><br>
        <span style="color:#999; font-size:12px;">Distance: </span>
        <span style="color:#000; font-size:12px; font-weight:bold;">{row['track_length']:.2f} km</span><br>
        <span style="color:#999; font-size:12px;">File: </span>
        <span style="color:#000; font-size:12px; font-weight:bold;">{row['gpx_name']}</span><br>
        <span style="color:#999; font-size:12px;">Matched Segments: </span>
        <span style="color:#000; font-size:12px; font-weight:bold;">{matched_segments}</span><br>
        <span style="color:#999; font-size:12px;">Matched Nodes: </span>
        <span style="color:#000; font-size:12px; font-weight:bold;">{matched_nodes}</span>
        <br><br>
        <i style="color:#999; font-size:14px;">Click to zoom in on this track</i>
    </div>
    """
    return html_string

def prepare_chart_data(df, id_col, date_col, freq="M"):
    """Aggregate counts of unique IDs by period."""
    df = df.copy()
    df["period"] = df[date_col].dt.to_period("M" if freq == "M" else "Y").dt.to_timestamp()
    agg = df.groupby("period")[id_col].nunique().reset_index(name="count")
    return agg.sort_values("period")

def build_empty_figure(message):
    """Empty placeholder figure in case there are no data"""
    fig = go.Figure()
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        annotations=[
            dict(
                text=f"<i>{message}</i>",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color=COLOR_MESSAGE),
            )
        ]
    )
    return fig

def build_coverage_figure(df, agg_level, plot_type, filter_mode):

    # Sort once for consistent order
    sorted_df = df.sort_values("period").copy()

    # Identify first & last rows
    first_idx = sorted_df.index[0]
    last_idx = sorted_df.index[-1]

    # Create label column (strings only)
    sorted_df["label"] = ""
    sorted_df.loc[first_idx, "label"] = str(int(sorted_df.loc[first_idx, "count"]))
    sorted_df.loc[last_idx, "label"] = str(int(sorted_df.loc[last_idx, "count"]))

    # Optionally add middle label if enough data points
    n_points = len(sorted_df)
    if n_points >= 5:
        # For odd → exact middle; for even → lower middle (e.g. 3rd for 6 points)
        mid_pos = (n_points - 1) // 2
        mid_idx = sorted_df.index[mid_pos]
        sorted_df.loc[mid_idx, "label"] = str(int(sorted_df.loc[mid_idx, "count"]))

    # Build figure
    fig = px.line(
        sorted_df,
        x="period",
        y="count",
        color="type",
        color_discrete_map={
            "node": COLOR_NODE,
            "segment": COLOR_SEGMENT,
        },
        markers=True,
        title=f"{'Cumulative' if plot_type=='cumulative' else 'Aggregate'} "
              f"{'Network Coverage' if filter_mode=='progress' else 'New Discoveries'} Over Time",
        text="label"
    )

    # Label styling
    fig.update_traces(
        textposition="top center",
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=16),
        showlegend=False,
    )

    # --- Tooltip sentence logic ---
    if plot_type == "cumulative":
        intro = "Up to"
        verb = "had covered"
    else:
        intro = "In"
        verb = "newly covered"
    suffix = "" if filter_mode == "progress" else " for the very first time"

    # --- Axis formatting & hovertemplate ---
    hover_date = "%{x|%Y}" if agg_level == "Y" else "%{x|%b %Y}"

    # Custom hover template (single natural sentence)
    fig.update_traces(
        hovertemplate=(
            f"{intro} <b>{hover_date}</b>, you {verb} "
            f"<b>%{{y:,}}</b> "
            f"%{{fullData.name}}s{suffix}"
            "<extra></extra>"
        )
    )

    # enable spike lines on both axes
    fig.update_xaxes(showspikes=True)
    fig.update_yaxes(showspikes=True)

    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Count",
        showlegend=False,
        hoverlabel=dict(font_size=18, bgcolor="white"),
        template="plotly_white",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return fig

def sanitize_filename(filename: str) -> str:
    """Remove potentially unsafe characters like '#' from filenames."""
    # Replace unsafe characters with underscores
    sanitized = re.sub(r'[^A-Za-z0-9._ -]', '_', filename)
    # Prevent consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized.strip('_ ').strip()
