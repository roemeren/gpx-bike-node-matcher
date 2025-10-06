import ssl  # import before fiona to avoid SSL issues on Windows
import platform
import subprocess
import fiona
from pathlib import Path
from scripts.geofabrik_date import *
from core.common import *
from tqdm import tqdm

# geoprocessing
SCRIPTS_FOLDER = "scripts"
NODE_WIDTH = 3
INPUT_GPKG = "data/intermediate/rcn_output.gpkg"
TQDM_DEFAULT = {"mininterval": 0.1, "miniters": 1}
SPARSITY_THRESHOLD = 0.9
MAIN_REGION_COUNTRIES = ["belgium", "netherlands"]
MAIN_COUNTRY = "belgium"

def parse_and_filter_tags(tag_string, tags_to_keep=None):
    """
    Parse a string-encoded dictionary of tags and optionally filter keys.

    Args:
        tag_string (str): String in the format '"key"=>"value", ...'.
        tags_to_keep (list, optional): List of keys to retain. If None or empty, all keys are returned.

    Returns:
        dict: Parsed and optionally filtered dictionary of tags.
    """
    # Regular expression to match key-value pairs in the format 'key'=>"value"
    tag_pairs = re.findall(r'"(.*?)"=>"(.*?)"', tag_string)
    tag_dict = dict(tag_pairs)

    # Replace colons in the keys with underscores
    tag_dict = {k.replace(':', '_'): v for k, v in tag_dict.items()}

    # If tags_to_keep is None or empty, return all tags
    if tags_to_keep is None or len(tags_to_keep) == 0:
        return tag_dict
    
    # Filter the dictionary to keep only the desired tags
    filtered_tags = {k: v for k, v in tag_dict.items() if k in tags_to_keep}
    return filtered_tags

def explode_tags(df, tags_column, tags_to_keep=None):
    """
    Expand a column of string-encoded dictionaries in a GeoDataFrame into separate columns.

    Args:
        df (GeoDataFrame): Input GeoDataFrame containing a column with dictionary strings.
        tags_column (str): Name of the column to parse and expand.
        tags_to_keep (list, optional): List of keys to retain. If None, all keys are kept.

    Returns:
        GeoDataFrame: Original GeoDataFrame with the dictionary keys expanded as columns.
    """
    # Convert the string representation of the dictionary to a Python dictionary
    exploded_tags = df[tags_column].apply(lambda x: parse_and_filter_tags(x, tags_to_keep) if isinstance(x, str) else {})
    
    # Create a DataFrame from the exploded tags
    tags_df = pd.json_normalize(exploded_tags)
    
    # Combine the original DataFrame with the new tags DataFrame
    exploded_df = pd.concat([df.drop(columns=[tags_column]), tags_df], axis=1)
    
    return exploded_df

