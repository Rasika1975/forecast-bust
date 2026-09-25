const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function getLatestRun() {
  const response = await fetch(`${API_BASE_URL}/api/runs/latest`);
  if (!response.ok) {
    throw new Error(`Failed to load run metadata: ${response.status}`);
  }
  return response.json();
}

export async function getForecastMap(leadDay) {
  const params = new URLSearchParams({
    lead_day: String(leadDay),
  });

  const response = await fetch(
    `${API_BASE_URL}/api/forecast/map?${params}`
  );
  if (!response.ok) {
    throw new Error(`Forecast map API failed: ${response.status}`);
  }
  return response.json();
}

export async function getDaySummary(leadDay) {
  const response = await fetch(
    `${API_BASE_URL}/api/summary?lead_day=${leadDay}`
  );
  if (!response.ok) {
    throw new Error(`Summary API failed: ${response.status}`);
  }
  return response.json();
}

export async function getCellDetail(cellId, leadDay) {
  const response = await fetch(
    `${API_BASE_URL}/api/risk/cell/${cellId}?lead_day=${leadDay}`
  );
  if (!response.ok) {
    throw new Error(`Cell detail API failed: ${response.status}`);
  }
  return response.json();
}

export async function getCellExplanation(cellId, leadDay) {
  const response = await fetch(
    `${API_BASE_URL}/api/explanation/cell/${cellId}?lead_day=${leadDay}`
  );
  if (!response.ok) {
    throw new Error(
      `Forecast API failed: ${response.status}`
    );
  }

  return response.json();
}