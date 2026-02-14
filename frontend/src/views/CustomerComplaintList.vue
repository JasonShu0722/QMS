<template>
  <div class="customer-complaint-list p-4 md:p-6">
    <!-- 页面标题 -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
      <h1 class="text-2xl font-bold mb-4 md:mb-0">客诉管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon class="mr-1"><Plus /></el-icon>
        创建客诉单
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <el-card class="mb-4">
      <el-form :model="queryParams" inline class="flex flex-wrap gap-2">
        <el-form-item label="客诉类型">
          <el-select v-model="queryParams.complaint_type" placeholder="全部" clearable class="w-full md:w-40">
            <el-option label="0KM客诉" value="0km" />
            <el-option label="售后客诉" value="after_sales" />
          </el-select>
        </el-form-item>

        <el-form-item label="客户代码">
          <el-input v-model="queryParams.customer_code" placeholder="请输入" clearable class="w-full md:w-40" />
        </el-form-item>

        <el-form-item label="产品类型">
          <el-input v-model="queryParams.product_type" placeholder="请输入" clearable class="w-full md:w-40" />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable class="w-full md:w-40">
            <el-option label="待一次因解析" value="pending_analysis" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="待8D提交" value="pending_8d" />
            <el-option label="审核中" value="under_review" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="w-full md:w-64"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <el-table
        v-loading="loading"
        :data="complaintList"
        stripe
        class="w-full"
      >
        <el-table-column prop="complaint_number" label="客诉编号" width="150" fixed />
        <el-table-column prop="complaint_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.complaint_type === '0km' ? 'danger' : 'warning'">
              {{ row.complaint_type === '0km' ? '0KM' : '售后' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="customer_code" label="客户代码" width="120" />
        <el-table-column prop="product_type" label="产品类型" width="120" />
        <el-table-column prop="defect_description" label="缺陷描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="severity_level" label="严重度" width="100" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cqe_name" label="CQE" width="100" />
        <el-table-column prop="responsible_user_name" label="责任人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">
              查看
            </el-button>
            <el-button
              v-if="row.status === 'pending_analysis'"
              link
              type="primary"
              size="small"
              @click="handleAnalysis(row)"
            >
              一次因解析
            </el-button>
            <el-button
              v-if="row.status === 'pending_8d' || row.status === 'in_progress'"
              link
              type="primary"
              size="small"
              @click="handle8D(row)"
            >
              8D报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 创建客诉单对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建客诉单"
      width="90%"
      :close-on-click-modal="false"
      class="max-w-2xl"
    >
      <CustomerComplaintForm
        @success="handleCreateSuccess"
        @cancel="showCreateDialog = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import { getCustomerComplaints } from '@/api/customer-quality';
import CustomerComplaintForm from '@/components/CustomerComplaintForm.vue';
import type { CustomerComplaint, CustomerComplaintListQuery } from '@/types/customer-quality';

const router = useRouter();

// 数据状态
const loading = ref(false);
const complaintList = ref<CustomerComplaint[]>([]);
const total = ref(0);
const showCreateDialog = ref(false);
const dateRange = ref<[string, string] | null>(null);

// 查询参数
const queryParams = reactive<CustomerComplaintListQuery>({
  page: 1,
  page_size: 20,
  complaint_type: undefined,
  customer_code: undefined,
  product_type: undefined,
  status: undefined,
  start_date: undefined,
  end_date: undefined
});

/**
 * 获取状态标签
 */
function getStatusLabel(status: string): string {
  const statusMap: Record<string, string> = {
    pending_analysis: '待一次因解析',
    in_progress: '进行中',
    pending_8d: '待8D提交',
    under_review: '审核中',
    closed: '已关闭'
  };
  return statusMap[status] || status;
}

/**
 * 获取状态类型
 */
function getStatusType(status: string): string {
  const typeMap: Record<string, string> = {
    pending_analysis: 'warning',
    in_progress: 'primary',
    pending_8d: 'warning',
    under_review: 'info',
    closed: 'success'
  };
  return typeMap[status] || 'info';
}

/**
 * 加载客诉单列表
 */
async function loadComplaints() {
  loading.value = true;
  try {
    // 处理日期范围
    if (dateRange.value) {
      queryParams.start_date = dateRange.value[0];
      queryParams.end_date = dateRange.value[1];
    } else {
      queryParams.start_date = undefined;
      queryParams.end_date = undefined;
    }

    const response = await getCustomerComplaints(queryParams);
    complaintList.value = response.items;
    total.value = response.total;
  } catch (error) {
    ElMessage.error('加载客诉单列表失败');
    console.error('Load complaints error:', error);
  } finally {
    loading.value = false;
  }
}

/**
 * 查询
 */
function handleSearch() {
  queryParams.page = 1;
  loadComplaints();
}

/**
 * 重置
 */
function handleReset() {
  queryParams.page = 1;
  queryParams.page_size = 20;
  queryParams.complaint_type = undefined;
  queryParams.customer_code = undefined;
  queryParams.product_type = undefined;
  queryParams.status = undefined;
  dateRange.value = null;
  loadComplaints();
}

/**
 * 查看详情
 */
function handleView(row: CustomerComplaint) {
  router.push(`/customer-complaints/${row.id}`);
}

/**
 * 一次因解析
 */
function handleAnalysis(row: CustomerComplaint) {
  router.push(`/customer-complaints/${row.id}/analysis`);
}

/**
 * 8D报告
 */
function handle8D(row: CustomerComplaint) {
  router.push(`/customer-complaints/${row.id}/8d`);
}

/**
 * 创建成功
 */
function handleCreateSuccess() {
  showCreateDialog.value = false;
  ElMessage.success('客诉单创建成功');
  loadComplaints();
}

// 初始化
onMounted(() => {
  loadComplaints();
});
</script>

<style scoped>
.customer-complaint-list {
  min-height: 100vh;
}

/* 移动端适配 */
@media (max-width: 768px) {
  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-button) {
    padding: 4px 8px;
    font-size: 12px;
  }
}
</style>
