const API_BASE_URL = "http://127.0.0.1:8000";

export async function getForecastMap(leadDay) {
  const response = await fetch(
    `${API_BASE_URL}/api/forecast/map?lead_day=${leadDay}`
  );

  if (!response.ok) {
    throw new Error(
      `Forecast API failed: ${response.status}`
    );
  }

  return response.json();
}