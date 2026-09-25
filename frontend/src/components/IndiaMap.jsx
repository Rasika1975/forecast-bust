import { useEffect, useMemo, useState } from "react";
import booleanPointInPolygon from "@turf/boolean-point-in-polygon";
import { point } from "@turf/helpers";
import L from "leaflet";
import {
  GeoJSON,
  MapContainer,
  Marker,
  Pane,
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


function getStateName(feature) {
  return feature?.properties?.ST_NM || feature?.properties?.state_name || null;
}


const REGION_BY_STATE_ID = Object.freeze({
  "IN-JK": "North India",
  "IN-LA": "North India",
  "IN-HP": "North India",
  "IN-PB": "North India",
  "IN-HR": "North India",
  "IN-CH": "North India",
  "IN-DL": "North India",
  "IN-UT": "North India",
  "IN-UP": "North India",
  "IN-RJ": "West India",
  "IN-GJ": "West India",
  "IN-MH": "West India",
  "IN-GA": "West India",
  "IN-DD": "West India",
  "IN-DN": "West India",
  "IN-MP": "Central India",
  "IN-CT": "Central India",
  "IN-BR": "East India",
  "IN-JH": "East India",
  "IN-OR": "East India",
  "IN-WB": "East India",
  "IN-AR": "Northeast India",
  "IN-AS": "Northeast India",
  "IN-ML": "Northeast India",
  "IN-MN": "Northeast India",
  "IN-MZ": "Northeast India",
  "IN-NL": "Northeast India",
  "IN-SK": "Northeast India",
  "IN-TR": "Northeast India",
  "IN-AP": "South India",
  "IN-KA": "South India",
  "IN-KL": "South India",
  "IN-TG": "South India",
  "IN-TN": "South India",
  "IN-PY": "South India",
  "IN-AN": "Island Territories",
  "IN-LD": "Island Territories",
});


function getStateInfo(feature) {
  const properties = feature?.properties;
  const stateName = getStateName(feature);
  if (!stateName) return null;

  return {
    stateName,
    region: REGION_BY_STATE_ID[properties?.ST_ID] || null,
  };
}


function getStateLabelIcon(stateName) {
  return L.divIcon({
    className: "state-label-icon",
    html: `<span>${stateName}</span>`,
    iconSize: [0, 0],
    iconAnchor: [0, 0],
  });
}


function getOuterRings(geometry) {
  if (!geometry) return [];
  if (geometry.type === "Polygon") return [geometry.coordinates[0]];
  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.map((polygon) => polygon[0]);
  }
  return [];
}


function findStateInfo(feature, boundaryFeatures) {
  const latitude = Number(feature?.properties?.latitude ?? 0);
  const longitude = Number(feature?.properties?.longitude ?? 0);
  const candidatePoints = [
    [longitude, latitude],
    ...getOuterRings(feature.geometry).flat(),
  ];
  const match = boundaryFeatures.find((boundaryFeature) => (
    candidatePoints.some((coordinates) => (
      booleanPointInPolygon(point(coordinates), boundaryFeature, {
        ignoreBoundary: false,
      })
    ))
  ));

  return getStateInfo(match);
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
    const cell = forecastByCell.get(String(cellId));

    if (!cell) {
      return {
        color: "#64748b",
        weight: 0.35,
        fillColor: "#d1d5db",
        fillOpacity: 0.18,
      };
    }

    const rainfall = Number(cell?.rainfall_mm ?? 0);

    return {
      color: "#475569",
      weight: 0.35,
      fillColor: getRainfallColor(rainfall),
      fillOpacity: 0.42,
    };
  };

  const onEachFeature = (feature, layer) => {
    const cellId = feature?.properties?.cell_id;
    const cell = forecastByCell.get(String(cellId));
    const stateInfo = findStateInfo(feature, boundaryFeatures);
    const geoCell = {
      cell_id: cellId,
      latitude: Number(feature?.properties?.latitude ?? 0),
      longitude: Number(feature?.properties?.longitude ?? 0),
      state_name: stateInfo?.stateName || null,
      region: stateInfo?.region || null,
      forecast_unavailable: !cell,
      ...(cell || {}),
    };

    const lat = Number(geoCell.latitude ?? 0);
    const lon = Number(geoCell.longitude ?? 0);
    const rainfall = Number(geoCell.rainfall_mm ?? 0);

    layer.bindPopup(`
      <div class="popup-content">
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

      {gridGeoJson && (
        <>
          <GeoJSON
            data={gridGeoJson}
            style={styleFeature}
            onEachFeature={onEachFeature}
          />
          {indiaBoundary && (
            <Pane
              name="state-boundaries"
              style={{ pointerEvents: "none", zIndex: 410 }}
            >
              <GeoJSON
                data={indiaBoundary}
                interactive={false}
                style={{
                  color: "#164e63",
                  weight: 1.1,
                  fillColor: "transparent",
                  fillOpacity: 0,
                }}
              />
            </Pane>
          )}
          {stateLabels.map(({ stateName, position }) => (
            <Marker
              key={stateName}
              position={position}
              icon={getStateLabelIcon(stateName)}
              interactive={false}
            />
          ))}
          <MapBoundsController geoJson={indiaBoundary || gridGeoJson} />
        </>
      )}
    </MapContainer>
  );
}