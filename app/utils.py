from app.constants import *
from pathlib import Path
import datetime
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

def make_gpx_tooltip(feature):
    """Return styled HTML string for a GPX feature tooltip."""
    row = feature["properties"]

    # Parse and format date
    try:
        date_str = datetime.fromisoformat(row['track_date']).strftime("%Y-%m-%d")
    except Exception:
        # fallback if it's already clean
        date_str = row['track_date'][:10]

    # Convert boolean to 'Yes'/'No'
    matched_text = "Yes" if row.get("matched_flag") else "No"

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
        <span style="color:#999; font-size:12px;">Matched: </span>
        <span style="color:#000; font-size:12px; font-weight:bold;">{matched_text}</span>
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
                text=message,
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color="#888"),
            )
        ]
    )
    return fig

def build_coverage_figure(df, agg_level, plot_type, filter_mode):

    fig = px.line(
        df,
        x="period",
        y="count",
        color="type",
        color_discrete_map={
            "Nodes": COLOR_NODE,
            "Segments": COLOR_SEGMENT
        },
        markers=True,
        title=f"{'Cumulative' if plot_type=='cumulative' else 'Aggregate'} "
              f"{'Network Coverage' if filter_mode=='progress' else 'New Discoveries'} Over Time",
    )

    if agg_level == "Y":
        # Format tick labels as just the year
        fig.update_xaxes(tickformat="%Y", dtick="M24")

        # Update hover label to show only the year as well
        fig.update_traces(hovertemplate="%{x|%Y}<br>%{y}")
    else:
        # Default monthly formatting
        fig.update_xaxes(tickformat="%b %Y")
        fig.update_traces(hovertemplate="%{x|%b %Y}<br>%{y}")

    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Count",
        legend_title="Element Type",
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=40, r=20, t=60, b=40),
    )

    return fig
