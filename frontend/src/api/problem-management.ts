import request from '@/utils/request'
import type { ProblemManagementCatalogResponse } from '@/types/problem-management'

export const problemManagementApi = {
  getCatalog(): Promise<ProblemManagementCatalogResponse> {
    return request.get('/v1/problem-management/catalog')
  }
}
