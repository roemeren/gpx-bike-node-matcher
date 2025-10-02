from core.common import *
from app.geoprocessing import *
from app.utils import *
import json
import base64
import threading
import datetime
import psutil
from dash import no_update, Dash, html, dcc, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash.exceptions import PreventUpdate
from dash_extensions.javascript import Namespace

# for debugging (usage: trigger = ctx.triggered_id)
from dash import callback_context as ctx  # or dash.ctx

color_network = '#7f8c8d'
color_gpx_1 = '#FC4C02'
color_gpx_2 = '#D62728'
color_gpx_selected = '#A3FF12'
color_processing = '#343a40'
color_highlight_segment = "red"
color_highlight_node = "purple"
min_zoom_points = 11
initial_center =  [50.65, 4.45]
initial_zoom = 8
date_picker_min_date = datetime.date(2010, 1, 1)
date_picker_max_date = datetime.date.today()

# segment layer rendering
weight_classes = [1, 5, 10, 20]  # thresholds for counts
weights = [2, 4, 6, 8, 10]       # corresponding line weights
color_segment = '#33A7AA'        # fixed color (alternatives: #78A2D2)

# gpx layer rendering
_tooltips_html = {}
KEEP_SELECTION_ACTIVE = True

# Ensure static folder exists
os.makedirs(STATIC_FOLDER, exist_ok=True)

# Load bike network GeoDataFrames (for processing)
bike_network_seg = gpd.read_parquet(multiline_parquet_proj)
bike_network_node = gpd.read_parquet(point_parquet_proj)

# Load simplified bike network GeoJSON lines (for mapping)
with open(multiline_geojson , "r") as f:
   geojson_network = json.load(f)

# If needed apply custom settings for debug mode (e.g. limit resources)
DEBUG_MODE = True

# Access JS functions in assets/ and make them callable from Python
# Source: https://www.dash-leaflet.com/docs/func_props
ns = Namespace("dashExtensions", "default")

SELECTED_KEY = "track_uid"  # change if you want a different identifier

# Themes: see https://www.dash-bootstrap-components.com/docs/themes/explorer/
app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR])
server = app.server

# Check memory usage before processing
process = psutil.Process(os.getpid())
print(f"Memory usage after initializing application: {process.memory_info().rss / 1024**2:.2f} MB")

