/**
 * UserModal Component - Modal para crear/editar usuarios
 *
 * Props:
 * - mode: 'create' | 'edit'
 * - user: Usuario a editar (null si es crear)
 * - onSave: Callback al guardar
 * - onClose: Callback al cerrar
 * - isLoading: Estado de carga
 */

import { useState, useEffect, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { User, UserCreate, UserUpdate } from '../../types';
import uploadService from '../../services/uploadService';
import locationService from '../../services/locationService';

interface UserModalProps {
  mode: 'create' | 'edit';
  user: User | null;
  onSave: (userData: UserCreate | UserUpdate) => void;
  onClose: () => void;
  isLoading: boolean;
}

export default function UserModal({ mode, user, onSave, onClose, isLoading }: UserModalProps) {
  const queryClient = useQueryClient();

  // Estado del formulario
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'technician' as 'super_admin' | 'service_admin' | 'technician' | 'guest',
    is_active: true,
    archived: false,
    allowed_location_ids: [] as number[],
    phone_number: '',
    profile_picture_url: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Locations disponibles para restringir el acceso del usuario
  const { data: locations = [] } = useQuery({
    queryKey: ['locations'],
    queryFn: () => locationService.getLocations(),
  });

  const toggleLocation = (locationId: number) => {
    setFormData((prev) => ({
      ...prev,
      allowed_location_ids: prev.allowed_location_ids.includes(locationId)
        ? prev.allowed_location_ids.filter((id) => id !== locationId)
        : [...prev.allowed_location_ids, locationId],
    }));
  };

  // Estado para foto de perfil
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Mutation para upload de foto (solo cuando user ya existe)
  const uploadPhotoMutation = useMutation({
    mutationFn: (file: File) => uploadService.uploadProfilePicture(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      alert('Foto actualizada exitosamente');
      setSelectedFile(null);
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || 'Error al subir la imagen';
      alert(message);
    },
  });

  // Cargar datos del usuario si estamos editando
  useEffect(() => {
    if (mode === 'edit' && user) {
      setFormData({
        email: user.email,
        password: '', // No mostramos la contraseña actual
        first_name: user.first_name,
        last_name: user.last_name,
        role: user.role,
        is_active: user.is_active,
        archived: user.archived,
        allowed_location_ids: user.allowed_location_ids || [],
        phone_number: user.phone_number || '',
        profile_picture_url: user.profile_picture_url || '',
      });

      // Cargar preview de foto existente
      if (user.profile_picture_url) {
        setPreviewUrl(user.profile_picture_url);
      }
    }
  }, [mode, user]);

  // Función para generar iniciales
  const getInitials = (firstName: string, lastName: string): string => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  // Handler para selección de archivo
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validar usando el servicio
      const validation = uploadService.validateImageFile(file);
      if (!validation.valid) {
        setErrors((prev) => ({ ...prev, profile_picture: validation.error || 'Archivo inválido' }));
        return;
      }

      // Limpiar error anterior
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.profile_picture;
        return newErrors;
      });

      setSelectedFile(file);

      // Crear preview local
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result as string;
        setPreviewUrl(base64String);
      };
      reader.readAsDataURL(file);
    }
  };

  // Handler para subir foto (solo en modo edit)
  const handleUploadPhoto = () => {
    if (selectedFile && mode === 'edit') {
      uploadPhotoMutation.mutate(selectedFile);
    }
  };

  // Handler para eliminar foto
  const handleRemovePhoto = () => {
    setSelectedFile(null);
    setPreviewUrl('');
    setFormData((prev) => ({ ...prev, profile_picture_url: '' }));
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Validar formulario
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email) {
      newErrors.email = 'El email es requerido';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (mode === 'create' && !formData.password) {
      newErrors.password = 'La contraseña es requerida';
    }

    if (formData.password && formData.password.length < 8) {
      newErrors.password = 'La contraseña debe tener al menos 8 caracteres';
    }

    if (!formData.first_name) {
      newErrors.first_name = 'El nombre es requerido';
    }

    if (!formData.last_name) {
      newErrors.last_name = 'El apellido es requerido';
    }

    // Validar teléfono (opcional)
    if (formData.phone_number && !/^\+?[\d\s\-()]+$/.test(formData.phone_number)) {
      newErrors.phone_number = 'Formato de teléfono inválido';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handler de submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    if (mode === 'create') {
      // En modo crear, NO enviamos la foto (se subirá después manualmente)
      const createData: UserCreate = {
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
        role: formData.role,
        is_active: formData.is_active,
        archived: formData.archived,
        allowed_location_ids: formData.allowed_location_ids.length > 0 ? formData.allowed_location_ids : null,
        phone_number: formData.phone_number || null,
        profile_picture_url: null,  // Siempre null en creación
      };
      onSave(createData);
    } else {
      // En modo editar, tampoco enviamos la foto aquí (se sube por separado con handleUploadPhoto)
      const updateData: UserUpdate = {
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        role: formData.role,
        is_active: formData.is_active,
        archived: formData.archived,
        allowed_location_ids: formData.allowed_location_ids.length > 0 ? formData.allowed_location_ids : null,
        phone_number: formData.phone_number || null,
        // NO incluimos profile_picture_url - se maneja por separado
      };

      // Solo incluir password si se cambió
      if (formData.password) {
        updateData.password = formData.password;
      }

      onSave(updateData);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            {mode === 'create' ? 'Crear Nuevo Usuario' : 'Editar Usuario'}
          </h3>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Foto de Perfil */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Foto de Perfil
              </label>
              <div className="flex items-center gap-6">
                {/* Avatar Preview */}
                <div className="flex-shrink-0">
                  {previewUrl ? (
                    <img
                      src={previewUrl}
                      alt="Preview"
                      className="w-24 h-24 rounded-full object-cover border-2 border-gray-200"
                    />
                  ) : (
                    <div className="w-24 h-24 rounded-full bg-im-orange/10 flex items-center justify-center border-2 border-im-orange/20">
                      <span className="text-2xl font-semibold text-im-orange">
                        {formData.first_name && formData.last_name
                          ? getInitials(formData.first_name, formData.last_name)
                          : '?'}
                      </span>
                    </div>
                  )}
                </div>

                {/* Upload/Remove Buttons */}
                <div className="flex-1">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-4 py-2 text-sm font-medium text-white bg-im-orange rounded-md hover:bg-im-orange-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-im-orange disabled:opacity-50"
                      disabled={isLoading || uploadPhotoMutation.isPending}
                    >
                      {previewUrl ? 'Cambiar Foto' : 'Seleccionar Foto'}
                    </button>
                    {selectedFile && mode === 'edit' && (
                      <button
                        type="button"
                        onClick={handleUploadPhoto}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                        disabled={isLoading || uploadPhotoMutation.isPending}
                      >
                        {uploadPhotoMutation.isPending ? 'Subiendo...' : 'Guardar Foto'}
                      </button>
                    )}
                    {previewUrl && (
                      <button
                        type="button"
                        onClick={handleRemovePhoto}
                        className="px-4 py-2 text-sm font-medium text-im-danger border border-im-danger rounded-md hover:bg-im-danger-light focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-im-danger disabled:opacity-50"
                        disabled={isLoading}
                      >
                        Quitar
                      </button>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {mode === 'create'
                      ? 'Nota: Crea el usuario primero. Podrás agregar su foto después al editarlo.'
                      : 'Formatos: JPG, PNG, GIF. Tamaño máximo: 5MB'}
                  </p>
                  {errors.profile_picture && (
                    <p className="text-sm text-red-600 mt-1">{errors.profile_picture}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-gray-200 my-4"></div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email *
              </label>
              <input
                type="email"
                id="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  errors.email ? 'border-red-300' : 'border-gray-300'
                }`}
                disabled={isLoading}
              />
              {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Contraseña {mode === 'create' ? '*' : '(dejar vacío para no cambiar)'}
              </label>
              <input
                type="password"
                id="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  errors.password ? 'border-red-300' : 'border-gray-300'
                }`}
                disabled={isLoading}
                placeholder={mode === 'edit' ? 'Dejar vacío para mantener la actual' : ''}
              />
              {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
            </div>

            {/* Nombre y Apellido */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                  Nombre *
                </label>
                <input
                  type="text"
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    errors.first_name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  disabled={isLoading}
                />
                {errors.first_name && <p className="mt-1 text-sm text-red-600">{errors.first_name}</p>}
              </div>

              <div>
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                  Apellido *
                </label>
                <input
                  type="text"
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                    errors.last_name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  disabled={isLoading}
                />
                {errors.last_name && <p className="mt-1 text-sm text-red-600">{errors.last_name}</p>}
              </div>
            </div>

            {/* Teléfono */}
            <div>
              <label htmlFor="phone_number" className="block text-sm font-medium text-gray-700">
                Teléfono
              </label>
              <input
                type="tel"
                id="phone_number"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className={`mt-1 block w-full rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${
                  errors.phone_number ? 'border-red-300' : 'border-gray-300'
                }`}
                disabled={isLoading}
                placeholder="+54 9 11 1234-5678"
              />
              <p className="mt-1 text-xs text-gray-500">Para notificaciones de Telegram</p>
              {errors.phone_number && <p className="mt-1 text-sm text-red-600">{errors.phone_number}</p>}
            </div>

            {/* Rol */}
            <div>
              <label htmlFor="role" className="block text-sm font-medium text-gray-700">
                Rol *
              </label>
              <select
                id="role"
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as typeof formData.role })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                disabled={isLoading}
              >
                <option value="super_admin">Super Admin</option>
                <option value="service_admin">Service Admin</option>
                <option value="technician">Técnico</option>
                <option value="guest">Invitado</option>
              </select>
            </div>

            {/* Estados */}
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <span className="text-sm text-gray-700">Usuario activo</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.archived}
                  onChange={(e) => setFormData({ ...formData, archived: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  disabled={isLoading}
                />
                <span className="text-sm text-gray-700">Archivado</span>
              </label>
            </div>

            {/* Locations permitidas */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ubicaciones permitidas
              </label>
              {formData.role === 'super_admin' ? (
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm text-gray-600">
                    Los <strong>Super Admin</strong> tienen acceso a todas las
                    ubicaciones; esta restricción no les aplica.
                  </p>
                </div>
              ) : (
                <>
                  <p className="text-xs text-gray-500 mb-2">
                    Sin selección, el usuario no tiene ubicaciones asignadas y no
                    verá dispositivos.
                  </p>
                  {locations.length === 0 ? (
                    <div className="bg-gray-50 p-4 rounded-md">
                      <p className="text-sm text-gray-600">
                        No hay ubicaciones creadas todavía. Crealas desde la
                        página Ubicaciones.
                      </p>
                    </div>
                  ) : (
                    <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-md divide-y divide-gray-100">
                      {locations.map((location) => (
                        <label
                          key={location.id}
                          className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={formData.allowed_location_ids.includes(location.id)}
                            onChange={() => toggleLocation(location.id)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            disabled={isLoading}
                          />
                          <span className="text-sm text-gray-700">
                            {location.name}
                            <span className="ml-1 text-xs text-gray-400">({location.code})</span>
                          </span>
                        </label>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              disabled={isLoading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? 'Guardando...' : mode === 'create' ? 'Crear Usuario' : 'Guardar Cambios'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
