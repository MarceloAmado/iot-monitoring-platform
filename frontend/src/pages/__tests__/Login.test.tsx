/**
 * Smoke test de la página de Login.
 */

import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { Login } from '@/pages/Login';
import { renderWithProviders } from '@/test-utils';

describe('Login', () => {
  it('renderiza el formulario de login', () => {
    renderWithProviders(<Login />, { route: '/login' });

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^contraseña/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /iniciar sesión/i })
    ).toBeInTheDocument();
  });

  it('tiene link de recuperación de contraseña', () => {
    renderWithProviders(<Login />, { route: '/login' });

    expect(
      screen.getByRole('link', { name: /olvidaste/i })
    ).toBeInTheDocument();
  });
});
