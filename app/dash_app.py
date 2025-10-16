from core.common import *
from app.constants import *
from app.geoprocessing import *
from app.utils import *
import json
import base64
import threading
import psutil
from dash import no_update, Dash, html, dcc, Output, Input, State, dash_table
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash.exceptions import PreventUpdate
from dash import callback_context as ctx
import time

# --- initialize folders ---
os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- module-level state ---
_tooltips_html = {}
_processing_thread = None

# --- load data ---
if os.getenv("RENDER") == "true":
    # use 'lite' version of the app containing only the Belgian network
    folder = OUTPUT_FOLDER_LITE
    app_header = "Belgian Bike Node Network Matcher"
    app_descr = "Upload a zip file with your GPX rides to see how they align with Belgium’s bike node network."
else:
    # use full version of the app using the full network
    folder = OUTPUT_FOLDER_FULL
    app_header = "Bike Node Network Matcher"
    app_descr = "Upload a ZIP file with your GPX rides to see how they align with the Belgian and Dutch bike node networks.",

seg_path_parquet =  Path(folder) / MULTILINE_PROJECTED_PARQUET_NAME
node_path_parquet = Path(folder) / POINT_PROJECTED_PARQUET_NAME
seg_path_geojson = Path(folder) / MULTILINE_GEOJSON_NAME

bike_network_seg = gpd.read_parquet(seg_path_parquet)
bike_network_node = gpd.read_parquet(node_path_parquet)
with open(seg_path_geojson , "r") as f:
   geojson_network = json.load(f)

# --- initialize app ---
# Themes: see https://www.dash-bootstrap-components.com/docs/themes/explorer/
app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR])
server = app.server

# Check memory usage before processing
process = psutil.Process(os.getpid())
print(f"Memory usage after initializing application: {process.memory_info().rss / 1024**2:.2f} MB")

