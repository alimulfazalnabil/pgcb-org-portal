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
  description_en?: string;
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
  description_en?: string;
  active_members?: number;
}

export interface CommitteeItem {
  id: number;
  name_bn: string;
  name_en?: string;
  designation_bn: string;
  designation_en?: string;
  message_bn?: string;
  message_en?: string;
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
  summary_en?: string;
  document_url?: string;
  published_at?: string;
  priority: number;
}

export interface EventItem {
  id: number;
  title_bn: string;
  title_en?: string;
  description_bn?: string;
  description_en?: string;
  event_date?: string;
  location_bn?: string;
  location_en?: string;
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
  code?: string;
  plan_code?: string;
  plan_id?: string;
  period?: string;
  label_en?: string;
  label_bn?: string;
  title_en?: string;
  title_bn?: string;
  years?: number;
  duration_years?: number;
  days?: number;
  fee?: number;
  amount?: number;
  amount_bdt?: number;
  amount_formatted?: string;
  net_fee?: number;
  formatted_net_fee?: string;
  projected_validity_date?: string;
  projected_validity_formatted?: string;
  projected_valid_until?: string;
  projected_valid_until_bn?: string;
  recommended?: boolean;
  currency?: string;
  [key: string]: any;
}

export interface NotificationPreferences {
  in_app_enabled?: boolean;
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled?: boolean;
}

