import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Flush stdout immediately
sys.stdout.reconfigure(line_buffering=True)

BASE_DIR = Path(__file__).resolve().parent.parent
GRID_FILE = BASE_DIR / "data" / "grid" / "india_grid_enriched.csv"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("Loading grid...", flush=True)
grid = pd.read_csv(GRID_FILE)
n_cells = len(grid)
print(f"Grid loaded: {n_cells} cells", flush=True)

# Profile lookup mapping
CLIMATE_PROFILES = {
    'Western Ghats': (45.0, 35.0, 25.0, 88.0, 1006.0, 24.0),
    'North-East': (40.0, 30.0, 26.0, 85.0, 1004.0, 16.0),
    'Konkan & Western Coast': (38.0, 30.0, 27.5, 84.0, 1005.0, 22.0),
    'Eastern Coastal': (22.0, 20.0, 29.0, 82.0, 1004.0, 20.0),
    'Central India': (18.0, 16.0, 29.5, 76.0, 1003.0, 15.0),
    'Deccan Plateau': (14.0, 14.0, 28.0, 72.0, 1007.0, 17.0),
    'Northern Plains': (12.0, 14.0, 31.0, 68.0, 1002.0, 13.0),
    'Southern Coastal': (10.0, 12.0, 29.0, 78.0, 1008.0, 18.0),
    'Northern Himalayas': (15.0, 18.0, 17.0, 74.0, 980.0, 12.0),
    'Northwest Arid': (4.0, 8.0, 34.0, 48.0, 1001.0, 18.0),
}

# Pre-extract numpy vectors for all cells
cell_ids = grid['cell_id'].values
lats = grid['latitude'].values
lons = grid['longitude'].values
regions = grid['region'].values
states = grid['state'].values

prof_rain_mean = np.array([CLIMATE_PROFILES[r][0] for r in regions], dtype=np.float32)
prof_rain_std  = np.array([CLIMATE_PROFILES[r][1] for r in regions], dtype=np.float32)
prof_temp      = np.array([CLIMATE_PROFILES[r][2] for r in regions], dtype=np.float32)
prof_rh        = np.array([CLIMATE_PROFILES[r][3] for r in regions], dtype=np.float32)
prof_press     = np.array([CLIMATE_PROFILES[r][4] for r in regions], dtype=np.float32)
prof_wind      = np.array([CLIMATE_PROFILES[r][5] for r in regions], dtype=np.float32)

spatial_pattern = (np.sin(lats * 1.5) * np.cos(lons * 1.2)).astype(np.float32)

# 1. GENERATE HISTORICAL RUNS
print("\n[1/5] Vectorized generation of historical forecast-observation pairs...", flush=True)
np.random.seed(42)

historical_runs = [
    "2024-06-15T00:00", "2024-06-25T00:00", "2024-07-05T00:00", "2024-07-15T00:00",
    "2024-07-25T00:00", "2024-08-04T00:00", "2024-08-14T00:00", "2024-08-24T00:00",
    "2024-09-03T00:00", "2024-09-13T00:00", "2025-06-20T00:00", "2025-07-10T00:00"
]

