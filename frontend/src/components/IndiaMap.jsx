import { useEffect, useMemo, useState } from "react";
import L from "leaflet";
import {
  GeoJSON,
  MapContainer,
  TileLayer,
  useMap,
} from "react-leaflet";


function getRainfallColor(rainfall) {
  if (rainfall < 5) return "#dcfce7";
  if (rainfall < 20) return "#86efac";
  if (rainfall < 50) return "#fde047";
  if (rainfall < 100) return "#fb923c";
  return "#ef4444";
}


function MapBoundsController({ geoJson }) {
  const map = useMap();

  useEffect(() => {
    if (!geoJson) return;

    const layer = L.geoJSON(geoJson);
    const bounds = layer.getBounds();

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [16, 16] });
      requestAnimationFrame(() => map.invalidateSize());
    }
  }, [geoJson, map]);

  return null;
}


export default function IndiaMap({ cells, onCellSelect }) {
  const [gridGeoJson, setGridGeoJson] = useState(null);
  const [indiaBoundary, setIndiaBoundary] = useState(null);

  useEffect(() => {
    fetch("/data/india_grid.geojson")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Failed to load grid GeoJSON: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => setGridGeoJson(data))
      .catch((error) => {
        console.error("Grid GeoJSON load failed:", error);
      });

    fetch("/data/india.geojson")
      .then((response) => {
        if (!response.ok) return null;
        return response.json();
      })
      .then((data) => {
        if (data) setIndiaBoundary(data);
      })
      .catch((error) => {
        console.warn("India boundary GeoJSON not loaded:", error);
      });
  }, []);

  const forecastByCell = useMemo(() => {
    return new Map(
      (cells || []).map((cell) => [String(cell.cell_id), cell])
    );
  }, [cells]);

  const styleFeature = (feature) => {
    const cellId = feature?.properties?.cell_id;
    const cell = forecastByCell.get(String(cellId));

    if (!cell) {
      return {
        color: "#334155",
        weight: 0.7,
        fillColor: "#d1d5db",
        fillOpacity: 0.8,
      };
    }

    const rainfall = Number(cell?.rainfall_mm ?? 0);

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

    layer.on({ click: () => onCellSelect(geoCell) });
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
        <>
          <GeoJSON
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