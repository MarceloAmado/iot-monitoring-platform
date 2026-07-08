/**
 * ForgotPassword Page - IdeaMakers IoT Monitoring
 *
 * Página de recuperación de contraseña con:
 * - Split layout (hero + form)
 * - Estilo consistente con Login.tsx
 * - Validación y feedback de estado
 * - Success state con instrucciones
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authService } from '@/services/authService';
import { IMButton, IMInput, Logo } from '@/components/common';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

export const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const forgotPasswordMutation = useMutation({
    mutationFn: (email: string) => authService.forgotPassword(email),
    onSuccess: () => {
      setSubmitted(true);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    forgotPasswordMutation.mutate(email);
  };

  // ========================================
  // SUCCESS STATE
  // ========================================
  if (submitted) {
    return (
      <div className="min-h-screen flex">
        {/* Left Side - Hero (hidden on mobile) */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-im-blue via-im-blue-dark to-im-neutral-900 p-12 flex-col justify-between relative overflow-hidden">
          {/* Background Pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-20 left-20 w-72 h-72 bg-im-orange rounded-full blur-3xl"></div>
            <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl"></div>
          </div>

          {/* Logo */}
          <div className="relative z-10">
            <Logo variant="horizontal-white" height={48} />
          </div>

          {/* Hero Content */}
          <div className="relative z-10 text-white">
            <h1 className="font-montserrat text-4xl font-bold mb-6">
              Recuperación Segura
            </h1>
            <p className="text-xl text-im-neutral-100 leading-relaxed">
              Te enviaremos un enlace seguro para restablecer tu contraseña.
              El enlace expirará en 10 minutos por tu seguridad.
            </p>
          </div>

          {/* Footer */}
          <div className="relative z-10 text-im-neutral-300 text-sm">
            © {new Date().getFullYear()} IdeaMakers. Sistema IoT Monitoring.
          </div>
        </div>

        {/* Right Side - Success Message */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
          <div className="w-full max-w-md">
            {/* Mobile Logo */}
            <div className="lg:hidden mb-8 text-center">
              <Logo variant="horizontal" height={80} className="inline-block" />
            </div>

            {/* Success Card */}
            <div className="text-center">
              {/* Success Icon */}
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-im-success-light mb-6">
                <svg
                  className="h-8 w-8 text-im-success"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>

              {/* Title */}
              <h2 className="font-montserrat text-3xl font-bold text-im-neutral-900 mb-4">
                ¡Correo enviado!
              </h2>

              {/* Message */}
              <div className="bg-im-blue/5 border border-im-blue/20 rounded-lg p-6 mb-8">
                <p className="text-im-neutral-700 leading-relaxed mb-4">
                  Si el email <span className="font-semibold text-im-blue">{email}</span> existe en nuestro sistema,
                  recibirás un enlace de recuperación en los próximos minutos.
                </p>
                <p className="text-sm text-im-neutral-600">
                  ⏱️ El enlace expirará en <span className="font-semibold">10 minutos</span>
                </p>
              </div>

              {/* Instructions */}
              <div className="bg-im-neutral-50 border border-im-neutral-200 rounded-lg p-4 mb-8 text-left">
                <h3 className="font-semibold text-im-neutral-900 mb-2 text-sm">
                  Próximos pasos:
                </h3>
                <ol className="text-sm text-im-neutral-700 space-y-1 list-decimal list-inside">
                  <li>Revisa tu bandeja de entrada</li>
                  <li>Haz clic en el enlace de recuperación</li>
                  <li>Establece tu nueva contraseña</li>
                </ol>
              </div>

              {/* Back to Login */}
              <Link to="/login">
                <IMButton variant="secondary" className="w-full">
                  <ArrowLeftIcon className="h-4 w-4 mr-2" />
                  Volver al login
                </IMButton>
              </Link>

              {/* Resend link */}
              <button
                onClick={() => setSubmitted(false)}
                className="mt-4 text-sm text-im-neutral-500 hover:text-im-orange transition-colors"
              >
                ¿No recibiste el correo? Reenviar
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ========================================
  // FORM STATE
  // ========================================
  return (
    <div className="min-h-screen flex">
      {/* Left Side - Hero (hidden on mobile) */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-im-blue via-im-blue-dark to-im-neutral-900 p-12 flex-col justify-between relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-im-orange rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>

        {/* Logo */}
        <div className="relative z-10">
          <Logo variant="horizontal-white" height={48} />
        </div>

        {/* Hero Content */}
        <div className="relative z-10 text-white">
          <h1 className="font-montserrat text-4xl font-bold mb-6">
            ¿Olvidaste tu contraseña?
          </h1>
          <p className="text-xl text-im-neutral-100 leading-relaxed mb-8">
            No te preocupes, es normal. Ingresa tu email y te enviaremos
            instrucciones para recuperar el acceso a tu cuenta.
          </p>

          {/* Security Features */}
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-im-orange/20 rounded-full flex items-center justify-center mt-0.5">
                <svg className="w-4 h-4 text-im-orange" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold mb-1">Enlace seguro</h3>
                <p className="text-sm text-im-neutral-300">Token único de un solo uso</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-im-orange/20 rounded-full flex items-center justify-center mt-0.5">
                <svg className="w-4 h-4 text-im-orange" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold mb-1">Expiración automática</h3>
                <p className="text-sm text-im-neutral-300">10 minutos de validez</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-im-orange/20 rounded-full flex items-center justify-center mt-0.5">
                <svg className="w-4 h-4 text-im-orange" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold mb-1">Privacidad garantizada</h3>
                <p className="text-sm text-im-neutral-300">No revelamos información de cuentas</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10 text-im-neutral-300 text-sm">
          © {new Date().getFullYear()} IdeaMakers. Sistema IoT Monitoring.
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden mb-8 text-center">
            <Logo variant="horizontal" height={80} className="inline-block" />
          </div>

          {/* Back Link */}
          <div className="mb-6">
            <Link
              to="/login"
              className="inline-flex items-center text-sm text-im-neutral-600 hover:text-im-orange transition-colors"
            >
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Volver al login
            </Link>
          </div>

          {/* Form Header */}
          <div className="mb-8">
            <h1 className="font-montserrat text-3xl font-bold text-im-neutral-900 mb-2">
              Recuperar Contraseña
            </h1>
            <p className="text-im-neutral-600">
              Ingresa tu email y te enviaremos un enlace para restablecer tu contraseña
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Email Input */}
            <div>
              <label htmlFor="email" className="im-label">
                Email
              </label>
              <IMInput
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@iot-monitoring.com"
                required
                autoFocus
                leftIcon={
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                }
              />
            </div>

            {/* Error Message */}
            {forgotPasswordMutation.isError && (
              <div className="bg-im-danger-light border border-im-danger/30 text-im-danger px-4 py-3 rounded-lg">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm">
                    Error al enviar el correo. Por favor, intenta nuevamente.
                  </p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <IMButton
              type="submit"
              variant="primary"
              size="lg"
              disabled={forgotPasswordMutation.isPending}
              loading={forgotPasswordMutation.isPending}
              className="w-full"
            >
              {forgotPasswordMutation.isPending ? 'Enviando...' : 'Enviar enlace de recuperación'}
            </IMButton>

            {/* Info Box */}
            <div className="bg-im-neutral-50 border border-im-neutral-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <svg className="w-5 h-5 text-im-blue flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-im-neutral-700">
                  Por seguridad, no revelamos si un email existe en nuestro sistema.
                  Si no recibes el correo, verifica la bandeja de spam.
                </p>
              </div>
            </div>
          </form>

          {/* Help Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-im-neutral-500">
              ¿Necesitas ayuda?{' '}
              <a href="mailto:soporte@ideamakers.com.ar" className="text-im-orange hover:text-im-orange-dark font-medium transition-colors">
                Contacta a soporte
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
