export type UserRole = 'MEMBER' | 'TEACHER' | 'LEARNER' | 'STUDENT' | 'ADMIN';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string;
  guru_id?: string;
  username?: string;
  bio?: string;
  skills?: string;
  is_guru_eligible?: boolean;
  followers_count?: number;
  following_count?: number;
  rooms_owned_count?: number;
  rooms_joined_count?: number;
  created_at?: string;
}

export interface MemberProfile {
  id: number;
  guru_id: string;
  username: string;
  full_name: string;
  email?: string;
  avatar_url?: string;
  bio?: string;
  skills?: string;
  followers_count: number;
  following_count: number;
  rooms_owned_count: number;
  rooms_joined_count: number;
  is_guru_eligible: boolean;
  is_following: boolean;
  created_at: string;
}

export interface TeacherProfile {
  id: number;
  user_id: number;
  employee_code?: string;
  department: string;
  designation: string;
  college_name: string;
  user?: User;
}

export interface LearnerProfile {
  id: number;
  user_id: number;
  learner_id: string;
  roll_number?: string;
  course?: string;
  semester?: string;
  department?: string;
  college_name?: string;
  phone?: string;
  user?: User;
}

export interface AuthMeResponse {
  user: User;
  role: UserRole;
  teacher?: TeacherProfile;
  learner?: LearnerProfile;
  id?: number;
  employee_code?: string;
  department?: string;
  designation?: string;
  college_name?: string;
}

export interface Room {
  id: number;
  owner_id?: number;
  teacher_id?: number;
  name: string;
  description?: string;
  code: string;
  visibility: 'PRIVATE' | 'PUBLIC';
  access_type?: 'PUBLIC_FREE' | 'PRIVATE_FREE' | 'PRIVATE_PAID';
  price?: number;
  currency?: string;
  is_active: boolean;
  active_members_count: number;
  owner_name?: string;
  owner_guru_id?: string;
  owner_username?: string;
  owner_avatar_url?: string;
  user_role?: 'OWNER' | 'MODERATOR' | 'MEMBER';
  membership_status?: 'ACTIVE' | 'PENDING' | 'REJECTED';
  created_at: string;
  updated_at?: string;
}

export interface RoomMembership {
  id: number;
  room_id: number;
  user_id: number;
  learner_id?: number;
  role: string;
  status: 'ACTIVE' | 'PENDING' | 'REJECTED' | 'REMOVED' | 'ARCHIVED';
  joined_at: string;
  created_at: string;
  room?: Room;
  user?: User;
  learner?: LearnerProfile;
}

export interface Folder {
  id: number;
  room_id: number;
  name: string;
  description?: string;
  is_active: boolean;
  resources_count: number;
  created_at: string;
  updated_at?: string;
}

export interface Resource {
  id: number;
  room_id: number;
  folder_id?: number;
  title: string;
  description?: string;
  resource_type: 'PDF' | 'PPT' | 'DOC' | 'VIDEO' | 'LINK' | 'IMAGE' | 'OTHER';
  file_url?: string;
  external_url?: string;
  mime_type?: string;
  file_size?: string;
  visibility: 'PUBLIC' | 'ROOM_ONLY';
  is_preview_allowed?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  folder_name?: string;
  room_name?: string;
  room_code?: string;
  teacher_name?: string;
}

export interface RoomPreviewFolderOut {
  id: number;
  name: string;
  resources_count: number;
}

export interface RoomPreviewResourceOut {
  id: number;
  title: string;
  resource_type: string;
  is_preview_allowed: boolean;
}

export interface RoomPreviewOut {
  id: number;
  code: string;
  name: string;
  description?: string;
  visibility: 'PRIVATE' | 'PUBLIC';
  access_type: 'PUBLIC_FREE' | 'PRIVATE_FREE' | 'PRIVATE_PAID';
  price: number;
  currency: string;
  owner_name: string;
  owner_guru_id: string;
  owner_username?: string;
  owner_avatar_url?: string;
  owner_followers_count: number;
  active_members_count: number;
  total_resources_count: number;
  folders: RoomPreviewFolderOut[];
  preview_resources: RoomPreviewResourceOut[];
  user_membership_status?: string | null;
}

export interface JoinRequestOut {
  id: number;
  room_id: number;
  room_name: string;
  user_id: number;
  user_name: string;
  user_guru_id: string;
  user_username?: string;
  user_avatar_url?: string;
  status: 'PENDING' | 'ACTIVE' | 'REJECTED';
  created_at: string;
}

