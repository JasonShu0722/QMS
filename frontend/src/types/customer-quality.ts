/**
 * Customer quality management types.
 */

// Complaint ledger

export enum ComplaintType {
  ZERO_KM = '0km',
  AFTER_SALES = 'after_sales',
}

export type ComplaintStatus =
  | 'pending'
  | 'in_analysis'
  | 'in_response'
  | 'in_review'
  | 'closed'
  | 'rejected'

export interface CustomerComplaint {
  id: number
  complaint_number: string
  complaint_type: ComplaintType
  customer_id?: number
  customer_code: string
  customer_name?: string
  end_customer_name?: string
  product_type: string
  defect_description: string
  severity_level: string
  is_return_required: boolean
  requires_physical_analysis: boolean
  vin_code?: string
  mileage?: number
  purchase_date?: string
  status: ComplaintStatus | 'pending_analysis' | 'in_progress' | 'pending_8d' | 'under_review'
  cqe_id?: number
  cqe_name?: string
  responsible_dept?: string
  responsible_user_id?: number
  responsible_user_name?: string
  created_at: string
  updated_at: string
}

export interface CustomerComplaintCreate {
  complaint_type: ComplaintType
  customer_id?: number
  customer_code?: string
  customer_name?: string
  end_customer_name?: string
  product_type: string
  defect_description: string
  is_return_required: boolean
  requires_physical_analysis: boolean
  vin_code?: string
  mileage?: number
  purchase_date?: string
}

export interface CustomerComplaintListQuery {
  page?: number
  page_size?: number
  complaint_type?: ComplaintType
  customer_id?: number
  customer_code?: string
  product_type?: string
  status?: ComplaintStatus
  start_date?: string
  end_date?: string
}

export interface CustomerComplaintListResponse {
  total: number
  page: number
  page_size: number
  items: CustomerComplaint[]
}

export interface CustomerComplaintCustomerOption {
  id: number
  code: string
  name: string
}

export interface PreliminaryAnalysis {
  root_cause_analysis: string
  responsible_dept: string
  responsible_user_id: number
  containment_actions: string
}

// Customer 8D

export enum EightDStatus {
  DRAFT = 'draft',
  D0_D3_COMPLETED = 'd0_d3_completed',
  D4_D7_PENDING = 'd4_d7_pending',
  D4_D7_COMPLETED = 'd4_d7_completed',
  D8_PENDING = 'd8_pending',
  UNDER_REVIEW = 'under_review',
  APPROVED = 'approved',
  REJECTED = 'rejected',
}

export enum ApprovalLevel {
  SECTION_MANAGER = 'section_manager',
  DEPARTMENT_HEAD = 'department_head',
}

export interface EightDCustomer {
  id: number
  complaint_id: number
  d0_d3_cqe: Record<string, any>
  d4_d7_responsible: Record<string, any>
  d8_horizontal: Record<string, any>
  status: EightDStatus
  approval_level: ApprovalLevel
  created_at: string
  updated_at: string
}

export interface D0D3Data {
  problem_description: string
  containment_actions: string
  containment_in_transit: boolean
  containment_inventory: boolean
  containment_customer: boolean
}

export interface D4D7Data {
  root_cause: string
  analysis_method: string
  corrective_actions: string
  verification_report_url?: string
  standardization: boolean
  standardization_files?: string[]
}

export interface D8Data {
  horizontal_deployment: string[]
  lessons_learned: string
  save_to_library: boolean
}

export interface EightDCustomerSubmit {
  d4_d7_data: D4D7Data
}

export interface EightDD8Submit {
  d8_data: D8Data
}

export interface EightDReview {
  approved: boolean
  review_comments: string
}

// Claims

export interface CustomerClaim {
  id: number
  complaint_ids: number[]
  claim_amount: number
  claim_currency: string
  claim_date: string
  customer_name: string
  created_at: string
  updated_at: string
}

export interface CustomerClaimCreate {
  complaint_ids: number[]
  claim_amount: number
  claim_currency: string
  claim_date: string
  customer_name: string
}

export interface CustomerClaimListQuery {
  page?: number
  page_size?: number
  customer_name?: string
  start_date?: string
  end_date?: string
}

export interface CustomerClaimListResponse {
  total: number
  page: number
  page_size: number
  items: CustomerClaim[]
}

export enum SupplierClaimStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  PAID = 'paid',
}

export interface SupplierClaim {
  id: number
  complaint_id: number
  supplier_id: number
  supplier_name?: string
  claim_amount: number
  claim_currency: string
  claim_date: string
  status: SupplierClaimStatus
  created_at: string
  updated_at: string
}

export interface SupplierClaimCreate {
  complaint_id: number
  supplier_id: number
  claim_amount: number
  claim_currency: string
  claim_date: string
}

export interface SupplierClaimListQuery {
  page?: number
  page_size?: number
  supplier_id?: number
  status?: SupplierClaimStatus
  start_date?: string
  end_date?: string
}

export interface SupplierClaimListResponse {
  total: number
  page: number
  page_size: number
  items: SupplierClaim[]
}

// Metrics

export interface CustomerQualityAnalysis {
  zero_km_ppm: number
  three_mis_ppm: number
  twelve_mis_ppm: number
  trend_data: Array<{
    date: string
    zero_km_ppm: number
    three_mis_ppm: number
    twelve_mis_ppm: number
  }>
  product_type_breakdown: Array<{
    product_type: string
    complaint_count: number
    ppm: number
  }>
}
