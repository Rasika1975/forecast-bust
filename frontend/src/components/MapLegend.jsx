const levels = [
  { label: "< 5 mm", color: "#dcfce7" },
  { label: "5–20 mm", color: "#86efac" },
  { label: "20–50 mm", color: "#fde047" },
  { label: "50–100 mm", color: "#fb923c" },
  { label: "> 100 mm", color: "#ef4444" },
];

const mapLayers = [
  { label: "Rainfall Forecast", active: true },
  { label: "Bust Risk", active: false },
  { label: "Confidence", active: false },
];

export default function MapLegend() {
  return (
    <div className="absolute bottom-4 left-4 z-1000 rounded-xl bg-white p-4 shadow-lg">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
        Map layers
      </p>

      <div className="mb-4 space-y-1 border-b border-slate-200 pb-3">
        {mapLayers.map((layer) => (
          <div
            key={layer.label}
            className={`flex items-center justify-between gap-4 text-xs ${layer.active ? "font-semibold text-slate-800" : "text-slate-400"}`}
          >
            <span>{layer.label}</span>
            <span>{layer.active ? "Active" : "Unavailable"}</span>
          </div>
        ))}
      </div>

      <p className="mb-2 text-sm font-bold text-slate-800">
        Forecast Rainfall
      </p>

      <div className="space-y-2">
        {levels.map((level) => (
          <div
            key={level.label}
            className="flex items-center gap-2 text-xs text-slate-600"
          >
            <span
              className="h-4 w-4 rounded"
              style={{ backgroundColor: level.color }}
            />
            {level.label}
          </div>
        ))}
      </div>
    </div>
  );
}