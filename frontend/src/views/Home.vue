<template>
  <div class="home-container">
    <!-- 欢迎横幅 -->
    <el-card class="welcome-card mb-3">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1>
            <el-icon class="welcome-icon"><Link /></el-icon>
            欢迎使用 STRM Linker
          </h1>
          <p class="welcome-description">
            专为 Emby/Jellyfin 设计的字幕软链管理工具，让您的媒体库字幕管理更加轻松高效
          </p>
          
          <!-- 快速操作按钮 -->
          <div class="quick-actions">
            <el-button type="primary" size="large" @click="$router.push('/scan')">
              <el-icon><Search /></el-icon>
              开始扫描
            </el-button>
            <el-button size="large" @click="$router.push('/schedule')">
              <el-icon><Timer /></el-icon>
              定时任务
            </el-button>
            <el-button size="large" @click="$router.push('/logs')">
              <el-icon><Document /></el-icon>
              查看日志
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 系统状态概览 -->
    <el-row :gutter="24" class="mb-3">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">系统状态</div>
              <div class="status-value">
                {{ systemStatus === 'healthy' ? '正常' : '异常' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon info">
              <el-icon><View /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">文件监听</div>
              <div class="status-value">
                {{ watchStatus.is_running ? '运行中' : '已停止' }}
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon warning">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">定时任务</div>
              <div class="status-value">{{ scheduledTasks.length }} 个</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="status-card">
          <div class="status-item">
            <div class="status-icon danger">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="status-content">
              <div class="status-label">错误日志</div>
              <div class="status-value">{{ errorLogCount }} 条</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 功能特性介绍 -->
    <el-row :gutter="24" class="mb-3">
      <el-col :xs="24" :md="12">
        <el-card class="feature-card">
          <template #header>
            <div class="feature-header">
              <el-icon class="feature-icon"><Search /></el-icon>
              <span>智能扫描</span>
            </div>
          </template>
          
          <div class="feature-content">
            <ul>
              <li>自动识别 .strm 文件并解析视频格式</li>
              <li>批量创建多种格式的软链接</li>
              <li>支持递归扫描子目录</li>
              <li>预览模式，安全可靠</li>
            </ul>
            
            <el-button type="text" @click="$router.push('/scan')">
              立即体验 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :md="12">
        <el-card class="feature-card">
          <template #header>
            <div class="feature-header">
              <el-icon class="feature-icon"><View /></el-icon>
              <span>实时监听</span>
            </div>
          </template>
          
          <div class="feature-content">
            <ul>
              <li>监控目录文件变化</li>
              <li>新增 .strm 文件自动处理</li>
              <li>支持多目录同时监听</li>
              <li>可自定义目标格式</li>
            </ul>
            
            <el-button type="text" @click="toggleWatcher">
              {{ watchStatus.is_running ? '停止监听' : '开始监听' }}
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="24">
      <el-col :xs="24" :md="12">
        <el-card class="feature-card">
          <template #header>
            <div class="feature-header">
              <el-icon class="feature-icon"><Timer /></el-icon>
              <span>定时任务</span>
            </div>
          </template>
          
          <div class="feature-content">
            <ul>
              <li>灵活的定时执行配置</li>
              <li>支持 Cron 表达式</li>
              <li>任务执行状态监控</li>
              <li>失败重试机制</li>
            </ul>
            
            <el-button type="text" @click="$router.push('/schedule')">
              管理任务 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :md="12">
        <el-card class="feature-card">
          <template #header>
            <div class="feature-header">
              <el-icon class="feature-icon"><Document /></el-icon>
              <span>日志管理</span>
            </div>
          </template>
          
          <div class="feature-content">
            <ul>
              <li>详细的操作日志记录</li>
              <li>多级别日志过滤</li>
              <li>日志搜索和导出</li>
              <li>自动清理旧日志</li>
            </ul>
            
            <el-button type="text" @click="$router.push('/logs')">
              查看日志 <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi, logsApi, systemApi } from '@/api'

// 系统状态
const systemStatus = ref('unknown')
const watchStatus = ref({ is_running: false, watch_directories: [] })
const scheduledTasks = ref([])
const errorLogCount = ref(0)

// 加载系统状态
const loadSystemStatus = async () => {
  try {
    // 获取系统健康状态
    const health = await systemApi.getHealth()
    systemStatus.value = health.status
    
    // 获取监听状态
    const watchInfo = await configApi.getWatchStatus()
    watchStatus.value = watchInfo
    
    // 获取定时任务
    const tasks = await configApi.getScheduledTasks()
    scheduledTasks.value = tasks
    
    // 获取错误日志统计
    const logStats = await logsApi.getLogStats()
    errorLogCount.value = logStats.recent_errors || 0
    
  } catch (error) {
    console.error('加载系统状态失败:', error)
  }
}

// 切换文件监听状态
const toggleWatcher = async () => {
  try {
    if (watchStatus.value.is_running) {
      await configApi.stopWatcher()
      ElMessage.success('已停止文件监听')
    } else {
      await configApi.startWatcher()
      ElMessage.success('已启动文件监听')
    }
    
    // 重新加载状态
    await loadSystemStatus()
  } catch (error) {
    ElMessage.error(`操作失败: ${error.message}`)
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSystemStatus()
  
  // 定期刷新状态
  setInterval(loadSystemStatus, 10000) // 每10秒刷新一次
})
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* 欢迎卡片 */
.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.welcome-card :deep(.el-card__body) {
  padding: 40px;
}

.welcome-content {
  text-align: center;
}

.welcome-text h1 {
  margin: 0 0 16px;
  font-size: 32px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.welcome-icon {
  font-size: 36px;
}

.welcome-description {
  font-size: 16px;
  margin: 0 0 32px;
  opacity: 0.9;
  line-height: 1.6;
}

.quick-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

/* 状态卡片 */
.status-card {
  height: 100%;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.status-icon.success {
  background: var(--el-color-success);
}

.status-icon.info {
  background: var(--el-color-info);
}

.status-icon.warning {
  background: var(--el-color-warning);
}

.status-icon.danger {
  background: var(--el-color-danger);
}

.status-content {
  flex: 1;
}

.status-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

/* 功能特性卡片 */
.feature-card {
  height: 100%;
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.feature-icon {
  color: var(--el-color-primary);
}

.feature-content ul {
  margin: 0 0 20px;
  padding-left: 20px;
}

.feature-content li {
  margin: 8px 0;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .welcome-text h1 {
    font-size: 24px;
    flex-direction: column;
    gap: 8px;
  }
  
  .welcome-icon {
    font-size: 28px;
  }
  
  .quick-actions {
    gap: 12px;
  }
  
  .quick-actions .el-button {
    flex: 1;
    min-width: 120px;
  }
  
  .status-item {
    gap: 12px;
  }
  
  .status-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
}
</style>
