import type { ComplaintStatus, CustomerComplaint } from '@/types/customer-quality'

export type CustomerComplaintStatusLike =
  | ComplaintStatus
  | 'pending_analysis'
  | 'in_progress'
  | 'pending_8d'
  | 'under_review'

type StatusMeta = {
  label: string
  tagType: 'success' | 'warning' | 'info' | 'primary' | 'danger'
}

const STATUS_META: Record<CustomerComplaintStatusLike, StatusMeta> = {
  pending: { label: '待处理', tagType: 'warning' },
  in_analysis: { label: '分析中', tagType: 'primary' },
  in_response: { label: '待回复', tagType: 'warning' },
  in_review: { label: '审核中', tagType: 'info' },
  closed: { label: '已关闭', tagType: 'success' },
  rejected: { label: '已驳回', tagType: 'danger' },
  pending_analysis: { label: '待一次因解析', tagType: 'warning' },
  in_progress: { label: '进行中', tagType: 'primary' },
  pending_8d: { label: '待8D提交', tagType: 'warning' },
  under_review: { label: '审核中', tagType: 'info' },
}

export function buildCustomerComplaintStatusOptions() {
  return [
    { value: 'pending', label: STATUS_META.pending.label },
    { value: 'in_analysis', label: STATUS_META.in_analysis.label },
    { value: 'in_response', label: STATUS_META.in_response.label },
    { value: 'in_review', label: STATUS_META.in_review.label },
    { value: 'rejected', label: STATUS_META.rejected.label },
    { value: 'closed', label: STATUS_META.closed.label },
  ] as Array<{ value: ComplaintStatus; label: string }>
}

export function getCustomerComplaintStatusLabel(status: CustomerComplaintStatusLike): string {
  return STATUS_META[status]?.label ?? status
}

export function getCustomerComplaintStatusType(
  status: CustomerComplaintStatusLike
): StatusMeta['tagType'] {
  return STATUS_META[status]?.tagType ?? 'info'
}

export function canSubmitCustomerComplaintAnalysis(
  complaint: Pick<CustomerComplaint, 'status' | 'requires_physical_analysis'>
): boolean {
  return complaint.requires_physical_analysis && ['pending', 'pending_analysis'].includes(complaint.status)
}

export function canOpenCustomerComplaintEightD(
  complaint: Pick<CustomerComplaint, 'status'>
): boolean {
  return ['in_analysis', 'in_response', 'in_progress', 'pending_8d'].includes(complaint.status)
}
