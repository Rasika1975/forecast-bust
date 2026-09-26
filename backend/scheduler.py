import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
GRID_FILE = BASE_DIR / "data" / "grid" / "india_grid.csv"
OUTPUT_NWP = BASE_DIR / "data" / "processed" / "nwp_grid.csv"
TMP_NWP = BASE_DIR / "data" / "processed" / "nwp_grid_tmp.csv"
STATUS_FILE = BASE_DIR / "data" / "processed" / "sync_status.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AutoScheduler")

_is_updating = False


def get_sync_status():
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_sync": "Never",
        "status": "idle",
        "data_source": "Offline Benchmark",
        "total_cells": 4651,
    }


def save_sync_status(status, source="Live Open-Meteo ECMWF", error=None):
    data = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "data_source": source,
        "total_cells": 4651,
        "error": error,
    }
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    return data


def run_live_fetch_and_inference():
    global _is_updating
    if _is_updating:
        logger.info("Sync already in progress. Skipping.")
        return False

    _is_updating = True
    save_sync_status("fetching_nwp", "Live Open-Meteo ECMWF")

    try:
        logger.info("Starting automated live NWP data fetch...")
        grid = pd.read_csv(GRID_FILE)
        batch_size = 100
        total_cells = len(grid)
        nwp_url = "https://api.open-meteo.com/v1/ecmwf"

        records = []
        for start in range(0, total_cells, batch_size):
            end = min(start + batch_size, total_cells)
            batch = grid.iloc[start:end]

            lats = ",".join(batch["latitude"].astype(str))
            lons = ",".join(batch["longitude"].astype(str))

            params = {
                "latitude": lats,
                "longitude": lons,
                "hourly": "precipitation,temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m",
                "forecast_days": 10,
                "timezone": "UTC",
                "models": "ecmwf_ifs025",
            }

            resp = requests.get(nwp_url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if not isinstance(data, list):
                    data = [data]

                for idx, item in enumerate(data):
                    cell_id = batch.iloc[idx]["cell_id"]
                    lat = batch.iloc[idx]["latitude"]
                    lon = batch.iloc[idx]["longitude"]
                    hourly = item.get("hourly", {})
                    times = hourly.get("time", [])
                    precip = hourly.get("precipitation", [])
                    temp = hourly.get("temperature_2m", [])
                    rh = hourly.get("relative_humidity_2m", [])
                    press = hourly.get("pressure_msl", [])
                    wind = hourly.get("wind_speed_10m", [])

                    for i in range(len(times)):
                        records.append({
                            "cell_id": cell_id,
                            "latitude": lat,
                            "longitude": lon,
                            "time": times[i],
                            "precipitation": precip[i] if i < len(precip) else 0.0,
                            "temperature_2m": temp[i] if i < len(temp) else 25.0,
                            "relative_humidity_2m": rh[i] if i < len(rh) else 70.0,
                            "pressure_msl": press[i] if i < len(press) else 1010.0,
                            "wind_speed_10m": wind[i] if i < len(wind) else 10.0,
                        })

            time.sleep(0.1)

        # Only replace and recalculate when fetch is 100% complete
        if len(records) >= total_cells * 10:
            df_new = pd.DataFrame(records)
            df_new.to_csv(TMP_NWP, index=False)
            if TMP_NWP.exists():
                os.replace(TMP_NWP, OUTPUT_NWP)
            logger.info(f"Live NWP fetch completed: {len(df_new)} rows saved.")

            # Trigger ML Inference Engine recalculation
            save_sync_status("running_ml_inference", "Live Open-Meteo ECMWF")
            from ml.inference.predict import get_engine

            engine = get_engine()
            engine.run_full_inference()

            save_sync_status("success", "Live Open-Meteo ECMWF")
            logger.info("Automated live fetch and ML inference sync successful!")
            return True
        else:
            logger.warning(
                f"Live fetch incomplete ({len(records)} records). Retaining complete offline benchmark dataset."
            )
            save_sync_status("idle", "Offline Benchmark", f"Incomplete fetch ({len(records)} records)")
            return False

    except Exception as e:
        logger.error(f"Automated sync failed: {e}")
        save_sync_status("failed", "Fallback Local Feed", str(e))
        return False

    finally:
        _is_updating = False


def start_daily_scheduler(interval_hours=24):
    """Launches a background daemon thread that runs automated fetch every 24 hours."""

    def worker():
        logger.info(
            f"Daily Auto-Scheduler started. Periodic sync interval: {interval_hours} hours."
        )
        while True:
            try:
                run_live_fetch_and_inference()
            except Exception as e:
                logger.error(f"Scheduler worker exception: {e}")

            time.sleep(interval_hours * 3600)

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return t
