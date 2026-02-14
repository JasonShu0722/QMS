<template>
  <div class="process-issue-list">
    <!-- 页面标题 -->
    <div class="page-header mb-6">
      <h1 class="text-2xl font-bold">制程问题清单</h1>
      <p class="text-gray-500 mt-2">制程质量问题发单与闭环管理</p>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card mb-4">
      <el-form :model="filterForm" inline>
        <el-form-item label="问题状态">
          <el-select
            v-model="filterForm.status"
            placeholder="请选择状态"
            clearable
            class="w-40"
          >
            <el-option label="待处理" value="open" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="验证中" value="verifying" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>

        <el-form-item label="责任类别">
          <el-select
            v-model="filterForm.responsibility_category"
            placeholder="请选择责任类别"
            clearable
            class="w-48"
          >
            <el-option
              v-for="cat in responsibilityCategories"
              :key="cat.value"
              :label="cat.label"
              :value="cat.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="是否逾期">
          <el-select
            v-model="filterForm.is_overdue"
            placeholder="全部"
            clearable
            class="w-32"
          >
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item label="创建日期">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="w-64"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">查询</el-button>
          <el-button :icon="Refresh" @click="handleReset">重置</el-button>
          <el-button type="success" :icon="Plus" @click="handleCreate">发起问题单</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="mb-4">
      <el-col :span="6" :xs="12">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value text-blue-600">{{ statistics.total }}</div>
            <div class="stat-label">总问题数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value text-orange-600">{{ statistics.open }}</div>
            <div class="stat-label">待处理</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value text-yellow-600">{{ statistics.in_progress }}</div>
            <div class="stat-label">处理中</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6" :xs="12">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value text-red-600">{{ statistics.overdue }}</div>
            <div class="stat-label">已逾期</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        border
        style="width: 100%"
      >
        <el-table-column prop="issue_number" label="问题单号" width="180" fixed="left" />
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-column>

        <el-table-column label="逾期" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_overdue" type="danger" size="small">逾期</el-tag>
            <el-tag v-else type="success" size="small">正常</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="issue_description" label="问题描述" min-width="250" show-overflow-tooltip />
        
        <el-table-column label="责任类别" width="120">
          <template #default="{ row }">
            <el-tag :type="getResponsibilityTagType(row.responsibility_category)">
              {{ getResponsibilityLabel(row.responsibility_category) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="verification_end_date" label="验证截止日期" width="120" />

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleView(row)">
              查看详情
            </el-button>
            <el-button
              v-if="canRespond(row)"
              type="success"
              size="small"
              link
              @click="handleRespond(row)"
            >
              填写对策
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { Search, Refresh, Plus } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';
import {
  getProcessIssues,
  getResponsibilityCategories
} from '@/api/process-quality';
import type {
  ProcessIssue,
  ProcessIssueFilter,
  ProcessIssueStatus,
  ResponsibilityCategory,
  ResponsibilityCategoryOption,
  ProcessIssueListResponse
} from '@/types/process-quality';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

// 状态
const loading = ref(false);
const tableData = ref<ProcessIssue[]>([]);
const responsibilityCategories = ref<ResponsibilityCategoryOption[]>([]);

// 日期范围
const dateRange = ref<[string, string] | null>(null);

// 筛选表单
const filterForm = reactive<ProcessIssueFilter>({
  status: undefined,
  responsibility_category: undefined,
  is_overdue: undefined,
  page: 1,
  page_size: 20
});

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
});

// 统计数据
const statistics = computed(() => {
  const stats = {
    total: tableData.value.length,
    open: 0,
    in_progress: 0,
    overdue: 0
  };

  tableData.value.forEach(item => {
    if (item.status === 'open') stats.open++;
    if (item.status === 'in_progress') stats.in_progress++;
    if (item.is_overdue) stats.overdue++;
  });

  return stats;
});

// 获取状态标签类型
const getStatusTagType = (status: ProcessIssueStatus): string => {
  const typeMap: Record<ProcessIssueStatus, string> = {
    open: 'warning',
    in_progress: 'primary',
    verifying: 'info',
    closed: 'success'
  };
  return typeMap[status] || 'info';
};

