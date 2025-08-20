<template>
  <div class="settings-container">
    <div class="page-header mb-3">
      <h1>
        <el-icon><Setting /></el-icon>
        设置
      </h1>
      <p>配置系统参数和监听服务</p>
    </div>

    <!-- 监听服务配置 -->
    <el-card class="mb-3">
      <template #header>
        <div class="card-header">
          <span>文件监听服务</span>
          <el-switch
            v-model="watcherEnabled"
            @change="toggleWatcher"
            :loading="watcherLoading"
          />
        </div>
      </template>

      <div class="watcher-config">
        <p>状态：{{ watchStatus.is_running ? '运行中' : '已停止' }}</p>
        <p>监听目录数量：{{ watchStatus.watch_directories?.length || 0 }} 个</p>
        
        <div v-if="watchStatus.watch_directories?.length > 0">
          <h4>监听目录列表：</h4>
          <el-tag
            v-for="dir in watchStatus.watch_directories"
            :key="dir.path"
            class="mb-1 mr-1"
          >
            {{ dir.path }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 系统信息 -->
    <el-card>
      <template #header>
        <span>系统信息</span>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="版本">v1.0.0</el-descriptions-item>
        <el-descriptions-item label="系统状态">
          <el-tag :type="systemHealth === 'healthy' ? 'success' : 'danger'">
            {{ systemHealth === 'healthy' ? '正常' : '异常' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="定时任务调度器">
          <el-tag :type="schedulerRunning ? 'success' : 'info'">
            {{ schedulerRunning ? '运行中' : '已停止' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="文件监听服务">
          <el-tag :type="watchStatus.is_running ? 'success' : 'info'">
            {{ watchStatus.is_running ? '运行中' : '已停止' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi, systemApi } from '@/api'

const watcherEnabled = ref(false)
const watcherLoading = ref(false)
const watchStatus = ref({ is_running: false, watch_directories: [] })
const systemHealth = ref('unknown')
const schedulerRunning = ref(false)

const loadStatus = async () => {
  try {
    // 加载监听服务状态
    const watchInfo = await configApi.getWatchStatus()
    watchStatus.value = watchInfo
    watcherEnabled.value = watchInfo.is_running

    // 加载系统健康状态
    const health = await systemApi.getHealth()
    systemHealth.value = health.status

    // 加载调度器状态
    const scheduler = await configApi.getSchedulerStatus()
    schedulerRunning.value = scheduler.is_running

  } catch (error) {
    ElMessage.error('加载状态失败')
  }
}

const toggleWatcher = async (enabled) => {
  try {
    watcherLoading.value = true
    
    if (enabled) {
      await configApi.startWatcher()
      ElMessage.success('已启动文件监听')
    } else {
      await configApi.stopWatcher()
      ElMessage.success('已停止文件监听')
    }
    
    // 重新加载状态
    await loadStatus()
  } catch (error) {
    ElMessage.error('操作失败')
    watcherEnabled.value = !enabled // 回滚状态
  } finally {
    watcherLoading.value = false
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.settings-container {
  max-width: 800px;
  margin: 0 auto;
}

.page-header h1 {
  margin: 0 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watcher-config p {
  margin: 8px 0;
  color: var(--el-text-color-regular);
}

.watcher-config h4 {
  margin: 16px 0 8px;
  color: var(--el-text-color-primary);
}
</style>
