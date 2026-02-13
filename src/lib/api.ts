/**
 * Centralized API client.
 * All backend calls go through here — no hardcoded URLs anywhere else.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Admin stats
  getStats: () => request<AdminStats>("/api/admin/stats"),
  getConversions: () => request<Conversion[]>("/api/admin/conversions"),
  getSettings: () => request<Settings>("/api/admin/settings"),
  saveSettings: (data: SettingsInput) =>
    request<{ status: string; message: string }>("/api/admin/settings", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Analytics
  getTimeseries: (days = 30) =>
    request<TimeseriesData[]>(`/api/admin/analytics/timeseries?days=${days}`),
  getFeatureUsage: () => request<FeatureUsageData[]>("/api/admin/analytics/features"),
  getUserAnalytics: () => request<UserAnalyticsData>("/api/admin/analytics/users"),
  getErrorTracking: () => request<ErrorTrackingData>("/api/admin/analytics/errors"),
  getSystemHealth: () => request<SystemHealthData>("/api/admin/system/health"),
  exportConversions: () =>
    fetch(`${API_BASE_URL}/api/admin/conversions/export`).then((r) => {
      if (!r.ok) throw new Error("Export failed");
      return r.blob();
    }),

  // Health
  getHealth: () => request<{ status: string; timestamp: string }>("/health"),
};

// Types
export interface AdminStats {
  total_conversions: number;
  today_conversions: number;
  success_rate: number;
  pending: number;
  active_users: number;
  avg_processing_time_ms: number;
  top_feature: string;
  total_bandwidth_mb: number;
}

export interface Conversion {
  id: string;
  phone_number: string;
  timestamp: string;
  status: "success" | "failed" | "pending";
  file_size: number;
  feature?: string;
  input_type?: string;
  output_type?: string;
  processing_time_ms?: number;
  error_message?: string;
  output_file_size?: number;
}

export interface Settings {
  whatsapp_business_account_id: string;
  phone_number_id: string;
  access_token: string;
  webhook_verify_token: string;
}

export interface SettingsInput extends Settings {
  admin_password: string;
}

export interface TimeseriesData {
  date: string;
  conversions: number;
  successes: number;
  failures: number;
}

export interface FeatureUsageData {
  feature: string;
  count: number;
  percentage: number;
}

export interface UserAnalyticsData {
  total_unique_users: number;
  repeat_users: number;
  new_users_today: number;
  top_users: { phone: string; count: number; last_active: string }[];
  country_distribution: { country: string; code: string; count: number }[];
}

export interface ErrorTrackingData {
  total_errors: number;
  error_rate: number;
  errors_today: number;
  error_types: { type: string; count: number; last_occurred: string }[];
  recent_errors: { id: string; timestamp: string; feature: string; message: string }[];
}

export interface SystemHealthData {
  cpu_percent: number;
  memory_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_used_gb: number;
  disk_total_gb: number;
  uptime_seconds: number;
  python_version: string;
  active_sessions: number;
}