all_dfs = []
for run_idx, run in enumerate(historical_runs):
    run_date = pd.to_datetime(run)
    synoptic_pulse = 1.0 + 0.5 * np.sin(run_idx * 1.3)
    
    for lead_day in range(1, 11):
        valid_date = (run_date + pd.Timedelta(days=lead_day)).strftime("%Y-%m-%d")
        
        # Base rain across all cells
        base_rain = np.maximum(0.0, prof_rain_mean * synoptic_pulse + prof_rain_std * 0.4 * spatial_pattern)
        
        # Forecast rain: gamma distribution with shape 2
        fcst_rain = np.random.gamma(shape=1.5, scale=np.maximum(base_rain / 1.5, 0.4), size=n_cells).astype(np.float32)
        
        # Atmospheric variables
        temp = prof_temp - 0.04 * fcst_rain + np.random.normal(0, 0.8, size=n_cells).astype(np.float32)
        rh = np.clip(prof_rh + 0.18 * fcst_rain + np.random.normal(0, 1.5, size=n_cells), 20.0, 99.0).astype(np.float32)
        press = prof_press - 0.08 * fcst_rain + np.random.normal(0, 0.5, size=n_cells).astype(np.float32)
        wind = prof_wind + 0.12 * fcst_rain + np.random.normal(0, 1.5, size=n_cells).astype(np.float32)
        
        # Observation simulation with lead-dependent error & 10% bust events
        is_bust = np.random.rand(n_cells) < (0.07 + 0.006 * lead_day)
        normal_noise = np.random.normal(0, (1.8 + 1.1 * lead_day) * (1.0 + 0.02 * base_rain), size=n_cells).astype(np.float32)
        
        obs_rain = np.maximum(0.0, fcst_rain + normal_noise)
        
        # Where bust occurred, apply large discrepancy
        high_fcst_mask = is_bust & (fcst_rain > 15.0)
        obs_rain[high_fcst_mask] = fcst_rain[high_fcst_mask] * np.random.uniform(0.05, 0.25, size=np.sum(high_fcst_mask))
        
        low_fcst_mask = is_bust & (~high_fcst_mask)
        obs_rain[low_fcst_mask] = fcst_rain[low_fcst_mask] + np.random.uniform(35.0, 95.0, size=np.sum(low_fcst_mask)) * (1.0 + 0.08 * lead_day)
        
        abs_err = np.abs(fcst_rain - obs_rain)
        bias = fcst_rain - obs_rain
        
        batch_df = pd.DataFrame({
            'run_id': f"RUN_{run_idx:02d}",
            'run': run,
            'lead_day': np.int8(lead_day),
            'valid_date': valid_date,
            'cell_id': cell_ids,
            'latitude': lats,
            'longitude': lons,
            'region': regions,
            'state': states,
            'forecast_rainfall_mm': np.round(fcst_rain, 1),
            'temperature_c': np.round(temp, 1),
            'humidity_percent': np.round(rh, 1),
            'pressure_hpa': np.round(press, 1),
            'wind_speed_kmh': np.round(wind, 1),
            'actual_rainfall': np.round(obs_rain, 1),
            'forecast_error_mm': np.round(abs_err, 1),
            'bias_mm': np.round(bias, 1)
        })
        all_dfs.append(batch_df)

df_hist = pd.concat(all_dfs, ignore_index=True)
print(f"Generated {len(df_hist)} historical records.", flush=True)
df_hist.to_csv(PROCESSED_DIR / "forecast_error.csv", index=False)
print("Saved forecast_error.csv", flush=True)

# 2. CALCULATE P80, P90, P95, MAE, BIAS PER CELL AND LEAD DAY
print("\n[2/5] Calculating historical bust thresholds (P90) and error statistics...", flush=True)
stats = df_hist.groupby(['cell_id', 'lead_day']).agg(
    mae=('forecast_error_mm', 'mean'),
    bias=('bias_mm', 'mean'),
    p80=('forecast_error_mm', lambda x: np.percentile(x, 80)),
    p90=('forecast_error_mm', lambda x: np.percentile(x, 90)),
    p95=('forecast_error_mm', lambda x: np.percentile(x, 95)),
    sample_count=('forecast_error_mm', 'count')
).reset_index()

# Add coordinates & region
cell_meta = grid[['cell_id', 'latitude', 'longitude', 'region', 'state']]
df_thresholds = stats.merge(cell_meta, on='cell_id', how='left')
df_thresholds = df_thresholds.round({
    'mae': 2, 'bias': 2, 'p80': 2, 'p90': 2, 'p95': 2
})
df_thresholds.to_csv(PROCESSED_DIR / "bust_thresholds.csv", index=False)
print(f"Saved bust_thresholds.csv for {len(df_thresholds)} cell-lead combinations.", flush=True)
print("Mean P90 error threshold by lead day:", flush=True)
print(df_thresholds.groupby('lead_day')[['mae', 'p90', 'p95']].mean(), flush=True)

