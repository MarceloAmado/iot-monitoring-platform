/**
 * Tests unitarios del hook useWebSocket.
 *
 * Mockea socket.io-client para verificar conexión, suscripción a rooms
 * e invalidación de queries ante eventos.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React, { ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock de socket.io-client
type Handler = (data: unknown) => void;

const handlers: Record<string, Handler> = {};
const mockSocket = {
  on: vi.fn((event: string, handler: Handler) => {
    handlers[event] = handler;
  }),
  emit: vi.fn(),
  disconnect: vi.fn(),
};

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => mockSocket),
}));

import { io } from 'socket.io-client';
import { useWebSocket } from '@/hooks/useWebSocket';

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe('useWebSocket', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    Object.keys(handlers).forEach((k) => delete handlers[k]);
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  });

  it('conecta al servidor con el path de Socket.IO', () => {
    renderHook(() => useWebSocket({ dashboard: true }), {
      wrapper: createWrapper(queryClient),
    });

    expect(io).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ path: '/ws/socket.io' })
    );
  });

  it('se une al room del dashboard al conectar', () => {
    renderHook(() => useWebSocket({ dashboard: true }), {
      wrapper: createWrapper(queryClient),
    });

    // Simular evento connect
    act(() => {
      handlers['connect']?.(undefined);
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('join_dashboard');
  });

  it('se une al room del device cuando se pasa deviceId', () => {
    renderHook(() => useWebSocket({ deviceId: 5 }), {
      wrapper: createWrapper(queryClient),
    });

    act(() => {
      handlers['connect']?.(undefined);
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('join_device', { device_id: 5 });
  });

  it('invalida queries de devices al recibir new_reading', () => {
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    renderHook(() => useWebSocket({ dashboard: true }), {
      wrapper: createWrapper(queryClient),
    });

    act(() => {
      handlers['new_reading']?.({ device_id: 1 });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['devices'] });
  });

  it('invalida queries de alerts al recibir alert_triggered', () => {
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    renderHook(() => useWebSocket({ dashboard: true }), {
      wrapper: createWrapper(queryClient),
    });

    act(() => {
      handlers['alert_triggered']?.({ device_id: 1, alert_id: 10 });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['alerts'] });
  });

  it('desconecta el socket al desmontar', () => {
    const { unmount } = renderHook(() => useWebSocket({ dashboard: true }), {
      wrapper: createWrapper(queryClient),
    });

    unmount();

    expect(mockSocket.disconnect).toHaveBeenCalled();
  });
});