def enrich_with_osm_ids(
    gdf_multiline: gpd.GeoDataFrame,
    gdf_point: gpd.GeoDataFrame,
    max_dist: float = 20.0,
    node_width: int = 3,
    tqdm_params: dict = TQDM_DEFAULT
):
    """
    Enrich segment MultiLineStrings with osm_id_from and osm_id_to using buffer intersection.
    
    Args:
        gdf_multiline (GeoDataFrame): Line segments with 'ref' column formatted as "node_from-node_to".
        gdf_point (GeoDataFrame): Points with 'rcn_ref' (node number) and 'osm_id'.
        max_dist (float, optional): Buffer distance around segments to find candidate nodes (meters). Defaults to 20.0.
        node_width (int, optional): Width for zero-padding node IDs. Defaults to 3.
        tqdm_params (dict): progress bar parameters

    Returns:
        tuple:
            gdf_multiline_enriched (GeoDataFrame): Segments with 'osm_id_from' and 'osm_id_to'.
            gdf_point_with_join (GeoDataFrame): Original points with added 'rcn_ref_join' for matching.

    Notes:
        An alternative strategy to use a fast nearest join based on endpoints produced poor results 
        due to complex or curved MultiLineString geometries. This buffer-based intersection method 
        ensures more reliable matches.
    """
    # Make explicit copies to avoid modifying originals
    gdf_multiline = gdf_multiline.copy()
    gdf_point = gdf_point.copy()

    # --- Step 0: normalize node IDs as strings with leading zeros ---
    gdf_multiline['node_from'] = (
        gdf_multiline['ref'].str.split('-', expand=True)[0].astype(str).str.zfill(node_width)
    )
    gdf_multiline['node_to'] = (
        gdf_multiline['ref'].str.split('-', expand=True)[1].astype(str).str.zfill(node_width)
    )

    # Keep original rcn_ref, add a join column
    gdf_point['rcn_ref_join'] = gdf_point['rcn_ref'].astype(str).str.zfill(node_width)

    # --- Step 1: loop over segments with buffer ---
    osm_from_list = []
    osm_to_list = []

    iterator = tqdm(
        gdf_multiline.iterrows(),
        total=len(gdf_multiline),
        desc="Matching segments",
        **tqdm_params
    )

    for _, seg in iterator:
        buffer_geom = seg.geometry.buffer(max_dist)

        # Node FROM
        candidates_from = gdf_point[gdf_point['rcn_ref_join'] == seg['node_from']]
        candidates_from = candidates_from[candidates_from.intersects(buffer_geom)]
        if not candidates_from.empty:
            osm_from_list.append(candidates_from['osm_id'].min())
        else:
            osm_from_list.append(None)

        # Node TO
        candidates_to = gdf_point[gdf_point['rcn_ref_join'] == seg['node_to']]
        candidates_to = candidates_to[candidates_to.intersects(buffer_geom)]
        if not candidates_to.empty:
            osm_to_list.append(candidates_to['osm_id'].min())
        else:
            osm_to_list.append(None)

    gdf_multiline['osm_id_from'] = osm_from_list
    gdf_multiline['osm_id_to'] = osm_to_list

    # --- Step 2: add match flag ---
    def match_flag(row):
        if pd.notna(row['osm_id_from']) and pd.notna(row['osm_id_to']):
            return 'full'
        elif pd.isna(row['osm_id_from']) and pd.isna(row['osm_id_to']):
            return 'none'
        else:
            return 'partial'

    gdf_multiline['osm_match_flag'] = gdf_multiline.apply(match_flag, axis=1)

    # --- Step 3: summary and printout ---
    missing = gdf_multiline[gdf_multiline['osm_match_flag'] != 'full']
    num_segments = len(gdf_multiline)
    num_full_matches = (gdf_multiline['osm_match_flag'] == 'full').sum()
    percent_full = 100 * num_full_matches / num_segments

    print(f"✅ Full matches: {num_full_matches}/{num_segments} ({percent_full:.3f}%)")

    if not missing.empty:
        display_cols = ['osm_id', 'node_from', 'node_to', 'osm_id_from', 'osm_id_to', 'osm_match_flag']
        print(f"⚠️ {len(missing)} segments missing matches (partial or none):")
        print(missing[display_cols].reset_index(drop=True))

    return gdf_multiline, gdf_point

def load_gpkg_layers_by_suffix(gpkg_path):
    """
    Load all layers from a GeoPackage and return combined GeoDataFrames
    for those ending with 'multiline' and 'point'.
    """
    # List all layer names in the GeoPackage
    layers = fiona.listlayers(gpkg_path)

    gdf_multiline_list = []
    gdf_point_list = []

    for layer_name in layers:
        if layer_name.endswith("multiline"):
            gdf = gpd.read_file(gpkg_path, layer=layer_name)
            gdf["source_layer"] = layer_name  # track origin
            gdf_multiline_list.append(gdf)
        elif layer_name.endswith("point"):
            gdf = gpd.read_file(gpkg_path, layer=layer_name)
            gdf["source_layer"] = layer_name  # track origin
            gdf_point_list.append(gdf)

    # Combine all multilines or points into single GeoDataFrames
    gdf_multiline = (
        gpd.GeoDataFrame(pd.concat(gdf_multiline_list, ignore_index=True))
        if gdf_multiline_list else gpd.GeoDataFrame()
    )
    gdf_point = (
        gpd.GeoDataFrame(pd.concat(gdf_point_list, ignore_index=True))
        if gdf_point_list else gpd.GeoDataFrame()
    )

    return gdf_multiline, gdf_point

def drop_sparse_columns(df, keep_cols=None, threshold=0.9, logging=False):
    """
    Drop columns that are sparse (too many missing or empty string values).
    """
    if keep_cols is None:
        keep_cols = []

    # Compute fraction of NaN or empty string per column
    sparsity = df.isna().mean() + (df == '').mean()

    # Columns to keep: below threshold or explicitly listed
    cols_to_keep = [c for c in df.columns if (sparsity.get(c, 0) < threshold) or (c in keep_cols)]
    dropped = set(df.columns) - set(cols_to_keep)

    if dropped and logging:
        print(f"[INFO] Dropped {len(dropped)} sparse columns: {', '.join(dropped)}")

    return df[cols_to_keep]

