/**
 * Tests del modal de notificaciones (campana).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { NotificationsModal } from '@/components/alerts/NotificationsModal';
import { renderWithProviders } from '@/test-utils';
import * as alertService from '@/services/alertService';

vi.mock('@/services/alertService', () => ({
  listAlertHistory: vi.fn(),
  acknowledgeAlert: vi.fn(),
}));

const mockAlert = {
  id: 1,
  alert_rule_id: 1,
  device_id: 1,
  sensor_reading_id: null,
  triggered_at: new Date().toISOString(),
  value_observed: 30.5,
  message: 'Temperatura alta en Heladera_Lab_001',
  notification_sent: null,
  acknowledged_by: null,
  acknowledged_at: null,
};

describe('NotificationsModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('muestra las alertas sin reconocer', async () => {
    vi.mocked(alertService.listAlertHistory).mockResolvedValue([mockAlert]);

    renderWithProviders(<NotificationsModal isOpen={true} onClose={() => {}} />);

    await waitFor(() => {
      expect(
        screen.getByText('Temperatura alta en Heladera_Lab_001')
      ).toBeInTheDocument();
    });

    expect(alertService.listAlertHistory).toHaveBeenCalledWith({
      acknowledged: false,
      limit: 20,
    });
  });

  it('muestra estado vacío cuando no hay alertas', async () => {
    vi.mocked(alertService.listAlertHistory).mockResolvedValue([]);

    renderWithProviders(<NotificationsModal isOpen={true} onClose={() => {}} />);

    await waitFor(() => {
      expect(screen.getByText(/no hay alertas pendientes/i)).toBeInTheDocument();
    });
  });

  it('permite reconocer una alerta', async () => {
    vi.mocked(alertService.listAlertHistory).mockResolvedValue([mockAlert]);
    vi.mocked(alertService.acknowledgeAlert).mockResolvedValue({
      ...mockAlert,
      acknowledged_by: 1,
      acknowledged_at: new Date().toISOString(),
    });

    renderWithProviders(<NotificationsModal isOpen={true} onClose={() => {}} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /reconocer/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /reconocer/i }));

    await waitFor(() => {
      expect(alertService.acknowledgeAlert).toHaveBeenCalledWith(1);
    });
  });

  it('no consulta la API cuando está cerrado', () => {
    renderWithProviders(<NotificationsModal isOpen={false} onClose={() => {}} />);

    expect(alertService.listAlertHistory).not.toHaveBeenCalled();
  });
});
