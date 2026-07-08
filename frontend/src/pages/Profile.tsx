/**
 * Profile - Página de perfil del usuario
 *
 * Permite al usuario ver y editar su información personal:
 * - Foto de perfil con upload
 * - Nombre y apellido
 * - Email
 * - Teléfono (para notificaciones Telegram)
 * - Cambiar contraseña
 * - Ver rol y permisos
 */

import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { IMCard, IMInput, IMButton, IMBadge } from '@/components/common';
import authService from '@/services/authService';
import userService from '@/services/userService';
import uploadService from '@/services/uploadService';
import type { User } from '@/types';

// ========================================
// TYPES
// ========================================

interface ProfileFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
}

interface PasswordFormData {
  old_password: string;
  new_password: string;
  confirm_password: string;
}

// ========================================
// HELPER: ROLE LABELS
// ========================================

const roleLabels: Record<string, { label: string; variant: any }> = {
  super_admin: { label: 'Super Administrador', variant: 'danger' },
  service_admin: { label: 'Administrador', variant: 'warning' },
  technician: { label: 'Técnico', variant: 'info' },
  guest: { label: 'Invitado', variant: 'neutral' },
};

// ========================================
// HELPER: GET INITIALS
// ========================================

const getInitials = (firstName: string, lastName: string): string => {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
};

// ========================================
// MAIN COMPONENT
// ========================================

