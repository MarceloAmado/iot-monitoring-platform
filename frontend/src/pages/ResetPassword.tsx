/**
 * ResetPassword Page - IdeaMakers IoT Monitoring
 *
 * Página de reseteo de contraseña con token:
 * - Split layout (hero + form)
 * - Validación de contraseñas
 * - Mostrar/ocultar contraseña
 * - Success state con redirección automática
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authService } from '@/services/authService';
import { IMButton, IMInput, Logo } from '@/components/common';
import { ArrowLeftIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

export const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationError, setValidationError] = useState('');

  useEffect(() => {
    if (!token) {
      navigate('/login');
    }
  }, [token, navigate]);

  const resetPasswordMutation = useMutation({
    mutationFn: (data: { token: string; newPassword: string }) =>
      authService.resetPassword(data.token, data.newPassword),
    onSuccess: () => {
      // Redirigir al login después de 2 segundos
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError('');

    // Validaciones
    if (newPassword.length < 8) {
      setValidationError('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    if (newPassword !== confirmPassword) {
      setValidationError('Las contraseñas no coinciden');
      return;
    }

    if (!token) {
      setValidationError('Token inválido');
      return;
    }

    resetPasswordMutation.mutate({ token, newPassword });
  };

  // Validación de fortaleza de contraseña
  const getPasswordStrength = (): { score: number; label: string; color: string } => {
    if (!newPassword) return { score: 0, label: '', color: '' };

    let score = 0;
    if (newPassword.length >= 8) score++;
    if (newPassword.length >= 12) score++;
    if (/[a-z]/.test(newPassword) && /[A-Z]/.test(newPassword)) score++;
    if (/\d/.test(newPassword)) score++;
    if (/[^a-zA-Z0-9]/.test(newPassword)) score++;

    if (score <= 2) return { score: 33, label: 'Débil', color: 'bg-im-danger' };
    if (score <= 3) return { score: 66, label: 'Media', color: 'bg-im-warning' };
    return { score: 100, label: 'Fuerte', color: 'bg-im-success' };
  };

  const strength = getPasswordStrength();

  // ========================================
  // SUCCESS STATE
  // ========================================
  if (resetPasswordMutation.isSuccess) {
    return (
      <div className="min-h-screen flex">
        {/* Left Side - Hero */}
        <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-im-blue via-im-blue-dark to-im-neutral-900 p-12 flex-col justify-between relative overflow-hidden">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-20 left-20 w-72 h-72 bg-im-orange rounded-full blur-3xl"></div>
            <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl"></div>
          </div>

          <div className="relative z-10">
            <Logo variant="horizontal-white" height={48} />
          </div>

          <div className="relative z-10 text-white">
            <h1 className="font-montserrat text-4xl font-bold mb-6">
              ¡Contraseña Actualizada!
            </h1>
            <p className="text-xl text-im-neutral-100 leading-relaxed">
              Tu contraseña ha sido actualizada exitosamente.
              Ahora puedes iniciar sesión con tu nueva contraseña.
            </p>
          </div>

          <div className="relative z-10 text-im-neutral-300 text-sm">
            © {new Date().getFullYear()} IdeaMakers. Sistema IoT Monitoring.
          </div>
        </div>

        {/* Right Side - Success Message */}
        <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
          <div className="w-full max-w-md">
            <div className="lg:hidden mb-8 text-center">
              <Logo variant="horizontal" height={80} className="inline-block" />
            </div>

            <div className="text-center">
              {/* Success Icon */}
              <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-im-success-light mb-6">
                <svg className="h-8 w-8 text-im-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <h2 className="font-montserrat text-3xl font-bold text-im-neutral-900 mb-4">
                ¡Contraseña actualizada!
              </h2>

              <div className="bg-im-success-light/30 border border-im-success/30 rounded-lg p-6 mb-8">
                <p className="text-im-neutral-700 leading-relaxed mb-2">
                  Tu contraseña ha sido actualizada exitosamente.
                </p>
                <p className="text-sm text-im-neutral-600">
                  Redirigiendo al login en 2 segundos...
                </p>
              </div>

              {/* Loading Spinner */}
              <div className="inline-block w-8 h-8 border-4 border-im-neutral-200 border-t-im-orange rounded-full animate-spin"></div>
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
      {/* Left Side - Hero */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-im-blue via-im-blue-dark to-im-neutral-900 p-12 flex-col justify-between relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-im-orange rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10">
          <Logo variant="horizontal-white" height={48} />
        </div>

        <div className="relative z-10 text-white">
          <h1 className="font-montserrat text-4xl font-bold mb-6">
            Nueva Contraseña
          </h1>
          <p className="text-xl text-im-neutral-100 leading-relaxed mb-8">
            Crea una contraseña segura para proteger tu cuenta.
            Recomendamos usar una combinación de letras, números y caracteres especiales.
          </p>

          {/* Password Tips */}
          <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg p-6">
            <h3 className="font-semibold mb-3">Consejos para una contraseña segura:</h3>
            <ul className="space-y-2 text-sm text-im-neutral-200">
              <li className="flex items-start gap-2">
                <span className="text-im-orange mt-0.5">•</span>
                <span>Mínimo 8 caracteres (recomendado 12+)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-im-orange mt-0.5">•</span>
                <span>Combina mayúsculas y minúsculas</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-im-orange mt-0.5">•</span>
                <span>Incluye números y símbolos</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-im-orange mt-0.5">•</span>
                <span>Evita palabras comunes o datos personales</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="relative z-10 text-im-neutral-300 text-sm">
          © {new Date().getFullYear()} IdeaMakers. Sistema IoT Monitoring.
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-md">
          <div className="lg:hidden mb-8 text-center">
            <Logo variant="horizontal" height={80} className="inline-block" />
          </div>

          <div className="mb-6">
            <Link
              to="/login"
              className="inline-flex items-center text-sm text-im-neutral-600 hover:text-im-orange transition-colors"
            >
              <ArrowLeftIcon className="h-4 w-4 mr-2" />
              Volver al login
            </Link>
          </div>

          <div className="mb-8">
            <h1 className="font-montserrat text-3xl font-bold text-im-neutral-900 mb-2">
              Establecer Nueva Contraseña
            </h1>
            <p className="text-im-neutral-600">
              Ingresa y confirma tu nueva contraseña
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Nueva Contraseña */}
            <div>
              <label htmlFor="newPassword" className="im-label">
                Nueva Contraseña
              </label>
              <div className="relative">
                <IMInput
                  id="newPassword"
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Mínimo 8 caracteres"
                  required
                  autoFocus
                  leftIcon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  }
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-im-neutral-500 hover:text-im-neutral-700 transition-colors"
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>

              {/* Password Strength Indicator */}
              {newPassword && (
                <div className="mt-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-im-neutral-600">Fortaleza:</span>
                    <span className={`text-xs font-semibold ${
                      strength.label === 'Fuerte' ? 'text-im-success' :
                      strength.label === 'Media' ? 'text-im-warning' : 'text-im-danger'
                    }`}>
                      {strength.label}
                    </span>
                  </div>
                  <div className="w-full bg-im-neutral-200 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full ${strength.color} transition-all duration-300`}
                      style={{ width: `${strength.score}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Confirmar Contraseña */}
            <div>
              <label htmlFor="confirmPassword" className="im-label">
                Confirmar Contraseña
              </label>
              <div className="relative">
                <IMInput
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repetir contraseña"
                  required
                  leftIcon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  }
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-im-neutral-500 hover:text-im-neutral-700 transition-colors"
                  aria-label={showConfirmPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  {showConfirmPassword ? (
                    <EyeSlashIcon className="h-5 w-5" />
                  ) : (
                    <EyeIcon className="h-5 w-5" />
                  )}
                </button>
              </div>

              {/* Match Indicator */}
              {confirmPassword && (
                <div className="mt-2">
                  {newPassword === confirmPassword ? (
                    <p className="text-xs text-im-success flex items-center gap-1">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Las contraseñas coinciden
                    </p>
                  ) : (
                    <p className="text-xs text-im-danger flex items-center gap-1">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      Las contraseñas no coinciden
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Error Message */}
            {(validationError || resetPasswordMutation.isError) && (
              <div className="bg-im-danger-light border border-im-danger/30 text-im-danger px-4 py-3 rounded-lg">
                <div className="flex items-start gap-2">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm">
                    {validationError || 'Token inválido o expirado. Solicita un nuevo enlace de recuperación.'}
                  </p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <IMButton
              type="submit"
              variant="primary"
              size="lg"
              disabled={resetPasswordMutation.isPending}
              loading={resetPasswordMutation.isPending}
              className="w-full"
            >
              {resetPasswordMutation.isPending ? 'Actualizando...' : 'Actualizar Contraseña'}
            </IMButton>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
