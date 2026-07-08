import api from './api';

export interface FirmwareVersion {
  id: number;
  version: string;
  file_path: string;
  file_size_bytes: number;
  file_size_mb: number;
  md5_checksum: string;
  release_notes: string | null;
  is_stable: boolean;
  is_latest: boolean;
  min_compatible_version: string | null;
  created_at: string;
  created_by_user_id: number | null;
}

export interface FirmwareUploadData {
  version: string;
  file: File;
  release_notes?: string;
  is_stable?: boolean;
  min_compatible_version?: string;
}

export interface FirmwareUpdateData {
  release_notes?: string | null;
  is_stable?: boolean | null;
  is_latest?: boolean | null;
  min_compatible_version?: string | null;
}

const firmwareService = {
  async getVersions(onlyStable?: boolean): Promise<FirmwareVersion[]> {
    const params = onlyStable ? { only_stable: true } : {};
    const response = await api.get<FirmwareVersion[]>('/firmware/versions', { params });
    return response.data;
  },

  async upload(data: FirmwareUploadData): Promise<FirmwareVersion> {
    const formData = new FormData();
    formData.append('version', data.version);
    formData.append('file', data.file);
    if (data.release_notes) formData.append('release_notes', data.release_notes);
    if (data.is_stable !== undefined) formData.append('is_stable', String(data.is_stable));
    if (data.min_compatible_version) formData.append('min_compatible_version', data.min_compatible_version);

    const response = await api.post<FirmwareVersion>('/firmware/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  async update(id: number, data: FirmwareUpdateData): Promise<FirmwareVersion> {
    const response = await api.patch<FirmwareVersion>(`/firmware/${id}`, data);
    return response.data;
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/firmware/${id}`);
  },

  async markAsLatest(id: number): Promise<FirmwareVersion> {
    const response = await api.patch<FirmwareVersion>(`/firmware/${id}`, { is_latest: true });
    return response.data;
  },
};

export default firmwareService;
