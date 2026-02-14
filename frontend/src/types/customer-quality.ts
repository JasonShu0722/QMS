/**
 * 客户质量管理类型定义
 * Customer Quality Management Type Definitions
 */

// ==================== 客诉单类型 ====================

/**
 * 客诉类型枚举
 */
export enum ComplaintType {
  ZERO_KM = '0km',
  AFTER_SALES = 'after_sales'
}

/**
 * 客诉状态枚举
 */
export enum ComplaintStatus {
  PENDING_ANALYSIS = 'pending_analysis',  // 待一次因解析
  IN_PROGRESS = 'in_progress',            // 进行中
  PENDING_8D = 'pending_8d',              // 待8D提交
  UNDER_REVIEW = 'under_review',          // 审核中
  CLOSED = 'closed'                       // 已关闭
}

/**
 * 客诉单基础信息
 */
export interface CustomerComplaint {
  id: number;
  complaint_number: string;
  complaint_type: ComplaintType;
  customer_code: string;
  product_type: string;
  defect_description: string;
  severity_level: string;
  vin_code?: string;
  mileage?: number;
  purchase_date?: string;
  status: ComplaintStatus;
  cqe_id?: number;
  cqe_name?: string;
  responsible_dept?: string;
  responsible_user_id?: number;
  responsible_user_name?: string;
  created_at: string;
  updated_at: string;
}

/**
 * 客诉单创建请求
 */
export interface CustomerComplaintCreate {
  complaint_type: ComplaintType;
  customer_code: string;
  product_type: string;
  defect_description: string;
  severity_level: string;
  vin_code?: string;
  mileage?: number;
  purchase_date?: string;
}

/**
 * 客诉单列表查询参数
 */
export interface CustomerComplaintListQuery {
  page?: number;
  page_size?: number;
  complaint_type?: ComplaintType;
  customer_code?: string;
  product_type?: string;
  status?: ComplaintStatus;
  start_date?: string;
  end_date?: string;
}

/**
 * 客诉单列表响应
 */
export interface CustomerComplaintListResponse {
  total: number;
  page: number;
  page_size: number;
  items: CustomerComplaint[];
}

/**
 * 一次因解析请求
 */
export interface PreliminaryAnalysis {
  root_cause_analysis: string;
  responsible_dept: string;
  responsible_user_id: number;
  containment_actions: string;
}

// ==================== 客诉 8D 报告类型 ====================

/**
 * 8D 报告状态
 */
export enum EightDStatus {
  DRAFT = 'draft',                    // 草稿
  D0_D3_COMPLETED = 'd0_d3_completed', // D0-D3完成
  D4_D7_PENDING = 'd4_d7_pending',    // 待D4-D7
  D4_D7_COMPLETED = 'd4_d7_completed', // D4-D7完成
  D8_PENDING = 'd8_pending',          // 待D8
  UNDER_REVIEW = 'under_review',      // 审核中
  APPROVED = 'approved',              // 已批准
  REJECTED = 'rejected'               // 已驳回
}

/**
 * 审批等级
 */
export enum ApprovalLevel {
  SECTION_MANAGER = 'section_manager',  // 科室经理
  DEPARTMENT_HEAD = 'department_head'   // 部长联合审批
}

/**
 * 8D 报告基础信息
 */
export interface EightDCustomer {
  id: number;
  complaint_id: number;
  d0_d3_cqe: Record<string, any>;
  d4_d7_responsible: Record<string, any>;
  d8_horizontal: Record<string, any>;
  status: EightDStatus;
  approval_level: ApprovalLevel;
  created_at: string;
  updated_at: string;
}

/**
 * D0-D3 数据结构
 */
export interface D0D3Data {
  problem_description: string;      // 问题描述 (5W2H)
  containment_actions: string;      // 围堵措施
  containment_in_transit: boolean;  // 在途品围堵
  containment_inventory: boolean;   // 库存品围堵
  containment_customer: boolean;    // 客户端库存围堵
}

/**
 * D4-D7 数据结构
 */
export interface D4D7Data {
  root_cause: string;               // 根本原因
  analysis_method: string;          // 分析方法 (5Why/鱼骨图/FTA)
  corrective_actions: string;       // 纠正措施
  verification_report_url?: string; // D6验证报告附件
  standardization: boolean;         // 是否涉及文件修改
  standardization_files?: string[]; // 标准化文件附件
}

/**
 * D8 数据结构
 */
export interface D8Data {
  horizontal_deployment: string[];  // 水平展开项目
  lessons_learned: string;          // 经验教训
  save_to_library: boolean;         // 是否沉淀到经验库
}

/**
 * 8D 报告提交请求
 */
export interface EightDCustomerSubmit {
  d4_d7_data: D4D7Data;
}

/**
 * D8 提交请求
 */
export interface EightDD8Submit {
  d8_data: D8Data;
}

/**
 * 8D 审核请求
 */
export interface EightDReview {
  approved: boolean;
  review_comments: string;
}

// ==================== 索赔管理类型 ====================

/**
 * 客户索赔
 */
export interface CustomerClaim {
  id: number;
  complaint_ids: number[];
  claim_amount: number;
  claim_currency: string;
  claim_date: string;
  customer_name: string;
  created_at: string;
  updated_at: string;
}

/**
 * 客户索赔创建请求
 */
export interface CustomerClaimCreate {
  complaint_ids: number[];
  claim_amount: number;
  claim_currency: string;
  claim_date: string;
  customer_name: string;
}

/**
 * 客户索赔列表查询参数
 */
export interface CustomerClaimListQuery {
  page?: number;
  page_size?: number;
  customer_name?: string;
  start_date?: string;
  end_date?: string;
}

/**
 * 客户索赔列表响应
 */
export interface CustomerClaimListResponse {
  total: number;
  page: number;
  page_size: number;
  items: CustomerClaim[];
}

/**
 * 供应商索赔状态
 */
export enum SupplierClaimStatus {
  PENDING = 'pending',      // 待处理
  APPROVED = 'approved',    // 已批准
  REJECTED = 'rejected',    // 已拒绝
  PAID = 'paid'            // 已支付
}

/**
 * 供应商索赔
 */
export interface SupplierClaim {
  id: number;
  complaint_id: number;
  supplier_id: number;
  supplier_name?: string;
  claim_amount: number;
  claim_currency: string;
  claim_date: string;
  status: SupplierClaimStatus;
  created_at: string;
  updated_at: string;
}

/**
 * 供应商索赔创建请求
 */
export interface SupplierClaimCreate {
  complaint_id: number;
  supplier_id: number;
  claim_amount: number;
  claim_currency: string;
  claim_date: string;
}

/**
 * 供应商索赔列表查询参数
 */
export interface SupplierClaimListQuery {
  page?: number;
  page_size?: number;
  supplier_id?: number;
  status?: SupplierClaimStatus;
  start_date?: string;
  end_date?: string;
}

/**
 * 供应商索赔列表响应
 */
export interface SupplierClaimListResponse {
  total: number;
  page: number;
  page_size: number;
  items: SupplierClaim[];
}

// ==================== 客户质量分析类型 ====================

/**
 * 客户质量分析数据
 */
export interface CustomerQualityAnalysis {
  zero_km_ppm: number;
  three_mis_ppm: number;
  twelve_mis_ppm: number;
  trend_data: {
    date: string;
    zero_km_ppm: number;
    three_mis_ppm: number;
    twelve_mis_ppm: number;
  }[];
  product_type_breakdown: {
    product_type: string;
    complaint_count: number;
    ppm: number;
  }[];
}
