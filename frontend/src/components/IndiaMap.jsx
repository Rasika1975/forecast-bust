import { useEffect, useMemo, useState } from "react";
import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import { point } from "@turf/helpers";
import L from "leaflet";
import {
  GeoJSON,
  MapContainer,
  TileLayer,
  useMap,
} from "react-leaflet";


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
    const layer = L.geoJSON(geoJson);
    const bounds = layer.getBounds();
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [18, 18], maxZoom: 5.2 });
      requestAnimationFrame(() => map.invalidateSize());
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
  regionFilter = "all"
}) {
  const [gridGeoJson, setGridGeoJson] = useState(null);
  const [indiaBoundary, setIndiaBoundary] = useState(null);

  useEffect(() => {
    fetch("/data/india_grid.geojson")
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load grid: ${res.status}`);
        return res.json();
      })
      .then((data) => setGridGeoJson(data))
      .catch((err) => console.error("Grid GeoJSON error:", err));

    fetch("/data/india.geojson")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => { if (data) setIndiaBoundary(data); })
      .catch((err) => console.warn("India boundary warning:", err));
  }, []);

  const cellDataMap = useMemo(() => {
    return new Map(cells.map((c) => [String(c.cell_id), c]));
  }, [cells]);

  const boundaryFeatures = useMemo(
    () => indiaBoundary?.features || [],
    [indiaBoundary]
  );

  const stateLabels = useMemo(() => {
    const states = new Map();

    boundaryFeatures.forEach((feature) => {
      const stateName = getStateName(feature);
      if (!stateName || states.has(stateName)) return;
      states.set(stateName, []);
    });

    boundaryFeatures.forEach((feature) => {
      const stateName = getStateName(feature);
      if (stateName && states.has(stateName)) {
        states.get(stateName).push(feature);
      }
    });

    return Array.from(states, ([stateName, features]) => {
      const bounds = L.geoJSON(features).getBounds();
      return {
        stateName,
        position: bounds.getCenter(),
      };
    }).filter(({ position }) => position && Number.isFinite(position.lat));
  }, [boundaryFeatures]);

  const styleFeature = (feature) => {
    const cellId = feature?.properties?.cell_id;
    const cell = cellDataMap.get(String(cellId));
    const isSelected = selectedCell && String(selectedCell.cell_id) === String(cellId);

    if (!cell) {
      return {
        color: "#334155",
        weight: 0.7,
        fillColor: "#d1d5db",
        fillOpacity: 0.8,
      };
    }

    // Apply Filter Dimming
    let matchesFilter = true;
    if (riskFilter === "high_risk" && !["high", "very_high"].includes(cell.risk_level)) {
      matchesFilter = false;
    } else if (riskFilter === "moderate_plus" && !["moderate", "high", "very_high"].includes(cell.risk_level)) {
      matchesFilter = false;
    }
    if (regionFilter !== "all" && cell.region !== regionFilter) {
      matchesFilter = false;
    }

    let fillColor;
    if (viewMode === "risk") {
      fillColor = getRiskColor(cell.bust_probability);
    } else {
      fillColor = getRainfallColor(cell.rainfall_mm);
    }

    return {
      color: "#334155",
      weight: 0.7,
      fillColor: getRainfallColor(rainfall),
      fillOpacity: 0.65,
    };
  };

  const onEachFeature = (feature, layer) => {
    const cellId = feature?.properties?.cell_id;
    const cell = forecastByCell.get(String(cellId));
    const geoCell = {
      cell_id: cellId,
      latitude: Number(feature?.properties?.latitude ?? 0),
      longitude: Number(feature?.properties?.longitude ?? 0),
      forecast_unavailable: !cell,
      ...(cell || {}),
    };

    const lat = Number(geoCell.latitude ?? 0);
    const lon = Number(geoCell.longitude ?? 0);
    const rainfall = Number(geoCell.rainfall_mm ?? 0);

    layer.bindPopup(`
      <div class="min-w-[180px]">
        <h3 class="font-bold">${geoCell.cell_id}</h3>
        <p>Latitude: ${lat.toFixed(2)}</p>
        <p>Longitude: ${lon.toFixed(2)}</p>
        <p>Rainfall: ${Number.isFinite(rainfall) ? `${rainfall.toFixed(1)} mm` : "Forecast unavailable"}</p>
        <p>Temperature: ${Number.isFinite(Number(geoCell.temperature_c)) ? `${Number(geoCell.temperature_c).toFixed(1)} °C` : "Forecast unavailable"}</p>
        <p>Humidity: ${Number.isFinite(Number(geoCell.humidity_percent)) ? `${Number(geoCell.humidity_percent).toFixed(1)} %` : "Forecast unavailable"}</p>
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
    <MapContainer
      center={[22.5, 79]}
      zoom={4.5}
      scrollWheelZoom={true}
      className="h-full w-full"
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {indiaBoundary && (
        <GeoJSON
          data={indiaBoundary}
          style={{
            color: "#0f172a",
            weight: 2,
            fillColor: "transparent",
            fillOpacity: 0,
          }}
        />
      )}

        {gridGeoJson && (
          <GeoJSON
            key={`${viewMode}-${riskFilter}-${regionFilter}-${selectedCell?.cell_id || ''}-${cells.length}`}
            data={gridGeoJson}
            style={styleFeature}
            onEachFeature={onEachFeature}
          />
          <MapBoundsController geoJson={gridGeoJson} />
        </>
      )}
    </MapContainer>
  );
}