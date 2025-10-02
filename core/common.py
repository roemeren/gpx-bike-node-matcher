# ---------- Imports ----------
import geopandas as gpd
import pandas as pd
import os

# ---------- Constants ----------
# files and folders
UPLOAD_FOLDER = "app/uploads"
STATIC_FOLDER = "app/static"

# geoprocessing
MULTILINE_GEOJSON_PATH = 'data/processed/gdf_multiline.geojson'
MULTILINE_PROJECTED_PARQUET_PATH = 'data/processed/gdf_multiline_projected.parquet'
POINT_PROJECTED_PARQUET_PATH = 'data/processed/gdf_point_projected.parquet'
SIMPLIFY_TOLERANCE_M = 10 #  meters, drastically improves memory and speed
BUFFER_DISTANCE_M = 20  # meters, for spatial buffer
INTERSECT_THRESHOLD = 0.75 # minimum overlap fraction for matching 
