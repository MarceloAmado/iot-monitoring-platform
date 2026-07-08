/**
 * Configuración ESLint — Vite + React 18 + TypeScript.
 *
 * Reglas pragmáticas: el objetivo es detectar errores reales
 * (hooks mal usados, variables sin usar, imports rotos), no pelear
 * con el estilo del código existente.
 */

module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': 'off',
    // El codebase usa `any` en helpers de UI; endurecer esto es deuda aparte
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-unused-vars': [
      'error',
      { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
  },
};
