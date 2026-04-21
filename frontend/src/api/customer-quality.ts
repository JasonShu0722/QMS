/**
 * Customer quality management API client.
 */
import request from '@/utils/request'
import type {
  CustomerClaim,
  CustomerClaimCreate,
  CustomerClaimListQuery,
  CustomerClaimListResponse,
  CustomerComplaint,
  CustomerComplaintCreate,
  CustomerComplaintCustomerOption,
  CustomerComplaintListQuery,
  CustomerComplaintListResponse,
  CustomerQualityAnalysis,
  EightDCustomer,
  EightDCustomerSubmit,
  EightDD8Submit,
  EightDReview,
  PreliminaryAnalysis,
  SupplierClaim,
  SupplierClaimCreate,
  SupplierClaimListQuery,
  SupplierClaimListResponse,
} from '@/types/customer-quality'

export async function getCustomerComplaints(
  params: CustomerComplaintListQuery
): Promise<CustomerComplaintListResponse> {
  return request({
    url: '/api/v1/customer-complaints',
    method: 'get',
    params,
  })
}

export async function getCustomerComplaint(id: number): Promise<CustomerComplaint> {
  return request({
    url: `/api/v1/customer-complaints/${id}`,
    method: 'get',
  })
}

export async function getCustomerComplaintCustomerOptions(
  params?: { keyword?: string }
): Promise<CustomerComplaintCustomerOption[]> {
  return request({
    url: '/api/v1/customer-complaints/customers',
    method: 'get',
    params,
  })
}

export async function createCustomerComplaint(data: CustomerComplaintCreate): Promise<CustomerComplaint> {
  return request({
    url: '/api/v1/customer-complaints',
    method: 'post',
    data,
  })
}

export async function submitPreliminaryAnalysis(
  id: number,
  data: PreliminaryAnalysis
): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${id}/preliminary-analysis`,
    method: 'post',
    data,
  })
}

export async function getEightDCustomer(complaintId: number): Promise<EightDCustomer> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d`,
    method: 'get',
  })
}

export async function submitEightDCustomer(
  complaintId: number,
  data: EightDCustomerSubmit
): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d`,
    method: 'post',
    data,
  })
}

export async function submitEightDD8(
  complaintId: number,
  data: EightDD8Submit
): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d/d8`,
    method: 'post',
    data,
  })
}

export async function reviewEightDCustomer(
  complaintId: number,
  data: EightDReview
): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d/review`,
    method: 'post',
    data,
  })
}

export async function rejectEightDCustomer(
  complaintId: number,
  reason: string
): Promise<{ message: string }> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/8d/reject`,
    method: 'post',
    data: { reason },
  })
}

export async function getCustomerClaims(params: CustomerClaimListQuery): Promise<CustomerClaimListResponse> {
  return request({
    url: '/api/v1/customer-claims',
    method: 'get',
    params,
  })
}

export async function getCustomerClaim(id: number): Promise<CustomerClaim> {
  return request({
    url: `/api/v1/customer-claims/${id}`,
    method: 'get',
  })
}

export async function createCustomerClaim(data: CustomerClaimCreate): Promise<CustomerClaim> {
  return request({
    url: '/api/v1/customer-claims',
    method: 'post',
    data,
  })
}

export async function getSupplierClaims(params: SupplierClaimListQuery): Promise<SupplierClaimListResponse> {
  return request({
    url: '/api/v1/supplier-claims',
    method: 'get',
    params,
  })
}

export async function getSupplierClaim(id: number): Promise<SupplierClaim> {
  return request({
    url: `/api/v1/supplier-claims/${id}`,
    method: 'get',
  })
}

export async function createSupplierClaim(data: SupplierClaimCreate): Promise<SupplierClaim> {
  return request({
    url: '/api/v1/supplier-claims',
    method: 'post',
    data,
  })
}

export async function transferToSupplierClaim(
  complaintId: number,
  data: Omit<SupplierClaimCreate, 'complaint_id'>
): Promise<SupplierClaim> {
  return request({
    url: `/api/v1/customer-complaints/${complaintId}/transfer-claim`,
    method: 'post',
    data,
  })
}

export async function getCustomerQualityAnalysis(
  params?: { start_date?: string; end_date?: string }
): Promise<CustomerQualityAnalysis> {
  return request({
    url: '/api/v1/quality-metrics/customer-analysis',
    method: 'get',
    params,
  })
}