# ---------- Layout ----------
app.layout = dbc.Container(
    [
        html.Div([
            html.H1(
                "Belgian Bike Node Network Matcher",
                className="text-center my-2 display-4"
            ),
            html.P(
                "Upload a zip file with your GPX rides and see how they align with Belgium’s bike node network.",
                className="text-center text-muted mb-4"
            )
        ]),

        dbc.Row([
            # Left panel
            dbc.Col(
                [
                    dcc.Upload(
                        id="upload-zip",
                        children=html.Div(["Drag & Drop or ", html.A("Browse for ZIP")]),
                        accept=".zip",
                        multiple=False,
                        style={
                            "width": "100%", "height": "60px", "lineHeight": "60px",
                            "borderWidth": "1px", "borderStyle": "dashed",
                            "borderRadius": "5px", "textAlign": "center",
                            "margin-bottom": "10px"
                        },
                    ),
                    html.Div(id="browse-info"),
                    dbc.Button("Process ZIP", id="btn-process", color="primary", className="mb-2", disabled=False),
                    dbc.Progress(id="progress", value=0, striped=True, animated=True, className="mb-2"),
                    html.Div(
                        id="processing-status",
                        style={
                            "padding": "5px 10px",
                            "borderRadius": "5px",
                            "fontFamily": "monospace",
                            "color": color_processing,
                            "fontSize": "0.95rem"
                        }
                    ),
                    html.Div(
                        dbc.Button(
                            "Download Results",
                            id="btn-download",
                            color="success",
                            className="mt-2",
                            external_link=True,
                            style={"display": "none"} # initially hidden
                        ),
                        id="download-container"
                    ),
                    # --- Show data and app version ---
                    html.Div([
                        f"Data version: {get_data_version()} (source: ",
                        html.A("Geofabrik", href="https://download.geofabrik.de/europe/belgium.html#", target="_blank"),
                        ")"
                    ], style={"fontSize": "12px", "color": "#666", "marginTop": "10px"}),
                    html.Div(f"App version: {get_app_version()}", style={"fontSize": "12px", "color": "#666"}),
                    # hidden polling interval
                    dcc.Interval(id="progress-poller", interval=2000, disabled=True),
                    # stores for some of the callback outputs
                    dcc.Store(id="upload-ready"),
                    dcc.Store(id="processing-started"),
                    dcc.Store(id="selected-track"),
                    # store matched segments and nodes
                    dcc.Store(id="geojson-store-full", data={}),
                    # store filtered & aggregated matched segments and nodes
                    dcc.Store(id="geojson-store-filtered", data={})
                ],
                width=3
            ),

            # Right panel
            dbc.Col(
                [
                    # KPI row
                    dbc.Row([
                        dbc.Col(dbc.Card(dbc.CardBody([
                            html.H5("No. Matched Nodes"),
                            html.H2(id="kpi-totnodes", children="–"),
                            html.Div(
                                f"out of {len(bike_network_node)}",
                                style={"fontSize": "12px", "color": "#666", "marginTop": "2px"}
                            )
                        ])), width=4),
                        dbc.Col(dbc.Card(dbc.CardBody([
                            html.H5("No. Matched Segments"),
                            html.H2(id="kpi-totsegments", children="–"),
                            html.Div(
                                f"out of {len(bike_network_seg)}",
                                style={"fontSize": "12px", "color": "#666", "marginTop": "2px"}
                            )
                        ])), width=4),
                        dbc.Col(dbc.Card(dbc.CardBody([
                            html.H5("Total Matched Segment Length (km)"),
                            html.H2(id="kpi-totlength", children="–"),
                            html.Div(
                                f"out of {bike_network_seg['length_km'].sum():.0f} km",
                                style={"fontSize": "12px", "color": "#666", "marginTop": "2px"}
                            )
                        ])), width=4),
                    ], className="mb-3"),
                    # Controls row
                    dbc.Row([
                        dbc.Col(
                            dbc.Button("Reset Map", id="reset-map-btn", color="secondary", style={"marginLeft": "20px"}),
                            width="auto",
                            style={"display": "flex", "alignItems": "center"}
                        ),
                        dbc.Col(
                            dcc.Checklist(
                                id="checkbox-show-hover",
                                options=[{"label": "Track Focus", "value": "hover"}],
                                value=[],  # default is unchecked, i.e., hover off
                                inputStyle={"margin-right": "5px"},
                                labelStyle={"display": "inline-block", "margin-right": "10px"},
                            )
                        ),
                        dbc.Col(
                            html.Div([
                                dbc.Label("From", html_for="start-date-picker"),
                                dcc.DatePickerSingle(
                                    id="start-date-picker",
                                    date=date_picker_min_date,
                                    display_format="DD/MM/YYYY",
                                    month_format="MMMM YYYY",
                                    style={"height": "40px", "zIndex": 9999, "position": "relative"}
                                )
                            ]),
                            width="auto",
                            # zIndex and position ensure the calendar popup is on top of the map
                            style={"marginLeft": "20px", "height": "40px", "zIndex": 9999, "position": "relative"}
                        ),
                        dbc.Col(
                            html.Div([
                                dbc.Label("To", html_for="end-date-picker"),
                                dcc.DatePickerSingle(
                                    id="end-date-picker",
                                    date=date_picker_max_date,
                                    display_format="DD/MM/YYYY",
                                    month_format="MMMM YYYY",
                                    style={"height": "40px", "zIndex": 9999, "position": "relative"}
                                )
                            ]),
                            width="3",
                            # zIndex and position ensure the calendar popup is on top of the map
                            style={"marginLeft": "20px", "height": "40px", "zIndex": 9999, "position": "relative"}
                        ),
                        dbc.Col(
                            html.Div([
                                dbc.Label("Node Cluster Radius", html_for="cluster-radius-slider"),
                                dcc.Slider(
                                    id="cluster-radius-slider",
                                    min=20,
                                    max=300,
                                    step=10,
                                    value=100,
                                    marks={i: str(i) for i in range(20, 301, 50)},
                                    tooltip={"always_visible": True}
                                )
                            ]),
                            width="3"
                        )
                    ], className="mb-2", align="center"),
                    # Map
                    dl.Map(
                        center=initial_center, 
                        zoom=initial_zoom,
                        style={"width": "100%", "height": "500px"},
                        children=[
                            # https://www.dash-leaflet.com/components/controls/layers_control (v1.1.2)
                            dl.LayersControl(
                                [
                                    dl.BaseLayer(
                                        dl.TileLayer(
                                            url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
                                            attribution='&copy; OSM &copy; <a href="https://carto.com/">CARTO</a>'
                                        ),
                                        name="Carto Light",
                                        checked=True
                                    ),
                                    dl.BaseLayer(
                                        dl.TileLayer(
                                            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
                                            attribution='&copy; OSM &copy; CARTO'
                                        ),
                                        name="Carto Voyager Lite",
                                        checked=False
                                    ),
                                ]
                                + [
                                    dl.Overlay(
                                        # Preloaded network layer (initially hidden)
                                        dl.GeoJSON(
                                            data=geojson_network,
                                            id='geojson-network',
                                            options=dict(style=dict(color=color_network, weight=1, opacity=0.6))
                                        ), 
                                        name="Bike Node Network", 
                                        checked=False,
                                    ),
                                    dl.Overlay(
                                        dl.GeoJSON(
                                            id='layer-gpx', 
                                            style=ns("gpxStyle"),
                                            options=dict(onEachFeature=ns("gpxBindTooltip")),
                                            # initialize hideout
                                            hideout=dict(
                                                selected_id=None,
                                                selected_key=SELECTED_KEY,
                                                selected_color=color_gpx_selected
                                            )
                                        ),
                                        name="GPX Tracks",
                                        checked=False,
                                    )
                                ],
                                id="layers-control",
                                # show all available layers without collapsing
                                collapsed=False,
                                # sort layers by name rather than load order
                                sortLayers=True
                            ),
                            # Matched segments & nodes layers (drawn on top of network)
                            dl.GeoJSON(
                                id="layer-segments",
                                style=ns("segmentStyle"),
                                hideout=dict(weight_classes=weight_classes, weights=weights, color=color_segment),
                            ),
                            dl.GeoJSON(
                                id="layer-nodes",
                                cluster=True,
                                zoomToBoundsOnClick=True,
                                pointToLayer=ns("pointToLayer"),
                            ),
                            # Highlighted segments
                            dl.LayerGroup(id="layer-selected-segments"),
                            # Highlighted segments from nodes
                            dl.LayerGroup(id="layer-selected-nodes")           
                        ],
                        id="map"
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.H4("Segment Statistics"),
                                    html.P(
                                        "Select one or more segments in the table to highlight them on the map (in red).",
                                        style={"fontStyle": "italic", "color": "#555", "marginTop": "5px"}
                                    ),
                                    html.Button("Unselect All", id="unselect-all-btn-seg", style={"display": "none"}),
                                    dash_table.DataTable(
                                        id="table-segments-agg",
                                        columns=[],
                                        data=[],
                                        page_size=25,
                                        row_selectable="multi", # <-- enable row selection
                                        style_table={
                                            'maxHeight': '400px',
                                            'overflowY': 'auto',
                                            'overflowX': 'auto',
                                            'border': 'thin lightgrey solid'
                                        },
                                        style_header={
                                            'backgroundColor': color_segment,
                                            'fontWeight': 'bold',
                                            'color': 'white',
                                            'textAlign': 'center',
                                            'fontFamily': 'Aptos, sans-serif',
                                        },
                                        style_cell={
                                            'textAlign': 'left',
                                            'padding': '5px',
                                            'minWidth': '80px',
                                            'width': '150px',
                                            'maxWidth': '200px',
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'fontFamily': 'Aptos, sans-serif',
                                        },
                                        style_data={
                                            'backgroundColor': 'white',
                                            'color': 'black'
                                        },
                                        fixed_rows={'headers': True},
                                        sort_action='native'
                                    )
                                ],
                                width=6,
                                style={"paddingRight": "10px"}  # add space to the right
                            ),
                            dbc.Col(
                                [
                                    html.H4("Node Statistics"),
                                    html.P(
                                        "Select one or more nodes in the table to highlight their segments on the map (in purple).",
                                        style={"fontStyle": "italic", "color": "#555", "marginTop": "5px"}
                                    ),
                                    html.Button("Unselect All", id="unselect-all-btn-nodes", style={"display": "none"}),
                                    dash_table.DataTable(
                                        id="table-nodes-agg",
                                        columns=[],
                                        data=[],
                                        page_size=25,
                                        row_selectable="multi", # <-- enable row selection
                                        style_table={
                                            'maxHeight': '400px',
                                            'overflowY': 'auto',
                                            'overflowX': 'auto',
                                            'border': 'thin lightgrey solid'
                                        },
                                        style_header={
                                            'backgroundColor': '#0074D9',
                                            'fontWeight': 'bold',
                                            'color': 'white',
                                            'textAlign': 'center',
                                            'fontFamily': 'Aptos, sans-serif',
                                        },
                                        style_cell={
                                            'textAlign': 'left',
                                            'padding': '5px',
                                            'minWidth': '80px',
                                            'width': '150px',
                                            'maxWidth': '200px',
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'fontFamily': 'Aptos, sans-serif',
                                        },
                                        style_data={
                                            'backgroundColor': 'white',
                                            'color': 'black'
                                        },
                                        fixed_rows={'headers': True},
                                        sort_action='native'
                                    )
                                ],
                                width=6,
                                style={"paddingLeft": "10px"}   # add space to the left
                            )
                        ],
                        className="mt-4"
                    )
                ],
                width=9
            )
        ])
    ],
    fluid=True
)

