import api from './api';

// Types
export interface AlertRule {
  id: number;
  location_id: number | null;
  device_id: number | null;
  name: string;
  check_type: string;
  variable_key: string;
  threshold_value: number | null;
  threshold_min: number | null;
  threshold_max: number | null;
  time_window_minutes: number | null;
  enabled: boolean;
  cooldown_minutes: number;
  notification_channels: string[];
  webhook_url: string | null;
  created_at: string;
}

export interface AlertHistory {
  id: number;
  alert_rule_id: number;
  device_id: number;
  sensor_reading_id: number | null;
  triggered_at: string;
  value_observed: number | null;
  message: string;
  notification_sent: Record<string, string> | null;
  acknowledged_by: number | null;
  acknowledged_at: string | null;
}

export interface AlertRuleCreate {
  location_id?: number | null;
  device_id?: number | null;
  name: string;
  check_type: string;
  variable_key: string;
  threshold_value?: number | null;
  threshold_min?: number | null;
  threshold_max?: number | null;
  time_window_minutes?: number | null;
  enabled?: boolean;
  cooldown_minutes?: number;
  notification_channels: string[];
  webhook_url?: string | null;
}

export interface AlertRuleUpdate {
  location_id?: number | null;
  device_id?: number | null;
  name?: string;
  check_type?: string;
  variable_key?: string;
  threshold_value?: number | null;
  threshold_min?: number | null;
  threshold_max?: number | null;
  time_window_minutes?: number | null;
  enabled?: boolean;
  cooldown_minutes?: number;
  notification_channels?: string[];
  webhook_url?: string | null;
}

export interface AlertStats {
  total_rules: number;
  active_rules: number;
  inactive_rules: number;
  total_alerts_triggered: number;
  unacknowledged_alerts: number;
  acknowledged_alerts: number;
}

// Service functions

export const listAlertRules = async (params?: {
  location_id?: number;
  device_id?: number;
  enabled?: boolean;
  skip?: number;
  limit?: number;
}): Promise<AlertRule[]> => {
  const response = await api.get('/alert-rules', { params });
  return response.data;
};

export const getAlertRule = async (ruleId: number): Promise<AlertRule> => {
  const response = await api.get(`/alert-rules/${ruleId}`);
  return response.data;
};

export const createAlertRule = async (ruleData: AlertRuleCreate): Promise<AlertRule> => {
  const response = await api.post('/alert-rules', ruleData);
  return response.data;
};

export const updateAlertRule = async (
  ruleId: number,
  ruleData: AlertRuleUpdate
): Promise<AlertRule> => {
  const response = await api.patch(`/alert-rules/${ruleId}`, ruleData);
  return response.data;
};

export const deleteAlertRule = async (ruleId: number): Promise<void> => {
  await api.delete(`/alert-rules/${ruleId}`);
};

export const listAlertHistory = async (params?: {
  rule_id?: number;
  device_id?: number;
  acknowledged?: boolean;
  skip?: number;
  limit?: number;
}): Promise<AlertHistory[]> => {
  const response = await api.get('/alert-history', { params });
  return response.data;
};

export const getAlertHistoryDetail = async (alertId: number): Promise<AlertHistory> => {
  const response = await api.get(`/alert-history/${alertId}`);
  return response.data;
};

export const acknowledgeAlert = async (alertId: number): Promise<AlertHistory> => {
  const response = await api.patch(`/alert-history/${alertId}/acknowledge`);
  return response.data;
};

export const getAlertStats = async (): Promise<AlertStats> => {
  const response = await api.get('/alert-stats');
  return response.data;
};

export default {
  listAlertRules,
  getAlertRule,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule,
  listAlertHistory,
  getAlertHistoryDetail,
  acknowledgeAlert,
  getAlertStats,
};