// 获取状态标签文本
const getStatusLabel = (status: ProcessIssueStatus): string => {
  const labelMap: Record<ProcessIssueStatus, string> = {
    open: '待处理',
    in_progress: '处理中',
    verifying: '验证中',
    closed: '已关闭'
  };
  return labelMap[status] || status;
};

// 获取责任类别标签类型
const getResponsibilityTagType = (category: ResponsibilityCategory): string => {
  const typeMap: Record<ResponsibilityCategory, string> = {
    material_defect: 'danger',
    operation_defect: 'warning',
    equipment_defect: 'info',
    process_defect: 'primary',
    design_defect: 'success'
  };
  return typeMap[category] || 'info';
};

// 获取责任类别标签文本
const getResponsibilityLabel = (category: ResponsibilityCategory): string => {
  const cat = responsibilityCategories.value.find(c => c.value === category);
  return cat?.label || category;
};

// 格式化日期时间
const formatDateTime = (dateTime: string): string => {
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 判断是否可以填写对策
const canRespond = (row: ProcessIssue): boolean => {
  // 只有待处理状态且当前用户是指派人才能填写对策
  return row.status === 'open' && row.assigned_to === authStore.userInfo?.id;
};

// 加载责任类别选项
const loadResponsibilityCategories = async () => {
  try {
    const response = await getResponsibilityCategories() as { categories: ResponsibilityCategoryOption[] };
    responsibilityCategories.value = response.categories;
  } catch (error) {
    console.error('Failed to load responsibility categories:', error);
  }
};

// 加载数据
const loadData = async () => {
  loading.value = true;
  try {
    const params: ProcessIssueFilter = {
      ...filterForm,
      start_date: dateRange.value?.[0],
      end_date: dateRange.value?.[1],
      page: pagination.page,
      page_size: pagination.page_size
    };

    const response = await getProcessIssues(params) as ProcessIssueListResponse;
    tableData.value = response.items;
    pagination.total = response.total;
  } catch (error) {
    console.error('Failed to load process issues:', error);
    ElMessage.error('加载制程问题单失败');
  } finally {
    loading.value = false;
  }
};

// 查询
const handleSearch = () => {
  pagination.page = 1;
  loadData();
};

// 重置
const handleReset = () => {
  Object.assign(filterForm, {
    status: undefined,
    responsibility_category: undefined,
    is_overdue: undefined,
    page: 1,
    page_size: 20
  });
  dateRange.value = null;
  handleSearch();
};

// 创建
const handleCreate = () => {
  router.push({ name: 'ProcessIssueCreate' });
};

// 查看详情
const handleView = (row: ProcessIssue) => {
  router.push({
    name: 'ProcessIssueDetail',
    params: { id: row.id }
  });
};

// 填写对策
const handleRespond = (row: ProcessIssue) => {
  router.push({
    name: 'ProcessIssueDetail',
    params: { id: row.id },
    query: { action: 'respond' }
  });
};

// 分页变化
const handleSizeChange = (size: number) => {
  pagination.page_size = size;
  pagination.page = 1;
  loadData();
};

const handlePageChange = (page: number) => {
  pagination.page = page;
  loadData();
};

// 生命周期
onMounted(() => {
  loadResponsibilityCategories();
  loadData();
});
</script>

<style scoped>
.process-issue-list {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.page-header {
  margin-bottom: 24px;
}

.filter-card {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  padding: 12px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.pagination-container {
  margin-top: 16px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .process-issue-list {
    padding: 12px;
  }

  .el-form--inline .el-form-item {
    display: block;
    margin-right: 0;
    margin-bottom: 12px;
  }

  .el-form--inline .el-form-item .el-input,
  .el-form--inline .el-form-item .el-select,
  .el-form--inline .el-form-item .el-date-picker {
    width: 100% !important;
  }

  .stat-value {
    font-size: 24px;
  }
}
</style>
