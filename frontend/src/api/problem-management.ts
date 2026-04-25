import request from '@/utils/request'
import type {
  ProblemIssueSummaryListResponse,
  ProblemIssueSummaryQuery,
  ProblemManagementCatalogResponse,
} from '@/types/problem-management'

export const problemManagementApi = {
  getCatalog(): Promise<ProblemManagementCatalogResponse> {
    return request.get('/v1/problem-management/catalog')
  },
  getIssueSummaries(params: ProblemIssueSummaryQuery): Promise<ProblemIssueSummaryListResponse> {
    return request.get('/v1/problem-management/issues', { params })
  }
}
