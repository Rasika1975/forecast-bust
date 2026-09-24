import numpy as np
import geopandas as gpd
from shapely.geometry import Point, box

# --------------------------------------------------
# IMD-style 0.25° grid
# --------------------------------------------------

LAT_MIN = 6.5
LAT_MAX = 38.5

LON_MIN = 66.5
LON_MAX = 100.0

STEP = 0.25

# Load India boundary
india = gpd.read_file("data/boundaries/india.geojson")

# Convert to geographic coordinates
india = india.to_crs("EPSG:4326")

# Merge all boundary pieces
india_shape = india.geometry.union_all()

records = []

latitudes = np.arange(
    LAT_MIN,
    LAT_MAX + STEP / 2,
    STEP
)

longitudes = np.arange(
    LON_MIN,
    LON_MAX + STEP / 2,
    STEP
)

cell_id = 0

for lat in latitudes:
    for lon in longitudes:

        # Grid point
        point = Point(lon, lat)

        # Only keep points inside India
        if not india_shape.contains(point):
            continue

        # Create visual grid-cell polygon around the point
        half = STEP / 2

        cell_polygon = box(
            lon - half,
            lat - half,
            lon + half,
            lat + half
        )

        # Clip cell to India boundary
        clipped = cell_polygon.intersection(india_shape)

        if clipped.is_empty:
            continue

        records.append({
            "cell_id": f"CELL_{cell_id:05d}",
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "geometry": clipped
        })

        cell_id += 1


grid = gpd.GeoDataFrame(
    records,
    crs="EPSG:4326"
)

# Save GeoJSON
grid.to_file(
    "data/grid/india_grid.geojson",
    driver="GeoJSON"
)

# Also save CSV for ML/backend use
grid.drop(columns="geometry").to_csv(
    "data/grid/india_grid.csv",
    index=False
)

print("Grid created successfully")
print("Number of grid cells:", len(grid))
print(grid.head())