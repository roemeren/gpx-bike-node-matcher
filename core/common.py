# ---------- Imports ----------
import geopandas as gpd
import pandas as pd
import os
from app.utils import Path

# ---------- Constants ----------
# files and folders
UPLOAD_FOLDER = "app/uploads"
STATIC_FOLDER = "app/static"
SAMPLE_FOLDER = Path(STATIC_FOLDER) / 'sample'
OUTPUT_FOLDER = os.path.join(STATIC_FOLDER, 'output')

# geoprocessing
OUTPUT_FOLDER_FULL = 'data/processed/full'
OUTPUT_FOLDER_LITE = 'data/processed/lite'
MULTILINE_GEOJSON_NAME = 'gdf_multiline.geojson'
MULTILINE_PROJECTED_PARQUET_NAME = 'gdf_multiline_projected.parquet'
POINT_PROJECTED_PARQUET_NAME = 'gdf_point_projected.parquet'
SIMPLIFY_TOLERANCE_M = [10, 20] #  meters, drastically improves memory and speed
BUFFER_DISTANCE_M = [20, 35]  # meters, for spatial buffer
INTERSECT_THRESHOLD = 0.75 # minimum overlap fraction for matching 
EPSG_PROJECTED = 25831 # cross-country CRS (alternatives: 3812, 3035)
