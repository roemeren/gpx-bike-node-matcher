from core.common import *
from app.utils import sanitize_filename
from shapely.geometry import Point, LineString, MultiLineString
import shutil
import zipfile
from lxml import etree
from concurrent.futures import ProcessPoolExecutor, as_completed

# --- concurrency parameters ---
# Minimum number of files before we even consider parallel parsing
PARALLEL_MIN_FILES = 200
# Minimum number of logical CPU cores required to enable parallel parsing (local only)
PARALLEL_MIN_CORES = 2
# Maximum number of worker processes for parallel GPX parsing
DEFAULT_MAX_WORKERS = 8

# --- application parameters ---
progress_state = {}

# --- helper function at module level (picklable) ---
def parse_single_gpx(gpx_file, zip_folder):
    """
    Parse a GPX file and return a list of dictionaries,
    one per <trk> element (track) found.
    """
    gpx_path = os.path.join(zip_folder, gpx_file)
    tree = etree.parse(gpx_path)
    root = tree.getroot()

    ns = {"gpx": "http://www.topografix.com/GPX/1/1"}  # GPX namespace

    gpx_name = os.path.basename(gpx_file)
    tracks_data = []

    # Iterate over every <trk> in the GPX
    for idx, trk in enumerate(root.findall(".//gpx:trk", namespaces=ns)):
        # Track name
        trk_name_elem = trk.find("gpx:name", namespaces=ns)
        track_name = trk_name_elem.text if trk_name_elem is not None else None

        # Create a unique-ish id: file + track index
        track_uid = f"{gpx_name}__{idx}"

        # Activity type (track-level first, fallback to root)
        type_elem = trk.find("gpx:type", namespaces=ns)
        if type_elem is None:
            type_elem = root.find("gpx:type", namespaces=ns)
        activity_type = type_elem.text if type_elem is not None else None

        # Collect all segments
        line_segments = []
        track_date = None
        for seg in trk.findall("gpx:trkseg", namespaces=ns):
            pts = []
            for p in seg.findall("gpx:trkpt", namespaces=ns):
                lon, lat = float(p.attrib["lon"]), float(p.attrib["lat"])
                pts.append((lon, lat))
                # first time element across all segments → track_date
                if track_date is None:
                    t_elem = p.find("gpx:time", namespaces=ns)
                    if t_elem is not None:
                        track_date = pd.to_datetime(t_elem.text, utc=True).date()
            if len(pts) > 1:
                line_segments.append(LineString(pts))

        if not line_segments or track_date is None:
            continue  # skip empty/bad tracks

        geom = MultiLineString(line_segments) if len(line_segments) > 1 else line_segments[0]

        tracks_data.append({
            "gpx_name": gpx_name,
            "track_name": track_name,
            "track_uid": track_uid,
            "track_date": track_date,
            "geometry": geom,
            "activity_type": activity_type
        })

    return tracks_data if tracks_data else None

