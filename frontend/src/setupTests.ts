/**
 * Setup global de Vitest.
 *
 * Registra los matchers de jest-dom (toBeInTheDocument, etc.)
 * y limpia el DOM entre tests.
 */

import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

afterEach(() => {
  cleanup();
  localStorage.clear();
});
