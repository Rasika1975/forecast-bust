const API_BASE_URL = "http://127.0.0.1:8000";

export async function getForecastMap(leadDay) {
  const params = new URLSearchParams({
    lead_day: String(leadDay),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/forecast/map?${params}`
  );

  if (!response.ok) {
    let message = `Forecast API failed: ${response.status}`;

    try {
      const error = await response.json();
      if (error.detail) message = error.detail;
    } catch {
      // Keep the status-based message when the API response is not JSON.
    }

    throw new Error(message);
  }

  return response.json();
}