# --- main function ---
def process_gpx_zip(zip_file_path, bike_network, point_geodf, stop_event=None):
    """
    Process a ZIP archive of GPX files and match tracks with a bike network.

    This function unzips the GPX files, parses each track into geometries,
    buffers them, calculates overlap with the bike network segments, filters
    segments exceeding the overlap threshold, and extracts corresponding bike nodes.

    Progress updates are written to `progress_state` throughout the steps.

    Uses sequential parsing for a small number of files and parallel parsing
    for larger ZIPs to improve performance.

    Args:
        zip_file_path (str): Path to the ZIP file containing GPX files.
        bike_network (GeoDataFrame): GeoDataFrame of bike network segments.
        point_geodf (GeoDataFrame): GeoDataFrame of bike nodes.
        stop_event (threading.Event, optional): Signal used for cooperative 
            cancellation. When set, processing stops gracefully. Defaults to None.

    Returns:
        tuple:
            GeoDataFrame: Matched bike network segments with GPX metadata.
            GeoDataFrame: Matched bike nodes corresponding to the segments.
            GeoDataFrame: Original GPX tracks with simplified geometry.

    Note:
        An alternative approach that processes GPX files individually with
        concurrency was tested and performs well locally, but is not suitable
        on Render free tier due to limited CPU and memory.
    """
    # Helper to exit early if user pressed Cancel
    def check_cancel():
        if stop_event and stop_event.is_set():
            print("Processing cancelled by user.")
            return True
        return False
    
    empty = gpd.GeoDataFrame()

    # --- unzip ---
    zip_base_name = sanitize_filename(os.path.splitext(os.path.basename(zip_file_path))[0])
    zip_folder = os.path.join(OUTPUT_FOLDER, f"{zip_base_name}", "temp")
    shutil.rmtree(zip_folder, ignore_errors=True)
    os.makedirs(zip_folder, exist_ok=True)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(zip_folder)
        if check_cancel(): 
            shutil.rmtree(zip_folder, ignore_errors=True)
            return empty, empty, empty, "Cancelled"

    gpx_files = [f for f in os.listdir(zip_folder) if f.lower().endswith(".gpx")]
    total_files = len(gpx_files)
    if total_files == 0:
        message = "No GPX files found in the uploaded ZIP. \
            Please upload a ZIP containing one or more GPX files."
        progress_state["pct"] = 100
        return empty, empty, empty, message

    # --- parse GPX files ---
    gpx_rows = []
    # added as environment variable in Render; used to disable parallel processing
    # on the free tier to prevent crashes or memory issues
    is_render = os.getenv("RENDER") == "true"
    use_parallel = (
        not is_render
        and os.cpu_count() >= PARALLEL_MIN_CORES
        and total_files >= PARALLEL_MIN_FILES
    )

    if not use_parallel:
        # Sequential parsing
        for i, gpx_file in enumerate(gpx_files, start=1):
            if check_cancel(): return empty, empty, empty, "Cancelled"
            progress_state["show-dots"] = False
            progress_state["current-task"] = f"Parsing GPX files: {i}/{total_files}"
            progress_state["pct"] = round(i / total_files * 50)
            results = parse_single_gpx(gpx_file, zip_folder)   # list of dicts
            if results:
                gpx_rows.extend(results)
    else:
        # Parallel parsing
        max_workers = min(DEFAULT_MAX_WORKERS, os.cpu_count())
        futures = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for gpx_file in gpx_files:
                futures.append(executor.submit(parse_single_gpx, gpx_file, zip_folder))
            for i, future in enumerate(as_completed(futures), start=1):
                # Check cancel before processing next finished future
                if check_cancel():
                    # Optionally cancel unfinished futures
                    for f in futures:
                        f.cancel()
                    return empty, empty, empty, "Cancelled"
                
                results = future.result()
                if results:
                    gpx_rows.extend(results)
                progress_state["current-task"] = f"Parsing GPX files (parallel): {i}/{total_files}"
                progress_state["pct"] = round(i / total_files * 50)

    # remove unzip folder
    shutil.rmtree(zip_folder)

    if not gpx_rows:
        message = "No valid GPX data found. Please upload a different file."
        progress_state["pct"] = 100
        return empty, empty, empty, message

    all_gpx_gdf = gpd.GeoDataFrame(gpx_rows, crs="EPSG:4326")

    # --- reproject ---
    progress_state["show-dots"] = True
    progress_state["current-task"] = f"Reprojecting GPX geometries to EPSG:{EPSG_PROJECTED}"
    if check_cancel(): return empty, empty, empty, "Cancelled"
    progress_state["pct"] = 55
    all_gpx_gdf = all_gpx_gdf.to_crs(epsg=EPSG_PROJECTED)

    # --- simplify & buffer GPX geometries---
    progress_state["current-task"] = "Buffering GPX geometries"
    if check_cancel(): return empty, empty, empty, "Cancelled"
    progress_state["pct"] = 60
    all_gpx_gdf['geometry'] = all_gpx_gdf['geometry'].simplify(
        tolerance=SIMPLIFY_TOLERANCE_M/2, preserve_topology=True
    )
    all_gpx_gdf["buffer_geom"] = all_gpx_gdf.geometry.buffer(BUFFER_DISTANCE_M)
    gpx_buffers = all_gpx_gdf.set_geometry("buffer_geom")

    # --- spatial join: find all segments that intersect each GPX track buffer ---
    progress_state["current-task"] = "Matching GPX tracks with bike node network"
    if check_cancel(): return empty, empty, empty, "Cancelled"
    progress_state["pct"] = 65
    joined = gpd.sjoin(
        bike_network,
        gpx_buffers[["gpx_name", "track_name", "track_date", "track_uid", "buffer_geom"]],
        how="inner",
        predicate="intersects"
    )

    if joined.empty:
        message = "No GPX tracks matched the bike node network. \
            Please verify your routes and try again."
        progress_state["pct"] = 100
        return empty, empty, empty, message

    joined = joined.reset_index()

    # look up buffer geometry
    joined = joined.merge(
        all_gpx_gdf[["buffer_geom"]],
        left_on="index_right", right_index=True, suffixes=("", "_gpx")
    )

    # --- intersection lengths: compute segment overlap with each GPX track buffer ---
    progress_state["current-task"] = "Calculating intersection lengths"
    if check_cancel(): return empty, empty, empty, "Cancelled"
    progress_state["pct"] = 75
    joined["segment_length"] = joined.geometry.length
    joined["intersection_geom"] = joined.geometry.intersection(joined["buffer_geom"])
    joined["intersection_length"] = joined["intersection_geom"].length.fillna(0)
    mask = joined["segment_length"] > 0
    joined["overlap_percentage"] = 0.0
    joined.loc[mask, "overlap_percentage"] = (
        (joined.loc[mask, "intersection_length"] /
         joined.loc[mask, "segment_length"]).clip(0, 1)
    )

    # --- filter segments by minimum overlap and remove unnecessary columns ---
    mask = joined["overlap_percentage"] >= INTERSECT_THRESHOLD
    drop_cols = [
        "index", "index_right", "buffer_geom", "segment_length", 
        "intersection_geom", "intersection_length"
    ]

    all_segments = joined.loc[mask].drop(columns=drop_cols, errors="ignore").copy()

    if all_segments.empty:
        message = "No GPX tracks met the matching threshold. \
            Partial overlaps were detected but not sufficient for valid matches.."
        progress_state["pct"] = 100
        return empty, empty, empty, message

    # --- matched nodes ---
    progress_state["current-task"] = "Extracting matched bike nodes"
    progress_state["pct"] = 90
    nodes_list = []
    for (gpx_name, track_name, track_date, track_uid), grp in all_segments.groupby(
        ["gpx_name", "track_name", "track_date", "track_uid"]
    ):
        if check_cancel(): return empty, empty, empty, "Cancelled"
        node_ids = pd.Index(
            grp["osm_id_from"].tolist() + grp["osm_id_to"].tolist()
        ).dropna().unique().tolist()
        if not node_ids:
            continue
        matched_nodes = point_geodf[point_geodf["osm_id"].isin(node_ids)].copy()
        if matched_nodes.empty:
            continue
        matched_nodes["gpx_name"] = gpx_name
        matched_nodes["track_name"] = track_name
        matched_nodes["track_date"] = track_date
        matched_nodes["track_uid"] = track_uid
        nodes_list.append(matched_nodes)

    all_nodes = (
        gpd.GeoDataFrame(pd.concat(nodes_list, ignore_index=True), crs=point_geodf.crs)
        if nodes_list
        else gpd.GeoDataFrame(
            columns=list(point_geodf.columns) + ["gpx_name", "track_name", "track_date", "track_uid"]
        )
    )

    progress_state["show-dots"] = False
    progress_state["current-task"] = "All GPX files processed successfully"
    if check_cancel(): return empty, empty, empty, "Cancelled"
    progress_state["pct"] = 100

    all_gpx_gdf = all_gpx_gdf.drop(columns="buffer_geom")
    all_gpx_gdf["track_length"] = all_gpx_gdf.geometry.length / 1000.0

    # --- add match stats per GPX track ---
    if check_cancel(): return empty, empty, empty, "Cancelled"
    seg_counts = (
        all_segments.groupby("track_uid")
        .size()
        .rename("matched_segments_count")
        .reset_index()
    )
    node_counts = (
        all_nodes.groupby("track_uid")
        .size()
        .rename("matched_nodes_count")
        .reset_index()
    )

    # merge counts into GPX dataframe
    all_gpx_gdf = (
        all_gpx_gdf
        .merge(seg_counts, on="track_uid", how="left")
        .merge(node_counts, on="track_uid", how="left")
    )

    # fill NaN counts with 0 for tracks without matches
    all_gpx_gdf[["matched_segments_count", "matched_nodes_count"]] = (
        all_gpx_gdf[["matched_segments_count", 
                     "matched_nodes_count"]].fillna(0).astype(int)
    )

    # --- add first matched date to segments and nodes ---
    all_segments["track_date_min"] = all_segments.groupby("osm_id")["track_date"].transform("min")
    all_nodes["track_date_min"] = all_nodes.groupby("osm_id")["track_date"].transform("min")

    message = ""
    return all_segments, all_nodes, all_gpx_gdf, message

def create_result_zip(base_name, segments_path, nodes_path, gpx_path):
    """
    Zip the output GeoJSON result files and return the zip file path.
    """
    zip_name = f"{base_name} match.zip"
    zip_folder = os.path.dirname(segments_path)
    zip_path = os.path.join(zip_folder, zip_name)

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(segments_path, arcname=os.path.basename(segments_path))
        zf.write(nodes_path, arcname=os.path.basename(nodes_path))
        zf.write(gpx_path, arcname=os.path.basename(gpx_path))
    
    return zip_name

def is_point_near_geometry(point_latlng, geometry, threshold=0.005):
    """Check if a lat/lon point is within `threshold` of a LineString or MultiLineString."""
    point = Point(point_latlng["lng"], point_latlng["lat"])
    
    geom_type = geometry["type"]
    coords = geometry["coordinates"]
    
    # compute minimum Euclidean distance between point and line
    if geom_type == "LineString":
        line = LineString(coords)
    elif geom_type == "MultiLineString":
        line = MultiLineString(coords)
    else:
        raise ValueError(f"Unsupported geometry type: {geom_type}")
  
    return point.distance(line) < threshold