# ---------- Layout ----------
app.layout = dbc.Container(
    [
        dbc.Row([
            # Left panel
            dbc.Col(
                [
                    # =======================
                    # FILE SELECTION SECTION
                    # =======================
                    html.H5("Select GPX Data", className="mb-3", style={"fontWeight": "600"}),

                    dbc.Tabs(
                        id="file-tabs",
                        active_tab="tab-sample",  # default tab
                        children=[
                            dbc.Tab(
                                label="Use Sample Dataset",
                                tab_id="tab-sample", # id within tabs container
                                id="tab-sample-content", # Dash component ID
                                children=[
                                    html.Div(
                                        [
                                            dbc.Label("Select a sample ZIP file"),
                                            dcc.Dropdown(
                                                id="sample-file-dropdown",
                                                options=[
                                                    {"label": f.name, "value": str(f)}
                                                    for f in Path("data/sample").glob("*.zip")
                                                ],
                                                placeholder="Choose sample dataset...",
                                                style={"width": "100%", "marginBottom": "33px"},
                                            ),
                                        ],
                                        className="p-2",
                                    ),
                                ],
                            ),
                            dbc.Tab(
                                label="Upload Your Own ZIP",
                                tab_id="tab-upload", # id within tabs container
                                id="tab-upload-content", # Dash component ID
                                children=[
                                    html.Div(
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
                                                    "marginBottom": "10px",
                                                },
                                            ),
                                            html.Div(
                                                id="browse-info",
                                                style={"fontSize": "14px", "color": COLOR_PROCESSING, "marginBottom": "10px"},
                                            ),
                                        ],
                                        className="p-2",
                                    ),
                                ],
                            ),
                        ],
                        style={"marginBottom": "5px"},
                    ),

                    dbc.Button(
                        "Process ZIP", 
                        id="btn-process", 
                        color="primary",
                        className="mb-3"
                    ),

                    dbc.Progress(
                        id="progress",
                        value=0,
                        striped=True,
                        animated=True,
                        className="mb-3",
                    ),

                    html.Div(
                        id="processing-status",
                        style={
                            "padding": "2px 8px",
                            "fontFamily": "monospace",
                            "color": COLOR_PROCESSING,
                            "fontSize": "0.85rem",
                            "minHeight": "2em",  # ensures one-line height
                        },
                        className="mb-1",
                    ),

                    dbc.Button(
                        "Download Results",
                        id="btn-download",
                        color="success",
                        className="mt-1",
                        external_link=True,
                        style={"visibility": "hidden"}  # keeps layout space
                    ),

                    html.Hr(className="my-4", style={"borderTop": "2px solid #ccc"}),

                    # =======================
                    # DASHBOARD CONTROLS
                    # =======================
                    html.H5("Dashboard Controls", className="mb-3", style={"fontWeight": "600"}),

                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div([
                                    dbc.Button(
                                        "Reset Map",
                                        id="reset-map-btn",
                                        color="secondary",
                                        size="sm",
                                        className="me-2"
                                    ),
                                    dbc.Tooltip(
                                        "Click to reset map view, base layer, and overlays",
                                        target="reset-map-btn",
                                        placement="top",
                                        delay=TOOLTIP_DELAY,
                                    )
                                ]),
                                width="auto",
                            ),
                            dbc.Col(
                                html.Div([
                                    dcc.Checklist(
                                        id="checkbox-show-hover",
                                        options=[{"label": "Track Focus", "value": "hover"}],
                                        value=[],  # default unchecked
                                        inputStyle={"margin-right": "5px"},
                                        labelStyle={
                                            "display": "inline-block",
                                            "margin-right": "10px",
                                            "font-size": "0.9rem"
                                        },
                                    ),
                                    dbc.Tooltip(
                                        "Highlight and zoom on hovered GPX tracks",
                                        target="checkbox-show-hover",
                                        placement="top",
                                        delay=TOOLTIP_DELAY,
                                    ),
                                ]),
                                width="auto",
                                className="d-flex align-items-center",
                            ),
                        ],
                        justify="start",
                        className="mb-4",
                        style={"marginLeft": "0px"},
                    ),

                    html.Div(
                        [
                            dbc.Label("Select Years"),
                            dcc.RangeSlider(
                                min=SLIDER_MIN_YEAR,
                                max=SLIDER_MAX_YEAR,
                                step=1,
                                id="year-slider",
                                marks={
                                    year: str(year)
                                    for year in range(SLIDER_MIN_YEAR, SLIDER_MAX_YEAR + 1)
                                    if year % 5 == 0
                                },
                                tooltip={"placement": "bottom", "always_visible": True},
                                value=[SLIDER_MIN_YEAR, SLIDER_MAX_YEAR],
                            ),
                            dbc.Tooltip(
                                "Filter tracks by their recording years",
                                target="year-slider",
                                placement="top",
                                delay=TOOLTIP_DELAY,
                            ),
                        ],
                        className="mb-5",
                        style={"marginLeft": "10px"},
                    ),

                    html.Div(
                        [
                            dbc.Label("Node Cluster Radius", html_for="cluster-radius-slider"),
                            dcc.Slider(
                                id="cluster-radius-slider",
                                min=20,
                                max=320,
                                step=10,
                                value=100,
                                marks={i: str(i) for i in range(20, 321, 50)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            ),
                            dbc.Tooltip(
                                "Adjust how closely nearby bike nodes are grouped into clusters",
                                target="cluster-radius-slider",
                                placement="top",
                                delay=TOOLTIP_DELAY,
                            ),
                        ], 
                        className="mb-5",
                        style={"marginLeft": "10px"},
                    ),

                    html.Hr(className="my-4", style={"borderTop": "2px solid #ccc"}),

                    # =======================
                    # META INFO
                    # =======================
                    html.Div([
                        html.Div([
                            f"Data version: {get_data_version()} (source: ",
                            html.A("Geofabrik", href=GEOFABRIK_URL, target="_blank"),
                            ")",
                        ]),
                        html.Div(f"App version: {get_app_version()}"),
                        html.Div([
                            "Project page: ",
                            html.A("GitHub", href=REPO_URL, target="_blank"),
                        ]),
                    ], style={"fontSize": "12px", "color": "#666", "marginTop": "10px", "lineHeight": "1.4"}),

                    # =======================
                    # HIDDEN ELEMENTS
                    # =======================
                    # hidden polling interval
                    dcc.Interval(id="progress-poller", interval=2000, disabled=True),
                    # stores for some of the callback outputs
                    dcc.Store(id="file-ready"),
                    dcc.Store(id="processing-started"),
                    dcc.Store(id="selected-track"),
                    # store matched segments and nodes
                    dcc.Store(id="geojson-store-full", data={}),
                    # store filtered & aggregated matched segments and nodes
                    dcc.Store(id="geojson-store-filtered", data={}),
                    # store selected sample file
                    dcc.Store(id="sample-file-store", data={}),
                ],
                # left panel width: around 2.5/12 (22%)
                width = "auto",
                className="p-3 rounded",
                style={"flex": "0 0 22%", "backgroundColor": "#f0f0f0"},
            ),
            # Right panel
            dbc.Col(
                [
                    # Header row
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Img(
                                        src=ICON_REPO,
                                        height="110px",
                                        style={"marginRight": "15px"}
                                    ),
                                    html.Div([
                                        html.H1(app_header, className="my-2 display-4 mb-0"),
                                        html.P(app_descr, className="text-muted mb-4"),
                                    ], style={"textAlign": "center"}
                                    ),
                                ], style={
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center"
                                }),
                            ])
                        ], 
                        className="align-items-center justify-content-center g-0",
                        style={
                            "backgroundColor": "#E6F7FF",
                            "marginBottom": "10px",     # spacing below header
                            "borderRadius": "8px"
                        },
                        ),
                    ]),

                    # KPI row
                    dbc.Row([
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("No. Matched Nodes", className="text-center mb-2"),

                                    # KPI row: icon + number
                                    html.Div([
                                        html.Img(
                                            src=ICON_NODE,
                                            width="36",
                                            height="36",
                                            style={"marginRight": "8px"}
                                        ),
                                        html.H2(id="kpi-totnodes", children="–", className="mb-0"),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center"
                                    }),

                                    html.Div(
                                        f"out of {len(bike_network_node)}",
                                        className="text-center text-muted",
                                        style={"fontSize": "12px", "marginTop": "4px"}
                                    ),
                                ])
                            ),
                            width=3
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("No. Matched Segments", className="text-center mb-2"),

                                    # KPI row: icon + number
                                    html.Div([
                                        html.Img(
                                            src=ICON_SEGMENT,
                                            width="36",
                                            height="36",
                                            style={"marginRight": "8px"}
                                        ),
                                        html.H2(id="kpi-totsegments", children="–", className="mb-0"),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center"
                                    }),

                                    html.Div(
                                        f"out of {len(bike_network_seg)}",
                                        className="text-center text-muted",
                                        style={"fontSize": "12px", "marginTop": "4px"}
                                    ),
                                ])
                            ),
                            width=3
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("Matched Segment Length", className="text-center mb-2"),

                                    # KPI row: icon + number
                                    html.Div([
                                        html.Img(
                                            src=ICON_LENGTH,
                                            width="36",
                                            height="36",
                                            style={"marginRight": "8px"}
                                        ),
                                        html.H2(id="kpi-totlength", children="–", className="mb-0"),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center"
                                    }),

                                    html.Div(
                                        f"out of {bike_network_seg['length_km'].sum():.0f} km",
                                        className="text-center text-muted",
                                        style={"fontSize": "12px", "marginTop": "4px"}
                                    ),
                                ])
                            ),
                            width=3
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody([
                                    html.H5("No. Matched Tracks", className="text-center mb-2"),

                                    # KPI row: icon + value
                                    html.Div([
                                        html.Img(
                                            src=ICON_MATCH,
                                            width="36",
                                            height="36",
                                            style={"marginRight": "8px"}
                                        ),
                                        html.H2(id="kpi-tottracks", children="–", className="mb-0"),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center"
                                    }),

                                    html.Div(
                                        id="kpi-tottracks-outof",
                                        className="text-center text-muted",
                                        style={"fontSize": "12px", "marginTop": "4px"}
                                    ),
                                ])
                            ),
                            width=3
                        ),
                    ], className="mb-3"),
                    
                    # Map & panels
                    dbc.Row([
                        dbc.Col(
                            # Map
                            dl.Map(
                                center=INITIAL_CENTER, 
                                zoom=INITIAL_ZOOM,
                                style={"width": "100%", "height": "625px"},
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
                                                    options=dict(style=dict(color=COLOR_NETWORK, weight=1, opacity=0.6))
                                                ), 
                                                name="Bike Node Network", 
                                                checked=False,
                                            ),
                                            dl.Overlay(
                                                dl.GeoJSON(
                                                    id='layer-track', 
                                                    style=ns("trackStyle"),
                                                    options=dict(onEachFeature=ns("trackBindTooltip")),
                                                    # initialize hideout
                                                    hideout=dict(
                                                        selected_id=None,
                                                        selected_key=SELECTED_KEY,
                                                        selected_color=COLOR_GPX_SELECTED
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
                                        hideout=dict(weight_classes=WEIGHT_CLASSES_SEGMENT, weights=WEIGHTS_SEGMENT, color=COLOR_SEGMENT),
                                    ),
                                    dl.GeoJSON(
                                        id="layer-nodes",
                                        cluster=True,
                                        zoomToBoundsOnClick=True,
                                        pointToLayer=ns("nodePointToLayer"),
                                    ),
                                    # Highlighted segments
                                    dl.LayerGroup(id="layer-selected-segments"),
                                    # Highlighted segments from nodes
                                    dl.LayerGroup(id="layer-selected-nodes"),
                                    # Add map controls
                                    dl.FullScreenControl(),
                                    dl.ScaleControl(position="bottomleft", imperial=False),
                                ],
                                id="map"
                            ),
                            width=7
                        ),
                        dbc.Col(
                            dbc.Tabs(
                                [
                                    dbc.Tab(
                                        label="Segment Statistics",
                                        tab_id="tab-segments",
                                        children=[
                                            html.P(
                                                id="segment-statistics-descr",
                                                style={"fontStyle": "italic", "color": COLOR_MESSAGE, 
                                                       "marginTop": "5px", "fontSize": "13px"}
                                            ),
                                            html.Button(
                                                "Unselect All", 
                                                id="unselect-all-btn-seg", 
                                                style={"display": "none"}
                                            ),
                                            dash_table.DataTable(
                                                id="table-segments-agg",
                                                columns=[],
                                                data=[],
                                                page_size=10,
                                                row_selectable="multi",
                                                style_table={
                                                    'maxHeight': '450px',
                                                    'overflowY': 'auto',
                                                    'overflowX': 'auto',
                                                    'border': 'thin lightgrey solid'
                                                },
                                                style_header={
                                                    'backgroundColor': COLOR_SEGMENT,
                                                    'fontWeight': 'bold',
                                                    'color': 'white',
                                                    'textAlign': 'center',
                                                    'fontFamily': FONT_MAIN,
                                                },
                                                style_cell={
                                                    "textAlign": "center",
                                                    "padding": "5px",
                                                    "minWidth": "0px",
                                                    "maxWidth": "none",
                                                    "whiteSpace": "normal",
                                                    "fontFamily": FONT_MAIN,
                                                },
                                                # explicitly make some columns wider
                                                style_cell_conditional=[
                                                    {"if": {"column_id": "segment"}, "width": "90px"},
                                                    {"if": {"column_id": "count_track"}, "width": "75px"},
                                                    {"if": {"column_id": "length_km"}, "width": "75px"},
                                                ],
                                                style_data={
                                                    'backgroundColor': 'white',
                                                    'color': 'black',
                                                },
                                                fixed_rows={'headers': True},
                                                sort_action='native'
                                            ),
                                        ],
                                    ),
                                    dbc.Tab(
                                        label="Node Statistics",
                                        tab_id="tab-nodes",
                                        children=[
                                            html.P(
                                                id="node-statistics-descr",
                                                style={"fontStyle": "italic", "color": COLOR_MESSAGE, 
                                                       "marginTop": "5px", "fontSize": "13px"}
                                            ),
                                            html.Button(
                                                "Unselect All", 
                                                id="unselect-all-btn-nodes", 
                                                style={"display": "none"}
                                            ),
                                            dash_table.DataTable(
                                                id="table-nodes-agg",
                                                columns=[],
                                                data=[],
                                                page_size=10,
                                                row_selectable="multi",
                                                style_table={
                                                    'maxHeight': '450px',
                                                    'overflowY': 'auto',
                                                    'overflowX': 'auto',
                                                    'border': 'thin lightgrey solid'
                                                },
                                                style_header={
                                                    'backgroundColor': COLOR_NODE,
                                                    'fontWeight': 'bold',
                                                    'color': 'white',
                                                    'textAlign': 'center',
                                                    'fontFamily': FONT_MAIN,
                                                },
                                                style_cell={
                                                    "textAlign": "center",
                                                    "padding": "5px",
                                                    "minWidth": "0px",
                                                    "maxWidth": "none",
                                                    "whiteSpace": "normal",
                                                    'fontFamily': FONT_MAIN,
                                                },
                                                # explicitly make track count column wider
                                                style_cell_conditional=[
                                                    {"if": {"column_id": "count_track"}, "width": "75px"},
                                                ],
                                                style_data={
                                                    'backgroundColor': 'white',
                                                    'color': 'black'
                                                },
                                                fixed_rows={'headers': True},
                                                sort_action='native'
                                            ),
                                        ],
                                    ),
                                    # Chart
                                    dbc.Tab(
                                        label="Coverage Over Time",
                                        tab_id="tab-chart",
                                        children = [
                                            dbc.Card(
                                                dbc.CardBody([
                                                    dbc.Row([
                                                        dbc.Col([
                                                            dbc.Label("Date Level"),
                                                            dbc.RadioItems(
                                                                id="agg-level",
                                                                options=[
                                                                    {"label": "Year", "value": "Y"},
                                                                    {"label": "Year/Month", "value": "M"},
                                                                ],
                                                                value="Y",
                                                                inline=True,
                                                            )
                                                        ], md=3),

                                                        dbc.Col([
                                                            dbc.Label("Plot Type"),
                                                            dbc.RadioItems(
                                                                id="plot-type",
                                                                options=[
                                                                    {"label": "Cumul", "value": "cumulative"},
                                                                    {"label": "Count", "value": "aggregate"},
                                                                ],
                                                                value="cumulative",
                                                                inline=True,
                                                            ),
                                                        ], md=3),

                                                        dbc.Col([
                                                            dbc.Label("Element Type"),
                                                            dbc.RadioItems(
                                                                id="element-type",
                                                                options=[
                                                                    {"label": "Nodes", "value": "node"},
                                                                    {"label": "Segments", "value": "segment"},
                                                                ],
                                                                value="node",
                                                                inline=True,
                                                            ),
                                                        ], md=3),

                                                        dbc.Col([
                                                            dbc.Label("Filter Mode"),
                                                            dbc.RadioItems(
                                                                id="filter-mode",
                                                                options=[
                                                                    {"label": "All", "value": "progress"},
                                                                    {"label": "New", "value": "discoveries"},
                                                                ],
                                                                value="progress",
                                                                inline=True,
                                                            ),
                                                        ], md=3),

                                                    ], className="gy-2"),
                                                ]),
                                                className="mb-2 shadow-sm",
                                            ),
                                            dcc.Graph(
                                                id="line-chart", 
                                                config={"displayModeBar": False},
                                                style={"height": "425px",},
                                            ),
                                        ]
                                    )
                                ],
                                id="stats-tabs",
                                active_tab="tab-segments",
                            ),
                            width=5,
                        )
                    ])
                ],
                # right panel width: fill up leftover space
                style={"flex": "1"}
            )
        ])
    ],
    fluid=True
)

