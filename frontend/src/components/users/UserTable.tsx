/**
 * UserTable Component - Tabla de usuarios con acciones
 *
 * Props:
 * - users: Array de usuarios a mostrar
 * - onEdit: Callback para editar usuario
 * - onToggleActive: Callback para activar/desactivar
 * - onToggleArchive: Callback para archivar/desarchivar
 * - onResetPassword: Callback para resetear contraseña
 */

import { User } from '../../types';

interface UserTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onToggleActive: (user: User) => void;
  onToggleArchive: (user: User) => void;
  onResetPassword: (user: User) => void;
}

export default function UserTable({
  users,
  onEdit,
  onToggleActive,
  onToggleArchive,
  onResetPassword,
}: UserTableProps) {
  // Mapeo de roles a texto legible
  const roleLabels: Record<string, string> = {
    super_admin: 'Super Admin',
    service_admin: 'Service Admin',
    technician: 'Técnico',
    guest: 'Invitado',
  };

  // Mapeo de roles a colores
  const roleColors: Record<string, string> = {
    super_admin: 'bg-purple-100 text-purple-800',
    service_admin: 'bg-blue-100 text-blue-800',
    technician: 'bg-green-100 text-green-800',
    guest: 'bg-gray-100 text-gray-800',
  };

  // Formatear fecha
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Nunca';
    return new Date(dateString).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (users.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <p className="text-gray-500">No se encontraron usuarios con los filtros aplicados</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Usuario
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Rol
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Estado
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Último Login
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Creado
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50">
                {/* Usuario */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
                        {user.first_name.charAt(0)}{user.last_name.charAt(0)}
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {user.first_name} {user.last_name}
                      </div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </div>
                </td>

                {/* Rol */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${roleColors[user.role]}`}>
                    {roleLabels[user.role]}
                  </span>
                </td>

                {/* Estado */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-col gap-1">
                    {user.archived ? (
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        Archivado
                      </span>
                    ) : user.is_active ? (
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Activo
                      </span>
                    ) : (
                      <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                        Inactivo
                      </span>
                    )}
                  </div>
                </td>

                {/* Último Login */}
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(user.last_login_at)}
                </td>

                {/* Creado */}
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(user.created_at)}
                </td>

                {/* Acciones */}
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div className="flex justify-end gap-2">
                    {/* Editar */}
                    <button
                      onClick={() => onEdit(user)}
                      className="text-blue-600 hover:text-blue-900"
                      title="Editar usuario"
                    >
                      Editar
                    </button>

                    {/* Activar/Desactivar */}
                    {!user.archived && (
                      <button
                        onClick={() => onToggleActive(user)}
                        className={user.is_active ? 'text-orange-600 hover:text-orange-900' : 'text-green-600 hover:text-green-900'}
                        title={user.is_active ? 'Desactivar usuario' : 'Activar usuario'}
                      >
                        {user.is_active ? 'Desactivar' : 'Activar'}
                      </button>
                    )}

                    {/* Archivar/Desarchivar */}
                    <button
                      onClick={() => onToggleArchive(user)}
                      className="text-gray-600 hover:text-gray-900"
                      title={user.archived ? 'Desarchivar usuario' : 'Archivar usuario'}
                    >
                      {user.archived ? 'Desarchivar' : 'Archivar'}
                    </button>

                    {/* Resetear Password */}
                    {!user.archived && (
                      <button
                        onClick={() => onResetPassword(user)}
                        className="text-purple-600 hover:text-purple-900"
                        title="Resetear contraseña"
                      >
                        Reset Pwd
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer con info */}
      <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
        <p className="text-sm text-gray-700">
          Mostrando <span className="font-medium">{users.length}</span> usuario(s)
        </p>
      </div>
    </div>
  );
}
