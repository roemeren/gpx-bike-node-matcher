# 🗺️ QGIS Geoprocessing Demo

This QGIS project illustrates, step by step, how the geoprocessing logic
used by the Dash app works under the hood.

It demonstrates the same workflow described in the wiki page  
**[🚴‍♂️ How the GPX Track Matching Works](../../wiki/How-the-GPX-Track-Matching-Works)**,  
but implemented manually inside QGIS rather than automated in Python.

To explore it, first **unzip `qgis_demo.zip`** (located in the same folder
as this README) and open `qgis_demo.qgz` in **QGIS 3.x**.  
You can download QGIS for free at [qgis.org/download](https://qgis.org/download/).

The project shows how a GPX ride is matched against the official bike
node network to determine which **segments** and **nodes** were actually
covered.

---

## ⚙️ Overview of the Process

| Step | Operation | Purpose |
|------|------------|----------|
| 1 | Parse GPX file | Import the ride as a line geometry |
| 2 | Buffer the track | Account for GPS noise |
| 3 | Clip & reproject the network | Restrict processing to the relevant extent |
| 4 | Intersect | Measure overlap between ride buffer and network segments |
| 5 | Filter by overlap % | Keep only segments actually ridden |
| 6 | Extract & deduplicate nodes | Identify unique visited nodes |
| 7 | Summarize results | Count matched segments/nodes and total distance |

All intermediate results are saved as **GeoJSON** files, while summary
statistics are stored as **CSV** files.

---

## 🧩 Step-by-Step Instructions (QGIS 3.x)

1. **Create project** — Open a new QGIS project and set the coordinate system to `EPSG:25831 (ETRS89 / UTM zone 31N)`.

2. **Load base data**
   - Import both layers from `rcn_output.gpkg`.
   - Rename the group to **Cycling Node Network** and layers to `nodes` and `segments`.

3. **Extract identifiers**
   - In the **nodes** layer's attribute table, calculate a `node` field (integer)  
     using  
     ```text
     regexp_substr("other_tags", '"rcn_ref"=>"([^"]+)"')
     ```
   - In the **segments** layer's attribute table, calculate a `segment` field (text)  
     using  
     ```text
     regexp_substr("other_tags", '"ref"=>"([^"]+)"')
     ```

4. **Import GPX track**
   - Load `sample_ride.gpx`, move its `tracks` layer outside the default group, and remove the group.
   - Set a consistent symbology (same color/width for all layers).

5. **Add basemaps**
   - Use the *QuickMapServices* plugin → **Search QMS** for:  
     - Carto Lite: https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png
     - Carto Voyager Light: https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png

6. **Reproject and buffer the track**
   - Reproject `track_011` to `EPSG:25831` → save as `track_011_reprojected`.
   - Buffer it by **20 m** → save as `tracks_reprojected_buffer.geojson`.

7. **Clip and reproject the network**
   - Clip `segments` by the extent of `tracks` (keep full features).  
     Save as `segments_clipped`.
   - Reproject to `EPSG:25831` → save as `segments_clipped_reprojected.geojson`.

8. **Compute segment length**
   - Add field `segment_length = $length` to the attribute table of `segments_clipped_reprojected` (verify result using the Measure tool).

9. **Intersect ride buffer and network**
   - Input: `segments_clipped_reprojected`  
     Overlay: `track_011_reprojected_buffer`  
     - Keep: `osm_id` and `segment_length` from input + `name` from the overlay.
     - Save as `segments_clipped_reprojected_intersection.geojson`.

10. **Calculate intersection metrics**
    - Add to attribute table of `segments_clipped_reprojected_intersection` layer:
      - `intersection_length = $length`
      - `intersection_percentage = 100 * "intersection_length" / "segment_length"`
      - `flag_match = intersection_percentage >= 75`

11. **Extract matched segments**
    - Filter where `flag_match = 1`  
      → save as `segments_clipped_reprojected_intersection_matched.geojson`.

12. **Join attributes**
    - Join `segments_clipped_reprojected` with the matched intersections on `osm_id`
      (one-to-one, discard unmatched).  
      Keep all fields from the first layer and only `intersection_percentage` from the second layer.  
      Save as `segments_matched.geojson`.

13. **Project nodes and find intersections**
    - Reproject `nodes` to `EPSG:25831` → `nodes_projected`.  
    - Buffer `segments_matched` by 20 m → `segments_matched_buffer`.  
    - Intersect `nodes_projected` with `segments_matched_buffer`.  
      Keep all fields from the first (nodes) layer and `osm_id` from the second (segments) layer.  
      Save as `nodes_reprojected_intersection.geojson`.

14. **Remove duplicate nodes**
    - Delete duplicates by `osm_id` → `nodes_reprojected_intersection_deduplicated`.  
      (Some duplicates remain because of distinct OSM objects.)
    - Delete further duplicates by `(node, osm_id_2)` combination.

15. **Compute basic statistics**
    - **Segments:** field `segment_length` → count = 33, total length ≈ 63 km.  
      Save as `segments_matched_stats.csv`.  
    - **Nodes:** field `osm_id` → count = 39.  
      Save as `nodes_matched_stats.csv`.

---

## 📦 Output Summary

| File | Description |
|------|--------------|
| `segments_matched.geojson` | Network segments with ≥ 75 % overlap |
| `nodes_matched.geojson` | Unique visited bike nodes |
| `segments_matched_stats.csv` | Count + total length of matched segments |
| `nodes_matched_stats.csv` | Count of matched nodes |

---

### 🔍 Comparing with the Dash App

You can verify the results of this QGIS project against the output generated by the Dash application included in the repository.

From the repository root, run:

```bash
python -m app.dash_app
```

Once the app is running, open it in your browser and go to the 'Use Sample Dataset' tab. Select the `sample_ride.zip` option to load the same example used in this QGIS project.

The resulting maps and KPIs should match what you see in QGIS — at least at the time this project was created (if the app evolves over time, the outputs might diverge slightly. Keeping both perfectly synchronized isn’t guaranteed).

### 🗂️ Notes

- The final outputs can be compared directly to the app’s output GeoJSON files:
  `matched_segments` and `matched_nodes`.
- This project demonstrates the main sequence that the Dash app
automates in Python (`geoprocessing.py`).