# ---------- Callbacks ----------
@app.callback(
    Output("file-ready", "data"),
    Output("upload-zip", "filename"),
    Output("sample-file-store", "data"),
    Input("file-tabs", "active_tab"),
    Input("upload-zip", "contents"),
    State("upload-zip", "filename"),
    Input("sample-file-dropdown", "value"),
    State("sample-file-store", "data"),
    prevent_initial_call=True
)
def handle_file_selection(active_tab, upload_contents, upload_filename, sample_path, sample_filename):
    """
    Handle both sample file selection and user uploads based on the active tab.
    Copies or decodes the selected ZIP into UPLOAD_FOLDER and updates readiness
    flags, while preserving the previously selected or uploaded file from the
    inactive tab.
    """
    # sample tab: copy paste sample file if not done already
    if active_tab == "tab-sample":
        if sample_path:
            sample_basename = os.path.basename(sample_path)
            dest_path = os.path.join(UPLOAD_FOLDER, sample_basename)
            if not os.path.exists(dest_path):
                shutil.copy(sample_path, dest_path)
            return True, upload_filename, sample_basename
        else:
            # no sample file selected or selection is cleared
            return upload_filename is not None, upload_filename, None

    # upload tab: upload file if not uploaded yet
    elif active_tab == "tab-upload" and upload_contents and upload_filename:
        dest_path = os.path.join(UPLOAD_FOLDER, upload_filename)
        if not os.path.exists(dest_path):
            _, content_string = upload_contents.split(",")
            decoded = base64.b64decode(content_string)
            with open(dest_path, "wb") as f:
                f.write(decoded)

        return True, upload_filename, sample_filename

    raise PreventUpdate

