import { useEffect, useState } from "react";
import "./App.css";

import IndiaMap from "./components/IndiaMap";
import DaySelector from "./components/DaySelector";
import GridInfoPanel from "./components/GridInfoPanel";
import MapLegend from "./components/MapLegend";
import {
  AnalyticsGrid,
  InsightPanel,
  MetricCard,
  StatusBanner,
} from "./components/DashboardWidgets";
import { getForecastMap } from "./services/api";

const TOTAL_INDIA_GRID_CELLS = 4651;

function App() {
  const [leadDay, setLeadDay] = useState(1);
  const [forecast, setForecast] = useState(null);
  const [cells, setCells] = useState([]);
  const [selectedCell, setSelectedCell] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadForecast() {
      try {
        setLoading(true);
        setError(null);

        const data = await getForecastMap(leadDay);
        if (cancelled) return;

        setForecast(data);
        setCells(data.cells || []);
        setSelectedCell(null);
      } catch (requestError) {
        if (cancelled) return;

        console.error(requestError);
        setForecast(null);
        setCells([]);
        setSelectedCell(null);
        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load forecast data."
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadForecast();

    return () => {
      cancelled = true;
    };
  }, [leadDay]);

  const availableCells = forecast?.forecast_data_available ?? cells.length;

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">FG</div>
          <div>
            <p className="brand-name">ForecastGuard <span>AI</span></p>
            <p className="brand-subtitle">AI forecast bust detection for India</p>
          </div>
        </div>

        <div className="topbar-meta">
          <div>
            <span className="eyebrow">NWP run</span>
            <strong>Forecast API</strong>
          </div>
          <div>
            <span className="eyebrow">Horizon</span>
            <strong>Day {leadDay} / 10</strong>
          </div>
          <div>
            <span className="eyebrow">Valid date</span>
            <strong>{forecast?.valid_date || "--"}</strong>
          </div>
        </div>
      </header>

      <main className="dashboard-content">
        <StatusBanner loading={loading} error={error} forecast={forecast} />

        <section className="intro-row">
          <div>
            <p className="eyebrow accent-label">Operational view / India</p>
            <h1>Forecast Guard</h1>
            <p className="intro-copy">
              Inspect daily rainfall guidance across the India forecast grid.
              Model-derived reliability signals will appear when the ML service is connected.
            </p>
          </div>
          <div className="run-stamp">
            <span className="eyebrow">Forecast start</span>
            <strong>{forecast?.forecast_start || "--"}</strong>
            <span>{forecast?.grid_resolution || "Awaiting data"}</span>
          </div>
        </section>

        <section className="metric-grid" aria-label="Forecast summary">
          <MetricCard
            label="Lead time"
            value={`Day ${leadDay}`}
            detail={forecast?.valid_date ? `Valid ${forecast.valid_date}` : "Awaiting forecast"}
            accent="cyan"
          />
          <MetricCard
            label="Grid coverage"
            value={availableCells.toLocaleString()}
            detail={`of ${TOTAL_INDIA_GRID_CELLS.toLocaleString()} India cells`}
            accent="green"
          />
          <MetricCard
            label="Resolution"
            value={forecast?.grid_resolution || "--"}
            detail="Forecast grid spacing"
            accent="amber"
          />
          <MetricCard
            label="ML reliability"
            value="Unavailable"
            detail="ML model not available yet"
            accent="red"
          />
        </section>

        <section className="dashboard-panel day-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Forecast horizon</p>
              <h2>Lead day selector</h2>
            </div>
            <span className="panel-meta">1-10 days</span>
          </div>
          <DaySelector selectedDay={leadDay} onChange={setLeadDay} disabled={loading} />
        </section>

        <section className="map-layout">
          <article className="dashboard-panel map-panel">
            <div className="panel-heading map-heading">
              <div>
                <p className="eyebrow">Live NWP field</p>
                <h2>India rainfall forecast</h2>
              </div>
              <span className="panel-meta">Day {leadDay}</span>
            </div>
            <div className="map-frame">
              {loading ? (
                <div className="map-state">
                  <span className="loader" aria-hidden="true" />
                  <strong>Loading forecast field</strong>
                  <p>Fetching real data for Day {leadDay}.</p>
                </div>
              ) : error ? (
                <div className="map-state map-state-error">
                  <strong>Forecast field unavailable</strong>
                  <p>{error}</p>
                </div>
              ) : (
                <>
                  <IndiaMap cells={cells} onCellSelect={setSelectedCell} />
                  <MapLegend />
                </>
              )}
            </div>
          </article>

          <GridInfoPanel
            cell={selectedCell}
            leadDay={leadDay}
            validDate={forecast?.valid_date}
          />
        </section>

        <AnalyticsGrid />

        <section className="lower-grid">
          <InsightPanel title="Error-prone regions">
            Region-level error history and bust risk are not provided by the current backend.
          </InsightPanel>
          <InsightPanel title="Why is confidence low?">
            Explanations require model outputs that are not available yet.
          </InsightPanel>
        </section>
      </main>
    </div>
  );
}

export default App;
