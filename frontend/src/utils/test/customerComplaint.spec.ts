import { describe, expect, it } from 'vitest'
import {
  buildCustomerComplaintStatusOptions,
  canOpenCustomerComplaintEightD,
  canSubmitCustomerComplaintAnalysis,
  getCustomerComplaintStatusLabel,
  getCustomerComplaintStatusType,
} from '@/utils/customerComplaint'

describe('customer complaint helpers', () => {
  it('maps backend statuses to readable labels and tag types', () => {
    expect(getCustomerComplaintStatusLabel('pending')).toBe('待处理')
    expect(getCustomerComplaintStatusLabel('in_response')).toBe('待回复')
    expect(getCustomerComplaintStatusType('closed')).toBe('success')
    expect(getCustomerComplaintStatusType('rejected')).toBe('danger')
  })

  it('keeps legacy customer complaint statuses compatible during transition', () => {
    expect(getCustomerComplaintStatusLabel('pending_analysis')).toBe('待一次因解析')
    expect(getCustomerComplaintStatusType('under_review')).toBe('info')
  })

  it('builds the current complaint status options in backend order', () => {
    expect(buildCustomerComplaintStatusOptions().map((item) => item.value)).toEqual([
      'pending',
      'in_analysis',
      'in_response',
      'in_review',
      'rejected',
      'closed',
    ])
  })

  it('derives action availability from complaint status and analysis requirement', () => {
    expect(
      canSubmitCustomerComplaintAnalysis({
        status: 'pending',
        requires_physical_analysis: true,
      })
    ).toBe(true)
    expect(
      canSubmitCustomerComplaintAnalysis({
        status: 'pending',
        requires_physical_analysis: false,
      })
    ).toBe(false)
    expect(canOpenCustomerComplaintEightD({ status: 'in_response' })).toBe(true)
    expect(canOpenCustomerComplaintEightD({ status: 'pending' })).toBe(false)
  })
})
