from pathlib import Path
import xarray as xr

BASE_DIR = Path(__file__).resolve().parent.parent

FILE = BASE_DIR / "data" / "imd" / "rainfall_2024.nc"

ds = xr.open_dataset(FILE)

print("\n========== DATASET ==========\n")
print(ds)

print("\n========== DIMENSIONS ==========\n")
print(ds.dims)

print("\n========== COORDINATES ==========\n")
print(list(ds.coords))

print("\n========== VARIABLES ==========\n")
print(list(ds.data_vars))