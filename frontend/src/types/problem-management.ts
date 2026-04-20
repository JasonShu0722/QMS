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
