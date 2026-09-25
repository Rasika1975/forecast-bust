import { useEffect, useState } from "react";

import IndiaMap from "./components/IndiaMap";
import DaySelector from "./components/DaySelector";
import GridInfoPanel from "./components/GridInfoPanel";

import { getForecastMap } from "./services/api";

const TOTAL_INDIA_GRID_CELLS = 4651;

function App() {
  const [leadDay, setLeadDay] = useState(1);
  const [forecast, setForecast] = useState(null);

  const [cells, setCells] = useState([]);
  const [selectedCell, setSelectedCell] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);


  async function loadForecast(day) {
    try {
      setLoading(true);
      setError(null);

      const data = await getForecastMap(day);

      setForecast(data);
      setCells(data.cells || []);
      setSelectedCell(null);

    } catch (err) {
      console.error(err);
      setError(err.message);

    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadForecast(leadDay);
  }, [leadDay]);


  return (
    <div className="min-h-screen bg-slate-100">

      {/* HEADER */}
      <header className="border-b bg-white">
        <div className="mx-auto max-w-[1600px] px-6 py-5">

          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">

            <div>
              <p className="text-sm font-medium text-blue-600">
                Problem Statement 26079
              </p>

              <h1 className="text-2xl font-bold text-slate-900">
                Forecast Guard AI
              </h1>

              <p className="text-sm text-slate-500">
                AI-Based Forecast Bust Detection
              </p>
            </div>

            {forecast && (
              <div className="rounded-xl bg-slate-50 px-4 py-3 text-sm">
                <p className="text-slate-500">
                  Forecast Start
                </p>

                <p className="font-semibold text-slate-900">
                  {forecast.forecast_start}
                </p>
              </div>
            )}

          </div>
        </div>
      </header>


      {/* MAIN */}
      <main className="mx-auto max-w-[1600px] space-y-5 px-6 py-6">

        {/* TOP CONTROL */}
        <section className="rounded-2xl bg-white p-5 shadow-sm">

          <div className="mb-3">
            <h2 className="text-lg font-bold text-slate-900">
              Forecast Lead Time
            </h2>

            <p className="text-sm text-slate-500">
              Select the forecast day to view the ECMWF rainfall
              forecast.
            </p>
          </div>

          <DaySelector
            selectedDay={leadDay}
            onChange={setLeadDay}
          />

        </section>


        {/* ERROR */}
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}


        {/* CONTENT */}
        <section className="grid gap-5 lg:grid-cols-[1fr_340px]">

          {/* MAP */}
          <div className="relative overflow-hidden rounded-2xl bg-white shadow-sm">

            <div className="h-[650px]">

              {loading ? (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

                    <p className="text-sm text-slate-500">
                      Loading real ECMWF forecast...
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <IndiaMap
                    cells={cells}
                    onCellSelect={setSelectedCell}
                  />

                  <MapLegend />
                </>
              )}

            </div>

          </div>


          {/* SIDE PANEL */}
          <div className="space-y-5">

            <GridInfoPanel
              cell={selectedCell}
              leadDay={leadDay}
              validDate={forecast?.valid_date}
            />


            {/* Current forecast summary */}
            <div className="rounded-2xl bg-white p-6 shadow-sm">

              <p className="text-xs uppercase tracking-wide text-slate-400">
                Current View
              </p>

              <h2 className="mt-1 text-xl font-bold text-slate-900">
                Day {leadDay}
              </h2>

              {forecast && (
                <div className="mt-4 space-y-3 text-sm">

                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      Valid Date
                    </span>

                    <span className="font-semibold">
                      {forecast.valid_date}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      Total India Grid Cells
                    </span>

                    <span className="font-semibold">
                      {TOTAL_INDIA_GRID_CELLS}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      Forecast Data Available
                    </span>

                    <span className="font-semibold">
                      {forecast.forecast_data_available ?? forecast.cells?.length ?? 0}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      Resolution
                    </span>

                    <span className="font-semibold">
                      {forecast.grid_resolution}
                    </span>
                  </div>

                </div>
              )}

            </div>


            {/* ML layer placeholder — NOT prediction data */}
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6">

              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                AI Reliability Layer
              </p>

              <h3 className="mt-2 font-semibold text-slate-700">
                Forecast Bust Detection
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                Bust probability and confidence maps will appear
                here after the ML model is integrated.
              </p>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;