@app.callback(
    Output("processing-started", "data"),
    Input("btn-process", "n_clicks"),
    State("upload-zip", "filename"),
    State("sample-file-store", "data"),
    State("file-ready", "data"),
    State("file-tabs", "active_tab"),
    prevent_initial_call=True
)
def start_processing(_, upload_filename, sample_filename, file_ready, active_tab):
    """
    Triggered by the 'Process ZIP' button.
    Decides which file (uploaded or sample) to process based on the active tab.
    """
    # guard clause: proceed only if a file has been fully saved to disk
    if not file_ready:
        raise PreventUpdate
    
    # get file name based on active tab
    if active_tab == "tab-upload":
        if not upload_filename:
            raise PreventUpdate
        filename = upload_filename
    elif active_tab == "tab-sample":
        if not sample_filename:
            raise PreventUpdate
        filename = sample_filename

    # initialize progress data
    progress_state["pct"] = 0
    progress_state["current-task"] = f"Preparing to process {filename}"
    progress_state["previous-task"] = ""
    progress_state["show-dots"] = True
    progress_state["dot-count"] = 0

    zip_file_path = os.path.join(UPLOAD_FOLDER, filename)

    def worker():
        progress_state["status"] = "running"
        all_segments, all_nodes, all_gpx, message = \
            process_gpx_zip(zip_file_path, bike_network_seg, bike_network_node)

        # Early exit if any DataFrame is empty (indicating an issue)
        if any(df.empty for df in [all_segments, all_nodes, all_gpx]):
            progress_state["current-task"] = f"Processing failed for {filename}: {message}"
            progress_state["pct"] = 100
            progress_state["status"] = "exited"
            return

        # Reproject all GeoDataFrames to WGS84 (EPSG:4326) for export and mapping
        all_segments = all_segments.to_crs(epsg=4326)
        all_nodes = all_nodes.to_crs(epsg=4326)
        all_gpx = all_gpx.to_crs(epsg=4326)

        segments_file_path = os.path.join(STATIC_FOLDER, "all_matched_segments_wgs84.geojson")
        nodes_file_path = os.path.join(STATIC_FOLDER, "all_matched_nodes_wgs84.geojson")
        gpx_file_path = os.path.join(STATIC_FOLDER, "all_gpx_wgs84.geojson")
        all_segments.to_file(segments_file_path, driver="GeoJSON")
        all_nodes.to_file(nodes_file_path, driver="GeoJSON")
        all_gpx.to_file(gpx_file_path, driver="GeoJSON")

        zip_name = create_result_zip(segments_file_path, nodes_file_path, gpx_file_path)

        # Calculate range for year range slider
        track_date_years = {
            "min": pd.to_datetime(all_gpx["track_date"], 
                                  errors="coerce").dt.year.min(),
            "max": pd.to_datetime(all_gpx["track_date"], 
                                  errors="coerce").dt.year.max(),
        }

        # Store all processed data for the frontend
        progress_state["store_data"] = {
            "segments": all_segments.__geo_interface__,
            "nodes": all_nodes.__geo_interface__,
            "gpx": all_gpx.__geo_interface__,
            # must be relative to app root here for Dash download link
            "download_href": os.path.join("static", zip_name),
            "track_date_years": track_date_years,
        }

        progress_state["pct"] = 100
        progress_state["current-task"] = f"Finished processing {filename}"
        # store timestamp for deactivation of polling
        progress_state["status"] = "finished"
        progress_state["finished_at"] = time.time()   

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
    Output("sample-file-dropdown", "disabled"),
    Output("tab-upload-content", "disabled"),
    Output("tab-sample-content", "disabled"),
    Output("year-slider", "min"),
    Output("year-slider", "max"),
    Output("year-slider", "value"),
    Input("progress-poller", "n_intervals"), # initially None
    Input("processing-started", "data"), # will (re)activate the poller
    State("file-tabs", "active_tab"),
    prevent_initial_call=True
)
def update_progress(*args):
    # Get active tab
    active_tab = args[-1]

    # Animate dots
    current_task = progress_state.get("current-task", "")
    prev_task = progress_state.get("previous-task")
    progress_state["dot-count"] = 0 if current_task != prev_task \
        else (progress_state.get("dot-count", 0) + 1) % 4
    progress_state["previous-task"] = current_task
    dots = "." * progress_state["dot-count"] if progress_state.get("show-dots") else ""
    current_task += dots

    # Base UI state while processing
    pct = progress_state.get("pct", 0)
    label = f"{pct}%" if pct >= 5 else ""
    btn_disabled = True
    href = progress_state.get("store_data", {}).get("download_href")
    style = {"width": "40%", "visibility": "visible" if pct >= 100 else "hidden"}
    finished_at = progress_state.get("finished_at")
    status = progress_state.get("status")
    poller_disabled = False
    store_data, min_year, max_year, slider_val = (no_update,) * 4
    upload_tab_disabled = (active_tab == "tab-sample")
    sample_tab_disabled = not upload_tab_disabled

    # Handle completion
    if status == "exited":
        # Early exit → reset immediately
        pct = 0
        label = ""
        poller_disabled = True
        btn_disabled = False
        upload_tab_disabled = False
        sample_tab_disabled = False
    elif status == "finished":
        # Normal completion
        store_data = progress_state.get("store_data")
        min_year = store_data["track_date_years"]["min"]
        max_year = store_data["track_date_years"]["max"]
        slider_val = [min_year, max_year]
        # Wait 3s before progress bar reset
        if time.time() - finished_at >= 3:
            pct = 0
            label = ""
            poller_disabled = True
            progress_state.pop("finished_at", None)
            btn_disabled = False
            upload_tab_disabled = False
            sample_tab_disabled = False

    return (
        pct,
        label,
        poller_disabled,
        current_task,
        btn_disabled,
        btn_disabled,
        href,
        style,
        store_data,
        btn_disabled,
        btn_disabled,
        upload_tab_disabled,
        sample_tab_disabled,
        min_year,
        max_year,
        slider_val
    )