# ---------- Callbacks ----------
# initialize module-level background processing thread before callback runs
_processing_thread = None

@app.callback(
    Output("upload-ready", "data"),
    Input("upload-zip", "contents"),
    State("upload-zip", "filename"),
)
def save_uploaded_file(contents, filename):
    if not contents or not filename:
        # no file available yet
        return False

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # decode base64 and save to disk
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    saved_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(saved_path, "wb") as f:
        f.write(decoded)

    # signal that the file was fully saved
    return True

@app.callback(
    Output("processing-started", "data"),
    Input("btn-process", "n_clicks"),
    State("upload-zip", "filename"),
    State("upload-ready", "data"),
    prevent_initial_call=True
)
def start_processing(_, filename, upload_ready):
    # guard clause: proceed only if the file has been fully saved to disk
    if not filename or not upload_ready:
        raise PreventUpdate

    # initialize progress data
    progress_state["pct"] = 0
    progress_state["btn-disabled"] = True
    progress_state["current-task"] = f"Preparing to process {filename}"
    progress_state["previous-task"] = ""
    progress_state["show-dots"] = True
    progress_state["dot-count"] = 0

    zip_file_path = os.path.join(UPLOAD_FOLDER, filename)

    def worker():
        progress_state["running"] = True
        all_segments, all_nodes, all_gpx = process_gpx_zip(zip_file_path, bike_network_seg, bike_network_node)

        all_segments = all_segments.to_crs(epsg=4326) if not all_segments.empty else gpd.GeoDataFrame()
        all_nodes = all_nodes.to_crs(epsg=4326) if not all_nodes.empty else gpd.GeoDataFrame()
        all_gpx = all_gpx.to_crs(epsg=4326) if not all_gpx.empty else gpd.GeoDataFrame()

        segments_file_path = os.path.join(STATIC_FOLDER, "all_matched_segments_wgs84.geojson")
        nodes_file_path = os.path.join(STATIC_FOLDER, "all_matched_nodes_wgs84.geojson")
        gpx_file_path = os.path.join(STATIC_FOLDER, "all_gpx_wgs84.geojson")
        all_segments.to_file(segments_file_path, driver="GeoJSON")
        all_nodes.to_file(nodes_file_path, driver="GeoJSON")
        all_gpx.to_file(gpx_file_path, driver="GeoJSON")

        zip_name = create_result_zip(segments_file_path, nodes_file_path, gpx_file_path)

        # Only update store when processing is done
        progress_state["store_data"] = {
            "segments": all_segments.__geo_interface__,
            "nodes": all_nodes.__geo_interface__,
            "gpx": all_gpx.__geo_interface__,
            # must be relative to app root here for Dash download link
            "download_href": os.path.join("static", zip_name)
        }
        progress_state["pct"] = 100
        progress_state["btn-disabled"] = False
        progress_state["current-task"] = f"Finished processing {filename}"
        # disable polling
        progress_state["running"] = False

    # assign to the module-level variable, not a new local variable
    global _processing_thread
    _processing_thread = threading.Thread(target=worker)
    _processing_thread.start()

    # no data returned but store write action will trigger update_progress
    return True

