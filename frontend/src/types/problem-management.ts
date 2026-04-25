export type ProblemResponseMode = 'brief' | 'eight_d'

export type ProblemHandlingLevel = 'simple' | 'complex' | 'major'

export type ProblemModuleKey =
  | 'customer_quality'
  | 'process_quality'
  | 'incoming_quality'
  | 'new_product_quality'
  | 'audit_management'

export type ProblemCategoryKey =
  | 'CQ0'
  | 'CQ1'
  | 'PQ0'
  | 'PQ1'
  | 'IQ0'
  | 'IQ1'
  | 'DQ0'
  | 'DQ1'
  | 'AQ0'
  | 'AQ1'
  | 'AQ2'
  | 'AQ3'

export type UnifiedProblemStatus =
  | 'open'
  | 'assigned'
  | 'responding'
  | 'pending_review'
  | 'verifying'
  | 'closed'
  | 'rejected'

export interface ProblemCategoryItem {
  key: ProblemCategoryKey
  category_code: string
  subcategory_code: string
  module_key: ProblemModuleKey
  label: string
}

export interface NumberingRuleItem {
  issue_prefix: string
  report_prefix: string
  issue_pattern: string
  report_pattern: string
}

export interface ProblemManagementCatalogResponse {
  response_modes: ProblemResponseMode[]
  handling_levels: ProblemHandlingLevel[]
  categories: ProblemCategoryItem[]
  numbering_rule: NumberingRuleItem
}

export interface ProblemIssueSummaryQuery {
  module_key?: ProblemModuleKey
  problem_category_key?: ProblemCategoryKey
  unified_status?: UnifiedProblemStatus
  keyword?: string
  only_assigned_to_me?: boolean
  only_actionable_to_me?: boolean
  only_created_by_me?: boolean
  only_overdue?: boolean
  page?: number
  page_size?: number
}

export interface ProblemIssueSummaryItem {
  source_type: 'customer_complaint' | 'process_issue' | 'trial_issue' | 'audit_nc' | 'scar' | string
  source_id: number
  source_label: string
  module_key: ProblemModuleKey | string
  problem_category_key: ProblemCategoryKey | string
  problem_category_label: string
  reference_no?: string | null
  title: string
  raw_status: string
  unified_status: UnifiedProblemStatus
  responsible_dept?: string | null
  assigned_to?: number | null
  action_owner_id?: number | null
  created_by_id?: number | null
  owner_id?: number | null
  verified_by?: number | null
  response_mode?: ProblemResponseMode | null
  customer_name?: string | null
  requires_physical_analysis?: boolean | null
  is_overdue: boolean
  due_at?: string | null
  created_at: string
  updated_at: string
}

export interface ProblemIssueSummaryListResponse {
  total: number
  page: number
  page_size: number
  module_counts?: Record<string, number>
  items: ProblemIssueSummaryItem[]
}
