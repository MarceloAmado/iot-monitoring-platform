/**
 * Alerts Page - IdeaMakers IoT Monitoring
 *
 * Sistema de alertas con:
 * - Configuración de reglas (RBAC)
 * - Historial de alertas con timeline
 * - Estadísticas en tiempo real
 * - Notificaciones multi-canal
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMButton, IMBadge } from '@/components/common';
import {
  listAlertRules,
  listAlertHistory,
  getAlertStats,
  acknowledgeAlert,
  deleteAlertRule,
  type AlertRule,
} from '../services/alertService';
import AlertRuleForm from '../components/alerts/AlertRuleForm';
import { RoleGate } from '../components/auth/RoleGate';
import { usePermissions } from '../hooks/usePermissions';

export default function Alerts() {
  const queryClient = useQueryClient();
  const { canWrite } = usePermissions();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);
  const [activeTab, setActiveTab] = useState<'rules' | 'history'>('rules');

  // ========================================
  // QUERIES
  // ========================================

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['alert-stats'],
    queryFn: getAlertStats,
    refetchInterval: 60000, // Refresh cada 60 segundos
  });

  const { data: rules, isLoading: rulesLoading } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: () => listAlertRules(),
    refetchInterval: 30000,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['alert-history'],
    queryFn: () => listAlertHistory({ limit: 50 }),
    refetchInterval: 30000,
  });

  // ========================================
  // MUTATIONS
  // ========================================

  const acknowledgeMutation = useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-history'] });
      queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAlertRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
      queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
    },
  });

  // ========================================
  // HANDLERS
  // ========================================

  const handleAcknowledge = (alertId: number) => {
    if (confirm('¿Marcar esta alerta como vista?')) {
      acknowledgeMutation.mutate(alertId);
    }
  };

  const handleDeleteRule = (ruleId: number, ruleName: string) => {
    if (confirm(`¿Eliminar la regla "${ruleName}"? Esta acción no se puede deshacer.`)) {
      deleteMutation.mutate(ruleId);
    }
  };

  const handleEditRule = (rule: AlertRule) => {
    setEditingRule(rule);
    setShowCreateForm(true);
  };

  const handleFormClose = () => {
    setShowCreateForm(false);
    setEditingRule(null);
  };

  const handleFormSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    queryClient.invalidateQueries({ queryKey: ['alert-stats'] });
    handleFormClose();
  };

  // ========================================
  // HELPER FUNCTIONS
  // ========================================

  const getCheckTypeLabel = (checkType: string): string => {
    const labels: Record<string, string> = {
      THRESHOLD_ABOVE: 'Supera umbral',
      THRESHOLD_BELOW: 'Bajo umbral',
      THRESHOLD_RANGE: 'Fuera de rango',
      RATE_OF_CHANGE: 'Cambio rápido',
      DEVICE_OFFLINE: 'Device offline',
      SENSOR_FAULT: 'Sensor roto',
    };
    return labels[checkType] || checkType;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString('es-AR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatRelativeTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins} min`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `Hace ${diffHours}h`;

    const diffDays = Math.floor(diffHours / 24);
    return `Hace ${diffDays}d`;
  };

  // ========================================
  // MAIN RENDER
  // ========================================

  return (
    <Layout
      title="Sistema de Alertas"
      breadcrumbs={[
        { label: 'Inicio', href: '/' },
        { label: 'Alertas' }
      ]}
    >
      {/* Page Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="font-montserrat text-3xl font-bold text-im-blue">Sistema de Alertas</h1>
          <p className="text-im-neutral-500 mt-1">
            Configura reglas y revisa el historial de alertas del sistema
          </p>
        </div>
        <RoleGate roles={['super_admin', 'service_admin']}>
          <IMButton
            variant="primary"
            size="md"
            onClick={() => setShowCreateForm(true)}
          >
            + Nueva Regla
          </IMButton>
        </RoleGate>
      </div>

      {/* ========================================
          STATS GRID (6 cards)
          ======================================== */}
      {statsLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="inline-block w-12 h-12 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
            <p className="mt-4 text-im-neutral-500 font-medium">Cargando estadísticas...</p>
          </div>
        </div>
      ) : stats ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 lg:gap-6 mb-8">
          {/* Total Reglas */}
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Total Reglas</p>
                <p className="text-3xl font-bold text-im-neutral-900">{stats.total_rules}</p>
              </div>
              <div className="p-3 rounded-md text-im-blue bg-im-blue/10">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
            </div>
          </IMCard>

          {/* Activas */}
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Activas</p>
                <p className="text-3xl font-bold text-im-success">{stats.active_rules}</p>
              </div>
              <div className="p-3 rounded-md text-im-success bg-im-success-light">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </IMCard>

          {/* Inactivas */}
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Inactivas</p>
                <p className="text-3xl font-bold text-im-neutral-500">{stats.inactive_rules}</p>
              </div>
              <div className="p-3 rounded-md text-im-neutral-500 bg-im-neutral-100">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
              </div>
            </div>
          </IMCard>

          {/* Total Alertas */}
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Total Alertas</p>
                <p className="text-3xl font-bold text-im-neutral-900">{stats.total_alerts_triggered}</p>
              </div>
              <div className="p-3 rounded-md text-im-orange bg-im-orange/10">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
            </div>
          </IMCard>

          {/* Sin Revisar */}
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Sin Revisar</p>
                <p className="text-3xl font-bold text-im-danger">{stats.unacknowledged_alerts}</p>
              </div>
              <div className="p-3 rounded-md text-im-danger bg-im-danger-light">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
          </IMCard>

          {/* Revisadas */}
          <IMCard hoverable className="hover-lift">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-im-neutral-500 mb-1">Revisadas</p>
                <p className="text-3xl font-bold text-im-success">{stats.acknowledged_alerts}</p>
              </div>
              <div className="p-3 rounded-md text-im-success bg-im-success-light">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </IMCard>
        </div>
      ) : null}

      {/* ========================================
          TABS (IM Design)
          ======================================== */}
      <div className="border-b border-im-neutral-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('rules')}
            className={`py-4 px-1 border-b-2 font-semibold text-sm transition-colors ${
              activeTab === 'rules'
                ? 'border-im-orange text-im-orange'
                : 'border-transparent text-im-neutral-500 hover:text-im-neutral-700 hover:border-im-neutral-300'
            }`}
          >
            Reglas Configuradas
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-4 px-1 border-b-2 font-semibold text-sm transition-colors ${
              activeTab === 'history'
                ? 'border-im-orange text-im-orange'
                : 'border-transparent text-im-neutral-500 hover:text-im-neutral-700 hover:border-im-neutral-300'
            }`}
          >
            Historial de Alertas
            {stats && stats.unacknowledged_alerts > 0 && (
              <IMBadge variant="danger" size="sm" className="ml-2">
                {stats.unacknowledged_alerts}
              </IMBadge>
            )}
          </button>
        </nav>
      </div>

      {/* ========================================
          TAB CONTENT: REGLAS
          ======================================== */}
      {activeTab === 'rules' && (
        <IMCard padding="none">
          {rulesLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="text-center">
                <div className="inline-block w-12 h-12 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
                <p className="mt-4 text-im-neutral-500 font-medium">Cargando reglas...</p>
              </div>
            </div>
          ) : rules && rules.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="im-table">
                <thead>
                  <tr>
                    <th>Nombre</th>
                    <th>Tipo</th>
                    <th>Variable</th>
                    <th>Estado</th>
                    <th>Canales</th>
                    <th className="text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {rules.map((rule) => (
                    <tr key={rule.id}>
                      {/* Nombre */}
                      <td>
                        <div>
                          <div className="font-semibold text-im-neutral-900">{rule.name}</div>
                          <div className="text-xs text-im-neutral-500 mt-0.5">
                            Cooldown: {rule.cooldown_minutes} min
                          </div>
                        </div>
                      </td>

                      {/* Tipo */}
                      <td>
                        <IMBadge variant="info" size="sm">
                          {getCheckTypeLabel(rule.check_type)}
                        </IMBadge>
                      </td>

                      {/* Variable */}
                      <td>
                        <code className="text-xs bg-im-neutral-100 px-2 py-1 rounded text-im-neutral-700">
                          {rule.variable_key}
                        </code>
                      </td>

                      {/* Estado */}
                      <td>
                        {rule.enabled ? (
                          <IMBadge variant="success" size="sm">Activa</IMBadge>
                        ) : (
                          <IMBadge variant="neutral" size="sm">Inactiva</IMBadge>
                        )}
                      </td>

                      {/* Canales */}
                      <td>
                        <div className="flex gap-1 flex-wrap">
                          {rule.notification_channels.map((channel) => (
                            <IMBadge key={channel} variant="neutral" size="sm">
                              {channel}
                            </IMBadge>
                          ))}
                        </div>
                      </td>

                      {/* Acciones */}
                      <td className="text-right space-x-2">
                        <RoleGate roles={['super_admin', 'service_admin']}>
                          <IMButton
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditRule(rule)}
                          >
                            Editar
                          </IMButton>
                          <IMButton
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteRule(rule.id, rule.name)}
                            className="text-im-danger hover:text-im-danger hover:bg-im-danger-light"
                          >
                            Eliminar
                          </IMButton>
                        </RoleGate>
                        {!canWrite() && (
                          <span className="text-im-neutral-400 text-xs">Solo lectura</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            // Empty State
            <div className="py-16 text-center">
              <svg
                className="mx-auto h-12 w-12 text-im-neutral-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
              <h3 className="mt-4 text-sm font-semibold text-im-neutral-900">
                No hay reglas configuradas
              </h3>
              <p className="mt-1 text-im-neutral-500">
                Comienza creando tu primera regla de alerta
              </p>
              <div className="mt-6">
                <RoleGate roles={['super_admin', 'service_admin']}>
                  <IMButton
                    variant="primary"
                    onClick={() => setShowCreateForm(true)}
                  >
                    + Crear primera regla
                  </IMButton>
                </RoleGate>
              </div>
            </div>
          )}
        </IMCard>
      )}

      {/* ========================================
          TAB CONTENT: HISTORIAL (Timeline Design)
          ======================================== */}
      {activeTab === 'history' && (
        <IMCard padding="lg">
          {historyLoading ? (
            <div className="flex items-center justify-center py-16">
              <div className="text-center">
                <div className="inline-block w-12 h-12 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
                <p className="mt-4 text-im-neutral-500 font-medium">Cargando historial...</p>
              </div>
            </div>
          ) : history && history.length > 0 ? (
            // Timeline Design
            <div className="space-y-6">
              {history.map((alert, index) => (
                <div key={alert.id} className="relative">
                  {/* Timeline connector */}
                  {index < history.length - 1 && (
                    <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-im-neutral-200" />
                  )}

                  {/* Alert Card */}
                  <div className={`flex gap-4 ${alert.acknowledged_by ? '' : 'bg-im-danger-light/20 -mx-4 px-4 py-3 rounded-lg'}`}>
                    {/* Icon */}
                    <div className="flex-shrink-0 relative">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        alert.acknowledged_by
                          ? 'bg-im-success-light text-im-success'
                          : 'bg-im-danger-light text-im-danger'
                      }`}>
                        {alert.acknowledged_by ? (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      {/* Header */}
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div>
                          <p className="text-sm font-semibold text-im-neutral-900">
                            {alert.message}
                          </p>
                          <p className="text-xs text-im-neutral-500 mt-1">
                            {formatDate(alert.triggered_at)} · {formatRelativeTime(alert.triggered_at)}
                          </p>
                        </div>
                        <div>
                          {alert.acknowledged_by ? (
                            <IMBadge variant="success" size="sm">Revisada</IMBadge>
                          ) : (
                            <IMBadge variant="danger" size="sm">Sin revisar</IMBadge>
                          )}
                        </div>
                      </div>

                      {/* Notification Status */}
                      {alert.notification_sent && (
                        <div className="flex gap-3 mb-3">
                          {Object.entries(alert.notification_sent).map(([channel, status]) => (
                            <div key={channel} className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full ${
                                status === 'success' ? 'bg-im-success' : 'bg-im-danger'
                              }`} />
                              <span className="text-xs text-im-neutral-600">
                                {channel}: <span className={status === 'success' ? 'text-im-success' : 'text-im-danger'}>
                                  {status}
                                </span>
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Actions */}
                      {!alert.acknowledged_by && (
                        <div className="mt-3">
                          <IMButton
                            variant="secondary"
                            size="sm"
                            onClick={() => handleAcknowledge(alert.id)}
                            disabled={acknowledgeMutation.isPending}
                          >
                            Marcar como vista
                          </IMButton>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            // Empty State
            <div className="py-16 text-center">
              <svg
                className="mx-auto h-12 w-12 text-im-neutral-300"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-4 text-sm font-semibold text-im-neutral-900">
                No hay alertas en el historial
              </h3>
              <p className="mt-1 text-im-neutral-500">
                Las alertas disparadas aparecerán aquí
              </p>
            </div>
          )}
        </IMCard>
      )}

      {/* ========================================
          MODAL FORM
          ======================================== */}
      {showCreateForm && (
        <AlertRuleForm
          rule={editingRule}
          onClose={handleFormClose}
          onSuccess={handleFormSuccess}
        />
      )}
    </Layout>
  );
}