export interface MemberDashboardData {
  greeting?: string;
  user?: Record<string, any>;
  member?: {
    id?: number;
    name_bn?: string;
    name_en?: string;
    membership_id?: string;
    photo_url?: string;
    circle?: string;
    circle_bn?: string;
    circle_en?: string;
    designation_bn?: string;
    designation_en?: string;
    email?: string;
    phone?: string;
    profile_completion?: number;
    [key: string]: any;
  };
  hero_card?: Record<string, any>;
  membership?: {
    id?: number;
    member_id?: string | number;
    membership_id?: string;
    membership_type?: string;
    status: string;
    type?: string;
    joined_at?: string;
    valid_until?: string;
    validity_date?: string;
    issue_date?: string;
    valid_until_formatted?: string;
    days_remaining?: number | null;
    days_until_expiry?: number | null;
    circle_id?: number | null;
    circle?: string;
    circle_bn?: string;
    circle_en?: string;
    circle_name_bn?: string;
    designation_bn?: string;
    designation_en?: string;
    [key: string]: any;
  };
  application?: {
    id: number;
    reference?: string;
    application_no: string;
    membership_id?: string | null;
    membership_type: string;
    status: string;
    status_label_en: string;
    status_label_bn: string;
    circle_bn?: string | null;
    circle_en?: string | null;
    submitted_at?: string | null;
    approved_at?: string | null;
    reviewer_notes?: string | null;
    stages: Array<{
      step: number;
      key: string;
      label_en: string;
      label_bn: string;
      status: string;
      icon: string;
    }>;
    required_actions: Array<{
      code: string;
      message_en: string;
      message_bn: string;
    }>;
    [key: string]: any;
  };
  payment_summary?: {
    total_paid?: number;
    total_paid_formatted?: string;
    successful?: number;
    pending?: number;
    failed?: number;
    payments_count?: number;
    paid_count?: number;
    pending_count?: number;
    latest_payment?: Record<string, any>;
    recent_payments?: Array<Record<string, any>>;
    [key: string]: any;
  };
  documents?: {
    total: number;
    verified: number;
    pending: number;
    items?: Array<Record<string, any>>;
    [key: string]: any;
  } | Array<Record<string, any>>;
  documents_list?: Array<Record<string, any>>;
  certificates?: CertificateWalletItem[];
  upcoming_events?: Array<{
    id: number;
    slug?: string;
    title: string;
    title_bn?: string;
    title_en?: string;
    summary_bn?: string;
    location?: string;
    location_bn?: string;
    location_en?: string;
    time?: string;
    day?: string;
    month?: string;
    event_date?: string;
    event_date_formatted?: string;
    is_registered?: boolean;
    registration_status?: string | null;
    registration_enabled?: boolean;
    [key: string]: any;
  }>;
  events?: Array<Record<string, any>>;
  circulars?: Array<Record<string, any>>;
  notifications?: Array<{
    id: number;
    title?: string;
    title_bn?: string;
    body?: string;
    body_bn?: string;
    type?: string;
    dot_color?: string;
    indicator_icon?: string;
    read_at?: string | null;
    is_read?: boolean;
    indicator?: string;
    created_at?: string;
    relative_time?: string;
    relative_time_en?: string;
    relative_time_bn?: string;
    href?: string;
    [key: string]: any;
  }>;
  unread_notifications_count?: number;
  profile_completion?: number;
  profile_completion_details?: {
    percentage: number;
    is_complete: boolean;
    completed_count: number;
    total_count: number;
    items: Array<{
      key: string;
      label_en: string;
      label_bn: string;
      completed: boolean;
      weight: number;
    }>;
  };
  digital_id_available?: boolean;
  change_requests?: Array<Record<string, any>>;
  quick_actions?: Array<Record<string, any>>;
  quick_stats?: Record<string, any>;
  recent_activity?: Array<{
    id?: string;
    type?: string;
    title?: string;
    title_en?: string;
    title_bn?: string;
    description?: string;
    subtitle_bn?: string;
    status?: string;
    timestamp?: string;
    relative_time?: string;
    relative_time_en?: string;
    relative_time_bn?: string;
    href?: string;
    [key: string]: any;
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

export interface VerificationBadge {
  field: string;
  status: 'VERIFIED' | 'PENDING' | 'REJECTED';
  label: string;
  label_bn: string;
  is_verified: boolean;
  description: string;
  description_bn: string;
}

export interface ProfileCompletionItem {
  key: string;
  field: string;
  label_en: string;
  label_bn: string;
  completed: boolean;
  weight: number;
  route: string;
}

export interface ProfileCompletionDetails {
  percentage: number;
  is_complete: boolean;
  completed_count: number;
  total_count: number;
  breakdown: Record<string, boolean>;
  items: ProfileCompletionItem[];
  missing: Array<{
    field: string;
    label: string;
    label_bn: string;
    route: string;
  }>;
}

export interface ProfileChangeRequest {
  id: number;
  member_id: number;
  field_name: string;
  field_label_en: string;
  field_label_bn: string;
  current_value?: string | null;
  requested_value: string;
  reason?: string | null;
  supporting_doc_url?: string | null;
  supporting_document_id?: number | null;
  status: 'PENDING' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'CANCELLED';
  reviewer_id?: number | null;
  reviewed_by?: number | null;
  reviewer_comment?: string | null;
  reviewer_note?: string | null;
  review_note?: string | null;
  created_at: string;
  reviewed_at?: string | null;
  member_name_en?: string | null;
  member_name_bn?: string | null;
  membership_id?: string | null;
}

export interface MemberProfile {
  id: number;
  user_id: number;
  name_bn?: string | null;
  name_en?: string | null;
  father_name?: string | null;
  mother_name?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  blood_group?: string | null;
  nid_number?: string | null;
  photo_url?: string | null;
  designation_bn?: string | null;
  designation_en?: string | null;
  organization?: string | null;
  department?: string | null;
  profession?: string | null;
  academic_qualification?: string | null;
  professional_qualification?: string | null;
  years_of_experience?: number | null;
  employee_id?: string | null;
  diploma_institution?: string | null;
  graduation_year?: number | null;
  email?: string | null;
  phone?: string | null;
  alternate_phone?: string | null;
  current_address?: string | null;
  permanent_address?: string | null;
  district?: string | null;
  circle_id?: number | null;
  circle_bn?: string | null;
  circle_en?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_relationship?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact_address?: string | null;
  emergency_contact?: {
    name?: string | null;
    relationship?: string | null;
    phone?: string | null;
    address?: string | null;
  };
  preferred_language?: string;
  profile_visibility?: string;
  directory_visibility?: boolean;
  contact_visibility?: boolean;
  membership_id?: string | null;
  membership_type?: string;
  status?: string;
  issue_date?: string | null;
  validity_date?: string | null;
  is_verified_member?: boolean;
  protected_fields?: string[];
  editable_fields?: string[];
  profile_completion?: number;
  profile_completion_details?: ProfileCompletionDetails;
  verification_badges?: Record<string, VerificationBadge>;
  pending_change_requests?: ProfileChangeRequest[];
  personal_information?: {
    name_bn?: string | null;
    name_en?: string | null;
    father_name?: string | null;
    mother_name?: string | null;
    date_of_birth?: string | null;
    gender?: string | null;
    blood_group?: string | null;
    nid_number?: string | null;
    photo_url?: string | null;
  };
  professional_information?: {
    designation_bn?: string | null;
    designation_en?: string | null;
    organization?: string | null;
    department?: string | null;
    profession?: string | null;
    academic_qualification?: string | null;
    professional_qualification?: string | null;
    years_of_experience?: number | null;
    employee_id?: string | null;
    diploma_institution?: string | null;
    graduation_year?: number | null;
    circle_id?: number | null;
    circle_bn?: string | null;
    circle_en?: string | null;
  };
  contact_information?: {
    email?: string | null;
    phone?: string | null;
    alternate_phone?: string | null;
    current_address?: string | null;
    permanent_address?: string | null;
    district?: string | null;
    circle_id?: number | null;
    circle_bn?: string | null;
    circle_en?: string | null;
  };
}

export interface MembershipHistoryItem {
  id: number;
  reference?: string | null;
  date: string;
  year: string;
  action: string;
  action_label_en: string;
  action_label_bn: string;
  old_status?: string | null;
  new_status?: string | null;
  status?: string | null;
  old_validity?: string | null;
  new_validity?: string | null;
  period_label?: string | null;
  reason?: string | null;
  performed_by?: string | null;
  payment_reference?: string | null;
  payment_id?: number | null;
  certificate_no?: string | null;
  certificate_id?: number | null;
  created_at: string;
}

export type MembershipHistoryRecord = MembershipHistoryItem;

export interface MembershipSummary {
  status: 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED' | 'SUSPENDED' | 'PENDING' | 'CANCELLED' | string;
  status_label_en: string;
  status_label_bn: string;
  membership_id?: string | null;
  membership_type?: string | null;
  membership_type_label_en?: string | null;
  membership_type_label_bn?: string | null;
  circle?: string | null;
  circle_bn?: string | null;
  circle_en?: string | null;
  joined_at?: string | null;
  valid_until?: string | null;
  days_remaining?: number | null;
  validity_progress_percentage: number;
  can_renew: boolean;
  renewal_blocked_reason?: string | null;
  digital_id_available: boolean;
  certificate_available: boolean;
  recent_history: MembershipHistoryItem[];
}

export type MembershipSummaryResponse = MembershipSummary;

export interface MembershipRenewalOption {
  duration_years: number;
  plan_code: string;
  label_en: string;
  label_bn: string;
  base_fee: number;
  discount_amount: number;
  net_fee: number;
  formatted_net_fee: string;
  projected_valid_until: string;
  projected_valid_until_bn: string;
  recommended: boolean;
  savings_note_en?: string | null;
  savings_note_bn?: string | null;
  code?: string;
  years?: number;
  currency?: string;
  [key: string]: any;
}

export type MembershipRenewalPlan = MembershipRenewalOption;

export interface MembershipRenewalOptions {
  membership_id: string;
  current_status: string;
  current_valid_until?: string | null;
  can_renew: boolean;
  ineligibility_reason?: string | null;
  unresolved_renewal_reference?: string | null;
  options: MembershipRenewalOption[];
  periods?: any[];
  plans?: any[];
  [key: string]: any;
}

export type MembershipRenewalOptionsResponse = MembershipRenewalOptions;

export interface MembershipRenewalRequest {
  duration_years: number;
  plan_code: string;
  payment_gateway?: string;
  notes?: string;
}

export interface MembershipRenewalResult {
  renewal_id: number;
  renewal_reference: string;
  duration_years: number;
  net_fee: number;
  formatted_net_fee: string;
  status: string;
  projected_valid_until: string;
  payment_id?: number | null;
  payment_checkout_url?: string | null;
  message: string;
}

export type MembershipRenewalResponse = MembershipRenewalResult;

export interface ApplicationTimelineStep {
  step_number: number;
  code: string;
  label_en: string;
  label_bn: string;
  description_en: string;
  description_bn: string;
  status: 'COMPLETED' | 'CURRENT' | 'PENDING' | 'REJECTED' | string;
  completed_at?: string | null;
  remarks?: string | null;
}

export interface ApplicationCenterDetails {
  has_application: boolean;
  application_no?: string | null;
  membership_id?: string | null;
  membership_type?: string | null;
  current_stage?: string | null;
  current_stage_label_en?: string | null;
  current_stage_label_bn?: string | null;
  submitted_at?: string | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  timeline: ApplicationTimelineStep[];
  missing_documents: string[];
  uploaded_documents: Array<{
    id?: number;
    document_type?: string;
    filename?: string;
    status?: string;
    review_status?: string;
    uploaded_at?: string;
    url?: string;
    [key: string]: any;
  }>;
  can_upload_documents: boolean;
  can_pay: boolean;
  payment_reference?: string | null;
  payment_amount?: number | null;
  payment_url?: string | null;
}

export type ApplicationDetailsResponse = ApplicationCenterDetails;

// ─────────────────────────────────────────────────────────────────────────────
// Phase 4: Document Center, Digital ID & Certificates
// ─────────────────────────────────────────────────────────────────────────────

export interface DocumentVersionItem {
  id: number;
  version_number: number;
  filename: string;
  file_size: number;
  content_type: string;
  replacement_reason?: string | null;
  created_at: string;
  download_url: string;
}

export interface DocumentVerificationEventItem {
  id: number;
  action: 'VERIFIED' | 'REJECTED' | 'UPLOADED' | 'REPLACED' | string;
  actor_name: string;
  actor_role: string;
  notes?: string | null;
  created_at: string;
}

export interface MemberDocumentListItem {
  id: number;
  document_type: string;
  title: string;
  filename: string;
  status: 'PENDING' | 'UNDER_REVIEW' | 'APPROVED' | 'VERIFIED' | 'REJECTED' | 'EXPIRED' | string;
  version: number;
  file_size: number;
  file_size_formatted: string;
  uploaded_at?: string | null;
  verified_at?: string | null;
  expires_at?: string | null;
  reviewer_note?: string | null;
  download_url: string;
  preview_url: string;
}

export interface MemberDocumentDetail extends MemberDocumentListItem {
  versions: DocumentVersionItem[];
  verification_history: DocumentVerificationEventItem[];
}

export interface MemberDocumentSummary {
  total_count: number;
  verified_count: number;
  pending_count: number;
  rejected_count: number;
  expired_count: number;
  documents: MemberDocumentListItem[];
}

export interface DigitalMemberIdData {
  identifier: string;
  membership_id: string;
  name_en: string;
  name_bn?: string | null;
  membership_type: string;
  circle_en: string;
  circle_bn: string;
  designation_en?: string | null;
  designation_bn?: string | null;
  photo_url?: string | null;
  status: 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED' | 'SUSPENDED' | string;
  issue_date?: string | null;
  valid_until?: string | null;
  valid_until_formatted?: string | null;
  days_remaining?: number | null;
  is_valid: boolean;
  qr_code_data: string;
  verification_url: string;
  pdf_download_url: string;
  image_download_url: string;
}

export interface MemberCertificateItem {
  id: number;
  certificate_no: string;
  certificate_number: string;
  title_bn: string;
  title_en: string;
  certificate_type: 'MEMBERSHIP' | 'EVENT' | 'TRAINING' | 'APPRECIATION' | string;
  recipient_name: string;
  issue_date: string;
  status: 'VALID' | 'REVOKED' | 'EXPIRED' | string;
  revoked_at?: string | null;
  revocation_reason?: string | null;
  download_url: string;
  preview_url: string;
  verify_url: string;
}

export interface PublicMemberVerificationResult {
  is_valid: boolean;
  membership_id: string;
  member_name: string;
  member_name_bn?: string | null;
  membership_type: string;
  circle: string;
  status: 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED' | 'SUSPENDED' | 'CANCELLED' | string;
  valid_until?: string | null;
  days_remaining?: number | null;
  photo_url?: string | null;
  designation?: string | null;
  verified_at: string;
  verification_reference: string;
}

export interface PublicCertificateVerificationResult {
  is_valid: boolean;
  certificate_no: string;
  recipient_name: string;
  certificate_type: string;
  issue_date?: string | null;
  status: 'VALID' | 'REVOKED' | 'EXPIRED' | string;
  revoked_at?: string | null;
  revocation_reason?: string | null;
  verified_at: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase 5: Payment Center & Receipts
// ─────────────────────────────────────────────────────────────────────────────

export interface PaymentTransactionItem {
  id: number;
  transaction_ref: string;
  purpose: 'MEMBERSHIP' | 'RENEWAL' | 'APPLICATION' | 'EVENT' | string;
  purpose_label_en: string;
  purpose_label_bn: string;
  amount: number;
  amount_formatted: string;
  currency: string;
  status: 'INITIATED' | 'PENDING' | 'PROCESSING' | 'PAID' | 'SUCCESS' | 'FAILED' | 'CANCELLED' | 'REFUNDED' | 'EXPIRED' | string;
  status_label_en: string;
  status_label_bn: string;
  provider: 'SSLCOMMERZ' | 'BKASH' | 'NAGAD' | 'OFFLINE' | string;
  provider_tran_id?: string | null;
  receipt_no?: string | null;
  paid_at?: string | null;
  created_at: string;
  receipt_url?: string | null;
  receipt_pdf_url?: string | null;
}

export interface PaymentSummary {
  total_paid: number;
  total_paid_formatted: string;
  successful_count: number;
  pending_count: number;
  failed_count: number;
  refunded_count: number;
  transactions: PaymentTransactionItem[];
}

export interface PaymentReceiptData {
  receipt_no: string;
  transaction_ref: string;
  payment_id: number;
  member_id?: number | null;
  membership_id?: string | null;
  member_name: string;
  member_name_bn?: string | null;
  purpose: string;
  purpose_title_en: string;
  purpose_title_bn: string;
  amount: number;
  amount_formatted: string;
  currency: string;
  payment_date: string;
  provider: string;
  provider_tran_id?: string | null;
  status: string;
  verification_url: string;
  verification_qr_data: string;
  download_pdf_url: string;
}
