// Tipos base del sistema

export interface User {
  id: number;
  email: string;
  role: 'super_admin' | 'service_admin' | 'technician' | 'guest';
  first_name: string;
  last_name: string;
  phone_number: string | null;
  profile_picture_url: string | null;
  is_active: boolean;
  archived: boolean;
  archived_at: string | null;
  allowed_location_ids: number[] | null;
  created_at: string;
  last_login_at: string | null;
  preferences: Record<string, unknown> | null;
}

export interface UserCreate {
  email: string;
  password: string;
  role: 'super_admin' | 'service_admin' | 'technician' | 'guest';
  first_name: string;
  last_name: string;
  is_active?: boolean;
  archived?: boolean;
  allowed_location_ids?: number[] | null;
  phone_number?: string | null;
  profile_picture_url?: string | null;
}

export interface UserUpdate {
  email?: string;
  password?: string;
  role?: 'super_admin' | 'service_admin' | 'technician' | 'guest';
  first_name?: string;
  last_name?: string;
  phone_number?: string | null;
  profile_picture_url?: string | null;
  is_active?: boolean;
  archived?: boolean;
  allowed_location_ids?: number[] | null;
}

export interface Device {
  id: number;
  asset_id: number | null;
  device_eui: string;
  name: string;
  status: 'active' | 'inactive' | 'maintenance' | 'error';
  firmware_version: string | null;
  last_seen_at: string | null;
  config: Record<string, any> | null;
  extra_data: Record<string, any> | null;
  created_at: string;
}

export interface SensorReading {
  id: number;
  device_id: number;
  data_payload: Record<string, any>;
  quality_score: number | null;
  processed: boolean;
  timestamp: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface DeviceVariable {
  key: string;
  label: string;
  unit: string;
  type: string;
  color?: string;
}

export interface DeviceSchema {
  device_id: number;
  variables: DeviceVariable[];
}

export interface Alert {
  id: number;
  device_id: number;
  triggered_at: string;
  message: string;
  value_observed: number | null;
}

export interface SensorCatalog {
  id: number;
  name: string;
  sensor_type: string;
  description: string | null;
  gpio_pin: number | null;
  protocol: string | null;
  i2c_address: string | null;
  calibration_offset: number;
  calibration_factor: number;
  value_min: number | null;
  value_max: number | null;
  unit: string | null;
  decimal_places: number;
  config: Record<string, any> | null;
  manufacturer: string | null;
  model: string | null;
  datasheet_url: string | null;
  is_active: boolean;
  is_builtin: boolean;
  created_at: string;
  updated_at: string | null;
}

export interface SensorCatalogCreate {
  name: string;
  sensor_type: string;
  description?: string | null;
  gpio_pin?: number | null;
  protocol?: string | null;
  i2c_address?: string | null;
  calibration_offset?: number;
  calibration_factor?: number;
  value_min?: number | null;
  value_max?: number | null;
  unit?: string | null;
  decimal_places?: number;
  config?: Record<string, any> | null;
  manufacturer?: string | null;
  model?: string | null;
  datasheet_url?: string | null;
  is_active?: boolean;
}

export interface SensorCatalogUpdate {
  name?: string;
  sensor_type?: string;
  description?: string | null;
  gpio_pin?: number | null;
  protocol?: string | null;
  i2c_address?: string | null;
  calibration_offset?: number;
  calibration_factor?: number;
  value_min?: number | null;
  value_max?: number | null;
  unit?: string | null;
  decimal_places?: number;
  config?: Record<string, any> | null;
  manufacturer?: string | null;
  model?: string | null;
  datasheet_url?: string | null;
  is_active?: boolean;
}

// ============================================
// Health Dashboard Types
// ============================================

export interface DeviceHealthMetrics {
  device_id: number;
  device_eui: string;
  name: string;
  status: string;
  is_online: boolean;

  // Timestamps
  last_seen_at: string | null;
  created_at: string;
  uptime_hours: number | null;

  // Conectividad
  rssi_dbm: number | null;
  wifi_quality: string | null;

  // Recursos del sistema
  free_heap_bytes: number | null;
  battery_mv: number | null;
  battery_percentage: number | null;

  // Firmware
  firmware_version: string | null;

  // Estadísticas de datos
  total_readings: number;
  readings_last_24h: number;
  avg_readings_per_day: number;

  // Alertas relacionadas
  active_alerts_count: number;

  // Location info
  location_name: string | null;
  asset_name: string | null;
}

export interface DeviceHealthDashboard {
  total_devices: number;
  devices_online: number;
  devices_offline: number;
  devices_with_alerts: number;

  // Métricas de calidad de conexión
  avg_rssi: number | null;
  devices_poor_signal: number;

  // Lista de devices con sus métricas
  devices: DeviceHealthMetrics[];
}
