/**
 * 客户质量管理 API 客户端
 * Customer Quality Management API Client
 */
import request from '@/utils/request';
import type {
  CustomerComplaint,
  CustomerComplaintCreate,
  CustomerComplaintListQuery,
  CustomerComplaintListResponse,
  PreliminaryAnalysis,
  EightDCustomer,
  EightDCustomerSubmit,
  EightDD8Submit,
  EightDReview,
  CustomerClaim,
  CustomerClaimCreate,
  CustomerClaimListQuery,
  CustomerClaimListResponse,
  SupplierClaim,
  SupplierClaimCreate,
  SupplierClaimListQuery,
  SupplierClaimListResponse,
  CustomerQualityAnalysis
} from '@/types/customer-quality';

// ==================== 客诉单 API ====================

/**
 * 获取客诉单列表
 */
export async function getCustomerComplaints(params: CustomerComplaintListQuery): Promise<CustomerComplaintListResponse> {
  return request({
    url: '/api/v1/customer-complaints',
    method: 'get',
    params
  });
}

/**
 * 获取客诉单详情
 */
export async function getCustomerComplaint(id: number): Promise<CustomerComplaint> {
  return request({
    url: `/api/v1/customer-complaints/${id}`,
    method: 'get'
  });
}

/**
 * 创建客诉单
 */
export async function createCustomerComplaint(data: CustomerComplaintCreate): Promise<CustomerComplaint> {
  return request({
    url: '/api/v1/customer-complaints',
    method: 'post',
    data
  });
}

/**
 * CQE 一次因解析
 */
export async function submitPreliminaryAnalysis(id: number, data: PreliminaryAnalysis): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${id}/preliminary-analysis`,
    method: 'post',
    data
  });
}

// ==================== 客诉 8D 报告 API ====================

/**
 * 获取 8D 报告详情
 */
export async function getEightDCustomer(complaintId: number): Promise<EightDCustomer> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d`,
    method: 'get'
  });
}

/**
 * 责任板块填写 D4-D7
 */
export async function submitEightDCustomer(complaintId: number, data: EightDCustomerSubmit): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d`,
    method: 'post',
    data
  });
}

/**
 * 提交 D8 水平展开和经验教训
 */
export async function submitEightDD8(complaintId: number, data: EightDD8Submit): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d/d8`,
    method: 'post',
    data
  });
}

/**
 * 审核 8D 报告
 */
export async function reviewEightDCustomer(complaintId: number, data: EightDReview): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d/review`,
    method: 'post',
    data
  });
}

/**
 * 驳回 8D 报告
 */
export async function rejectEightDCustomer(complaintId: number, reason: string): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d/reject`,
    method: 'post',
    data: { reason }
  });
}

// ==================== 客户索赔 API ====================

/**
 * 获取客户索赔列表
 */
export async function getCustomerClaims(params: CustomerClaimListQuery): Promise<CustomerClaimListResponse> {
  return request({
    url: '/api/v1/customer-claims',
    method: 'get',
    params
  });
}

/**
 * 获取客户索赔详情
 */
export async function getCustomerClaim(id: number): Promise<CustomerClaim> {
  return request({
    url: `/api/v1/customer-claims/${id}`,
    method: 'get'
  });
}

/**
 * 创建客户索赔
 */
export async function createCustomerClaim(data: CustomerClaimCreate): Promise<CustomerClaim> {
  return request({
    url: '/api/v1/customer-claims',
    method: 'post',
    data
  });
}

// ==================== 供应商索赔 API ====================

/**
 * 获取供应商索赔列表
 */
export async function getSupplierClaims(params: SupplierClaimListQuery): Promise<SupplierClaimListResponse> {
  return request({
    url: '/api/v1/supplier-claims',
    method: 'get',
    params
  });
}

/**
 * 获取供应商索赔详情
 */
export async function getSupplierClaim(id: number): Promise<SupplierClaim> {
  return request({
    url: `/api/v1/supplier-claims/${id}`,
    method: 'get'
  });
}

/**
 * 创建供应商索赔
 */
export async function createSupplierClaim(data: SupplierClaimCreate): Promise<SupplierClaim> {
  return request({
    url: '/api/v1/supplier-claims',
    method: 'post',
    data
  });
}

/**
 * 从客诉单一键转嫁供应商索赔
 */
export async function transferToSupplierClaim(complaintId: number, data: Omit<SupplierClaimCreate, 'complaint_id'>): Promise<SupplierClaim> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/transfer-claim`,
    method: 'post',
    data
  });
}

// ==================== 客户质量分析 API ====================

/**
 * 获取客户质量分析数据
 */
export async function getCustomerQualityAnalysis(params?: { start_date?: string; end_date?: string }): Promise<CustomerQualityAnalysis> {
  return request({
    url: '/api/v1/quality-metrics/customer-analysis',
    method: 'get',
    params
  });
}
