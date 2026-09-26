import { useEffect, useState } from "react";
import { getCellDetail } from "../services/api";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";

function getRiskBadge(level) {
  switch (level) {
    case "very_high":
      return { label: "Very High Bust Risk", variant: "danger" };
    case "high":
      return { label: "High Bust Risk", variant: "highRisk" };
    case "moderate":
      return { label: "Moderate Risk", variant: "warning" };
    case "low":
      return { label: "Low Bust Risk", variant: "success" };
    case "very_low":
    default:
      return { label: "High Confidence", variant: "success" };
  }
}

function formatValue(val, decimals = 2) {
  if (val == null || !Number.isFinite(Number(val))) return "N/A";
  return Number(val).toFixed(decimals);
}

function getCellValue(cell, detail, key, decimals = 1, unit = "") {
  const val = detail?.[key] ?? cell?.[key];
  if (val == null || !Number.isFinite(Number(val))) return "Unavailable";
  return `${Number(val).toFixed(decimals)}${unit}`;
}

export default function GridInfoPanel({ cell, leadDay, validDate, hazard = "rain" }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!cell?.cell_id) {
      setDetail(null);
      return;
    }

    let isMounted = true;
    setLoading(true);

    getCellDetail(cell.cell_id, leadDay, hazard)
      .then((data) => {
        if (isMounted) setDetail(data);
      })
      .catch((err) => {
        console.error("Failed to load cell detail:", err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [cell?.cell_id, leadDay, hazard]);

  if (!cell) {
    return (
      <Card className="shadow-sm border-slate-200">
        <CardHeader className="p-5">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold text-lg">
              ℹ️
            </div>
            <div>
              <CardTitle className="text-base">Grid Cell Inspection</CardTitle>
              <CardDescription className="text-xs">Interactive operational drilldown</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-5 pt-0">
          <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-6 text-center">
            <p className="text-sm font-semibold text-slate-700">No Cell Selected</p>
            <p className="mt-1.5 text-xs text-slate-400 max-w-[260px] mx-auto leading-relaxed">
              Click any 0.25° grid cell on the map to inspect calibrated bust risk, atmospheric variables, SHAP drivers, and historical analogs.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const riskBadge = getRiskBadge(detail?.risk_level || cell?.risk_level);
  const bustProbPct = Number(((detail?.bust_probability ?? cell?.bust_probability ?? 0) * 100).toFixed(1));
  const confPct = Number(((detail?.confidence ?? cell?.confidence ?? 1) * 100).toFixed(1));
  const rainVal = Number(detail?.forecast_rainfall_mm ?? cell?.rainfall_mm ?? 0).toFixed(1);

  return (
    <Card className="shadow-sm border-slate-200 bg-white">
      <CardHeader className="p-5 pb-3">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {detail?.region || cell?.region || "India Grid"}
              </span>
              <span className="text-[11px] text-slate-400">• Day {leadDay} • {hazard === "temp" ? "Heatwave Temp" : hazard === "wind" ? "Windstorm" : "Precipitation"}</span>
            </div>
            <CardTitle className="text-xl mt-0.5">{cell.cell_id}</CardTitle>
            <CardDescription className="text-xs text-slate-500 mt-0.5">
              {detail?.state || cell?.state || ""} ({Number(cell.latitude).toFixed(2)}°N, {Number(cell.longitude).toFixed(2)}°E)
            </CardDescription>
          </div>

          <Badge variant={riskBadge.variant} className="text-xs font-bold py-1 px-2.5">
            {riskBadge.label}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="p-5 pt-1 space-y-4">
        {/* KPI METRICS */}
        <div className="grid grid-cols-2 gap-3 rounded-xl bg-slate-50 p-3">
          <div>
            <span className="text-[11px] text-slate-500 font-medium">Bust Risk</span>
            <p className="text-lg font-bold text-slate-900">{bustProbPct}%</p>
            <Progress value={bustProbPct} className="h-1.5 mt-1 bg-slate-200" />
          </div>
          <div>
            <span className="text-[11px] text-slate-500 font-medium">Confidence</span>
            <p className="text-lg font-bold text-emerald-600">{confPct}%</p>
            <Progress value={confPct} className="h-1.5 mt-1 bg-slate-200" />
          </div>
        </div>

        {/* TABS DRILLDOWN */}
        <Tabs defaultValue="risk" className="w-full">
          <TabsList className="grid w-full grid-cols-3 h-9 bg-slate-100 p-1">
            <TabsTrigger value="risk" className="text-xs font-semibold">Risk & Weather</TabsTrigger>
            <TabsTrigger value="shap" className="text-xs font-semibold">SHAP Drivers</TabsTrigger>
            <TabsTrigger value="analogs" className="text-xs font-semibold">Historical</TabsTrigger>
          </TabsList>

          {/* TAB 1: RISK & WEATHER */}
          <TabsContent value="risk" className="mt-3 space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Valid Date</span>
              <span className="font-semibold text-slate-900">{validDate || cell.valid_date || "2026-09-24"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Forecast Rainfall</span>
              <span className="font-semibold text-blue-600">{rainVal} mm</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Historical P90 Threshold</span>
              <span className="font-semibold text-slate-800">{getCellValue(cell, detail, "historical_p90_error_mm", 1, " mm")}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Temperature (2m)</span>
              <span className="font-semibold text-slate-800">{getCellValue(cell, detail, "temperature_c", 1, " °C")}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">Relative Humidity</span>
              <span className="font-semibold text-slate-800">{getCellValue(cell, detail, "humidity_percent", 1, " %")}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-100">
              <span className="text-slate-500">MSL Pressure</span>
              <span className="font-semibold text-slate-800">{getCellValue(cell, detail, "pressure_hpa", 1, " hPa")}</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">10m Wind Speed</span>
              <span className="font-semibold text-slate-800">{getCellValue(cell, detail, "wind_speed_kmh", 1, " km/h")}</span>
            </div>
          </TabsContent>

          {/* TAB 2: SHAP DRIVERS */}
          <TabsContent value="shap" className="mt-3 space-y-2 text-xs">
            {loading ? (
              <p className="text-center text-slate-400 py-4">Calculating SHAP feature attributions...</p>
            ) : detail?.top_reasons && detail.top_reasons.length > 0 ? (
              <div className="space-y-2">
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Top Meteorological Drivers</p>
                {detail.top_reasons.map((reason, idx) => (
                  <div key={idx} className="flex items-start gap-2 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    <span className="text-blue-500 font-bold">•</span>
                    <span className="text-slate-700 leading-snug">{reason}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 text-center py-4">No significant risk drivers flagged for this cell.</p>
            )}
          </TabsContent>

          {/* TAB 3: HISTORICAL ANALOGS */}
          <TabsContent value="analogs" className="mt-3 space-y-2 text-xs">
            {loading ? (
              <p className="text-center text-slate-400 py-4">Searching 92,474 historical analogs...</p>
            ) : detail?.similar_historical_events && detail.similar_historical_events.length > 0 ? (
              <div className="space-y-2">
                <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Similar Historical Bust Cases</p>
                {detail.similar_historical_events.map((caseItem, idx) => (
                  <div key={idx} className="rounded-lg bg-amber-50/60 p-2.5 border border-amber-200/60 space-y-1">
                    <div className="flex justify-between font-semibold text-slate-800">
                      <span>{caseItem.historical_run || caseItem.date || `Analog #${idx + 1}`}</span>
                      <span className="text-amber-700">{caseItem.similarity_score_percent}% Similarity</span>
                    </div>
                    <div className="flex justify-between text-slate-600 text-[11px]">
                      <span>Fcst: {caseItem.forecast_rain_mm ?? caseItem.forecast_rainfall_mm} mm</span>
                      <span>Realized Error: <strong className="text-red-600">{caseItem.realized_error_mm} mm</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-400 text-center py-4">No historical analogs matching condition threshold.</p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}