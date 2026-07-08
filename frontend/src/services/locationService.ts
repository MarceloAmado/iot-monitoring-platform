/**
 * Servicio para Location Groups, Locations y Assets
 */

import api from './api';

// ========================================
// Types
// ========================================

export interface LocationGroup {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export interface LocationGroupCreate {
  name: string;
  description?: string;
}

export interface Location {
  id: number;
  location_group_id: number;
  name: string;
  code: string;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
}

export interface LocationCreate {
  location_group_id: number;
  name: string;
  code: string;
  address?: string;
  latitude?: number;
  longitude?: number;
}

export interface Asset {
  id: number;
  location_id: number;
  name: string;
  type: string;
  description: string | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
}

export interface AssetCreate {
  location_id: number;
  name: string;
  type: string;
  description?: string;
  extra_data?: Record<string, unknown>;
}

// ========================================
// Location Groups
// ========================================

export const getLocationGroups = async (): Promise<LocationGroup[]> => {
  const response = await api.get('/location-groups');
  return response.data;
};

export const createLocationGroup = async (data: LocationGroupCreate): Promise<LocationGroup> => {
  const response = await api.post('/location-groups', data);
  return response.data;
};

export const updateLocationGroup = async (id: number, data: Partial<LocationGroupCreate>): Promise<LocationGroup> => {
  const response = await api.patch(`/location-groups/${id}`, data);
  return response.data;
};

export const deleteLocationGroup = async (id: number): Promise<void> => {
  await api.delete(`/location-groups/${id}`);
};

// ========================================
// Locations
// ========================================

export const getLocations = async (groupId?: number): Promise<Location[]> => {
  const params = groupId ? { group_id: groupId } : {};
  const response = await api.get('/locations', { params });
  return response.data;
};

export const createLocation = async (data: LocationCreate): Promise<Location> => {
  const response = await api.post('/locations', data);
  return response.data;
};

export const updateLocation = async (id: number, data: Partial<LocationCreate>): Promise<Location> => {
  const response = await api.patch(`/locations/${id}`, data);
  return response.data;
};

export const deleteLocation = async (id: number): Promise<void> => {
  await api.delete(`/locations/${id}`);
};

// ========================================
// Assets
// ========================================

export const getAssets = async (locationId?: number): Promise<Asset[]> => {
  const params = locationId ? { location_id: locationId } : {};
  const response = await api.get('/assets', { params });
  return response.data;
};

export const createAsset = async (data: AssetCreate): Promise<Asset> => {
  const response = await api.post('/assets', data);
  return response.data;
};

export const updateAsset = async (id: number, data: Partial<AssetCreate>): Promise<Asset> => {
  const response = await api.patch(`/assets/${id}`, data);
  return response.data;
};

export const deleteAsset = async (id: number): Promise<void> => {
  await api.delete(`/assets/${id}`);
};

export default {
  getLocationGroups,
  createLocationGroup,
  updateLocationGroup,
  deleteLocationGroup,
  getLocations,
  createLocation,
  updateLocation,
  deleteLocation,
  getAssets,
  createAsset,
  updateAsset,
  deleteAsset,
};
