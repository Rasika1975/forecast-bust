const riskLevels = [
  { label: "0% – 20% (Very Low Risk / 80-100% Confidence)", color: "#10b981", badge: "High Confidence" },
  { label: "20% – 40% (Low Risk / 60-80% Confidence)", color: "#84cc16", badge: "Moderate High" },
  { label: "40% – 60% (Moderate Risk / 40-60% Confidence)", color: "#f59e0b", badge: "Caution" },
  { label: "60% – 80% (High Risk / 20-40% Confidence)", color: "#f97316", badge: "Elevated Danger" },
  { label: "80% – 100% (Very High Risk / 0-20% Confidence)", color: "#ef4444", badge: "Bust Alert" },
];

const rainLevels = [
  { label: "< 5 mm (Trace / Dry)", color: "#dcfce7" },
  { label: "5 – 20 mm (Light Rain)", color: "#86efac" },
  { label: "20 – 50 mm (Moderate Rain)", color: "#fde047" },
  { label: "50 – 100 mm (Heavy Rain)", color: "#fb923c" },
  { label: "> 100 mm (Extreme Rain)", color: "#ef4444" },
];

export default function MapLegend({ viewMode = "risk" }) {
  const isRiskMode = viewMode === "risk";
  const levels = isRiskMode ? riskLevels : rainLevels;

  return (
    <div className="absolute bottom-4 left-4 z-[1000] rounded-xl bg-white/95 backdrop-blur p-4 shadow-lg border border-slate-200">
      <p className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-700">
        {isRiskMode ? "Bust Risk & Confidence" : "Forecast Precipitation"}
      </p>

      <div className="space-y-2">
        {levels.map((level) => (
          <div
            key={level.label}
            className="flex items-center gap-2 text-xs text-slate-600"
          >
            <span
              className="h-3.5 w-3.5 rounded shadow-sm shrink-0 border border-black/10"
              style={{ backgroundColor: level.color }}
            />
            <span className="truncate font-medium">{level.label}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 pt-2 border-t border-slate-100 text-[11px] text-slate-400">
        {isRiskMode ? (
          <p>Confidence = 1 - P(Bust). Calibrated P90 error threshold per cell.</p>
        ) : (
          <p>ECMWF IFS 0.25° 24-hr cumulative surface precipitation.</p>
        )}
      </div>
    </div>
  );
}