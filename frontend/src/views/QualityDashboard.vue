<template>
  <div class="quality-dashboard">
    <!-- 页面标题和控制栏 -->
    <div class="dashboard-header">
      <h1 class="text-2xl font-bold mb-4">质量数据仪表盘</h1>
      
      <!-- 控制按钮组 -->
      <div class="controls flex flex-wrap gap-4 mb-6">
        <!-- 日期选择 -->
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="loadDashboard"
        />

        <!-- 指标类型选择 -->
        <el-select
          v-model="selectedMetricType"
          placeholder="选择指标类型"
          @change="loadTrendData"
          class="w-64"
        >
          <el-option
            v-for="metric in availableMetrics"
            :key="metric.value"
            :label="metric.label"
            :value="metric.value"
          />
        </el-select>

        <!-- 时间范围选择 -->
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="loadTrendData"
        />

        <!-- 刷新按钮 -->
        <el-button :icon="Refresh" @click="refreshAll">刷新</el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- 仪表盘内容 -->
    <div v-else class="dashboard-content">
      <!-- 指标卡片网格 -->
      <div class="metrics-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <el-card
          v-for="metric in dashboardData?.metrics"
          :key="metric.metric_type"
          class="metric-card cursor-pointer hover:shadow-lg transition-shadow"
          :class="getMetricCardClass(metric.status)"
          @click="handleMetricClick(metric)"
        >
          <div class="metric-header flex justify-between items-start mb-2">
            <span class="metric-name font-semibold">{{ metric.metric_name }}</span>
            <el-tag :type="getTagType(metric.status)" size="small">
              {{ getStatusText(metric.status) }}
            </el-tag>
          </div>

          <div class="metric-value text-3xl font-bold mb-2">
            {{ formatMetricValue(metric.current_value, metric.metric_type) }}
          </div>

          <div class="metric-footer flex justify-between items-center text-sm">
            <span class="text-gray-500">
              目标: {{ metric.target_value !== null ? formatMetricValue(metric.target_value, metric.metric_type) : 'N/A' }}
            </span>
            <span :class="getTrendClass(metric.trend)">
              <el-icon v-if="metric.trend === 'up'"><Top /></el-icon>
              <el-icon v-else-if="metric.trend === 'down'"><Bottom /></el-icon>
              <el-icon v-else><Minus /></el-icon>
              {{ metric.change_percentage !== null ? Math.abs(metric.change_percentage).toFixed(1) + '%' : '' }}
            </span>
          </div>
        </el-card>
      </div>

      <!-- 汇总信息 -->
      <el-card class="summary-card mb-6" v-if="dashboardData">
        <div class="summary-content flex justify-around items-center">
          <div class="summary-item text-center">
            <div class="text-2xl font-bold">{{ dashboardData.summary.total_metrics }}</div>
            <div class="text-gray-500">总指标数</div>
          </div>
          <div class="summary-item text-center">
            <div class="text-2xl font-bold text-green-600">{{ dashboardData.summary.good_count }}</div>
            <div class="text-gray-500">达标指标</div>
          </div>
          <div class="summary-item text-center">
            <div class="text-2xl font-bold text-red-600">{{ dashboardData.summary.danger_count }}</div>
            <div class="text-gray-500">未达标指标</div>
          </div>
        </div>
      </el-card>

      <!-- 趋势图表 -->
      <el-card class="chart-card mb-6" v-if="selectedMetricType">
        <template #header>
          <div class="flex justify-between items-center">
            <span class="font-semibold">{{ getMetricLabel(selectedMetricType) }} - 趋势分析</span>
            <el-button-group>
              <el-button size="small" @click="setQuickDateRange('week')">近7天</el-button>
              <el-button size="small" @click="setQuickDateRange('month')">近30天</el-button>
              <el-button size="small" @click="setQuickDateRange('quarter')">近3个月</el-button>
            </el-button-group>
          </div>
        </template>
        <div ref="trendChartRef" class="chart-container" style="width: 100%; height: 400px;"></div>
      </el-card>

      <!-- 专项分析标签页 -->
      <el-card class="analysis-card">
        <el-tabs v-model="activeAnalysisTab" @tab-change="handleTabChange">
          <!-- 供应商分析 -->
          <el-tab-pane label="供应商质量分析" name="supplier">
            <div class="analysis-content">
              <div class="mb-4">
                <el-select v-model="supplierMetricType" @change="loadTopSuppliers" class="w-64">
                  <el-option label="来料批次合格率" value="incoming_batch_pass_rate" />
                  <el-option label="物料上线不良PPM" value="material_online_ppm" />
                </el-select>
              </div>
              <div ref="supplierChartRef" style="width: 100%; height: 400px;"></div>
            </div>
          </el-tab-pane>

          <!-- 制程分析 -->
          <el-tab-pane label="制程质量分析" name="process">
            <div class="analysis-content">
              <div ref="processChartRef" style="width: 100%; height: 400px;"></div>
            </div>
          </el-tab-pane>

          <!-- 客户分析 -->
          <el-tab-pane label="客户质量分析" name="customer">
            <div class="analysis-content">
              <div ref="customerChartRef" style="width: 100%; height: 400px;"></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- AI 助手组件 -->
    <AIAssistant />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Refresh, Top, Bottom, Minus } from '@element-plus/icons-vue';
