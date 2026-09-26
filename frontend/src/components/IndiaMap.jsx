import { useEffect, useMemo, useState } from "react";
import L from "leaflet";
import {
  GeoJSON,
  MapContainer,
  TileLayer,
  useMap,
} from "react-leaflet";
import MapLegend from "./MapLegend";

function getRiskColor(prob) {
  const p = Number(prob ?? 0);
  if (p < 0.20) return "#10b981"; // Green (Very Low Risk)
  if (p < 0.40) return "#84cc16"; // Lime (Low Risk)
  if (p < 0.60) return "#f59e0b"; // Amber (Moderate Risk)
  if (p < 0.80) return "#f97316"; // Orange (High Risk)
  return "#ef4444";             // Red (Very High Risk)
}

function getRainfallColor(rainfall) {
  const r = Number(rainfall ?? 0);
  if (r < 5) return "#dcfce7";
  if (r < 20) return "#86efac";
  if (r < 50) return "#fde047";
  if (r < 100) return "#fb923c";
  return "#ef4444";
}

function MapBoundsController({ geoJson }) {
  const map = useMap();

  useEffect(() => {
    if (!geoJson) return;
    try {
      const layer = L.geoJSON(geoJson);
      const bounds = layer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [18, 18], maxZoom: 5.2 });
        requestAnimationFrame(() => map.invalidateSize());
      }
    } catch (e) {
      console.warn("Bounds calculation error:", e);
    }
  }, [geoJson, map]);

  return null;
}

