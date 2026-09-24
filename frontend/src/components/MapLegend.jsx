const levels = [
  { label: "< 5 mm", color: "#dcfce7" },
  { label: "5–20 mm", color: "#86efac" },
  { label: "20–50 mm", color: "#fde047" },
  { label: "50–100 mm", color: "#fb923c" },
  { label: "> 100 mm", color: "#ef4444" },
];

export default function MapLegend() {
  return (
    <div className="absolute bottom-4 left-4 z-[1000] rounded-xl bg-white p-4 shadow-lg">
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