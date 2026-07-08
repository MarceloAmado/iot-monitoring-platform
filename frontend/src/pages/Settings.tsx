/**
 * Settings - Página de configuración del sistema
 *
 * Configuraciones generales de la aplicación:
 * - Preferencias de notificaciones
 * - Configuración de alertas
 * - Opciones de visualización
 * - Información del sistema
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMButton, IMBadge } from '@/components/common';
import { useAuth } from '@/hooks/useAuth';
import { authService } from '@/services/authService';

// ========================================
// TYPES
// ========================================

interface NotificationSettings {
  emailAlerts: boolean;
  telegramAlerts: boolean;
  webhookAlerts: boolean;
  soundNotifications: boolean;
}

interface DisplaySettings {
  theme: 'light' | 'dark' | 'auto';
  language: 'es' | 'en';
  dateFormat: 'dd/mm/yyyy' | 'mm/dd/yyyy' | 'yyyy-mm-dd';
  timezone: string;
}

// ========================================
// MAIN COMPONENT
// ========================================

export const Settings = () => {
  const { user } = useAuth();

  // ========================================
  // STATE
  // ========================================

  // Las preferencias guardadas viajan en el usuario (users.preferences JSONB)
  const savedPrefs = (user?.preferences ?? {}) as {
    notifications?: Partial<NotificationSettings>;
    display?: Partial<DisplaySettings>;
  };

  const [notificationSettings, setNotificationSettings] = useState<NotificationSettings>({
    emailAlerts: true,
    telegramAlerts: false,
    webhookAlerts: false,
    soundNotifications: true,
    ...savedPrefs.notifications,
  });

  const [displaySettings, setDisplaySettings] = useState<DisplaySettings>({
    theme: 'light',
    language: 'es',
    dateFormat: 'dd/mm/yyyy',
    timezone: 'America/Argentina/Buenos_Aires',
    ...savedPrefs.display,
  });

  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const savePreferencesMutation = useMutation({
    mutationFn: (preferences: Record<string, unknown>) =>
      authService.updateMyPreferences(preferences),
    onSuccess: () => {
      setSaveMessage('Preferencias guardadas correctamente');
      setTimeout(() => setSaveMessage(null), 3000);
    },
    onError: () => {
      setSaveMessage('Error al guardar las preferencias. Intenta nuevamente.');
      setTimeout(() => setSaveMessage(null), 5000);
    },
  });

  // ========================================
  // HANDLERS - NOTIFICATIONS
  // ========================================

  const handleToggleNotification = (key: keyof NotificationSettings) => {
    setNotificationSettings((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  const handleSaveNotificationSettings = () => {
    savePreferencesMutation.mutate({ notifications: notificationSettings });
  };

  // ========================================
  // HANDLERS - DISPLAY
  // ========================================

  const handleDisplaySettingChange = (key: keyof DisplaySettings, value: any) => {
    setDisplaySettings((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSaveDisplaySettings = () => {
    savePreferencesMutation.mutate({ display: displaySettings });
  };

  // ========================================
  // RENDER
  // ========================================

  const isAdmin = user?.role === 'super_admin' || user?.role === 'service_admin';

  return (
    <Layout
      title="Configuración"
      breadcrumbs={[{ label: 'Configuración' }]}
    >
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="font-montserrat text-3xl font-bold text-im-blue">Configuración</h1>
        <p className="text-im-neutral-500 mt-1">
          Personaliza la aplicación según tus preferencias
        </p>
      </div>

      {/* Save feedback */}
      {saveMessage && (
        <div
          className={`mb-6 rounded-md border p-3 text-sm font-medium ${
            saveMessage.startsWith('Error')
              ? 'bg-im-danger-light border-im-danger text-im-danger'
              : 'bg-im-success-light border-im-success text-im-success'
          }`}
        >
          {saveMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Settings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Notification Settings Card */}
          <IMCard
            title="Preferencias de Notificaciones"
            subtitle="Configura cómo deseas recibir las alertas del sistema"
          >
            <div className="space-y-4">
              {/* Email Alerts */}
              <div className="flex items-center justify-between py-3 border-b border-im-neutral-100 last:border-0">
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-im-neutral-900">
                    Alertas por Email
                  </h3>
                  <p className="text-sm text-im-neutral-500 mt-1">
                    Recibe notificaciones de alertas críticas por correo electrónico
                  </p>
                </div>
                <button
                  onClick={() => handleToggleNotification('emailAlerts')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notificationSettings.emailAlerts ? 'bg-im-orange' : 'bg-im-neutral-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notificationSettings.emailAlerts ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Telegram Alerts */}
              <div className="flex items-center justify-between py-3 border-b border-im-neutral-100 last:border-0">
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-im-neutral-900">
                    Alertas por Telegram
                  </h3>
                  <p className="text-sm text-im-neutral-500 mt-1">
                    Recibe notificaciones instantáneas en tu cuenta de Telegram
                  </p>
                </div>
                <button
                  onClick={() => handleToggleNotification('telegramAlerts')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notificationSettings.telegramAlerts ? 'bg-im-orange' : 'bg-im-neutral-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notificationSettings.telegramAlerts ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Webhook Alerts */}
              {isAdmin && (
                <div className="flex items-center justify-between py-3 border-b border-im-neutral-100 last:border-0">
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold text-im-neutral-900">
                      Webhooks
                    </h3>
                    <p className="text-sm text-im-neutral-500 mt-1">
                      Enviar notificaciones a endpoints HTTP personalizados
                    </p>
                  </div>
                  <button
                    onClick={() => handleToggleNotification('webhookAlerts')}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      notificationSettings.webhookAlerts ? 'bg-im-orange' : 'bg-im-neutral-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        notificationSettings.webhookAlerts ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              )}

              {/* Sound Notifications */}
              <div className="flex items-center justify-between py-3">
                <div className="flex-1">
                  <h3 className="text-sm font-semibold text-im-neutral-900">
                    Sonido de Notificaciones
                  </h3>
                  <p className="text-sm text-im-neutral-500 mt-1">
                    Reproducir sonido cuando lleguen nuevas alertas
                  </p>
                </div>
                <button
                  onClick={() => handleToggleNotification('soundNotifications')}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notificationSettings.soundNotifications ? 'bg-im-orange' : 'bg-im-neutral-300'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notificationSettings.soundNotifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="pt-4 border-t border-im-neutral-100">
                <IMButton
                  variant="primary"
                  onClick={handleSaveNotificationSettings}
                  disabled={savePreferencesMutation.isPending}
                >
                  {savePreferencesMutation.isPending ? 'Guardando...' : 'Guardar Preferencias'}
                </IMButton>
              </div>
            </div>
          </IMCard>

          {/* Display Settings Card */}
          <IMCard
            title="Preferencias de Visualización"
            subtitle="Personaliza cómo se muestra la información"
          >
            <div className="space-y-4">
              {/* Theme */}
              <div>
                <label className="text-sm font-semibold text-im-neutral-900 mb-2 block">
                  Tema
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['light', 'dark', 'auto'] as const).map((theme) => (
                    <button
                      key={theme}
                      onClick={() => handleDisplaySettingChange('theme', theme)}
                      className={`px-4 py-3 rounded-md border-2 transition-all ${
                        displaySettings.theme === theme
                          ? 'border-im-orange bg-im-orange/10 text-im-orange font-semibold'
                          : 'border-im-neutral-200 hover:border-im-neutral-300'
                      }`}
                    >
                      {theme === 'light' ? '☀️ Claro' : theme === 'dark' ? '🌙 Oscuro' : '🔄 Auto'}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-im-neutral-500 mt-2">
                  {displaySettings.theme === 'auto'
                    ? 'Se ajustará según tu sistema operativo'
                    : 'Tema fijo seleccionado'}
                </p>
              </div>

              {/* Language - Deshabilitado hasta implementar */}
              <div className="opacity-50">
                <label className="text-sm font-semibold text-im-neutral-900 mb-2 block">
                  Idioma
                  <span className="ml-2 text-xs font-normal text-im-warning">(Próximamente)</span>
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {(['es', 'en'] as const).map((lang) => (
                    <button
                      key={lang}
                      disabled
                      className={`px-4 py-3 rounded-md border-2 transition-all cursor-not-allowed ${
                        lang === 'es'
                          ? 'border-im-orange bg-im-orange/10 text-im-orange font-semibold'
                          : 'border-im-neutral-200'
                      }`}
                    >
                      {lang === 'es' ? '🇪🇸 Español' : '🇺🇸 English'}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-im-neutral-500 mt-2">
                  La funcionalidad de cambio de idioma estará disponible en una próxima versión
                </p>
              </div>

              {/* Date Format */}
              <div>
                <label className="text-sm font-semibold text-im-neutral-900 mb-2 block">
                  Formato de Fecha
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {(['dd/mm/yyyy', 'mm/dd/yyyy', 'yyyy-mm-dd'] as const).map((format) => (
                    <button
                      key={format}
                      onClick={() => handleDisplaySettingChange('dateFormat', format)}
                      className={`px-4 py-3 rounded-md border-2 transition-all text-sm ${
                        displaySettings.dateFormat === format
                          ? 'border-im-orange bg-im-orange/10 text-im-orange font-semibold'
                          : 'border-im-neutral-200 hover:border-im-neutral-300'
                      }`}
                    >
                      {format}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-im-neutral-100">
                <IMButton
                  variant="primary"
                  onClick={handleSaveDisplaySettings}
                  disabled={savePreferencesMutation.isPending}
                >
                  {savePreferencesMutation.isPending ? 'Guardando...' : 'Guardar Preferencias'}
                </IMButton>
              </div>
            </div>
          </IMCard>
        </div>

        {/* Right Column - System Info */}
        <div className="space-y-6">
          {/* System Information Card */}
          <IMCard title="Información del Sistema">
            <div className="space-y-4">
              <div>
                <p className="text-sm text-im-neutral-500 mb-1">Versión</p>
                <IMBadge variant="info" size="md">
                  v1.1.0
                </IMBadge>
              </div>

              <div>
                <p className="text-sm text-im-neutral-500 mb-1">Entorno</p>
                <IMBadge variant="warning" size="md">
                  Desarrollo
                </IMBadge>
              </div>

              <div>
                <p className="text-sm text-im-neutral-500 mb-1">Backend API</p>
                <p className="text-xs font-mono text-im-neutral-700 bg-im-neutral-50 px-2 py-1 rounded">
                  {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}
                </p>
              </div>

              <div>
                <p className="text-sm text-im-neutral-500 mb-1">Estado del Servidor</p>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-im-success rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-im-success">Conectado</span>
                </div>
              </div>
            </div>
          </IMCard>

          {/* Quick Actions Card */}
          <IMCard title="Acciones Rápidas">
            <div className="space-y-3">
              <IMButton variant="ghost" size="sm" fullWidth>
                📄 Ver Documentación
              </IMButton>
              <IMButton variant="ghost" size="sm" fullWidth>
                🐛 Reportar Problema
              </IMButton>
              <IMButton variant="ghost" size="sm" fullWidth>
                💡 Solicitar Función
              </IMButton>
              <IMButton variant="ghost" size="sm" fullWidth>
                📊 Ver Logs del Sistema
              </IMButton>
            </div>
          </IMCard>

          {/* Danger Zone (Admin Only) */}
          {isAdmin && (
            <IMCard title="Zona de Peligro">
              <div className="space-y-3">
                <p className="text-sm text-im-neutral-600 mb-4">
                  Acciones que requieren confirmación adicional
                </p>
                <IMButton variant="danger" size="sm" fullWidth>
                  🗑️ Limpiar Cache
                </IMButton>
                <IMButton variant="danger" size="sm" fullWidth>
                  ⚠️ Reiniciar Sistema
                </IMButton>
              </div>
            </IMCard>
          )}
        </div>
      </div>

      {/* Info Banner */}
      <div className="mt-8 bg-im-blue/5 border border-im-blue/20 rounded-md p-4">
        <div className="flex items-start gap-3">
          <svg
            className="w-5 h-5 text-im-blue flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <p className="text-sm font-semibold text-im-blue mb-1">
              Nota sobre configuraciones
            </p>
            <p className="text-sm text-im-neutral-700">
              Tus preferencias se guardan en el servidor asociadas a tu cuenta,
              por lo que se mantienen en todos tus dispositivos. El cambio de
              idioma estará disponible en una próxima versión.
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Settings;