@app.callback(
    Output("progress", "value"),
    Output("progress", "label"),
    Output("progress-poller", "disabled"),
    Output("processing-status", "children"),
    Output("btn-process", "disabled"),
    Output("btn-download", "disabled"),
    Output("btn-download", "href"),
    Output("btn-download", "style"),
    Output("geojson-store-full", "data"),
    Output("upload-zip", "disabled"),
    Input("progress-poller", "n_intervals"), # initially None
    Input("processing-started", "data"), # will (re)activate the poller
    prevent_initial_call=True
)
def update_progress(*_):
    # reset or increment dots
    current_task = progress_state.get("current-task", "")
    prev_task = progress_state.get("previous-task", None)
    if current_task != prev_task:
        progress_state["dot-count"] = 0
    else:
        progress_state["dot-count"] = (progress_state["dot-count"] + 1) % 4
    progress_state["previous-task"] = current_task
    dots = "." * progress_state["dot-count"] if progress_state.get("show-dots") else ""

    current_task = progress_state.get("current-task", "") + dots
    btn_disabled = progress_state.get("btn-disabled", False)
    # disable poller once the background processing thread reports finished
    poller_disabled = not progress_state.get("running", True)
    pct = progress_state.get("pct", 0)
    label = f"{pct}%" if pct >= 5 else ""
    href = progress_state.get("store_data", {}).get("download_href")
    style = {"width": "40%", "display": "block" if pct >= 100 else "none"}

    # Only update store when ready
    store_data = progress_state.get("store_data") if pct >= 100 else no_update

    outputs = (pct, label, poller_disabled, current_task,
           btn_disabled, btn_disabled, href, style, store_data, btn_disabled)

    return outputs