import * as echarts from 'echarts';
import type { ECharts } from 'echarts';
import {
  getDashboard,
  getMetricTrend,
  getTopSuppliers,
  getProcessAnalysis,
  getCustomerAnalysis
} from '@/api/quality-metrics';
import type {
  DashboardResponse,
  DashboardMetricSummary,
  MetricTrendResponse,
  MetricStatus
} from '@/types/quality-metrics';
import AIAssistant from '@/components/AIAssistant.vue';

// 状态
const loading = ref(false);
const selectedDate = ref<string>(new Date().toISOString().split('T')[0]);
const selectedMetricType = ref<string>('');
const dateRange = ref<[string, string]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  new Date().toISOString().split('T')[0]
]);
const dashboardData = ref<DashboardResponse>();
const activeAnalysisTab = ref('supplier');
const supplierMetricType = ref('incoming_batch_pass_rate');

// 图表实例
const trendChartRef = ref<HTMLElement>();
const supplierChartRef = ref<HTMLElement>();
const processChartRef = ref<HTMLElement>();
const customerChartRef = ref<HTMLElement>();
let trendChart: ECharts | null = null;
let supplierChart: ECharts | null = null;
let processChart: ECharts | null = null;
let customerChart: ECharts | null = null;

// 可用指标列表
const availableMetrics = [
  { label: '来料批次合格率', value: 'incoming_batch_pass_rate' },
  { label: '物料上线不良PPM', value: 'material_online_ppm' },
  { label: '制程不合格率', value: 'process_defect_rate' },
  { label: '制程直通率', value: 'process_fpy' },
  { label: '0KM不良PPM', value: '0km_ppm' },
  { label: '3MIS售后不良PPM', value: '3mis_ppm' },
  { label: '12MIS售后不良PPM', value: '12mis_ppm' }
];

// 获取指标标签
const getMetricLabel = (metricType: string): string => {
  const metric = availableMetrics.find(m => m.value === metricType);
  return metric?.label || metricType;
};

// 加载仪表盘数据
const loadDashboard = async () => {
  loading.value = true;
  try {
    dashboardData.value = await getDashboard(selectedDate.value);
    
    // 默认选择第一个指标
    if (dashboardData.value.metrics.length > 0 && !selectedMetricType.value) {
      selectedMetricType.value = dashboardData.value.metrics[0].metric_type;
      await loadTrendData();
    }
  } catch (error) {
    console.error('Failed to load dashboard:', error);
    ElMessage.error('加载仪表盘数据失败');
  } finally {
    loading.value = false;
  }
};

// 加载趋势数据
const loadTrendData = async () => {
  if (!selectedMetricType.value || !dateRange.value) return;

  try {
    const response: MetricTrendResponse = await getMetricTrend({
      metric_type: selectedMetricType.value,
      start_date: dateRange.value[0],
      end_date: dateRange.value[1]
    });

    renderTrendChart(response);
  } catch (error) {
    console.error('Failed to load trend data:', error);
    ElMessage.error('加载趋势数据失败');
  }
};

