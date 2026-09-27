/**
 * Institutional Data Models and TypeScript Interfaces for PGCB Portal.
 */

export interface PublicStats {
  active_members: number;
  active_circles: number;
  publications: number;
  upcoming_events: number;
  notices_count?: number;
  documents_count?: number;
}

export interface Notice {
  id: number;
  title_bn: string;
  title_en?: string;
  content_bn: string;
  content_en?: string;
  priority: 'NORMAL' | 'HIGH' | 'URGENT';
  category: string;
  attachment_url?: string;
  is_pinned: boolean;
  is_published: boolean;
  published_at?: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: number;
  title_bn: string;
  title_en?: string;
  category: string;
  description_bn?: string;
  file_path: string;
  file_size?: number;
  content_type?: string;
  version: string;
  download_count: number;
  created_at: string;
}

export interface PublicMember {
  membership_id: string;
  name_bn: string;
  name_en?: string;
  designation_bn?: string;
  designation_en?: string;
  circle_name_bn?: string;
  circle_name_en?: string;
  status: string;
}

export interface CircleItem {
  id: number;
  name_bn: string;
  name_en: string;
  description_bn?: string;
}

export interface CommitteeItem {
  id: number;
  name_bn: string;
  name_en?: string;
  designation_bn: string;
  designation_en?: string;
  message_bn?: string;
  photo_url?: string;
  term_start?: number;
  term_end?: number;
}

export interface CircularItem {
  id: number;
  category: string;
  reference_no?: string;
  title_bn: string;
  title_en?: string;
  summary_bn?: string;
  document_url?: string;
  published_at?: string;
  priority: number;
}

export interface EventItem {
  id: number;
  title_bn: string;
  title_en?: string;
  description_bn?: string;
  event_date?: string;
  location_bn?: string;
  cover_image_url?: string;
  registration_enabled: boolean;
  capacity?: number;
  fee_amount: number;
  fee_currency: string;
}

export interface TimelineStep {
  step: number;
  title: string;
  status: 'COMPLETED' | 'IN_PROGRESS' | 'PENDING' | 'REJECTED';
  date: string | null;
  description: string;
}

export interface ApplicationTrackResult {
  application_no: string;
  status: string;
  applicant_name_masked: string;
  circle_bn: string;
  submission_date: string;
  application_note: string;
  timeline: TimelineStep[];
  membership_id: string | null;
}