@app.callback(
    Output("kpi-totsegments", "children"),
    Output("kpi-totnodes", "children"),
    Output("kpi-totlength", "children"),
    Output("geojson-store-filtered", "data"),
    Input("geojson-store-full", "data"),
    Input("start-date-picker", "date"),
    Input("end-date-picker", "date"),
)
def filter_data(store, start_date, end_date):
    """Filter bike segments and nodes by date and compute KPIs."""
    
    if not store or not store.get("segments", {}).get("features"):
        return None, None, None, {}

    gdf_segments = gpd.GeoDataFrame.from_features(store["segments"]["features"])
    gdf_nodes = gpd.GeoDataFrame.from_features(store["nodes"]["features"])
    gdf_gpx = gpd.GeoDataFrame.from_features(store["gpx"]["features"])

    gdf_segments["track_date"] = pd.to_datetime(gdf_segments["track_date"]).dt.date
    gdf_nodes["track_date"] = pd.to_datetime(gdf_nodes["track_date"]).dt.date
    gdf_gpx["track_date"] = pd.to_datetime(gdf_gpx["track_date"]).dt.date

    try:
        start = pd.to_datetime(start_date).date() if start_date else gdf_segments["track_date"].min()
        end = pd.to_datetime(end_date).date() if end_date else gdf_segments["track_date"].max()
    except Exception:
        return None, None, None, {}

    seg_mask = (gdf_segments["track_date"] >= start) & (gdf_segments["track_date"] <= end)
    node_mask = (gdf_nodes["track_date"] >= start) & (gdf_nodes["track_date"] <= end)
    gpx_mask = (gdf_gpx["track_date"] >= start) & (gdf_gpx["track_date"] <= end)

    gdf_segments_filtered = gdf_segments.loc[seg_mask].copy()
    gdf_nodes_filtered = gdf_nodes.loc[node_mask].copy()
    gdf_gpx_filtered = gdf_gpx.loc[gpx_mask].copy()

    gdf_segments_filtered["track_date"] = pd.to_datetime(gdf_segments_filtered["track_date"])
    gdf_nodes_filtered["track_date"] = pd.to_datetime(gdf_nodes_filtered["track_date"])
    gdf_gpx_filtered["track_date"] = pd.to_datetime(gdf_gpx_filtered["track_date"])

    # Helper function for building tooltip
    def build_tooltip(label_prefix, label_value, kpi_dict):
        # First line: prefix in light grey, value in black and larger font
        tooltip_lines = [
            f'<span style="color: #999; font-size: 14px;">{label_prefix}</span>'
            f'<span style="color: #000; font-size: 16px; font-weight: bold;">{label_value}</span>'
            '<br>'  # simple line break for spacing
        ]
        
        # KPI lines in smaller font
        for kpi_name, kpi_value in kpi_dict.items():
            tooltip_lines.append(
                f'<span style="color: #999; font-size: 11px;">{kpi_name}: </span>'
                f'<b style="color: #000; font-size: 11px;">{kpi_value}</b>'
            )
        return "<br>".join(tooltip_lines)

    # -- Aggregate segments --
    # Use dropna=False to keep groups with missing keys e.g. missing osm_id_from/to
    agg_seg = gdf_segments_filtered.groupby((["ref", "osm_id", "osm_id_from", "osm_id_to"]), dropna=False).agg(
        length_km=("length_km", "max"),
        count_track=("track_uid", "nunique"),
        max_overlap_percentage=("overlap_percentage", "max"),
        first_date=("track_date", "min"),
        last_date=("track_date", "max"),
        # preserve geometry
        geometry=("geometry", "first")
    ).reset_index()

    agg_seg = gpd.GeoDataFrame(agg_seg, geometry="geometry", crs=gdf_segments_filtered.crs)
    # Apply formatting and sort result
    agg_seg["length_km"] = agg_seg["length_km"].round(2)
    agg_seg["max_overlap_percentage"] = agg_seg["max_overlap_percentage"].round(2)
    agg_seg["first_date"] = agg_seg["first_date"].dt.strftime("%Y-%m-%d")
    agg_seg["last_date"] = agg_seg["last_date"].dt.strftime("%Y-%m-%d")
    agg_seg = agg_seg.sort_values("count_track", ascending=False)

    # Add tooltip
    agg_seg["tooltip"] = agg_seg.apply(
        lambda row: build_tooltip(
            "Segment ",
            row["ref"],
            {
                "Visits (Tracks)": row["count_track"],
                "First visit": row["first_date"],
                "Last visit": row["last_date"],
                "Length": f'{row["length_km"]:.1f} km',
                "Best match (%)": f'{100*row["max_overlap_percentage"]:.0f}%'
            }
        ),
        axis=1
    )

    # -- Aggregate nodes --
    # Use dropna=False to keep groups with missing keys e.g. missing osm_id_from/to
    agg_nodes = gdf_nodes_filtered.groupby(["rcn_ref", "osm_id"], dropna=False).agg(
        count_track=("track_date", "nunique"),
        first_date=("track_date", "min"),
        last_date=("track_date", "max"),
        # preserve geometry
        geometry=("geometry", "first")
    ).reset_index()
    agg_nodes = gpd.GeoDataFrame(agg_nodes, geometry="geometry", crs=gdf_nodes_filtered.crs)

    # Apply formatting and sort result
    agg_nodes["first_date"] = agg_nodes["first_date"].dt.strftime("%Y-%m-%d")
    agg_nodes["last_date"] = agg_nodes["last_date"].dt.strftime("%Y-%m-%d")
    agg_nodes = agg_nodes.sort_values("count_track", ascending=False)

    # Add tooltip
    agg_nodes["tooltip"] = agg_nodes.apply(
        lambda row: build_tooltip(
            "Node ",
            row["rcn_ref"],
            {
                "Visits (GPX)": row["count_track"],
                "First visit": row["first_date"],
                "Last visit": row["last_date"],
            }
        ),
        axis=1
    )

    # Calculate KPIs
    total_segments = len(agg_seg)
    total_nodes = len(agg_nodes)
    total_length = round(agg_seg["length_km"].sum(), 2)

    return (
        total_segments,
        total_nodes,
        total_length,
        {
            "segments": agg_seg.__geo_interface__,
            "nodes": agg_nodes.__geo_interface__,
            "gpx": gdf_gpx_filtered.__geo_interface__
        }
    )