// 渲染趋势图表
const renderTrendChart = (data: MetricTrendResponse) => {
  if (!trendChartRef.value) return;

  if (!trendChart) {
    trendChart = echarts.init(trendChartRef.value);
  }

  const dates = data.data_points.map(p => p.metric_date);
  const values = data.data_points.map(p => p.value);
  const targets = data.data_points.map(p => p.target_value);

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['实际值', '目标值']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: dates
    },
    yAxis: {
      type: 'value',
      name: getMetricLabel(selectedMetricType.value)
    },
    series: [
      {
        name: '实际值',
        type: 'line',
        data: values,
        smooth: true,
        itemStyle: {
          color: '#409eff'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '目标值',
        type: 'line',
        data: targets,
        lineStyle: {
          type: 'dashed',
          color: '#67c23a'
        },
        itemStyle: {
          color: '#67c23a'
        }
      }
    ]
  };

  trendChart.setOption(option);
};

// 加载Top供应商数据
const loadTopSuppliers = async () => {
  if (!supplierChartRef.value) return;

  try {
    const response = await getTopSuppliers({
      metric_type: supplierMetricType.value,
      period: 'monthly'
    });

    if (!supplierChart) {
      supplierChart = echarts.init(supplierChartRef.value);
    }

    const option: echarts.EChartsOption = {
      title: {
        text: 'Top 5 供应商'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'category',
        data: response.top_suppliers.map(s => s.supplier_name)
      },
      yAxis: {
        type: 'value',
        name: response.metric_name
      },
      series: [
        {
          type: 'bar',
          data: response.top_suppliers.map(s => ({
            value: s.metric_value,
            itemStyle: {
              color: s.status === 'good' ? '#67c23a' : s.status === 'warning' ? '#e6a23c' : '#f56c6c'
            }
          })),
          label: {
            show: true,
            position: 'top',
            formatter: '{c}'
          }
        }
      ]
    };

    supplierChart.setOption(option);
  } catch (error) {
    console.error('Failed to load top suppliers:', error);
    ElMessage.error('加载供应商数据失败');
  }
};

// 加载制程分析数据
const loadProcessAnalysis = async () => {
  if (!processChartRef.value || !dateRange.value) return;

  try {
    const response = await getProcessAnalysis({
      start_date: dateRange.value[0],
      end_date: dateRange.value[1]
    });

    if (!processChart) {
      processChart = echarts.init(processChartRef.value);
    }

    const option: echarts.EChartsOption = {
      title: {
        text: '制程质量月度趋势'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['不合格率', '直通率']
      },
      xAxis: {
        type: 'category',
        data: response.monthly_trend.map(t => t.month)
      },
      yAxis: [
        {
          type: 'value',
          name: '不合格率 (%)',
          position: 'left'
        },
        {
          type: 'value',
          name: '直通率 (%)',
          position: 'right'
        }
      ],
      series: [
        {
          name: '不合格率',
          type: 'line',
          data: response.monthly_trend.map(t => t.avg_defect_rate),
          itemStyle: { color: '#f56c6c' }
        },
        {
          name: '直通率',
          type: 'line',
          yAxisIndex: 1,
          data: response.monthly_trend.map(t => t.avg_fpy),
          itemStyle: { color: '#67c23a' }
        }
      ]
    };

    processChart.setOption(option);
  } catch (error) {
    console.error('Failed to load process analysis:', error);
    ElMessage.error('加载制程分析数据失败');
  }
};

// 加载客户分析数据
const loadCustomerAnalysis = async () => {
  if (!customerChartRef.value || !dateRange.value) return;

  try {
    const response = await getCustomerAnalysis({
      start_date: dateRange.value[0],
      end_date: dateRange.value[1]
    });

    if (!customerChart) {
      customerChart = echarts.init(customerChartRef.value);
    }

    const option: echarts.EChartsOption = {
      title: {
        text: '客户质量月度趋势'
      },
      tooltip: {
        trigger: 'axis'
      },
      legend: {
        data: ['0KM PPM', '3MIS PPM', '12MIS PPM']
      },
      xAxis: {
        type: 'category',
        data: response.monthly_trend.map(t => t.month)
      },
      yAxis: {
        type: 'value',
        name: 'PPM'
      },
      series: [
        {
          name: '0KM PPM',
          type: 'line',
          data: response.monthly_trend.map(t => t.avg_okm_ppm),
          itemStyle: { color: '#409eff' }
        },
        {
          name: '3MIS PPM',
          type: 'line',
          data: response.monthly_trend.map(t => t.avg_mis_3_ppm),
          itemStyle: { color: '#e6a23c' }
        },
        {
          name: '12MIS PPM',
          type: 'line',
          data: response.monthly_trend.map(t => t.avg_mis_12_ppm),
          itemStyle: { color: '#f56c6c' }
        }
      ]
    };

    customerChart.setOption(option);
  } catch (error) {
    console.error('Failed to load customer analysis:', error);
    ElMessage.error('加载客户分析数据失败');
  }
};