def clean_ref(ref: str, logging: bool = False) -> str | None:
    """
    Clean and validate a 'ref' string of the form:
    1–3 digits, a dash, and 1–3 digits (with optional leading zeroes).
    
    - Accepts patterns like "04-09", "4-115", "04 -09", "5- 150"
    - Strips and normalizes spaces around the dash
    - Returns cleaned string if valid, otherwise None
    - Prints debug info when cleaned or invalid
    """
    if ref is None:
        print("None → None")
        return None

    original = ref
    # Attempt to match pattern (allows spaces around the dash)
    match = re.fullmatch(r"\s*(\d{1,3})\s*-\s*(\d{1,3})\s*", ref)

    if match:
        cleaned = f"{match.group(1)}-{match.group(2)}"
        if cleaned != original and logging:
            print(f"Cleaned: '{original}' → '{cleaned}'")
        return cleaned
    elif logging:
        print(f"Invalid: '{original}' → None")
        return None

def process_osm_data(tqdm_params):
    """
    Download Belgium OSM data, process segments and points, 
    enrich segments with OSM node IDs, and save GeoJSON outputs.
    """
    current_os = platform.system()
    print(f"[INFO] Running on {current_os}")

    osm_version = get_latest_geofabrik_date()
    print(f"[INFO] Latest Geofabrik OSM version: {osm_version}")

    # Download OSM data, extract rcn relations, create GeoPackage and keep key files
    if current_os == "Windows":
        # Get absolute path to batch script to avoid relative path issues on Windows
        script_path = Path(SCRIPTS_FOLDER) / "geofabrik_preprocessing.bat"
        files_path = Path(SCRIPTS_FOLDER) / "geofabrik_file_list.txt"
        with open(files_path, "r", encoding="utf-8") as f:
            regions = [line.strip() for line in f if line.strip()]
        print(f"[INFO] Using script: {script_path}")

        for region in regions:
            print(f"[INFO] Processing region: {region}")
            try:
                subprocess.run(
                    [str(script_path), osm_version, region],
                    check=True,
                    shell=True,  # required for .bat
                )
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Script failed for region '{region}': {e}")

    # Read and combine layers from geopackage
    print(f"[INFO] Reading GeoPackage: {INPUT_GPKG}")
    gdf_multiline, gdf_point = load_gpkg_layers_by_suffix(INPUT_GPKG)

    # Deduplicate lines and points near border regions
    n_multi, n_point = len(gdf_multiline), len(gdf_point)
    gdf_multiline = gdf_multiline.dissolve(by="osm_id", aggfunc="first").reset_index()
    gdf_point = gdf_point.drop_duplicates(subset="osm_id", keep="first").reset_index(drop=True)
    print(f"[INFO] Loaded {len(gdf_multiline)} multilines (-{n_multi - len(gdf_multiline)} dupes) "
        f"and {len(gdf_point)} points (-{n_point - len(gdf_point)} dupes).")
    
    # Keep only features originating from main countries ---
    mask_main_region = gdf_multiline["source_layer"].str.startswith(tuple(MAIN_REGION_COUNTRIES))
    n_before = len(gdf_multiline)
    gdf_multiline = gdf_multiline[mask_main_region].reset_index(drop=True)
    gdf_multiline["is_main_country"] = gdf_multiline["source_layer"].str.startswith(MAIN_COUNTRY)
    print(
        f"[INFO] Kept {len(gdf_multiline)} multilines from {MAIN_REGION_COUNTRIES} "
        f"(-{n_before - len(gdf_multiline)} non-region features removed)."
    )
    print(
        f"[INFO] Marked {gdf_multiline['is_main_country'].sum()} multilines as belonging to {MAIN_COUNTRY}."
    )

    # Process the multilinestrings tags
    print("[INFO] Exploding multiline tags...")
    tags_to_keep = ["network_type", "ref", "route"]
    tags_column = 'other_tags'
    gdf_multiline = explode_tags(gdf_multiline, tags_column, tags_to_keep)
    before_filter = len(gdf_multiline)
    gdf_multiline["ref"] = gdf_multiline["ref"].astype(str)
    gdf_multiline["ref"] = gdf_multiline["ref"].apply(clean_ref)
    gdf_multiline = gdf_multiline[(gdf_multiline["network_type"] == "node_network") & (gdf_multiline['ref'].fillna('').str.contains('-', na=False))]
    print(f"[INFO] Filtered multilines from {before_filter} → {len(gdf_multiline)} valid segments.")

    # Process the points tags
    print("[INFO] Exploding point tags...")
    gdf_point = explode_tags(gdf_point, tags_column)
    before_filter = len(gdf_point)
    # better match if network_type == "node_network" condition is removed here
    gdf_point = gdf_point[gdf_point['rcn_ref'].fillna('') != '']
    before_filter_cols = gdf_point.shape[1]
    gdf_point = drop_sparse_columns(
        gdf_point,
        keep_cols=["osm_id", "rcn_ref"],
        threshold=SPARSITY_THRESHOLD
    )
    gdf_point["is_main_country"] = gdf_point["source_layer"].str.startswith(MAIN_COUNTRY)
    print(
        f"[INFO] Marked {gdf_point['is_main_country'].sum()} nodes as belonging to {MAIN_COUNTRY}."
    )
    print(f"[INFO] No. columns reduced from {before_filter_cols} → {gdf_point.shape[1]} columns.")
    print(f"[INFO] Filtered nodes from {before_filter} → {len(gdf_point)} valid nodes.")

    # Convert to projected coordinate system
    print("[INFO] Projecting...")
    gdf_multiline_projected = gdf_multiline.to_crs(epsg=EPSG_PROJECTED)
    gdf_point_projected = gdf_point.to_crs(epsg=EPSG_PROJECTED)

    # Look up matching node osm_id for segment nodes
    print("[INFO] Enriching multilines with OSM node IDs...")
    gdf_multiline_projected, gdf_point_projected = \
        enrich_with_osm_ids(gdf_multiline_projected, gdf_point_projected, 
                            BUFFER_DISTANCE_M, NODE_WIDTH, tqdm_params)
    print("[INFO] Enrichment completed.")

    # --- Keep only nodes used in enriched segments ---
    print("[INFO] Filtering points to keep only those referenced in multilines...")

    # collect all osm_ids referenced by the network
    referenced_ids = set(
        pd.concat([gdf_multiline_projected["osm_id_from"], gdf_multiline_projected["osm_id_to"]])
        .dropna()
        .astype(str)
        .unique()
    )

    before_filter = len(gdf_point_projected)
    gdf_point_projected = gdf_point_projected[gdf_point_projected["osm_id"].isin(referenced_ids)]
    print(f"[INFO] Filtered points from {before_filter} → {len(gdf_point_projected)} nodes used in network.")

    # Simplify geometry (with tolerance in m) & add segment length
    # Note: only keeping relevant attribute columns doesn't make much difference
    gdf_multiline_projected['geometry'] = gdf_multiline_projected['geometry'].simplify(tolerance=SIMPLIFY_TOLERANCE_M, preserve_topology=True)
    gdf_multiline_projected["length_km"] = gdf_multiline_projected.geometry.length / 1000.0

    # Make separate version for main country only
    gdf_multiline_projected_main = gdf_multiline_projected[gdf_multiline_projected['is_main_country']]
    gdf_point_projected_main = gdf_point_projected[gdf_point_projected['is_main_country']]

    # Convert the enriched result back to WGS84
    print("[INFO] Converting back to WGS84 (EPSG:4326)...")
    gdf_multiline = gdf_multiline_projected.to_crs(epsg=4326)
    gdf_multiline_main = gdf_multiline_projected_main.to_crs(epsg=4326)
    
    # Dissolve all geometries in a GeoDataFrame into one combined geometry
    merged = gdf_multiline.geometry.union_all()
    gdf_multiline = gpd.GeoDataFrame(geometry=[merged], crs=gdf_multiline.crs)

    # Save the outputs as GeoJSON and parquet for use in the app
    # compared to shapefiles there is no truncation of column names but takes longer
    print("[INFO] Saving outputs...")
    os.makedirs(OUTPUT_FOLDER_FULL, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER_LITE, exist_ok=True)
    
    # main outputs
    gdf_multiline.to_file(Path(OUTPUT_FOLDER_FULL) / MULTILINE_GEOJSON_NAME, driver='GeoJSON')
    gdf_multiline_projected.to_parquet(Path(OUTPUT_FOLDER_FULL) / MULTILINE_PROJECTED_PARQUET_NAME, engine="pyarrow")
    gdf_point_projected.to_parquet(Path(OUTPUT_FOLDER_FULL) / POINT_PROJECTED_PARQUET_NAME, engine="pyarrow")
    gdf_multiline_main.to_file(Path(OUTPUT_FOLDER_LITE) / MULTILINE_GEOJSON_NAME, driver='GeoJSON')
    gdf_multiline_projected_main.to_parquet(Path(OUTPUT_FOLDER_LITE) / MULTILINE_PROJECTED_PARQUET_NAME, engine="pyarrow")
    gdf_point_projected_main.to_parquet(Path(OUTPUT_FOLDER_LITE) / POINT_PROJECTED_PARQUET_NAME, engine="pyarrow")
    print("[INFO] All outputs saved successfully.")

if __name__ == "__main__":
    current_os = platform.system()
    if current_os == "Windows":
        # Local usage (more frequent updates)
        tqdm_params = TQDM_DEFAULT
    else:
        # GitHub Actions / CI (less frequent updates)
        tqdm_params = dict(mininterval=3.0, miniters=50) 
    process_osm_data(tqdm_params)