@app.callback(
    Output("layer-segments", "data"),
    Output("layer-gpx", "data"),
    Input("geojson-store-filtered", "data"),
)
def update_lines(filtered_data):
    """Render filtered bike segments and GPX tracks on the map."""
    if not filtered_data:
        return None, None

    # initialize track layer
    res_gpx = filtered_data["gpx"]

    # add tooltips per unique track
    global _tooltips_html
    _tooltips_html = {
        feature["properties"]["track_uid"]: make_gpx_tooltip(feature)
        for feature in res_gpx["features"]
    }

    return  filtered_data["segments"], res_gpx

@app.callback(
    Output("layer-nodes", "data"),
    Output("layer-nodes", "superClusterOptions"),
    Input("geojson-store-filtered", "data"),
    Input("cluster-radius-slider", "value")
)
def update_node_layer(filtered_data, cluster_radius):
    """Render bike nodes"""
    cluster_options = {"radius": cluster_radius}

    if not filtered_data:
        return None, cluster_options
    
    return filtered_data["nodes"], cluster_options

@app.callback(
    Output("table-segments-agg", "data"),
    Output("table-segments-agg", "columns"),
    Output("table-nodes-agg", "data"),
    Output("table-nodes-agg", "columns"),
    Output("unselect-all-btn-seg", "style"),
    Output("unselect-all-btn-nodes", "style"),
    Input("geojson-store-filtered", "data"),
)
def update_tables(filtered_data):
    """Aggregate segment and node data for display in Dash tables."""
    
    if not filtered_data:
        return [], [], [], [], {"display": "none"}, {"display": "none"}
    
    agg_seg = gpd.GeoDataFrame.from_features(filtered_data["segments"]["features"])
    agg_nodes = gpd.GeoDataFrame.from_features(filtered_data["nodes"]["features"])

    # check if all data are filtered out
    if agg_seg.empty or agg_nodes.empty:
        return [], [], [], [], {"display": "none"}, {"display": "none"}

    # remove and rename columns
    agg_seg = agg_seg.drop(columns=["osm_id_from", "osm_id_to", "tooltip", "geometry"])
    agg_seg = agg_seg.rename(columns={"ref": "segment"})
    agg_nodes = agg_nodes.drop(columns=["tooltip", "geometry"])
    agg_nodes = agg_nodes.rename(columns={"rcn_ref": "node"})

    seg_columns = [{"name": c, "id": c} for c in agg_seg.columns]
    seg_data = agg_seg.to_dict("records")
    node_columns = [{"name": c, "id": c} for c in agg_nodes.columns]
    node_data = agg_nodes.to_dict("records")

    outputs = seg_data, seg_columns, node_data, node_columns, \
        {"display": "inline-block"}, {"display": "inline-block"}

    return outputs

