# constants.py - global constants and config values used across the app
from core.common import *
import datetime
from dash_extensions.javascript import Namespace

# Colors
COLOR_NETWORK = '#7f8c8d'
COLOR_GPX_CARTO_LIGHT = '#FC4C02'
COLOR_GPX_CARTO_VOYAGER = '#D62728'
COLOR_GPX_SELECTED = '#A3FF12'

# Segment rendering
WEIGHT_CLASSES_SEGMENT = [1, 5, 10, 20]     # thresholds for counts
WEIGHTS_SEGMENT = [2, 4, 6, 8, 10]          # corresponding line weights
COLOR_SEGMENT = '#33A7AA'                   # fixed color (alternatives: #78A2D2)
COLOR_PROCESSING = '#343a40'
COLOR_HIGHLIGHT_SEGMENT = "red"
COLOR_HIGHLIGHT_NODE = "purple"
FONT_MAIN = "Segoe UI, sans-serif"

# Map settings
INITIAL_CENTER =  [50.65, 4.45]
INITIAL_ZOOM = 8
KEEP_TRACK_SELECTION_ACTIVE = True
SLIDER_MIN_YEAR=2010
SLIDER_MAX_YEAR=datetime.datetime.now().year

# App settings
DEBUG_MODE = False

# JS settings
SELECTED_KEY = "track_uid"
# Access JS functions in assets/ and make them callable from Python
# Source: https://www.dash-leaflet.com/docs/func_props
ns = Namespace("dashExtensions", "default")
