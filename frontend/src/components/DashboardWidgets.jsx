const chartPanels = [
  {
    title: "Confidence trend",
    meta: "Day 1-10",
    description: "Confidence history is not part of the current forecast API.",
  },
  {
    title: "Bust probability",
    meta: "By lead time",
    description: "Bust probability requires the ML layer.",
  },
  {
    title: "Forecast vs actual rainfall",
    meta: "mm / day",
    description: "Observed rainfall is not available from the current API.",
  },
];

export function StatusBanner({ loading, error, forecast }) {
  const isError = Boolean(error);
  const label = isError
    ? "Forecast connection issue"
    : loading
      ? "Refreshing forecast data"
      : forecast
        ? "Live forecast data loaded"
        : "Waiting for forecast data";
  const message = isError
    ? error
    : loading
      ? "Requesting the selected lead day from the forecast service."
      : forecast
        ? `${forecast.forecast_data_available ?? forecast.cells?.length ?? 0} grid cells available for Day ${forecast.lead_day}.`
        : "Select a lead day to load the forecast.";

  return (
    <section className={`status-banner ${isError ? "status-banner-error" : ""}`}>
      <span className="status-dot" aria-hidden="true" />
      <div>
        <p className="eyebrow">System status</p>
        <p className="status-title">{label}</p>
        <p className="status-copy">{message}</p>
      </div>
      <span className="status-tag">{isError ? "Action needed" : "NWP stream"}</span>
    </section>
  );
}

export function MetricCard({ label, value, detail, accent = "cyan" }) {
  return (
    <article className={`metric-card metric-${accent}`}>
      <p className="eyebrow">{label}</p>
      <p className="metric-value">{value}</p>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}

export function UnavailablePanel({ title, meta, description }) {
  return (
    <article className="dashboard-panel unavailable-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Analytics</p>
          <h3>{title}</h3>
        </div>
        <span className="panel-meta">{meta}</span>
      </div>
      <div className="chart-placeholder" aria-label={`${title}: ML model not available yet`}>
        <div className="placeholder-lines" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
        </div>
        <strong>ML model not available yet</strong>
        <p>{description}</p>
      </div>
    </article>
  );
}

export function AnalyticsGrid() {
  return (
    <div className="analytics-grid">
      {chartPanels.map((panel) => (
        <UnavailablePanel key={panel.title} {...panel} />
      ))}
    </div>
  );
}

export function InsightPanel({ title, children }) {
  return (
    <article className="dashboard-panel insight-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Model output</p>
          <h3>{title}</h3>
        </div>
        <span className="panel-meta">Unavailable</span>
      </div>
      <div className="insight-empty">
        <strong>ML model not available yet</strong>
        <p>{children}</p>
      </div>
    </article>
  );
}
