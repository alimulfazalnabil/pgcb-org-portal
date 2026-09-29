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
  slug?: string;
  description_bn?: string;
  active_members?: number;
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

export interface NewsArticle {
  id: number;
  slug: string;
  title_bn: string;
  title_en?: string;
  summary_bn?: string;
  summary_en?: string;
  content_bn?: string;
  content_en?: string;
  body_bn?: string;
  body_en?: string;
  category: string;
  tags: string[];
  cover_image_url?: string;
  gallery_urls?: string[];
  author_name?: string;
  is_featured: boolean;
  is_published: boolean;
  workflow_status?: string;
  scheduled_at?: string;
  published_at?: string;
  view_count: number;
  structured_data?: Record<string, any>;
  seo?: {
    meta_title: string;
    meta_description: string;
    og_image_url?: string;
    canonical_url: string;
    json_ld: Record<string, any>;
  };
  created_at: string;
  updated_at: string;
}

export type NewsItem = NewsArticle;

export interface CertificateWalletItem {
  id: number;
  certificate_no: string;
  certificate_number: string;
  certificate_type: string;
  title_bn: string;
  title_en?: string;
  recipient_name: string;
  issuer: string;
  issue_date: string;
  status: 'ISSUED' | 'REVOKED' | 'ACTIVE';
  revoked: boolean;
  revocation_reason?: string;
  verification_token: string;
  view_url: string;
  download_url: string;
  png_url: string;
  verify_url: string;
  qr_verify_url: string;
}

export interface DigitalCardDetails {
  membership_id: string;
  name_bn: string;
  name_en?: string;
  designation_bn?: string;
  designation_en?: string;
  circle_name_bn?: string;
  circle_name_en?: string;
  employee_id?: string;
  blood_group?: string;
  organization: string;
  status: 'ACTIVE' | 'EXPIRED' | 'REVOKED' | 'PENDING';
  issued_at?: string;
  expires_at?: string;
  offline_cacheable: boolean;
  verify_url: string;
  qr_verify_url: string;
  card_png_url: string;
  card_back_png_url: string;
  card_pdf_url: string;
}

export interface RenewalOptionItem {
  code: string;
  plan_id?: string;
  label_en: string;
  label_bn: string;
  years: number;
  fee: number;
  amount_bdt?: number;
  currency: string;
}

export interface NotificationPreferences {
  in_app_enabled?: boolean;
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled?: boolean;
}

export interface MemberDashboardData {
  greeting?: string;
  hero_card?: Record<string, any>;
  membership?: {
    member_id: string;
    status: string;
    valid_until?: string;
    valid_until_formatted?: string;
    days_remaining?: number | null;
    circle_name_bn?: string;
    designation_bn?: string;
  };
  quick_actions?: Array<Record<string, any>>;
  quick_stats?: Record<string, any>;
  recent_activity?: Array<{
    title?: string;
    title_bn?: string;
    status?: string;
    timestamp?: string;
  }>;
}

export interface KnowledgeDocumentItem {
  id: number;
  title_bn: string;
  title_en?: string | null;
  category: string;
  version: string;
  is_current: boolean;
  supersedes_id?: number | null;
  superseded_by_id?: number | null;
  publication_date?: string | null;
  effective_date?: string | null;
  author?: string | null;
  approval_status: string;
  source_type: string;
  source_url?: string | null;
  access_level: string;
  circle_id?: number | null;
  chunk_count: number;
  created_at?: string | null;
}

export interface KnowledgeFAQItem {
  id: number;
  document_id?: number | null;
  question_bn: string;
  question_en?: string | null;
  answer_bn: string;
  answer_en?: string | null;
  category: string;
  section_ref?: string | null;
  page_ref?: number | null;
  status: string;
  approved_by?: number | null;
  published_at?: string | null;
}

export interface AIUsageAnalytics {
  questions_today: number;
  total_questions: number;
  documents_searched: number;
  unanswered: number;
  security_blocked: number;
  avg_response_time_sec: number;
  failure_rate: number;
  total_tokens: number;
  estimated_cost_usd: number;
  by_category: Record<string, number>;
  top_source_documents: Array<{ title: string; citations: number }>;
}

export interface AdminIntelligenceDashboard {
  members: number;
  active: number;
  pending: number;
  expiring_next_30_days: number;
  applications_this_month: number;
  revenue_this_month: number;
  revenue_this_month_formatted: string;
  circles_by_pending_applications: Array<{
    circle_id: number;
    circle_code: string;
    circle_name_en: string;
    circle_name_bn: string;
    pending_applications: number;
    active_members: number;
  }>;
}



