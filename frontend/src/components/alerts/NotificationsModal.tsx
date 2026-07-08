/**
 * NotificationsModal - IdeaMakers IoT Monitoring
 *
 * Modal de notificaciones (campana del topbar): lista las alertas
 * sin reconocer y permite reconocerlas una a una.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { IMModal, IMButton, IMBadge } from '@/components/common';
import { listAlertHistory, acknowledgeAlert } from '@/services/alertService';
import type { AlertHistory } from '@/services/alertService';

interface NotificationsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const NotificationsModal = ({ isOpen, onClose }: NotificationsModalProps) => {
  const queryClient = useQueryClient();

  const { data: alerts, isLoading } = useQuery<AlertHistory[]>({
    queryKey: ['alerts', 'unacknowledged'],
    queryFn: () => listAlertHistory({ acknowledged: false, limit: 20 }),
    enabled: isOpen,
  });

  const acknowledgeMutation = useMutation({
    mutationFn: (alertId: number) => acknowledgeAlert(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  return (
    <IMModal
      isOpen={isOpen}
      onClose={onClose}
      title="Notificaciones"
      subtitle="Alertas pendientes de reconocer"
      size="md"
    >
      {isLoading ? (
        <div className="py-8 text-center">
          <div className="inline-block w-8 h-8 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
        </div>
      ) : alerts && alerts.length > 0 ? (
        <div className="divide-y divide-im-neutral-100 -mx-2">
          {alerts.map((alert) => (
            <div key={alert.id} className="flex items-start gap-3 px-2 py-3">
              <div className="flex-shrink-0 mt-1">
                <IMBadge variant="danger" size="sm">Alerta</IMBadge>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-im-neutral-900 break-words">{alert.message}</p>
                <p className="text-xs text-im-neutral-500 mt-1">
                  {formatDistanceToNow(new Date(alert.triggered_at), {
                    addSuffix: true,
                    locale: es,
                  })}
                </p>
              </div>
              <IMButton
                variant="ghost"
                size="sm"
                onClick={() => acknowledgeMutation.mutate(alert.id)}
                disabled={acknowledgeMutation.isPending}
              >
                Reconocer
              </IMButton>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-8 text-center">
          <svg
            className="mx-auto h-10 w-10 text-im-neutral-300"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <p className="mt-3 text-sm font-medium text-im-neutral-500">
            No hay alertas pendientes
          </p>
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-im-neutral-100 text-right">
        <Link to="/alerts" onClick={onClose}>
          <IMButton variant="secondary" size="sm">
            Ver historial completo →
          </IMButton>
        </Link>
      </div>
    </IMModal>
  );
};

export default NotificationsModal;