export const Profile = () => {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ========================================
  // STATE
  // ========================================

  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const [profileForm, setProfileForm] = useState<ProfileFormData>({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
  });

  const [passwordForm, setPasswordForm] = useState<PasswordFormData>({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [profileErrors, setProfileErrors] = useState<Partial<ProfileFormData>>({});
  const [passwordErrors, setPasswordErrors] = useState<Partial<PasswordFormData>>({});

  // ========================================
  // QUERIES
  // ========================================

  const { data: user, isLoading } = useQuery<User>({
    queryKey: ['current-user'],
    queryFn: () => authService.getCurrentUser(),
  });

  useEffect(() => {
    if (user) {
      setProfileForm({
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email,
        phone_number: user.phone_number || '',
      });
    }
  }, [user]);

  // ========================================
  // MUTATIONS
  // ========================================

  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<User>) => userService.updateUser(user!.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      setIsEditingProfile(false);
      setSelectedFile(null);
      setPreviewUrl(null);
      alert('Perfil actualizado exitosamente');
    },
    onError: (error: any) => {
      console.error('Error actualizando perfil:', error);
      alert('Error al actualizar el perfil. Por favor intenta nuevamente.');
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: ({ oldPassword, newPassword }: { oldPassword: string; newPassword: string }) =>
      authService.changePassword(oldPassword, newPassword),
    onSuccess: () => {
      setPasswordForm({
        old_password: '',
        new_password: '',
        confirm_password: '',
      });
      setIsChangingPassword(false);
      alert('Contraseña cambiada exitosamente');
    },
    onError: (error: any) => {
      console.error('Error cambiando contraseña:', error);
      if (error?.response?.status === 401) {
        setPasswordErrors({ old_password: 'La contraseña actual es incorrecta' });
      } else {
        alert('Error al cambiar la contraseña. Por favor intenta nuevamente.');
      }
    },
  });

  // ========================================
  // MUTATIONS - PHOTO UPLOAD
  // ========================================

  const uploadPhotoMutation = useMutation({
    mutationFn: (file: File) => uploadService.uploadProfilePicture(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      alert('Foto de perfil actualizada exitosamente');
      setSelectedFile(null);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Error al subir la imagen';
      alert(message);
    },
  });

  const deletePhotoMutation = useMutation({
    mutationFn: (filename: string) => uploadService.deleteProfilePicture(filename),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-user'] });
      setPreviewUrl(null);
      alert('Foto de perfil eliminada exitosamente');
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Error al eliminar la imagen';
      alert(message);
    },
  });

  // ========================================
  // HANDLERS - PROFILE PICTURE
  // ========================================

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar usando el servicio
      const validation = uploadService.validateImageFile(file);
      if (!validation.valid) {
        alert(validation.error);
        return;
      }

      setSelectedFile(file);

      // Crear preview local
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUploadPhoto = () => {
    if (selectedFile) {
      uploadPhotoMutation.mutate(selectedFile);
    }
  };

  const handleRemovePhoto = () => {
    if (user?.profile_picture_url) {
      const filename = user.profile_picture_url.split('/').pop();
      if (filename) {
        deletePhotoMutation.mutate(filename);
      }
    }

    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // ========================================
  // HANDLERS - PROFILE
  // ========================================

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfileForm((prev) => ({ ...prev, [name]: value }));
    if (profileErrors[name as keyof ProfileFormData]) {
      setProfileErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleEditProfile = () => {
    setIsEditingProfile(true);
  };

  const handleCancelEditProfile = () => {
    setIsEditingProfile(false);
    if (user) {
      setProfileForm({
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email,
        phone_number: user.phone_number || '',
      });
    }
    setProfileErrors({});
    setSelectedFile(null);
    setPreviewUrl(null);
  };

  const validateProfileForm = (): boolean => {
    const errors: Partial<ProfileFormData> = {};

    if (!profileForm.first_name.trim()) {
      errors.first_name = 'El nombre es requerido';
    }

    if (!profileForm.last_name.trim()) {
      errors.last_name = 'El apellido es requerido';
    }

    if (!profileForm.email.trim()) {
      errors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profileForm.email)) {
      errors.email = 'Email inválido';
    }

    if (profileForm.phone_number && !/^\+?[\d\s\-()]+$/.test(profileForm.phone_number)) {
      errors.phone_number = 'Formato de teléfono inválido';
    }

    setProfileErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSaveProfile = async () => {
    if (!validateProfileForm()) return;

    // La foto se sube por separado con handleUploadPhoto
    // Aquí solo actualizamos datos de texto
    updateProfileMutation.mutate({
      first_name: profileForm.first_name.trim(),
      last_name: profileForm.last_name.trim(),
      email: profileForm.email.trim(),
      phone_number: profileForm.phone_number.trim() || null,
    });
  };

  // ========================================
  // HANDLERS - PASSWORD
  // ========================================

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordForm((prev) => ({ ...prev, [name]: value }));
    if (passwordErrors[name as keyof PasswordFormData]) {
      setPasswordErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleTogglePasswordForm = () => {
    setIsChangingPassword(!isChangingPassword);
    setPasswordForm({
      old_password: '',
      new_password: '',
      confirm_password: '',
    });
    setPasswordErrors({});
  };

  const validatePasswordForm = (): boolean => {
    const errors: Partial<PasswordFormData> = {};

    if (!passwordForm.old_password) {
      errors.old_password = 'La contraseña actual es requerida';
    }

    if (!passwordForm.new_password) {
      errors.new_password = 'La nueva contraseña es requerida';
    } else if (passwordForm.new_password.length < 8) {
      errors.new_password = 'La contraseña debe tener al menos 8 caracteres';
    }

    if (!passwordForm.confirm_password) {
      errors.confirm_password = 'Confirma tu nueva contraseña';
    } else if (passwordForm.new_password !== passwordForm.confirm_password) {
      errors.confirm_password = 'Las contraseñas no coinciden';
    }

    setPasswordErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleChangePassword = () => {
    if (!validatePasswordForm()) return;

    changePasswordMutation.mutate({
      oldPassword: passwordForm.old_password,
      newPassword: passwordForm.new_password,
    });
  };

  // ========================================
  // LOADING STATE
  // ========================================

  if (isLoading) {
    return (
      <Layout title="Mi Perfil">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="text-center">
            <div className="inline-block w-16 h-16 border-4 border-im-neutral-100 border-t-im-orange rounded-full animate-spin"></div>
            <p className="mt-4 text-im-neutral-500 font-medium">Cargando perfil...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!user) {
    return (
      <Layout title="Mi Perfil">
        <div className="text-center text-im-danger">Error al cargar el perfil</div>
      </Layout>
    );
  }

  const roleInfo = roleLabels[user.role] || { label: user.role, variant: 'neutral' };

  // Determinar URL de foto: preview local > foto del servidor
  const currentPhotoUrl = previewUrl || uploadService.getImageUrl(user.profile_picture_url);

  // ========================================
  // RENDER
  // ========================================

  return (
    <Layout
      title="Mi Perfil"
      breadcrumbs={[{ label: 'Mi Perfil' }]}
    >
      {/* Page Header */}
      <div className="mb-6">
        <h1 className="font-montserrat text-3xl font-bold text-im-blue">Mi Perfil</h1>
        <p className="text-im-neutral-500 mt-1">
          Gestiona tu información personal y configuración de cuenta
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Profile Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Profile Picture Card */}
          <IMCard title="Foto de Perfil">
            <div className="flex items-center gap-6">
              {/* Avatar */}
              <div className="relative">
                {currentPhotoUrl ? (
                  <img
                    src={currentPhotoUrl}
                    alt="Foto de perfil"
                    className="w-24 h-24 rounded-full object-cover border-4 border-im-neutral-100"
                  />
                ) : (
                  <div className="w-24 h-24 rounded-full bg-im-blue/10 border-4 border-im-neutral-100 flex items-center justify-center">
                    <span className="text-2xl font-bold text-im-blue">
                      {getInitials(user.first_name, user.last_name)}
                    </span>
                  </div>
                )}
                {isEditingProfile && (
                  <button
                    onClick={handleUploadClick}
                    className="absolute bottom-0 right-0 bg-im-orange text-white p-2 rounded-full shadow-lg hover:bg-im-orange-dark transition-colors"
                    aria-label="Cambiar foto"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Upload Controls */}
              <div className="flex-1">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                {isEditingProfile ? (
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-im-neutral-900">
                      {selectedFile ? selectedFile.name : 'Selecciona una imagen'}
                    </p>
                    <p className="text-xs text-im-neutral-500">
                      JPG, PNG o GIF. Máximo 5MB.
                    </p>
                    <div className="flex gap-2">
                      <IMButton variant="secondary" size="sm" onClick={handleUploadClick}>
                        Seleccionar Archivo
                      </IMButton>
                      {selectedFile && (
                        <IMButton
                          variant="primary"
                          size="sm"
                          onClick={handleUploadPhoto}
                          disabled={uploadPhotoMutation.isPending}
                        >
                          {uploadPhotoMutation.isPending ? 'Subiendo...' : 'Guardar Foto'}
                        </IMButton>
                      )}
                      {currentPhotoUrl && (
                        <IMButton
                          variant="ghost"
                          size="sm"
                          onClick={handleRemovePhoto}
                          disabled={deletePhotoMutation.isPending}
                        >
                          {deletePhotoMutation.isPending ? 'Eliminando...' : 'Quitar Foto'}
                        </IMButton>
                      )}
                    </div>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm font-medium text-im-neutral-900">
                      {user.first_name} {user.last_name}
                    </p>
                    <p className="text-sm text-im-neutral-500">{user.email}</p>
                  </div>
                )}
              </div>
            </div>
          </IMCard>

          {/* Personal Information Card */}
          <IMCard
            title="Información Personal"
            actions={
              !isEditingProfile && (
                <IMButton
                  variant="secondary"
                  size="sm"
                  onClick={handleEditProfile}
                >
                  Editar
                </IMButton>
              )
            }
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <IMInput
                  label="Nombre"
                  name="first_name"
                  value={profileForm.first_name}
                  onChange={handleProfileChange}
                  disabled={!isEditingProfile}
                  error={profileErrors.first_name}
                  required
                />

                <IMInput
                  label="Apellido"
                  name="last_name"
                  value={profileForm.last_name}
                  onChange={handleProfileChange}
                  disabled={!isEditingProfile}
                  error={profileErrors.last_name}
                  required
                />
              </div>

              <IMInput
                label="Email"
                name="email"
                type="email"
                value={profileForm.email}
                onChange={handleProfileChange}
                disabled={!isEditingProfile}
                error={profileErrors.email}
                required
              />

              <IMInput
                label="Teléfono"
                name="phone_number"
                type="tel"
                value={profileForm.phone_number}
                onChange={handleProfileChange}
                disabled={!isEditingProfile}
                error={profileErrors.phone_number}
                helperText="Para notificaciones de Telegram (ej: +54 9 11 1234-5678)"
                placeholder="+54 9 11 1234-5678"
              />

              {isEditingProfile && (
                <div className="flex gap-3 pt-2">
                  <IMButton
                    variant="primary"
                    onClick={handleSaveProfile}
                    loading={updateProfileMutation.isPending}
                  >
                    Guardar Cambios
                  </IMButton>
                  <IMButton
                    variant="secondary"
                    onClick={handleCancelEditProfile}
                    disabled={updateProfileMutation.isPending}
                  >
                    Cancelar
                  </IMButton>
                </div>
              )}
            </div>
          </IMCard>

          {/* Change Password Card */}
          <IMCard
            title="Cambiar Contraseña"
            actions={
              <IMButton
                variant={isChangingPassword ? 'secondary' : 'ghost'}
                size="sm"
                onClick={handleTogglePasswordForm}
              >
                {isChangingPassword ? 'Cancelar' : 'Cambiar'}
              </IMButton>
            }
          >
            {!isChangingPassword ? (
              <p className="text-im-neutral-500">
                Por razones de seguridad, te recomendamos cambiar tu contraseña regularmente.
              </p>
            ) : (
              <div className="space-y-4">
                <IMInput
                  label="Contraseña Actual"
                  name="old_password"
                  type="password"
                  value={passwordForm.old_password}
                  onChange={handlePasswordChange}
                  error={passwordErrors.old_password}
                  required
                />

                <IMInput
                  label="Nueva Contraseña"
                  name="new_password"
                  type="password"
                  value={passwordForm.new_password}
                  onChange={handlePasswordChange}
                  error={passwordErrors.new_password}
                  helperText="Mínimo 8 caracteres"
                  required
                />

                <IMInput
                  label="Confirmar Nueva Contraseña"
                  name="confirm_password"
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={handlePasswordChange}
                  error={passwordErrors.confirm_password}
                  required
                />

                <div className="flex gap-3 pt-2">
                  <IMButton
                    variant="primary"
                    onClick={handleChangePassword}
                    loading={changePasswordMutation.isPending}
                  >
                    Cambiar Contraseña
                  </IMButton>
                  <IMButton
                    variant="secondary"
                    onClick={handleTogglePasswordForm}
                    disabled={changePasswordMutation.isPending}
                  >
                    Cancelar
                  </IMButton>
                </div>
              </div>
            )}
          </IMCard>
        </div>

        {/* Right Column - Account Info */}
        <div className="space-y-6">
          {/* Account Status Card */}
          <IMCard title="Estado de Cuenta">
            <div className="space-y-4">
              <div>
                <p className="text-sm text-im-neutral-500 mb-1">Rol</p>
                <IMBadge variant={roleInfo.variant} size="md">
                  {roleInfo.label}
                </IMBadge>
              </div>

              <div>
                <p className="text-sm text-im-neutral-500 mb-1">Estado</p>
                <IMBadge variant={user.is_active ? 'success' : 'danger'} size="md">
                  {user.is_active ? 'Activo' : 'Inactivo'}
                </IMBadge>
              </div>

              <div>
                <p className="text-sm text-im-neutral-500 mb-1">Creado</p>
                <p className="text-sm font-medium text-im-neutral-900">
                  {new Date(user.created_at).toLocaleDateString('es-ES', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
              </div>

              {user.last_login_at && (
                <div>
                  <p className="text-sm text-im-neutral-500 mb-1">Último Acceso</p>
                  <p className="text-sm font-medium text-im-neutral-900">
                    {new Date(user.last_login_at).toLocaleDateString('es-ES', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              )}
            </div>
          </IMCard>

          {/* Permissions Info Card (si no es super admin) */}
          {user.role !== 'super_admin' && user.allowed_location_ids && (
            <IMCard title="Permisos de Acceso">
              <div className="space-y-3">
                <p className="text-sm text-im-neutral-700">
                  Tienes acceso a <strong>{user.allowed_location_ids.length}</strong> ubicaciones
                </p>
                <div className="bg-im-blue/5 border border-im-blue/20 rounded-md p-3">
                  <p className="text-xs text-im-neutral-600">
                    IDs de ubicaciones: {user.allowed_location_ids.join(', ')}
                  </p>
                </div>
              </div>
            </IMCard>
          )}

          {user.role === 'super_admin' && (
            <IMCard title="Permisos de Acceso">
              <div className="bg-im-success/5 border border-im-success/20 rounded-md p-3">
                <p className="text-sm text-im-success font-medium">
                  ✓ Acceso completo a todo el sistema
                </p>
              </div>
            </IMCard>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Profile;