@app.callback(
    Output("kpi-totsegments", "children"),
    Output("kpi-totnodes", "children"),
    Output("kpi-totlength", "children"),
    Output("kpi-tottracks-outof", "children"),
    Output("kpi-tottracks", "children"),
    Output("geojson-store-filtered", "data"),
    Input("geojson-store-full", "data"),
    Input("year-slider", "value"),
)
def filter_data(store, date_range):
    """Filter bike segments and nodes by date and compute KPIs."""
    
    if not store or not store.get("segments", {}).get("features"):
        return None, None, None, MESSAGE_NO_DATA, None, {}

    gdf_segments = gpd.GeoDataFrame.from_features(store["segments"]["features"])
    gdf_nodes = gpd.GeoDataFrame.from_features(store["nodes"]["features"])
    gdf_gpx = gpd.GeoDataFrame.from_features(store["gpx"]["features"])

    # --- Ensure all datetime columns once ---
    for df in [gdf_segments, gdf_nodes, gdf_gpx]:
        for col in ["track_date", "track_date_min"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    # --- Build datetime range ---
    start_year, end_year = date_range
    start = pd.Timestamp(start_year, 1, 1)
    end = pd.Timestamp(end_year, 12, 31)

    # --- Filter directly (datetime64 works perfectly) ---
    seg_mask = gdf_segments["track_date"].between(start, end)
    node_mask = gdf_nodes["track_date"].between(start, end)
    gpx_mask = gdf_gpx["track_date"].between(start, end)

    gdf_segments_filtered = gdf_segments.loc[seg_mask].copy()
    gdf_nodes_filtered = gdf_nodes.loc[node_mask].copy()
    gdf_gpx_filtered = gdf_gpx.loc[gpx_mask].copy()

    # Helper function for building tooltip
    def build_tooltip(label_prefix, label_value, kpi_dict):
        # First line: prefix in light grey, value in black and larger font
        tooltip_lines = [
            # optional: add font-family: {FONT_MAIN} but default looks better imo
            f'<span style="color: #999; font-size: 14px;">{label_prefix}</span>'
            f'<span style="color: #000; font-size: 16px; font-weight: bold;">{label_value}</span>'
            '<br>'  # simple line break for spacing
        ]
        
        # KPI lines in smaller font
        for kpi_name, kpi_value in kpi_dict.items():
            tooltip_lines.append(
                f'<span style="color: #999; font-size: 12px;">{kpi_name}: </span>'
                f'<b style="color: #000; font-size: 12px;">{kpi_value}</b>'
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
        first_date_global=("track_date_min", "min"),
        # preserve geometry
        geometry=("geometry", "first")
    ).reset_index()

    agg_seg = gpd.GeoDataFrame(agg_seg, geometry="geometry", crs=gdf_segments_filtered.crs)
    
    # Apply formatting and sort result
    agg_seg["length_km"] = agg_seg["length_km"].round(2)
    agg_seg["max_overlap_percentage"] = agg_seg["max_overlap_percentage"].round(2)
    agg_seg["first_date"] = agg_seg["first_date"].dt.strftime("%Y-%m-%d")
    agg_seg["last_date"] = agg_seg["last_date"].dt.strftime("%Y-%m-%d")
    agg_seg["first_date_global"] = agg_seg["first_date_global"].dt.strftime("%Y-%m-%d")
    agg_seg = agg_seg.sort_values("count_track", ascending=False)

    # Add tooltip
    agg_seg["tooltip"] = agg_seg.apply(
        lambda row: build_tooltip(
            "Segment ",
            row["ref"],
            {
                "Visits": row["count_track"],
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
        first_date_global=("track_date_min", "min"),
        # preserve geometry
        geometry=("geometry", "first")
    ).reset_index()
    agg_nodes = gpd.GeoDataFrame(agg_nodes, geometry="geometry", crs=gdf_nodes_filtered.crs)

    # Apply formatting and sort result
    agg_nodes["first_date"] = agg_nodes["first_date"].dt.strftime("%Y-%m-%d")
    agg_nodes["last_date"] = agg_nodes["last_date"].dt.strftime("%Y-%m-%d")
    agg_nodes["first_date_global"] = agg_nodes["first_date_global"].dt.strftime("%Y-%m-%d")
    agg_nodes = agg_nodes.sort_values("count_track", ascending=False)

    # Add tooltip
    agg_nodes["tooltip"] = agg_nodes.apply(
        lambda row: build_tooltip(
            "Node ",
            row["rcn_ref"],
            {
                "Visits": row["count_track"],
                "First visit": row["first_date"],
                "Last visit": row["last_date"],
            }
        ),
        axis=1
    )

    # Calculate KPIs
    total_segments = len(agg_seg)
    total_nodes = len(agg_nodes)
    total_length = round(agg_seg["length_km"].sum())
    total_tracks = len(gdf_gpx_filtered)
    total_matched = (gdf_gpx_filtered["matched_segments_count"] > 0).sum()

    return (
        total_segments,
        total_nodes,
        f"{total_length} km",
        f"out of {total_tracks}",
        total_matched,
        {
            "segments": agg_seg.__geo_interface__,
            "nodes": agg_nodes.__geo_interface__,
            "gpx": gdf_gpx_filtered.__geo_interface__
        }
    )

@app.callback(
    Output("layer-segments", "data"),
    Output("layer-track", "data"),
    Input("geojson-store-filtered", "data"),
)
def update_line_layers(filtered_data):
    """Render filtered bike segments and GPX tracks on the map."""
    if not filtered_data:
        return None, None

    # initialize track layer
    res_gpx = filtered_data["gpx"]

    # add tooltips per unique track
    global _tooltips_html
    _tooltips_html = {
        feature["properties"]["track_uid"]: make_track_tooltip(feature)
        for feature in res_gpx["features"]
    }

    return filtered_data["segments"], res_gpx

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
    Output("segment-statistics-descr", "children"),
    Output("node-statistics-descr", "children"),
    Input("geojson-store-filtered", "data"),
)
def update_tables(filtered_data):
    """Aggregate segment and node data for display in Dash tables."""
    
    if not filtered_data:
        return [], [], [], [], {"display": "none"}, {"display": "none"}, \
            MESSAGE_NO_DATA, MESSAGE_NO_DATA
    
    agg_seg = gpd.GeoDataFrame.from_features(filtered_data["segments"]["features"])
    agg_nodes = gpd.GeoDataFrame.from_features(filtered_data["nodes"]["features"])

    # check if all data are filtered out
    if agg_seg.empty or agg_nodes.empty:
        return [], [], [], [], {"display": "none"}, {"display": "none"}, \
            MESSAGE_NO_FILTERED_DATA, MESSAGE_NO_FILTERED_DATA

    # remove and rename columns
    agg_seg = agg_seg.drop(columns=["osm_id_from", "osm_id_to", "tooltip", "geometry"])
    agg_seg = agg_seg.rename(columns={"ref": "segment"})
    agg_nodes = agg_nodes.drop(columns=["tooltip", "geometry"])
    agg_nodes = agg_nodes.rename(columns={"rcn_ref": "node"})

    # columns that are shown/hidden in the segments table
    COL_LABELS = {
        "segment": "Segment",
        "count_track": "Visits",
        "length_km": "Length (km)",
        "first_date": "First visit",
        "last_date": "Last visit",
    } 
    seg_columns = [
        {"name": COL_LABELS.get(c, c.replace("_", " ").title()), "id": c}
        for c in agg_seg.columns
        if c not in ["osm_id", "max_overlap_percentage", "first_date_global"]
    ]
    seg_data = agg_seg.to_dict("records")

    # columns that are shown/hidden in the nodes table
    COL_LABELS = {
        "node": "Node",
        "count_track": "Visits",
        "first_date": "First visit",
        "last_date": "Last visit",
    } 
    node_columns = [
        {"name": COL_LABELS.get(c, c.replace("_", " ").title()), "id": c}
        for c in agg_nodes.columns
        if c not in ["osm_id", "first_date_global"]
    ]
    node_data = agg_nodes.to_dict("records")

    outputs = seg_data, seg_columns, node_data, node_columns, \
        {"display": "inline-block"}, {"display": "inline-block"}, \
        "Select one or more segments in the table to highlight them on the map (in red).", \
        "Select one or more nodes in the table to highlight their segments on the map (in purple)."
    
    return outputs

@app.callback(
    Output("line-chart", "figure"),
    Input("geojson-store-filtered", "data"),
    Input("agg-level", "value"),
    Input("plot-type", "value"),
    Input("element-type", "value"),
    Input("filter-mode", "value"),
    State("year-slider", "value"),
)
def update_chart(filtered_data, agg_level, plot_type, element_type, filter_mode, date_range):

    if not filtered_data:
        return build_empty_figure(MESSAGE_NO_DATA)

    # get dataframes
    agg_segs = gpd.GeoDataFrame.from_features(filtered_data["segments"]["features"])
    agg_nodes = gpd.GeoDataFrame.from_features(filtered_data["nodes"]["features"])

    if agg_segs.empty or agg_nodes.empty:
        return build_empty_figure(MESSAGE_NO_FILTERED_DATA)

    # date conversions
    agg_segs["first_date"] = pd.to_datetime(agg_segs["first_date"])
    agg_segs["first_date_global"] = pd.to_datetime(agg_segs["first_date_global"])
    agg_nodes["first_date"] = pd.to_datetime(agg_nodes["first_date"])
    agg_nodes["first_date_global"] = pd.to_datetime(agg_nodes["first_date_global"])

    # get date range
    start_year, end_year = date_range
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)

    # get chart settings
    id_col = "osm_id"
    if filter_mode == "discoveries":
        date_col = "first_date_global"
        # filter rows to only include new discoveries
        agg_segs = agg_segs.query("@start <= first_date_global <= @end")
        agg_nodes = agg_nodes.query("@start <= first_date_global <= @end")
    else:
        date_col = "first_date"
    
    # initialize dataframes
    df_segs = prepare_chart_data(agg_segs, id_col, date_col, agg_level)
    df_nodes = prepare_chart_data(agg_nodes, id_col, date_col, agg_level)

    # calculate cumulative counts if needed
    if plot_type == "cumulative":
        df_segs["count"] = df_segs["count"].cumsum()
        df_nodes["count"] = df_nodes["count"].cumsum()

    # assign type (for coloring) and choose dataframe
    df_segs["type"] = "segment"
    df_nodes["type"] = "node"

    if element_type == "segment":
        df = df_segs
    else:
        df = df_nodes

    # in case of 'discoveries' the resulting data frame may still be empty
    if df.empty:
        return build_empty_figure(MESSAGE_NO_FILTERED_DATA)

    fig = build_coverage_figure(df, agg_level, plot_type, filter_mode)

    return fig

@app.callback(
    Output("table-segments-agg", "selected_rows"),
    Input("unselect-all-btn-seg", "n_clicks"),
    # also clear selection when user modifies filters
    Input("table-segments-agg", "data"),
)
def unselect_all_segments(*_):
    """Clear all selected rows in the segments table when triggered."""
    return []

@app.callback(
    Output("table-nodes-agg", "selected_rows"),
    Input("unselect-all-btn-nodes", "n_clicks"),
    # also clear selection when user modifies filters
    Input("table-segments-agg", "data"),
)
def unselect_all_nodes(*_):
    """Clear all selected rows in the nodes table when triggered."""
    return []

@app.callback(
    Output("browse-info", "children"),
    Input("upload-zip", "contents"),
    State('upload-zip', 'filename')
)
def show_info(_, f):
    """Display selected filename from upload component (if available)"""
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
    """Recenter the map to its initial center and zoom level."""
    return INITIAL_CENTER, INITIAL_ZOOM, f"map-{n_clicks}"

@app.callback(
    Output("layer-selected-segments", "children"),
    Input("table-segments-agg", "selected_rows"),
    State("table-segments-agg", "data"),
    State("geojson-store-filtered", "data"),
)
def highlight_segments(selected_rows, table_data, filtered_data):
    """Highlight selected segments on the map"""
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
        options=dict(style=dict(color=COLOR_HIGHLIGHT_SEGMENT, weight=8)),
        zoomToBounds=True,
    )