export interface UniversalSearchResult {
  query: string;
  members: {
    id: number;
    guru_id: string;
    username: string;
    full_name: string;
    avatar_url?: string;
    bio?: string;
    followers_count: number;
    rooms_owned_count: number;
  }[];
  rooms: {
    id: number;
    code: string;
    name: string;
    description?: string;
    access_type: 'PUBLIC_FREE' | 'PRIVATE_FREE' | 'PRIVATE_PAID';
    price: number;
    owner_name: string;
    owner_guru_id?: string;
  }[];
  resources: {
    id: number;
    room_id: number;
    room_name: string;
    title: string;
    description?: string;
    resource_type: string;
    file_url?: string;
    external_url?: string;
  }[];
}

export type ActivityType = 'SEMINAR' | 'ASSIGNMENT' | 'PBL' | 'PGL' | 'OTHER' | 'ASSESSMENT';
export type ActivityStatus = 'PENDING' | 'IN_PROGRESS' | 'SUBMITTED' | 'COMPLETED' | 'LATE' | 'REJECTED';
export type StudentStatus = 'GOOD' | 'NEEDS_ATTENTION' | 'CRITICAL';

export interface EvidenceFile {
  id: number;
  file_name: string;
  file_path: string;
  file_size: string;
  mime_type: string;
  uploaded_at: string;
}

export interface SeminarDetail {
  id: number;
  topic: string;
  seminar_date: string;
  presentation_mode: 'OFFLINE' | 'ONLINE' | 'HYBRID';
}

export interface AssignmentDetail {
  id: number;
  unit?: string;
  submission_status: string;
  submitted_at?: string;
  feedback?: string;
}

export interface PblDetail {
  id: number;
  guide_name?: string;
  team_name?: string;
  progress_percentage: number;
  start_date?: string;
  deadline?: string;
}

export interface PglDetail {
  id: number;
  activity_date?: string;
  participation_level: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface Activity {
  id: number;
  teacher_id?: number;
  room_id?: number;
  student_id?: number;
  class_id?: number;
  type: string;
  title: string;
  description?: string;
  status: ActivityStatus;
  marks_obtained?: number;
  max_marks?: number;
  remarks?: string;
  due_date?: string;
  room_name?: string;
  room_code?: string;
  created_at: string;
  seminar_detail?: SeminarDetail;
  assignment_detail?: AssignmentDetail;
  pbl_detail?: PblDetail;
  pgl_detail?: PglDetail;
  evidence_files: EvidenceFile[];
}

export interface Student {
  id: number;
  name: string;
  roll_number: string;
  course: string;
  semester: string;
  department?: string;
  phone?: string;
  avatar_url?: string;
  status: StudentStatus;
  created_at: string;
  overall_progress?: number;
  attendance_percentage?: number;
  pending_activities_count?: number;
}

export interface StudentProfile extends Student {
  seminars_count: string;
  seminars_status: string;
  assignments_count: string;
  assignments_status: string;
  pbl_count: string;
  pbl_status: string;
  pgl_count: string;
  pgl_status: string;
  other_count: string;
  other_status: string;
  activities: Activity[];
}

export interface Material {
  id: number;
  title: string;
  description?: string;
  course: string;
  semester: string;
  unit: string;
  type: 'NOTES' | 'PPT' | 'VIDEO' | 'QUESTION_BANK' | 'LINK' | 'OTHER';
  file_path?: string;
  file_url?: string;
  file_size: string;
  uploaded_by: string;
  created_at: string;
}

export interface DashboardSummary {
  teacher_name: string;
  designation: string;
  college_name: string;
  date_str: string;
  unread_notifications_count: number;
  total_students: number;
  seminars_completed: number;
  seminars_total: number;
  assignments_completed: number;
  assignments_total: number;
  pbl_completed: number;
  pbl_total: number;
  pgl_completed: number;
  pgl_total: number;
  other_completed: number;
  other_total: number;
}

export interface AttentionStudent {
  id: number;
  name: string;
  roll_number: string;
  course: string;
  progress_percentage: number;
  status: StudentStatus;
  pending_reason: string;
  avatar_initials: string;
  avatar_color: string;
}

export interface ClassInsights {
  overall_progress: number;
  attendance_rate: number;
  assignments_rate: number;
  seminars_rate: number;
  pbl_rate: number;
  pgl_rate: number;
}

// Runtime dummy object exports for JS bundling compatibility
export const TYPES_MODULE = 'GURU_YUKTHA_TYPES';
export const DashboardSummary = {};
export const AttentionStudent = {};
export const ClassInsights = {};
export const Student = {};
export const StudentProfile = {};
export const Activity = {};
export const Material = {};