# 3. LABEL HISTORICAL RUNS
print("\n[3/5] Assigning bust labels...", flush=True)
df_merged = df_hist.merge(
    df_thresholds[['cell_id', 'lead_day', 'p90', 'mae', 'bias']],
    on=['cell_id', 'lead_day'],
    how='left'
)
df_merged['bust_label'] = (df_merged['forecast_error_mm'] > df_merged['p90']).astype(np.int8)
bust_rate = df_merged['bust_label'].mean()
print(f"Bust rate in labeled dataset: {bust_rate:.4f} (target ~10%)", flush=True)
df_merged.to_csv(PROCESSED_DIR / "bust_labels.csv", index=False)
print("Saved bust_labels.csv", flush=True)

# 4. GENERATE OPERATIONAL 10-DAY FORECAST FOR ACTIVE RUN
print("\n[4/5] Generating operational 10-day ECMWF forecast (nwp_grid.csv)...", flush=True)
init_time = pd.to_datetime("2026-09-24 00:00:00")
nwp_list = []

for day_idx in range(10):
    day_date = init_time + pd.Timedelta(days=day_idx)
    lead_day = day_idx + 1
    
    # Synoptic system track: Monsoonal depression over Bay of Bengal moving NW
    sys_lat = 19.5 + 0.35 * day_idx
    sys_lon = 84.5 - 0.75 * day_idx
    dist_to_sys = np.sqrt((lats - sys_lat)**2 + (lons - sys_lon)**2)
    sys_influence = np.exp(-0.5 * (dist_to_sys / 3.2)**2).astype(np.float32)
    
    is_ghats = np.isin(regions, ['Western Ghats', 'Konkan & Western Coast'])
    ghats_rain = np.where(is_ghats, (38.0 + 32.0 * np.sin(lats * 0.8)), 0.0).astype(np.float32)
    
    precip = np.maximum(0.0, prof_rain_mean * 0.5 + sys_influence * 90.0 + ghats_rain + np.random.exponential(scale=2.0, size=n_cells)).astype(np.float32)
    temp = (prof_temp - sys_influence * 4.5 + np.random.normal(0, 0.7, size=n_cells)).astype(np.float32)
    rh = np.clip(prof_rh + sys_influence * 18.0 + np.random.normal(0, 1.8, size=n_cells), 20.0, 99.0).astype(np.float32)
    press = (prof_press - sys_influence * 12.0 + np.random.normal(0, 0.5, size=n_cells)).astype(np.float32)
    wind = (prof_wind + sys_influence * 28.0 + np.random.normal(0, 2.0, size=n_cells)).astype(np.float32)
    
    # 4 time steps per day (00, 06, 12, 18 UTC)
    for h in [0, 6, 12, 18]:
        hour_time = day_date + pd.Timedelta(hours=h)
        nwp_df = pd.DataFrame({
            'cell_id': cell_ids,
            'latitude': lats,
            'longitude': lons,
            'time': hour_time.strftime("%Y-%m-%d %H:%M:%S"),
            'precipitation': np.round(precip / 4.0, 2),
            'temperature_2m': np.round(temp, 1),
            'relative_humidity_2m': np.round(rh, 1),
            'pressure_msl': np.round(press, 1),
            'wind_speed_10m': np.round(wind, 1)
        })
        nwp_list.append(nwp_df)

full_nwp_df = pd.concat(nwp_list, ignore_index=True)
full_nwp_df.to_csv(PROCESSED_DIR / "nwp_grid.csv", index=False)
print(f"Saved operational nwp_grid.csv with {len(full_nwp_df)} rows.", flush=True)

print("\n[5/5] All foundation datasets created successfully!", flush=True)
