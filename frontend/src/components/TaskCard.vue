<template>
  <div 
    class="task-card"
    :class="`task-card--${task.color}`"
    @click="handleClick"
  >
    <!-- 任务类型标签 -->
    <div class="task-card__header">
      <el-tag :type="tagType" size="small">
        {{ task.task_type }}
      </el-tag>
      <span class="task-card__id">{{ task.task_id }}</span>
    </div>

    <!-- 任务标题（如果有） -->
    <div v-if="task.title" class="task-card__title">
      {{ task.title }}
    </div>

    <!-- 任务描述（如果有） -->
    <div v-if="task.description" class="task-card__description">
      {{ task.description }}
    </div>

    <!-- 时间信息 -->
    <div class="task-card__footer">
      <div class="task-card__time">
        <el-icon><Clock /></el-icon>
        <span>{{ formattedRemainingTime }}</span>
      </div>
      <div class="task-card__deadline">
        截止: {{ formattedDeadline }}
      </div>
    </div>

    <!-- 紧急程度指示器 -->
    <div class="task-card__indicator" :class="`task-card__indicator--${task.color}`"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Clock } from '@element-plus/icons-vue'
import type { TodoTask } from '@/types/workbench'

interface Props {
  task: TodoTask
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [task: TodoTask]
}>()

/**
 * Element Plus Tag 类型映射
 */
const tagType = computed(() => {
  switch (props.task.color) {
    case 'red':
      return 'danger'
    case 'yellow':
      return 'warning'
    case 'green':
      return 'success'
    default:
      return 'info'
  }
})

/**
 * 格式化剩余时间
 */
const formattedRemainingTime = computed(() => {
  const hours = props.task.remaining_hours
  
  if (hours < 0) {
    const overdue = Math.abs(hours)
    if (overdue < 24) {
      return `已超期 ${Math.floor(overdue)} 小时`
    } else {
      return `已超期 ${Math.floor(overdue / 24)} 天`
    }
  } else if (hours < 24) {
    return `剩余 ${Math.floor(hours)} 小时`
  } else {
    return `剩余 ${Math.floor(hours / 24)} 天`
  }
})

/**
 * 格式化截止时间
 */
const formattedDeadline = computed(() => {
  const date = new Date(props.task.deadline)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

/**
 * 处理点击事件
 */
function handleClick() {
  emit('click', props.task)
}
</script>

<style scoped>
.task-card {
  position: relative;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.3s;
  overflow: hidden;
}

.task-card:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.task-card--red {
  border-left: 4px solid #f56c6c;
}

.task-card--yellow {
  border-left: 4px solid #e6a23c;
}

.task-card--green {
  border-left: 4px solid #67c23a;
}

.task-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-card__id {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.task-card__title {
  font-size: 15px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 8px;
  line-height: 1.5;
}

.task-card__description {
  font-size: 13px;
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.5;
}

.task-card__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.task-card__time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.task-card--red .task-card__time {
  color: #f56c6c;
}

.task-card--yellow .task-card__time {
  color: #e6a23c;
}

.task-card--green .task-card__time {
  color: #67c23a;
}

.task-card__deadline {
  color: #909399;
}

.task-card__indicator {
  position: absolute;
  top: 0;
  right: 0;
  width: 0;
  height: 0;
  border-style: solid;
  border-width: 0 40px 40px 0;
  opacity: 0.1;
}

.task-card__indicator--red {
  border-color: transparent #f56c6c transparent transparent;
}

.task-card__indicator--yellow {
  border-color: transparent #e6a23c transparent transparent;
}

.task-card__indicator--green {
  border-color: transparent #67c23a transparent transparent;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .task-card {
    padding: 12px;
  }

  .task-card__header {
    margin-bottom: 8px;
  }

  .task-card__title {
    font-size: 14px;
    margin-bottom: 6px;
  }

  .task-card__description {
    font-size: 12px;
    margin-bottom: 8px;
  }

  .task-card__footer {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}
</style>
