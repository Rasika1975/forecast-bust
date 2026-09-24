export default function GridInfoPanel({ cell, leadDay }) {
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
            Latitude
          </span>

          <span className="font-semibold">
            {Number(cell.latitude).toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Longitude
          </span>

          <span className="font-semibold">
            {Number(cell.longitude).toFixed(2)}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Rainfall
          </span>

          <span className="font-semibold text-blue-600">
            {Number(cell.rainfall_mm).toFixed(1)} mm
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Temperature
          </span>

          <span className="font-semibold">
            {Number(cell.temperature_c).toFixed(1)} °C
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Humidity
          </span>

          <span className="font-semibold">
            {Number(cell.humidity_percent).toFixed(1)} %
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">
            Pressure
          </span>

          <span className="font-semibold">
            {Number(cell.pressure_hpa).toFixed(1)} hPa
          </span>
        </div>
      </div>
    </div>
  );
}