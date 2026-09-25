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

export default function GridInfoPanel({ cell, leadDay, validDate }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!cell?.cell_id) {
      setDetail(null);
      return;
    }

    let isMounted = true;
    setLoading(true);

    getCellDetail(cell.cell_id, leadDay)
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
  }, [cell?.cell_id, leadDay]);

  if (!cell) {
    return (
      <Card className="shadow-sm">
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
    <Card className="shadow-sm border-slate-200">
      <CardHeader className="p-5 pb-3">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                {detail?.region || cell?.region || "India Grid"}
              </span>
              <span className="text-[11px] text-slate-400">• Day {leadDay}</span>
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
            {cell.forecast_unavailable || !Number.isFinite(Number(cell.rainfall_mm)) ? "Forecast unavailable" : `${Number(cell.rainfall_mm).toFixed(1)} mm`}
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