export default function IndiaMap({
  cells = [],
  selectedCell,
  onCellSelect,
  viewMode = "risk",
  riskFilter = "all",
  regionFilter = "all",
}) {
  const [gridGeoJson, setGridGeoJson] = useState(null);
  const [indiaBoundary, setIndiaBoundary] = useState(null);
  const [fetchError, setFetchError] = useState(null);

  useEffect(() => {
    fetch("/data/india_grid.geojson")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status} loading grid`);
        return res.json();
      })
      .then((data) => {
        if (data && data.features) setGridGeoJson(data);
      })
      .catch((err) => {
        console.error("Grid GeoJSON error:", err);
        setFetchError(err.message);
      });

    fetch("/data/india.geojson")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.features) setIndiaBoundary(data);
      })
      .catch((err) => console.warn("India boundary warning:", err));
  }, []);

  const cellDataMap = useMemo(() => {
    return new Map(cells.map((c) => [String(c.cell_id), c]));
  }, [cells]);

  const styleFeature = (feature) => {
    const cellId = feature?.properties?.cell_id;
    const cell = cellDataMap.get(String(cellId));
    const isSelected = selectedCell && String(selectedCell.cell_id) === String(cellId);

    if (!cell) {
      return {
        color: "#cbd5e1",
        weight: 0.3,
        fillColor: "#e2e8f0",
        fillOpacity: 0.4,
      };
    }

    // Apply Filter Dimming
    let opacity = 0.75;
    if (riskFilter === "high_risk" && !["high", "very_high"].includes(cell.risk_level)) {
      opacity = 0.12;
    } else if (riskFilter === "moderate_plus" && !["moderate", "high", "very_high"].includes(cell.risk_level)) {
      opacity = 0.12;
    } else if (riskFilter !== "all" && cell.risk_level !== riskFilter) {
      opacity = 0.12;
    }

    if (regionFilter !== "all" && cell.region !== regionFilter) {
      opacity = 0.12;
    }

    const fillColor =
      viewMode === "risk"
        ? getRiskColor(cell.bust_probability)
        : getRainfallColor(cell.rainfall_mm);

    return {
      color: isSelected ? "#0f172a" : "#64748b",
      weight: isSelected ? 2.5 : 0.4,
      fillColor: fillColor,
      fillOpacity: opacity,
    };
  };

  const onEachFeature = (feature, layer) => {
    const cellId = feature?.properties?.cell_id;
    const cell = cellDataMap.get(String(cellId));

    const lat = Number(cell?.latitude ?? feature?.properties?.latitude ?? 0);
    const lon = Number(cell?.longitude ?? feature?.properties?.longitude ?? 0);
    const rainfall = Number(cell?.rainfall_mm ?? cell?.forecast_rainfall_mm ?? 0);
    const prob = Number(cell?.bust_probability ?? 0);
    const conf = Number(cell?.confidence ?? 1);
    const stateName = cell?.state || feature?.properties?.state || "India";
    const regionName = cell?.region || feature?.properties?.region || "Region";

    layer.bindPopup(`
      <div class="p-1 min-w-[210px] text-xs font-sans">
        <div class="font-bold text-sm text-slate-900 flex justify-between items-center mb-1">
          <span>${cellId}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded uppercase font-semibold bg-slate-100">${cell?.risk_level || "Unknown"}</span>
        </div>
        <p class="text-slate-500 font-medium mb-0.5">${stateName}</p>
        <p class="text-[11px] text-blue-600 font-semibold mb-2">${regionName} (${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E)</p>
        
        <div class="space-y-1 border-t border-slate-100 pt-1.5">
          <div class="flex justify-between"><span class="text-slate-500">Bust Probability:</span><span class="font-semibold text-slate-800">${(prob * 100).toFixed(1)}%</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Forecast Confidence:</span><span class="font-semibold text-emerald-600">${(conf * 100).toFixed(1)}%</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Forecast Rain:</span><span class="font-semibold text-blue-600">${rainfall.toFixed(1)} mm</span></div>
          ${cell?.temperature_c != null ? `<div class="flex justify-between"><span class="text-slate-500">Temperature:</span><span class="font-semibold">${Number(cell.temperature_c).toFixed(1)} °C</span></div>` : ""}
          ${cell?.pressure_hpa != null ? `<div class="flex justify-between"><span class="text-slate-500">Pressure:</span><span class="font-semibold">${Number(cell.pressure_hpa).toFixed(1)} hPa</span></div>` : ""}
        </div>
      </div>
    `);

    layer.on({
      click: () => {
        if (cell && onCellSelect) {
          onCellSelect(cell);
        }
      },
      mouseover: (e) => {
        const l = e.target;
        l.setStyle({ weight: 2.0, color: "#0f172a" });
      },
      mouseout: (e) => {
        const l = e.target;
        l.setStyle(styleFeature(feature));
      },
    });
  };

  return (
    <div className="relative h-full w-full min-h-[650px] bg-slate-50">
      {fetchError && (
        <div className="absolute top-2 left-2 z-[1000] bg-red-100 border border-red-300 text-red-700 text-xs px-3 py-1.5 rounded-lg shadow">
          Grid Layer Load Warning: {fetchError}
        </div>
      )}

      <MapContainer
        center={[22.5, 79]}
        zoom={4.5}
        scrollWheelZoom={true}
        className="h-full w-full min-h-[650px] rounded-2xl z-0"
        style={{ height: "100%", width: "100%", minHeight: "650px" }}
      >
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* 1. GRID INTERACTIVE LAYER */}
        {gridGeoJson && (
          <>
            <GeoJSON
              key={`${viewMode}-${riskFilter}-${regionFilter}-${selectedCell?.cell_id || ""}-${cells.length}`}
              data={gridGeoJson}
              style={styleFeature}
              onEachFeature={onEachFeature}
            />
            <MapBoundsController geoJson={gridGeoJson} />
          </>
        )}

        {/* 2. STATE BOUNDARIES OVERLAY - NON INTERACTIVE TO ALLOW GRID CLICKS */}
        {indiaBoundary && (
          <GeoJSON
            key="india-state-borders"
            data={indiaBoundary}
            interactive={false}
            style={{
              color: "#0f172a",
              weight: 1.8,
              fillColor: "transparent",
              fillOpacity: 0,
            }}
          />
        )}
      </MapContainer>

      <MapLegend viewMode={viewMode} />
    </div>
  );
}