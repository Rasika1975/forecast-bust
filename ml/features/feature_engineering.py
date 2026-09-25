import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy import sparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent
GRID_FILE = BASE_DIR / "data" / "grid" / "india_grid_enriched.csv"
THRESHOLDS_FILE = BASE_DIR / "data" / "processed" / "bust_thresholds.csv"

FEATURE_COLUMNS = [
    'lead_day',
    'forecast_rainfall_mm',
    'temperature_c',
    'humidity_percent',
    'pressure_hpa',
    'wind_speed_kmh',
    'latitude',
    'longitude',
    'historical_mae',
    'historical_bias',
    'historical_p90_error',
    'neighbor_mean_rain',
    'neighbor_max_rain',
    'neighbor_std_rain',
    'spatial_gradient',
    'temporal_rain_diff',
    'temporal_pressure_diff',
    'is_heavy_rain_regime',
    'is_cyclonic_convective',
    'rain_to_p90_ratio',
    'convective_gradient'
]


class FeatureEngineer:
    def __init__(self, grid_file=None, thresholds_file=None):
        self.grid_file = grid_file or GRID_FILE
        self.thresholds_file = thresholds_file or THRESHOLDS_FILE
        self._load_metadata()

    def _load_metadata(self):
        self.grid = pd.read_csv(self.grid_file)
        self.thresholds = pd.read_csv(self.thresholds_file)
        self.n_cells = len(self.grid)

        # Precompute spatial neighbor indices using cKDTree
        coords = self.grid[['latitude', 'longitude']].values
        self.tree = cKDTree(coords)
        self.neighbors_idx = self.tree.query_ball_tree(self.tree, r=0.36)
        
        # Build normalized sparse adjacency matrix for instantaneous neighborhood means
        rows = []
        cols = []
        vals = []
        for i, neighs in enumerate(self.neighbors_idx):
            k = len(neighs)
            for j in neighs:
                rows.append(i)
                cols.append(j)
                vals.append(1.0 / k)
        
        self.adj_matrix = sparse.csr_matrix(
            (vals, (rows, cols)),
            shape=(self.n_cells, self.n_cells),
            dtype=np.float32
        )
        self.cell_to_idx = {cid: idx for idx, cid in enumerate(self.grid['cell_id'].values)}

    def compute_spatial_vectorized(self, rain_matrix):
        """
        rain_matrix: (n_cells, n_timesteps)
        Computes neighbor_mean for all cells across all timesteps simultaneously!
        """
        means = self.adj_matrix.dot(rain_matrix) # (n_cells, n_timesteps)
        gradients = np.abs(rain_matrix - means)
        return means, gradients

    def transform_dataframe(self, df):
        """
        Ultra-fast vectorized feature engineering over large historical tables.
        """
        print("  Merging historical threshold baselines...", flush=True)
        thresh_subset = self.thresholds[['cell_id', 'lead_day', 'mae', 'bias', 'p90']].copy()
        thresh_subset.rename(columns={
            'mae': 'historical_mae',
            'bias': 'historical_bias',
            'p90': 'historical_p90_error'
        }, inplace=True)

        merged = df.merge(thresh_subset, on=['cell_id', 'lead_day'], how='left')
        merged['historical_mae'] = merged['historical_mae'].fillna(10.0).astype(np.float32)
        merged['historical_bias'] = merged['historical_bias'].fillna(0.0).astype(np.float32)
        merged['historical_p90_error'] = merged['historical_p90_error'].fillna(20.0).astype(np.float32)

        print("  Computing spatial neighborhood features via sparse matrix projection...", flush=True)
        # Pivot table to (cell_id x group)
        group_col = 'run_group'
        if 'run' in merged.columns:
            merged['run_group'] = merged['run'].astype(str) + "_" + merged['lead_day'].astype(str)
        else:
            merged['run_group'] = merged['lead_day'].astype(str)

        # Map cell_id to index
        merged['cell_idx'] = merged['cell_id'].map(self.cell_to_idx).fillna(0).astype(int)

        # Pivot to 2D array
        pivot_rain = merged.pivot(index='cell_idx', columns='run_group', values='forecast_rainfall_mm').reindex(range(self.n_cells)).fillna(0.0).values
        means_2d, grads_2d = self.compute_spatial_vectorized(pivot_rain)

        # Map back to dataframe
        # Create lookup dataframe
        group_names = merged['run_group'].unique()
        piv_df = pd.DataFrame(means_2d, columns=group_names)
        piv_df['cell_idx'] = range(self.n_cells)
        melted_means = piv_df.melt(id_vars=['cell_idx'], value_name='neighbor_mean_rain', var_name='run_group')

        grad_df = pd.DataFrame(grads_2d, columns=group_names)
        grad_df['cell_idx'] = range(self.n_cells)
        melted_grads = grad_df.melt(id_vars=['cell_idx'], value_name='spatial_gradient', var_name='run_group')

        merged = merged.merge(melted_means, on=['cell_idx', 'run_group'], how='left')
        merged = merged.merge(melted_grads, on=['cell_idx', 'run_group'], how='left')

        # Add proxy for max and std from mean & gradient
        merged['neighbor_max_rain'] = np.round(merged['neighbor_mean_rain'] + 0.6 * merged['spatial_gradient'], 2)
        merged['neighbor_std_rain'] = np.round(0.4 * merged['spatial_gradient'], 2)

        print("  Computing temporal differentials and weather regimes...", flush=True)
        # Sort and compute temporal features
        sort_cols = ['run', 'cell_id', 'lead_day'] if 'run' in merged.columns else ['cell_id', 'lead_day']
        merged.sort_values(sort_cols, inplace=True)

        group_cell = ['run', 'cell_id'] if 'run' in merged.columns else ['cell_id']
        merged['temporal_rain_diff'] = merged.groupby(group_cell)['forecast_rainfall_mm'].diff().fillna(0.0).round(2).astype(np.float32)
        merged['temporal_pressure_diff'] = merged.groupby(group_cell)['pressure_hpa'].diff().fillna(0.0).round(2).astype(np.float32)

        # Weather regime indicators
        merged['is_heavy_rain_regime'] = (merged['forecast_rainfall_mm'] > 30.0).astype(np.int8)
        merged['is_cyclonic_convective'] = ((merged['pressure_hpa'] < 1002.0) & (merged['wind_speed_kmh'] > 22.0)).astype(np.int8)

        # Interactions
        merged['rain_to_p90_ratio'] = np.round(merged['forecast_rainfall_mm'] / (merged['historical_p90_error'] + 1.0), 2).astype(np.float32)
        merged['convective_gradient'] = np.round(merged['spatial_gradient'] * (merged['wind_speed_kmh'] / 15.0), 2).astype(np.float32)

        # Drop temporary columns
        merged.drop(columns=['run_group', 'cell_idx'], errors='ignore', inplace=True)
        return merged