// 处理标签页切换
const handleTabChange = (tabName: string | number) => {
  if (tabName === 'supplier') {
    loadTopSuppliers();
  } else if (tabName === 'process') {
    loadProcessAnalysis();
  } else if (tabName === 'customer') {
    loadCustomerAnalysis();
  }
};

// 设置快捷日期范围
const setQuickDateRange = (range: 'week' | 'month' | 'quarter') => {
  const end = new Date();
  const start = new Date();
  
  if (range === 'week') {
    start.setDate(end.getDate() - 7);
  } else if (range === 'month') {
    start.setDate(end.getDate() - 30);
  } else if (range === 'quarter') {
    start.setMonth(end.getMonth() - 3);
  }

  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ];
  
  loadTrendData();
};

// 刷新所有数据
const refreshAll = () => {
  loadDashboard();
  loadTrendData();
  handleTabChange(activeAnalysisTab.value);
};

// 处理指标卡片点击（下钻功能）
const handleMetricClick = (metric: DashboardMetricSummary) => {
  selectedMetricType.value = metric.metric_type;
  loadTrendData();
  ElMessage.info(`查看 ${metric.metric_name} 详细趋势`);
};

// 格式化指标值
const formatMetricValue = (value: number, metricType: string): string => {
  if (metricType.includes('ppm')) {
    return value.toFixed(0) + ' PPM';
  } else if (metricType.includes('rate') || metricType.includes('fpy')) {
    return value.toFixed(2) + '%';
  }
  return value.toFixed(2);
};

// 获取指标卡片样式类
const getMetricCardClass = (status: MetricStatus): string => {
  if (status === 'good') return 'border-l-4 border-green-500';
  if (status === 'danger') return 'border-l-4 border-red-500';
  if (status === 'warning') return 'border-l-4 border-yellow-500';
  return 'border-l-4 border-gray-300';
};

// 获取标签类型
const getTagType = (status: MetricStatus): 'success' | 'danger' | 'warning' | 'info' => {
  if (status === 'good') return 'success';
  if (status === 'danger') return 'danger';
  if (status === 'warning') return 'warning';
  return 'info';
};

// 获取状态文本
const getStatusText = (status: MetricStatus): string => {
  if (status === 'good') return '达标';
  if (status === 'danger') return '未达标';
  if (status === 'warning') return '警告';
  return '未知';
};

// 获取趋势样式类
const getTrendClass = (trend: string): string => {
  if (trend === 'up') return 'text-red-500';
  if (trend === 'down') return 'text-green-500';
  return 'text-gray-500';
};

// 响应式调整
const handleResize = () => {
  trendChart?.resize();
  supplierChart?.resize();
  processChart?.resize();
  customerChart?.resize();
};

// 生命周期
onMounted(() => {
  loadDashboard();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  trendChart?.dispose();
  supplierChart?.dispose();
  processChart?.dispose();
  customerChart?.dispose();
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.quality-dashboard {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.dashboard-header {
  margin-bottom: 24px;
}

.controls {
  display: flex;
  align-items: center;
}

.loading-container {
  padding: 40px;
}

.dashboard-content {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.metric-card {
  transition: all 0.3s ease;
}

.metric-card:hover {
  transform: translateY(-4px);
}

.chart-container {
  min-height: 400px;
}

.analysis-content {
  padding: 20px 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .quality-dashboard {
    padding: 12px;
  }

  .controls {
    flex-direction: column;
    align-items: stretch;
  }

  .controls > * {
    width: 100%;
    margin-bottom: 8px;
  }

  .metrics-grid {
    grid-template-columns: 1fr !important;
  }

  .chart-container {
    height: 300px !important;
  }
}
</style>
