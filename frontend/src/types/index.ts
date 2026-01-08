/**
 * TypeScript type definitions for the application.
 */

export interface User {
  id: number;
  email: string;
  full_name: string;
  phone?: string;
  is_active: boolean;
  roles: Role[];
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface Role {
  id: number;
  name: string;
  display_name: string;
  description?: string;
  permissions?: string[];
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  owner_id: number;
  status: ProjectStatus;
  project_type?: string;
  location_address?: string;
  location_district?: string;
  location_city?: string;
  site_area_m2?: number;
  uda_zone?: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
  approved_by?: number;
}

export type ProjectStatus =
  | 'DRAFT'
  | 'UNDER_ARCHITECT_REVIEW'
  | 'UNDER_ENGINEER_REVIEW'
  | 'UNDER_REGULATOR_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'NEEDS_REVISION';

export interface Layout {
  id: number;
  project_id: number;
  version: number;
  name?: string;
  status: ProjectStatus;
  generation_job_id?: string;
  building_count?: number;
  total_floor_area_m2?: number;
  open_space_area_m2?: number;
  parking_spaces?: number;
  max_building_height_m?: number;
  blend_file_path?: string;
  glb_file_path?: string;
  preview_image_path?: string;
  created_at: string;
  updated_at: string;
}

export interface ValidationReport {
  id: number;
  project_id: number;
  layout_id?: number;
  report_type: 'UDA_COMPLIANCE' | 'ML_PREDICTION' | 'FULL_VALIDATION';
  is_compliant?: boolean;
  compliance_score?: number;
  rule_checks: RuleCheck[];
  ml_predictions: MLPrediction[];
  recommendations: Recommendation[];
  generated_at: string;
}

export interface RuleCheck {
  rule_name: string;
  rule_description: string;
  status: 'PASS' | 'FAIL' | 'WARNING' | 'N/A';
  actual_value?: any;
  required_value?: any;
  message: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
}

export interface MLPrediction {
  model_name: string;
  model_version: string;
  prediction: any;
  confidence?: number;
}

export interface Recommendation {
  title: string;
  description: string;
  impact: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface Approval {
  id: number;
  project_id: number;
  layout_id?: number;
  status_from?: ProjectStatus;
  status_to: ProjectStatus;
  user_id: number;
  user_role: string;
  timestamp: string;
  comment?: string;
  is_admin_override: boolean;
  user_name?: string;
}

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  title: string;
  message?: string;
  related_project_id?: number;
  related_layout_id?: number;
  is_read: boolean;
  created_at: string;
}
