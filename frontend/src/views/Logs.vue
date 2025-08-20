<template>
  <div class="logs-container">
    <div class="page-header mb-3">
      <h1>
        <el-icon><Document /></el-icon>
        日志查看
      </h1>
      <p>查看系统运行日志和操作记录</p>
    </div>

    <!-- 过滤工具栏 -->
    <el-card class="mb-3">
      <div class="filter-toolbar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索日志内容..."
          clearable
          style="width: 250px"
          @input="loadLogs"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select v-model="selectedLevel" placeholder="选择日志级别" clearable @change="loadLogs">
          <el-option label="所有级别" value="" />
          <el-option label="调试" value="DEBUG" />
          <el-option label="信息" value="INFO" />
          <el-option label="警告" value="WARNING" />
          <el-option label="错误" value="ERROR" />
          <el-option label="严重" value="CRITICAL" />
        </el-select>
        
        <el-button @click="loadLogs">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        
        <el-button @click="clearLogs">
          <el-icon><Delete /></el-icon>
          清理日志
        </el-button>
      </div>
    </el-card>

    <!-- 日志列表 -->
    <el-card>
      <div class="logs-list" v-loading="loading">
        <div
          v-for="(log, index) in logs"
          :key="index"
          :class="['log-entry', `log-${log.levelname.toLowerCase()}`]"
        >
          <div class="log-header">
            <el-tag :type="getLogLevelType(log.levelname)" size="small">
              {{ log.levelname }}
            </el-tag>
            <span class="log-time">{{ formatTime(log.asctime) }}</span>
            <span class="log-source">{{ log.name }}</span>
          </div>
          <div class="log-message">{{ log.message }}</div>
        </div>
        
        <div v-if="logs.length === 0" class="empty-logs">
          <el-empty description="暂无日志记录" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logsApi } from '@/api'
import dayjs from 'dayjs'

const loading = ref(false)
const logs = ref([])
const searchQuery = ref('')
const selectedLevel = ref('')

const loadLogs = async () => {
  try {
    loading.value = true
    logs.value = await logsApi.getLogs({
      limit: 200,
      level: selectedLevel.value || undefined,
      search: searchQuery.value || undefined
    })
  } catch (error) {
    ElMessage.error('加载日志失败')
  } finally {
    loading.value = false
  }
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm('确定要清理7天前的旧日志吗？', '确认清理', {
      type: 'warning'
    })
    
    await logsApi.clearOldLogs(7)
    ElMessage.success('日志清理完成')
    loadLogs()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理日志失败')
    }
  }
}

const getLogLevelType = (level) => {
  const types = {
    DEBUG: 'info',
    INFO: 'success',
    WARNING: 'warning',
    ERROR: 'danger',
    CRITICAL: 'danger'
  }
  return types[level] || 'info'
}

const formatTime = (timeStr) => {
  return dayjs(timeStr).format('MM-DD HH:mm:ss')
}

onMounted(loadLogs)
</script>

<style scoped>
.logs-container {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header h1 {
  margin: 0 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-toolbar {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.logs-list {
  max-height: 600px;
  overflow-y: auto;
}

.log-entry {
  border-left: 4px solid #ddd;
  padding: 12px;
  margin-bottom: 8px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.log-entry.log-error,
.log-entry.log-critical {
  border-left-color: var(--el-color-danger);
}

.log-entry.log-warning {
  border-left-color: var(--el-color-warning);
}

.log-entry.log-info {
  border-left-color: var(--el-color-success);
}

.log-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.log-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.log-source {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

.log-message {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  color: var(--el-text-color-primary);
}

.empty-logs {
  padding: 40px;
}
</style>
