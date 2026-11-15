const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function queryString(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}

async function request(path, params) {
  const response = await fetch(`${API_BASE_URL}${path}${queryString(params)}`);
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new ApiError(
      payload?.detail || `The API returned HTTP ${response.status}`,
      response.status,
    );
  }
  return payload;
}

export function getHealth() {
  return request("/health");
}

export function getReadiness() {
  return request("/api/v1/system/ready");
}

export function getEarthquakes(filters, options = {}) {
  return request("/api/v1/earthquakes", { ...filters, ...options });
}

export function getSummary(filters) {
  return request("/api/v1/analytics/summary", filters);
}

export function getProvinceActivity(filters) {
  return request("/api/v1/analytics/provinces", filters);
}

export function getClusters(filters, options = {}) {
  return request("/api/v1/analytics/clusters", {
    ...filters,
    min_k: 2,
    max_k: 8,
    include_assignments: true,
    ...options,
  });
}
