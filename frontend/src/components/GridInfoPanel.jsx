function formatValue(value, digits = 2) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toFixed(digits) : "N/A";
}

function getCellValue(cell, key, digits = 2, suffix = "") {
  if (cell?.forecast_unavailable || cell == null || !Object.prototype.hasOwnProperty.call(cell, key) || !Number.isFinite(Number(cell[key]))) {
    return "Forecast unavailable";
  }

  const value = Number(cell[key]);
  return `${value.toFixed(digits)}${suffix}`;
}

export default function GridInfoPanel({ cell, leadDay, validDate }) {
  if (!cell) {
    return (
      <div className="rounded-2xl bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          Grid Details
        </h2>

        <p className="mt-3 text-sm text-slate-500">
          Click any forecast grid cell on the map.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white p-6 shadow-sm">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-wide text-slate-400">
          Selected Grid
        </p>

        <h2 className="text-xl font-bold text-slate-900">
          {cell.cell_id}
        </h2>
      </div>

      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-slate-500">
            Lead Day
          </span>

          <span className="font-semibold">
            Day {leadDay}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Valid Date
          </span>

          <span className="font-semibold">
            {validDate || "Forecast unavailable"}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            State
          </span>

          <span className="max-w-[170px] text-right font-semibold">
            {cell.state_name || "Forecast unavailable"}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Region
          </span>

          <span className="max-w-[170px] text-right font-semibold">
            {cell.region || "Forecast unavailable"}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Latitude
          </span>

          <span className="font-semibold">
            {cell.latitude != null ? formatValue(cell.latitude) : "Forecast unavailable"}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Longitude
          </span>

          <span className="font-semibold">
            {cell.longitude != null ? formatValue(cell.longitude) : "Forecast unavailable"}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Rainfall
          </span>

          <span className="font-semibold text-blue-600">
            {getCellValue(cell, "rainfall_mm", 1, " mm")}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Temperature
          </span>

          <span className="font-semibold">
            {getCellValue(cell, "temperature_c", 1, " °C")}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Humidity
          </span>

          <span className="font-semibold">
            {getCellValue(cell, "humidity_percent", 1, " %")}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Pressure
          </span>

          <span className="font-semibold">
            {getCellValue(cell, "pressure_hpa", 1, " hPa")}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Wind Speed
          </span>

          <span className="font-semibold">
            {getCellValue(cell, "wind_speed_kmh", 1, " km/h")}
          </span>
        </div>
      </div>
    </div>
  );
}