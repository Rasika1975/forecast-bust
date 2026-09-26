import { useEffect, useState } from "react";

import IndiaMap from "./components/IndiaMap";
import DaySelector from "./components/DaySelector";
import GridInfoPanel from "./components/GridInfoPanel";
import VerificationModal from "./components/VerificationModal";

import { getForecastMap, getDaySummary, getSyncStatus, triggerSync } from "./services/api";

const TOTAL_INDIA_GRID_CELLS = 4651;

function App() {
  const [leadDay, setLeadDay] = useState(1);
  const [hazard, setHazard] = useState("rain"); // "rain" | "temp" | "wind"
  const [forecast, setForecast] = useState(null);
  const [summary, setSummary] = useState(null);
  const [syncInfo, setSyncInfo] = useState(null);

  const [cells, setCells] = useState([]);
  const [selectedCell, setSelectedCell] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  // Controls & Filters
  const [viewMode, setViewMode] = useState("risk"); // "risk" | "rainfall"
  const [riskFilter, setRiskFilter] = useState("all"); // "all" | "high_risk" | "moderate_plus"
  const [regionFilter, setRegionFilter] = useState("all");
  const [showVerificationModal, setShowVerificationModal] = useState(false);

  async function loadForecast(day, hazardMode = hazard) {
    try {
      setLoading(true);
      setError(null);

      const [mapData, summaryData, statusData] = await Promise.all([
        getForecastMap(day, hazardMode),
        getDaySummary(day, hazardMode).catch(() => null),
        getSyncStatus().catch(() => null),
      ]);

      setForecast(mapData);
      setCells(mapData.cells || []);
      setSummary(summaryData);
      if (statusData) setSyncInfo(statusData);
      setSelectedCell(null);
    } catch (err) {
      console.error("Forecast load error:", err);
      setError(
        `Failed to connect to backend server (${err.message}). Ensure FastAPI is running on http://127.0.0.1:8000`
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleAutoSync() {
    try {
      setSyncing(true);
      await triggerSync();
      // Poll sync status after 4 seconds
      setTimeout(() => {
        loadForecast(leadDay, hazard);
        setSyncing(false);
      }, 4000);
    } catch (err) {
      console.error("Sync trigger error:", err);
      setSyncing(false);
    }
  }

  useEffect(() => {
    loadForecast(leadDay, hazard);
  }, [leadDay, hazard]);

  return (
    <div className="min-h-screen bg-slate-100 font-sans text-slate-800">
      {/* HEADER */}
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto max-w-[1600px] px-6 py-4">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700">
                  PS 26079
                </span>
                <span className="text-xs font-semibold text-slate-400">
                  Operational Reliability Layer
                </span>
                <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Auto-Sync Active (24h)
                </span>
              </div>
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight mt-1">
                Forecast Guard AI
              </h1>
              <p className="text-xs text-slate-500">
                Multi-Hazard Weather Forecast Bust Detection (ECMWF IFS 0.25° Grid)
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleAutoSync}
                disabled={syncing}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-100 transition cursor-pointer disabled:opacity-60"
              >
                {syncing ? "🔄 Syncing Live NWP..." : "🔄 Refresh Live NWP Feed"}
              </button>

              <button
                onClick={() => setShowVerificationModal(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-slate-800 transition cursor-pointer"
              >
                📊 Multi-Hazard Metrics (Sec 19)
              </button>

              {forecast && (
                <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-right text-xs">
                  <p className="text-slate-400">NWP Run Init</p>
                  <p className="font-bold text-slate-800">{forecast.forecast_start || "2026-09-24 00:00 Z"}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* MAIN */}
      <main className="mx-auto max-w-[1600px] space-y-5 px-6 py-6">
        {/* TOP CONTROLS & KPI BAR */}
        <section className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200 space-y-4">
          {/* HAZARD SELECTOR ROW */}
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Multi-Hazard Target Selector
              </h2>
              <p className="text-xs text-slate-500">
                Select hazard domain to evaluate dedicated XGBoost bust prediction models.
              </p>
            </div>

            <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl shrink-0">
              <button
                onClick={() => setHazard("rain")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                  hazard === "rain"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                🌧️ Heavy Rain Busts
              </button>
              <button
                onClick={() => setHazard("temp")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                  hazard === "temp"
                    ? "bg-white text-amber-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                🌡️ Heatwave Temp Busts
              </button>
              <button
                onClick={() => setHazard("wind")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                  hazard === "wind"
                    ? "bg-white text-teal-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                💨 Windstorm Busts
              </button>
            </div>
          </div>

          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Forecast Horizon Selector
              </h2>
              <p className="text-xs text-slate-500">
                Select target lead day (Day 1 to 10) to evaluate calibrated bust probabilities.
              </p>
            </div>

            {/* VIEW MODE TOGGLE */}
            <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl shrink-0">
              <button
                onClick={() => setViewMode("risk")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                  viewMode === "risk"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                🛡️ Bust Risk & Confidence
              </button>
              <button
                onClick={() => setViewMode("rainfall")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                  viewMode === "rainfall"
                    ? "bg-white text-blue-600 shadow-sm"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {hazard === "temp" ? "🌡️ Temperature Field" : hazard === "wind" ? "💨 Wind Speed Field" : "🌧️ Precipitation Forecast"}
              </button>
            </div>
          </div>

          <DaySelector
            selectedDay={leadDay}
            onChange={setLeadDay}
            forecastStart={forecast?.forecast_start}
          />

          {/* QUICK FILTERS */}
          <div className="flex flex-wrap items-center gap-4 text-xs pt-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-500">Risk Filter:</span>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 font-medium text-slate-700 outline-none focus:border-blue-500 cursor-pointer"
              >
                <option value="all">All Cells (4,651)</option>
                <option value="high_risk">High & Very High Risk</option>
                <option value="moderate_plus">Moderate Risk & Above</option>
                <option value="very_high">Very High Risk Only</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-500">Region Filter:</span>
              <select
                value={regionFilter}
                onChange={(e) => setRegionFilter(e.target.value)}
                className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 font-medium text-slate-700 outline-none focus:border-blue-500 cursor-pointer"
              >
                <option value="all">All Sub-Regions</option>
                <option value="Western Ghats">Western Ghats</option>
                <option value="North-East">North-East</option>
                <option value="Central India">Central India</option>
                <option value="Northern Plains">Northern Plains</option>
                <option value="Deccan Plateau">Deccan Plateau</option>
                <option value="Eastern Coastal">Eastern Coastal</option>
                <option value="Northwest Arid">Northwest Arid</option>
              </select>
            </div>

            {summary && (
              <div className="ml-auto flex items-center gap-4 text-xs border-l border-slate-200 pl-4 hidden md:flex">
                <div>
                  <span className="text-slate-400">High Risk Cells ({hazard.toUpperCase()}): </span>
                  <strong className="text-amber-600 font-bold">{summary.high_risk_cells} ({summary.high_risk_percentage}%)</strong>
                </div>
                <div>
                  <span className="text-slate-400">Domain Confidence: </span>
                  <strong className="text-emerald-600 font-bold">{summary.average_confidence}%</strong>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* ERROR MESSAGE */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-medium text-red-700 shadow-sm flex items-center justify-between">
            <span>❌ {error}</span>
            <button
              onClick={() => loadForecast(leadDay)}
              className="px-3 py-1 bg-red-600 text-white rounded-lg font-bold text-xs hover:bg-red-700 cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* MAIN DASHBOARD CONTENT GRID */}
        <section className="grid gap-5 lg:grid-cols-[1fr_360px]">
          {/* MAP DISPLAY */}
          <div className="relative overflow-hidden rounded-2xl bg-white shadow-sm border border-slate-200 min-h-[650px]">
            <div className="h-[650px] w-full min-h-[650px]">
              {loading ? (
                <div className="flex h-full min-h-[650px] items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />
                    <p className="text-xs font-semibold text-slate-500">
                      Loading calibrated XGBoost predictions...
                    </p>
                  </div>
                </div>
              ) : (
                <IndiaMap
                  cells={cells}
                  selectedCell={selectedCell}
                  onCellSelect={setSelectedCell}
                  viewMode={viewMode}
                  riskFilter={riskFilter}
                  regionFilter={regionFilter}
                />
              )}
            </div>
          </div>

          {/* DRILLDOWN SIDE PANEL */}
          <div className="space-y-5">
            <GridInfoPanel
              cell={selectedCell}
              leadDay={leadDay}
              validDate={forecast?.valid_date}
              hazard={hazard}
            />

            {/* DOMAIN SUMMARY CARD */}
            <div className="rounded-2xl bg-white p-5 shadow-sm border border-slate-200 space-y-3">
              <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Operational Summary • Day {leadDay}
              </p>
              <h2 className="text-base font-bold text-slate-900">
                Valid Date: {forecast?.valid_date || "2026-09-24"}
              </h2>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Total Grid Cells</span>
                  <span className="font-semibold text-slate-900">{TOTAL_INDIA_GRID_CELLS}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Spatial Resolution</span>
                  <span className="font-semibold text-slate-800">0.25° (~27 km)</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-500">Data Feed</span>
                  <span className="font-semibold text-emerald-600">{syncInfo?.data_source || "Open-Meteo ECMWF"}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-500">Mean Domain Confidence</span>
                  <span className="font-semibold text-emerald-600">{summary?.average_confidence ? `${summary.average_confidence}%` : "Calculated"}</span>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* MODEL VERIFICATION MODAL */}
      <VerificationModal
        isOpen={showVerificationModal}
        onClose={() => setShowVerificationModal(false)}
      />
    </div>
  );
}

export default App;
