import type { 
  DashboardSummary, AttentionStudent, ClassInsights, Student, StudentProfile, 
  Activity, Material, Room, RoomMembership, Folder, Resource 
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

export const AUTH_TOKEN_KEY = 'guru_yuktha_token';
export const LEGACY_TOKEN_KEY = 'student360_token';

export function getAuthToken(): string | null {
  return localStorage.getItem(AUTH_TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY);
}

export function setAuthToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function removeAuthToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(LEGACY_TOKEN_KEY);
}

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getAuthToken();
  
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(errorData.detail || `API request failed with status ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Auth & Profile
  login: (credentials: { email: string; password: string }) => fetchApi<any>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  }),

  signup: (data: any) => fetchApi<any>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  getMe: () => fetchApi<any>('/auth/me'),
  getTeacherProfile: () => fetchApi<any>('/auth/me'),

  updateTeacherProfile: (profile: any) => fetchApi<any>('/auth/profile', {
    method: 'PUT',
    body: JSON.stringify(profile),
  }),

  uploadTeacherAvatar: (formData: FormData) => fetchApi<any>('/auth/avatar', {
    method: 'POST',
    body: formData,
  }),

  // Rooms (Phase 2)
  getRooms: () => fetchApi<Room[]>('/rooms'),
  createRoom: (data: { name: string; description?: string; visibility?: string }) => fetchApi<Room>('/rooms', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getRoomDetails: (id: number) => fetchApi<Room>(`/rooms/${id}`),
  updateRoom: (id: number, data: Partial<Room>) => fetchApi<Room>(`/rooms/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  archiveRoom: (id: number) => fetchApi<{ message: string; id: number }>(`/rooms/${id}`, {
    method: 'DELETE',
  }),
  getRoomMembers: (id: number) => fetchApi<RoomMembership[]>(`/rooms/${id}/members`),
  getMyMemberships: () => fetchApi<RoomMembership[]>('/rooms/my/memberships'),

  // Folders & Resources (Phase 3)
  getRoomFolders: (roomId: number) => fetchApi<Folder[]>(`/rooms/${roomId}/folders`),
  createFolder: (roomId: number, data: { name: string; description?: string }) => fetchApi<Folder>(`/rooms/${roomId}/folders`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  updateFolder: (roomId: number, folderId: number, data: Partial<Folder>) => fetchApi<Folder>(`/rooms/${roomId}/folders/${folderId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  archiveFolder: (roomId: number, folderId: number) => fetchApi<{ message: string; id: number }>(`/rooms/${roomId}/folders/${folderId}`, {
    method: 'DELETE',
  }),

  getRoomResources: (roomId: number, folderId?: number) => {
    const q = folderId ? `?folder_id=${folderId}` : '';
    return fetchApi<Resource[]>(`/rooms/${roomId}/resources${q}`);
  },
  createResource: (roomId: number, data: { title: string; description?: string; folder_id?: number; resource_type?: string; file_url?: string; visibility?: string }) => fetchApi<Resource>(`/rooms/${roomId}/resources`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getResourceDetail: (roomId: number, resourceId: number) => fetchApi<Resource>(`/rooms/${roomId}/resources/${resourceId}`),
  updateResource: (roomId: number, resourceId: number, data: Partial<Resource>) => fetchApi<Resource>(`/rooms/${roomId}/resources/${resourceId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  archiveResource: (roomId: number, resourceId: number) => fetchApi<{ message: string; id: number }>(`/rooms/${roomId}/resources/${resourceId}`, {
    method: 'DELETE',
  }),

  // Public Resources Discovery
  getPublicResources: (params?: { search?: string; resource_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.resource_type) query.append('resource_type', params.resource_type);
    const str = query.toString();
    return fetchApi<Resource[]>(`/resources/public${str ? `?${str}` : ''}`);
  },

  // Dashboard
  getDashboardSummary: () => fetchApi<DashboardSummary>('/dashboard/summary'),
  getAttentionStudents: () => fetchApi<AttentionStudent[]>('/dashboard/attention'),
  getClassInsights: () => fetchApi<ClassInsights>('/dashboard/insights'),

  // Students
  getStudents: (params?: { search?: string; status?: string; course?: string }) => {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.status) query.append('status', params.status);
    if (params?.course) query.append('course', params.course);
    const str = query.toString();
    return fetchApi<Student[]>(`/students${str ? `?${str}` : ''}`);
  },

  getStudentProfile: (id: number) => fetchApi<StudentProfile>(`/students/${id}`),

  createStudent: (student: Partial<Student>) => fetchApi<Student>('/students', {
    method: 'POST',
    body: JSON.stringify(student),
  }),

  updateStudent: (id: number, student: Partial<Student>) => fetchApi<Student>(`/students/${id}`, {
    method: 'PUT',
    body: JSON.stringify(student),
  }),

  deleteStudent: (id: number) => fetchApi<{ message: string; id: number }>(`/students/${id}`, {
    method: 'DELETE',
  }),

  // Activities Quick Actions
  createSeminar: (data: any) => fetchApi<Activity>('/activities/seminar', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  createAssignment: (data: any) => fetchApi<Activity>('/activities/assignment', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  createPbl: (data: any) => fetchApi<Activity>('/activities/pbl', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  createPgl: (data: any) => fetchApi<Activity>('/activities/pgl', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  createGenericActivity: (data: any) => fetchApi<Activity>('/activities/generic', {
    method: 'POST',
    body: JSON.stringify(data),
  }),

  // Materials
  getMaterials: (params?: { category?: string; course?: string; unit?: string; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.course) query.append('course', params.course);
    if (params?.unit) query.append('unit', params.unit);
    if (params?.search) query.append('search', params.search);
    const str = query.toString();
    return fetchApi<Material[]>(`/materials${str ? `?${str}` : ''}`);
  },

  createMaterial: (formData: FormData) => fetchApi<Material>('/materials', {
    method: 'POST',
    body: formData,
  }),

  // Upload evidence file
  uploadEvidence: (formData: FormData) => fetchApi<any>('/evidence/upload', {
    method: 'POST',
    body: formData,
  }),

  // Attendance
  markAttendance: (batchData: any) => fetchApi<any>('/attendance/batch', {
    method: 'POST',
    body: JSON.stringify(batchData),
  }),

  // Reports & Files
  getStudentReportPdfUrl: (studentId: number) => `${API_BASE}/reports/student/${studentId}/pdf`,
  getClassSummaryPdfUrl: () => `${API_BASE}/reports/class/summary/pdf`,
  getExportCsvUrl: () => `${API_BASE}/reports/export/csv`,
  getEvidenceFileUrl: (fileId: number) => `${API_BASE}/evidence/file/${fileId}`,
};
