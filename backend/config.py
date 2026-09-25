from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
NWP_FILE = BASE_DIR / "data" / "processed" / "nwp_grid.csv"

API_TITLE = "Forecast Guard API"
API_DESCRIPTION = "PS 26079 - AI Forecast Bust Detection"
API_VERSION = "1.0.0"
CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)
TOTAL_INDIA_GRID_CELLS = 4651
GRID_RESOLUTION = "0.25 degree"