@app.callback(
    Output("table-segments-agg", "selected_rows"),
    Input("unselect-all-btn-seg", "n_clicks"),
    # also clear selection when user modifies filters
    Input("table-segments-agg", "data"),
)
def unselect_all_seg(*_):
    return []

@app.callback(
    Output("table-nodes-agg", "selected_rows"),
    Input("unselect-all-btn-nodes", "n_clicks"),
    # also clear selection when user modifies filters
    Input("table-segments-agg", "data"),
)
def unselect_all_nodes(*_):
    return []

@app.callback(
    Output("browse-info", "children"),
    Input("upload-zip", "contents"), # input required (also in def)
    State('upload-zip', 'filename')
)
def show_info(_, f):
    if f is None:
        return "No file selected"
    return f"Selected file: {f}"

@app.callback(
    Output("map", "center"),
    Output("map", "zoom"),
    Output("map", "key"),  # Force the map to fully re-render
    Input("reset-map-btn", "n_clicks"),
    prevent_initial_call=True
)
def reset_map(n_clicks):
    """Recenter the map to its initial center and zoom level.

    Args:
        n_clicks (int): Number of times the recenter button was clicked.

    Returns:
        list, int, str: Default center [lat, lon], default zoom, and updated key.
    """
    return initial_center, initial_zoom, f"map-{n_clicks}"

@app.callback(
    Output("layer-selected-segments", "children"),
    Input("table-segments-agg", "selected_rows"),
    State("table-segments-agg", "data"),
    State("geojson-store-filtered", "data"),
)
def highlight_segments(selected_rows, table_data, filtered_data):
    """Highlight selected segments on the map."""
    if not selected_rows or not filtered_data \
        or "segments" not in filtered_data or not table_data:
        return None

    # Get all selected 'ref' values
    ref_values = [table_data[i]["osm_id"] for i in selected_rows]

    # Convert filtered segments to GeoDataFrame
    gdf_seg = gpd.GeoDataFrame.from_features(filtered_data["segments"]["features"])

    # Filter for the selected segments
    if not gdf_seg.empty:
        gdf_highlight = gdf_seg[gdf_seg["osm_id"].isin(ref_values)]
    else:
        gdf_highlight = gpd.GeoDataFrame()

    # Check if filtered DataFrame is empty
    if gdf_highlight.empty:
        return None

    # Return GeoJSON layer for all selected segments
    return dl.GeoJSON(
        data=gdf_highlight.__geo_interface__,
        options=dict(style=dict(color=color_highlight_segment, weight=8)),
        zoomToBounds=True,
    )