@app.callback(
    Output("layer-selected-nodes", "children"),
    Input("table-nodes-agg", "selected_rows"),
    State("table-nodes-agg", "data"),
    State("geojson-store-filtered", "data"),
)
def highlight_segments_from_nodes(selected_rows, table_data, filtered_data):
    """Highlight segments connected to selected nodes on the map"""
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
        options=dict(style=dict(color=COLOR_HIGHLIGHT_NODE, weight=8)),
        zoomToBounds=True,
    )

@app.callback(
    Output("layer-track", "hoverStyle"),
    Output("layer-track", "zoomToBoundsOnClick"),
    Input("checkbox-show-hover", "value"),
    Input("layer-track", "data"),
)
def toggle_track_focus(hover_enabled, gpx_geojson):
    """Toggle GPX track hover style and zoom behavior"""
    if not gpx_geojson:
        # no track layer available yet -> do nothing
        raise PreventUpdate
    
    if "hover" in hover_enabled: 
        # activate hoverstyle function
        hover = ns("trackHoverStyle")
        return hover, True
    
    return None, False

@app.callback(
    Output("selected-track", "data"),
    Input("layer-track", "clickData"),
    Input("map", "clickData"),
    Input("checkbox-show-hover", "value")
)
def update_selected_track(layer_click, map_click, checkbox):
    """Update the dcc.Store storing the selected GPX track"""
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
        # (triggers: ['layer-track.clickData', 'map.clickData'])
        return selected_id
    elif any("map" in item for item in triggers):
        # user either clicked on the same feature or outside the layer
        # (trigger: only ['map.clickData'] )
        if KEEP_TRACK_SELECTION_ACTIVE:
            # keep selection until new feature is clicked or Track Focus is deactivated
            return selected_id
        # check if user clicked close enough to the same feature to keep it active
        elif is_point_near_geometry(map_click["latlng"], layer_click["geometry"]):
            return selected_id
    
    # reset selection for all other conditions
    return None

@app.callback(
    Output("layer-track", "hideout"),
    Input("selected-track", "data"),
    Input("checkbox-show-hover", "value"),
    Input("layers-control", "baseLayer"),
    State("layer-track", "hideout"),
    Input("layer-track", "data"),
)
def update_gpx_layer_hideout(selected_id, checkbox_value, base_layer, current_hideout, _):
    """Update the GPX layer's hideout dict to control attributes based on current state."""
    # update state container for the layer triggered to control styling
    hideout = dict(current_hideout)
    hideout["selected_id"] = selected_id
    hideout["track_focus"] = (checkbox_value != [])
    hideout["base_color"] = (
        COLOR_GPX_CARTO_LIGHT if base_layer == "Carto Light" 
        else COLOR_GPX_CARTO_VOYAGER
    )
    hideout["tooltips"] = _tooltips_html
    hideout["tooltip_opacity"] = 0.0 if checkbox_value == [] else 0.9

    return hideout

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE)
