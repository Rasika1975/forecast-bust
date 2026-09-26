import json
from pathlib import Path
import pandas as pd
from shapely.geometry import Point, shape

BASE_DIR = Path(__file__).resolve().parent.parent
BOUNDARY_FILE = BASE_DIR / "data" / "boundaries" / "india.geojson"
GRID_ENRICHED_FILE = BASE_DIR / "data" / "grid" / "india_grid_enriched.csv"
GRID_GEOJSON_DATA = BASE_DIR / "data" / "grid" / "india_grid.geojson"
GRID_GEOJSON_FRONTEND = BASE_DIR / "frontend" / "public" / "data" / "india_grid.geojson"

REGION_MAPPING = {
    "Kerala": "Western Ghats",
    "Goa": "Western Ghats",
    "Tamil Nadu": "Southern Peninsular",
    "Puducherry": "Southern Peninsular",
    "Karnataka": "Southern Peninsular",
    "Andhra Pradesh": "Southern Peninsular",
    "Telangana": "Deccan Plateau",
    "Maharashtra": "Deccan Plateau",
    "Gujarat": "Northwest Arid",
    "Rajasthan": "Northwest Arid",
    "Madhya Pradesh": "Central India",
    "Chhattisgarh": "Central India",
    "Odisha": "Eastern Coastal",
    "Uttar Pradesh": "Northern Plains",
    "Bihar": "Northern Plains",
    "Jharkhand": "Northern Plains",
    "West Bengal": "Eastern Coastal",
    "Assam": "North-East",
    "Arunachal Pradesh": "North-East",
    "Meghalaya": "North-East",
    "Manipur": "North-East",
    "Mizoram": "North-East",
    "Nagaland": "North-East",
    "Tripura": "North-East",
    "Sikkim": "Northern Himalayas",
    "Jammu & Kashmir": "Northern Himalayas",
    "Ladakh": "Northern Himalayas",
    "Himachal Pradesh": "Northern Himalayas",
    "Uttarakhand": "Northern Himalayas",
    "Punjab": "Northern Plains",
    "Haryana": "Northern Plains",
    "NCT of Delhi": "Northern Plains",
    "Chandigarh": "Northern Plains",
    "Andaman & Nicobar Island": "Islands",
    "Dadara & Nagar Havelli": "Northwest Arid",
    "Daman & Diu": "Northwest Arid",
}


def main():
    print("Loading state boundary polygons...")
    with open(BOUNDARY_FILE, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    state_shapes = []
    for feat in geojson_data["features"]:
        st_name = feat["properties"].get("ST_NM") or feat["properties"].get("NAME_1")
        if not st_name:
            continue
        geom = shape(feat["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        state_shapes.append((st_name, geom))

    print(f"Loaded {len(state_shapes)} state polygon features.")

    grid_df = pd.read_csv(GRID_ENRICHED_FILE)
    print(f"Processing {len(grid_df)} grid cells for spatial matching...")

    new_states = []
    new_regions = []

    for _, row in grid_df.iterrows():
        pt = Point(row["longitude"], row["latitude"])
        matched_st = None

        # 1. Exact container match
        for st_name, s_geom in state_shapes:
            if s_geom.contains(pt) or s_geom.intersects(pt):
                matched_st = st_name
                break

        # 2. Distance fallback for border grid points
        if not matched_st:
            min_dist = float("inf")
            for st_name, s_geom in state_shapes:
                d = s_geom.distance(pt)
                if d < min_dist:
                    min_dist = d
                    matched_st = st_name

        reg = REGION_MAPPING.get(matched_st, "Central India")
        new_states.append(matched_st)
        new_regions.append(reg)

    grid_df["state"] = new_states
    grid_df["region"] = new_regions

    grid_df.to_csv(GRID_ENRICHED_FILE, index=False)
    print(f"Updated {GRID_ENRICHED_FILE.name} successfully.")
    print("State breakdown:")
    print(grid_df["state"].value_counts())

    # Sync state & region into GeoJSON files
    for geojson_path in [GRID_GEOJSON_DATA, GRID_GEOJSON_FRONTEND]:
        if geojson_path.exists():
            with open(geojson_path, "r", encoding="utf-8") as f:
                gdata = json.load(f)

            meta_map = {
                r["cell_id"]: {"state": r["state"], "region": r["region"]}
                for _, r in grid_df.iterrows()
            }

            for feat in gdata.get("features", []):
                cid = feat.get("properties", {}).get("cell_id")
                if cid in meta_map:
                    feat["properties"]["state"] = meta_map[cid]["state"]
                    feat["properties"]["region"] = meta_map[cid]["region"]

            with open(geojson_path, "w", encoding="utf-8") as f:
                json.dump(gdata, f)
            print(f"Updated properties in {geojson_path.name}")


if __name__ == "__main__":
    main()
