import {
  MapContainer,
  TileLayer,
  Rectangle,
  Popup,
} from "react-leaflet";


function getRainfallColor(rainfall) {
  if (rainfall < 5) return "#dcfce7";
  if (rainfall < 20) return "#86efac";
  if (rainfall < 50) return "#fde047";
  if (rainfall < 100) return "#fb923c";
  return "#ef4444";
}


export default function IndiaMap({ cells, onCellSelect }) {
  return (
    <MapContainer
      center={[22.5, 79]}
      zoom={4.5}
      scrollWheelZoom={true}
      className="h-full w-full"
    >

      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {cells.map((cell) => {
        const lat = Number(cell.latitude);
        const lon = Number(cell.longitude);
        const rainfall = Number(cell.rainfall_mm ?? 0);

        const half = 0.125;

        const bounds = [
          [lat - half, lon - half],
          [lat + half, lon + half],
        ];

        return (
          <Rectangle
            key={cell.cell_id}
            bounds={bounds}
            pathOptions={{
              color: "#334155",
              weight: 0.7,
              fillColor: getRainfallColor(rainfall),
              fillOpacity: 0.65,
            }}
            eventHandlers={{
              click: () => onCellSelect(cell),
            }}
          >
            <Popup>
              <div className="min-w-[180px]">
                <h3 className="font-bold">
                  {cell.cell_id}
                </h3>

                <p>
                  Latitude: {lat.toFixed(2)}
                </p>

                <p>
                  Longitude: {lon.toFixed(2)}
                </p>

                <p>
                  Rainfall: {rainfall.toFixed(1)} mm
                </p>

                <p>
                  Temperature:{" "}
                  {Number(cell.temperature_c).toFixed(1)} °C
                </p>

                <p>
                  Humidity:{" "}
                  {Number(cell.humidity_percent).toFixed(1)} %
                </p>
              </div>
            </Popup>
          </Rectangle>
        );
      })}
    </MapContainer>
  );
}