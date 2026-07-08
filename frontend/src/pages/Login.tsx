/**
 * Login Page - IdeaMakers IoT Monitoring
 *
 * Split layout con hero image y formulario de login
 * Diseño responsive mobile-first
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { IMButton, IMInput, Logo } from '@/components/common';
import { useAuth } from '@/hooks/useAuth';

export const Login = () => {
  const { login, loginLoading, loginError } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});

  // Usar apiError solo para mostrar el error del hook
  const apiError = loginError ?
    (loginError as any).response?.data?.detail || 'Error al iniciar sesión. Verifica tus credenciales.'
    : '';

  // ========================================
  // HANDLERS
  // ========================================

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Limpiar error del campo cuando el usuario empieza a escribir
    if (errors[name as keyof typeof errors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: typeof errors = {};

    if (!formData.email) {
      newErrors.email = 'El email es requerido';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    // Llamar a login con objeto { email, password } que espera el hook
    // El hook maneja loading state y navegación automáticamente
    login({ email: formData.email, password: formData.password });
  };

  // ========================================
  // RENDER
  // ========================================

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* ========================================
          LEFT: Hero Section (Hidden on mobile)
          ======================================== */}
      <div className="hidden lg:flex items-center justify-center bg-gradient-to-br from-im-blue via-im-blue-light to-im-blue-hover relative overflow-hidden">
        {/* Background Pattern (opcional) */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-im-orange rounded-full filter blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-im-orange-soft rounded-full filter blur-3xl"></div>
        </div>

        {/* Hero Content */}
        <div className="relative z-10 text-white px-12 max-w-xl">
          {/* Logo blanco (si existe, sino usar horizontal normal) */}
          <div className="mb-8">
            <Logo variant="horizontal-white" height={60} className="mb-6" />
          </div>

          {/* Tagline */}
          <h1 className="font-montserrat text-4xl font-bold mb-4">
            Monitoreo IoT en Tiempo Real
          </h1>
          <p className="text-lg text-white/90 mb-8">
            Plataforma profesional para control de sensores de temperatura, humedad y presión.
            Alertas automáticas y visualización dinámica de datos.
          </p>

          {/* Features List */}
          <ul className="space-y-3">
            {[
              'Dashboard en tiempo real',
              'Alertas configurables',
              'Exportación de datos',
              'Gestión de usuarios RBAC',
            ].map((feature, index) => (
              <li key={index} className="flex items-center gap-3">
                <svg
                  className="w-5 h-5 text-im-orange-soft flex-shrink-0"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-white/90">{feature}</span>
              </li>
            ))}
          </ul>

          {/* Hero Image (si la tenés) */}
          {/* <img
            src="/assets/images/hero-iot-login.jpg"
            alt="IoT Monitoring"
            className="rounded-lg shadow-2xl mt-8"
          /> */}
        </div>
      </div>

      {/* ========================================
          RIGHT: Login Form
          ======================================== */}
      <div className="flex items-center justify-center p-6 bg-im-bg">
        <div className="w-full max-w-md">
          {/* Logo mobile (visible solo en mobile) */}
          <div className="lg:hidden mb-8 flex justify-center">
            <Logo variant="horizontal" height={80} />
          </div>

          {/* Card */}
          <div className="im-card">
            {/* Header */}
            <div className="mb-6">
              <h2 className="font-montserrat text-3xl font-bold text-im-blue mb-2">
                Iniciar Sesión
              </h2>
              <p className="text-im-neutral-500">
                Ingresa tus credenciales para acceder al sistema
              </p>
            </div>

            {/* API Error Alert */}
            {apiError && (
              <div
                className="mb-4 p-3 rounded-md bg-im-danger-light border border-im-danger text-im-danger text-sm"
                role="alert"
              >
                {apiError}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Email */}
              <IMInput
                label="Email"
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="tu@email.com"
                error={errors.email}
                required
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207"
                    />
                  </svg>
                }
              />

              {/* Password */}
              <IMInput
                label="Contraseña"
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                error={errors.password}
                required
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                    />
                  </svg>
                }
                rightIcon={
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="text-im-neutral-500 hover:text-im-neutral-900 transition-colors"
                    aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  >
                    {showPassword ? (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                        />
                      </svg>
                    ) : (
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                        />
                      </svg>
                    )}
                  </button>
                }
              />

              {/* Forgot Password Link */}
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-4 h-4 rounded border-im-neutral-300 text-im-orange focus:ring-im-orange-soft/30"
                  />
                  <span className="text-im-neutral-700">Recordarme</span>
                </label>

                <Link
                  to="/forgot-password"
                  className="text-im-orange hover:text-im-orange-hover font-semibold"
                >
                  ¿Olvidaste tu contraseña?
                </Link>
              </div>

              {/* Submit Button */}
              <IMButton
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                loading={loginLoading}
              >
                Iniciar Sesión
              </IMButton>
            </form>

            {/* Demo Credentials (solo en desarrollo) */}
            {import.meta.env.DEV && (
              <div className="mt-6 p-3 bg-im-info-light rounded-md border border-im-info/20">
                <p className="text-xs text-im-info font-semibold mb-1">
                  Credenciales de prueba:
                </p>
                <p className="text-xs text-im-info">
                  <strong>Email:</strong> admin@iot-monitoring.com<br />
                  <strong>Password:</strong> admin123
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-im-neutral-500 mt-6">
            Desarrollado por{' '}
            <a
              href="https://ideamakers.com.ar"
              target="_blank"
              rel="noopener noreferrer"
              className="text-im-orange hover:text-im-orange-hover font-semibold"
            >
              IdeaMakers
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