@app.callback(
    Output("layer-selected-nodes", "children"),
    Input("table-nodes-agg", "selected_rows"),
    State("table-nodes-agg", "data"),
    State("geojson-store-filtered", "data"),
)
def highlight_segments_from_nodes(selected_rows, table_data, filtered_data):
    """Highlight segments connected to selected nodes on the map."""
    if not selected_rows or not filtered_data \
        or "segments" not in filtered_data or not table_data:
        return None

    # Get selected node IDs or refs
    selected_nodes = [table_data[i]["osm_id"] for i in selected_rows]

    # Convert filtered segments to GeoDataFrame
    gdf_seg = gpd.GeoDataFrame.from_features(filtered_data["segments"]["features"])

    # Filter segments where node_from or node_to is in selected_nodes
    if not gdf_seg.empty:
        mask = gdf_seg["osm_id_from"].isin(selected_nodes) | gdf_seg["osm_id_to"].isin(selected_nodes)
        gdf_highlight = gdf_seg[mask]
    else:
        gdf_highlight = gpd.GeoDataFrame()

    # Check if filtered DataFrame is empty
    if gdf_highlight.empty:
        return None

    # Return GeoJSON layer with blue highlight
    return dl.GeoJSON(
        data=gdf_highlight.__geo_interface__,
        options=dict(style=dict(color=color_highlight_node, weight=8)),
        zoomToBounds=True,
    )

@app.callback(
    Output("layer-gpx", "hoverStyle"),
    Output("layer-gpx", "zoomToBoundsOnClick"),
    Input("checkbox-show-hover", "value"),
    Input("layer-gpx", "data"),
)
def toggle_track_focus(hover_enabled, gpx_geojson):
    if not gpx_geojson:
        # no track layer available yet -> do nothing
        raise PreventUpdate
    
    if "hover" in hover_enabled: 
        # activate hoverstyle function
        hover = ns("gpxHoverStyle")
        return hover, True
    
    return None, False

@app.callback(
    Output("selected-track", "data"),
    Input("layer-gpx", "clickData"),
    Input("map", "clickData"),
    Input("checkbox-show-hover", "value")
)
def update_selected_track(layer_click, map_click, checkbox):
    if checkbox == []:
        # Focus Track not active
        return None

    triggers = [t["prop_id"] for t in ctx.triggered]

    if layer_click:
        # get (previously) selected feature ID
        props = layer_click.get("properties", {})
        if props: selected_id = props.get(SELECTED_KEY)
    else:
        # no feature clicked yet on the map
        return None

    if any("layer" in item for item in triggers):
        # a new feature has been clicked on the map
        # (triggers: ['layer-gpx.clickData', 'map.clickData'])
        return selected_id
    elif any("map" in item for item in triggers):
        # user either clicked on the same feature or outside the layer
        # (trigger: only ['map.clickData'] )
        if KEEP_SELECTION_ACTIVE:
            # keep selection until new feature is clicked or Track Focus is deactivated
            return selected_id
        # check if user clicked close enough to the same feature to keep it active
        elif is_point_near_geometry(map_click["latlng"], layer_click["geometry"]):
            return selected_id
    
    # reset selection for all other conditions
    return None

@app.callback(
    Output("layer-gpx", "hideout"),
    Input("selected-track", "data"),
    Input("checkbox-show-hover", "value"),
    Input("layers-control", "baseLayer"),
    State("layer-gpx", "hideout"),
    Input("layer-gpx", "data"),
)
def update_gpx_layer_hideout(selected_id, checkbox_value, base_layer, current_hideout, _):
    # update state container for the layer triggered to control styling
    hideout = dict(current_hideout)
    hideout["selected_id"] = selected_id
    hideout["track_focus"] = (checkbox_value != [])
    hideout["base_color"] = color_gpx_1 if base_layer == "Carto Light" else color_gpx_2
    hideout["tooltips"] = _tooltips_html
    hideout["tooltip_opacity"] = 0.0 if checkbox_value == [] else 0.9

    return hideout

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)
