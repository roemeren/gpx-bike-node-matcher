#!/bin/bash
set -e

echo "=== START OSM PROCESSING ==="

RESULTS_DIR="data/intermediate"
mkdir -p "$RESULTS_DIR"
echo "[INFO] Temp directory ensured: $RESULTS_DIR"

# --- Get parameters ---
DATE=$1
INPUT_FILE=$2  # full path to cached .osm.pbf

# --- Derive region name from input file ---
BASENAME=$(basename "$INPUT_FILE")
REGION=${BASENAME%-latest.osm.pbf}

if [ -z "$DATE" ] || [ -z "$INPUT_FILE" ]; then
    echo "[ERROR] Usage: $0 <yymmdd> <input_file>"
    exit 1
fi

echo "[INFO] Using cached input file: $INPUT_FILE"
echo "[INFO] Processing date: $DATE"

# --- Filter OSM data ---
RCN_RELATIONS="$RESULTS_DIR/rcn_relations.osm.pbf"
RCN_POINTS="$RESULTS_DIR/rcn_ref_points.osm.pbf"

echo "[INFO] Filtering OSM relations (network=rcn)..."
osmium tags-filter "$INPUT_FILE" r/network=rcn -o "$RCN_RELATIONS"
echo "[INFO] Relations saved to: $RCN_RELATIONS"

echo "[INFO] Filtering OSM points (rcn_ref)..."
osmium tags-filter "$RCN_RELATIONS" n/rcn_ref -o "$RCN_POINTS"
echo "[INFO] Points saved to: $RCN_POINTS"

# --- Create GeoPackage ---
OUTPUT_GPKG="$RESULTS_DIR/rcn_output.gpkg"
LAYER_NAME_MULTILINE="${REGION}_multiline"
LAYER_NAME_POINT="${REGION}_point"

if [ -f "$OUTPUT_GPKG" ]; then
    echo "[INFO] Appending to existing GeoPackage: $OUTPUT_GPKG"
    ogr2ogr -f "GPKG" -update "$OUTPUT_GPKG" "$RCN_RELATIONS" multilinestrings -nln "$LAYER_NAME" -overwrite
else
    echo "[INFO] Creating new GeoPackage: $OUTPUT_GPKG"
    ogr2ogr -f "GPKG" "$OUTPUT_GPKG" "$RCN_RELATIONS" multilinestrings -nln "$LAYER_NAME"
fi
echo "[INFO] Added multilinestrings layer '$LAYER_NAME' to GeoPackage"

ogr2ogr -f "GPKG" -update "$OUTPUT_GPKG" "$RCN_POINTS" points -nln "$LAYER_NAME_POINTS" -overwrite
echo "[INFO] Added points layer to GeoPackage"

echo "[INFO] GeoPackage created successfully: $OUTPUT_GPKG"

echo "[INFO] Processing complete."
echo "=== END OSM PROCESSING ==="
