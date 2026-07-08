/**
 * Hook de WebSocket con Socket.IO para actualizaciones en tiempo real.
 *
 * Conecta al servidor Socket.IO del backend y permite suscribirse
 * a eventos de readings, device status y alertas.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { io, Socket } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_API_BASE_URL?.replace('/api/v1', '') || 'http://localhost:8000';

interface UseWebSocketOptions {
  /** ID del device para suscribirse a su room */
  deviceId?: number;
  /** Suscribirse al room del dashboard global */
  dashboard?: boolean;
}

interface WebSocketState {
  connected: boolean;
  lastEvent: string | null;
}

/**
 * Hook que conecta al servidor WebSocket y auto-invalida queries
 * cuando llegan datos nuevos.
 *
 * Uso en Dashboard:
 *   useWebSocket({ dashboard: true });
 *
 * Uso en DeviceDetail:
 *   useWebSocket({ deviceId: 5 });
 */
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { deviceId, dashboard = false } = options;
  const queryClient = useQueryClient();
  const socketRef = useRef<Socket | null>(null);
  const [state, setState] = useState<WebSocketState>({
    connected: false,
    lastEvent: null,
  });

  const handleNewReading = useCallback(
    (_data: { device_id: number }) => {
      setState((prev) => ({ ...prev, lastEvent: 'new_reading' }));

      // Invalidar queries de readings para que se refresquen
      if (deviceId) {
        queryClient.invalidateQueries({ queryKey: ['readings', String(deviceId)] });
      }

      // Invalidar lista de devices en dashboard (actualiza last_seen)
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
    [queryClient, deviceId]
  );

  const handleDeviceStatus = useCallback(
    (_data: { device_id: number }) => {
      setState((prev) => ({ ...prev, lastEvent: 'device_status' }));

      // Invalidar device específico y lista
      if (deviceId) {
        queryClient.invalidateQueries({ queryKey: ['device', String(deviceId)] });
      }
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
    [queryClient, deviceId]
  );

  const handleAlertTriggered = useCallback(
    (_data: { device_id: number }) => {
      setState((prev) => ({ ...prev, lastEvent: 'alert_triggered' }));
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
    [queryClient]
  );

  useEffect(() => {
    // Conectar al servidor Socket.IO
    const socket = io(WS_URL, {
      path: '/ws/socket.io',
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 2000,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setState((prev) => ({ ...prev, connected: true }));

      // Unirse a rooms según opciones
      if (dashboard) {
        socket.emit('join_dashboard');
      }
      if (deviceId) {
        socket.emit('join_device', { device_id: deviceId });
      }
    });

    socket.on('disconnect', () => {
      setState((prev) => ({ ...prev, connected: false }));
    });

    // Escuchar eventos
    socket.on('new_reading', handleNewReading);
    socket.on('device_status', handleDeviceStatus);
    socket.on('alert_triggered', handleAlertTriggered);

    return () => {
      // Salir de rooms antes de desconectar
      if (dashboard) {
        socket.emit('leave_dashboard');
      }
      if (deviceId) {
        socket.emit('leave_device', { device_id: deviceId });
      }
      socket.disconnect();
      socketRef.current = null;
    };
  }, [deviceId, dashboard, handleNewReading, handleDeviceStatus, handleAlertTriggered]);

  return {
    connected: state.connected,
    lastEvent: state.lastEvent,
  };
}

export default useWebSocket;
