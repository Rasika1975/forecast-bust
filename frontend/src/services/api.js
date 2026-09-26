const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://forecast-guard-backend.onrender.com";

export async function getLatestRun() {
  const response = await fetch(`${API_BASE_URL}/api/runs/latest`);
  if (!response.ok) {
    throw new Error(`Failed to load run metadata: ${response.status}`);
  }
  return response.json();
}

export async function getForecastMap(leadDay, hazard = "rain") {
  const params = new URLSearchParams({
    lead_day: String(leadDay),
    hazard: hazard,
  });

  const response = await fetch(
    `${API_BASE_URL}/api/forecast/map?${params}`
  );
  if (!response.ok) {
    throw new Error(`Forecast map API failed: ${response.status}`);
  }
  return response.json();
}

export async function getDaySummary(leadDay, hazard = "rain") {
  const response = await fetch(
    `${API_BASE_URL}/api/summary?lead_day=${leadDay}&hazard=${hazard}`
  );
  if (!response.ok) {
    throw new Error(`Summary API failed: ${response.status}`);
  }
  return response.json();
}

export async function getCellDetail(cellId, leadDay, hazard = "rain") {
  const response = await fetch(
    `${API_BASE_URL}/api/risk/cell/${cellId}?lead_day=${leadDay}&hazard=${hazard}`
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

export async function getVerificationMetrics(hazard = "rain") {
  const response = await fetch(`${API_BASE_URL}/api/verification/metrics?hazard=${hazard}`);
  if (!response.ok) {
    throw new Error(`Verification metrics API failed: ${response.status}`);
  }
  return response.json();
}

export async function getSyncStatus() {
  const response = await fetch(`${API_BASE_URL}/api/runs/sync-status`);
  if (!response.ok) {
    throw new Error(`Sync status API failed: ${response.status}`);
  }
  return response.json();
}

export async function triggerSync() {
  const response = await fetch(`${API_BASE_URL}/api/runs/sync-now`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Sync trigger API failed: ${response.status}`);
  }
  return response.json();
}
