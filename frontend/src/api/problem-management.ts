import request from '@/utils/request'
import type {
  InternalUserOption,
  ProblemIssueSummaryListResponse,
  ProblemIssueSummaryQuery,
  ProblemManagementCatalogResponse,
} from '@/types/problem-management'

export const problemManagementApi = {
  getCatalog(): Promise<ProblemManagementCatalogResponse> {
    return request.get('/v1/problem-management/catalog')
  },
  getInternalUsers(params?: { keyword?: string }): Promise<InternalUserOption[]> {
    return request.get('/v1/problem-management/internal-users', { params })
  },
  getIssueSummaries(params: ProblemIssueSummaryQuery): Promise<ProblemIssueSummaryListResponse> {
    return request.get('/v1/problem-management/issues', { params })
  }
}
