<template>
  <el-config-provider :locale="locale">
    <div id="app" class="app-container">
      <!-- 主要布局 -->
      <el-container class="layout-container">
        <!-- 顶部导航 -->
        <el-header class="app-header">
          <div class="header-content">
            <!-- Logo 和标题 -->
            <div class="logo-section">
              <el-icon class="logo-icon" :size="28" color="#409EFF">
                <Link />
              </el-icon>
              <h1 class="app-title">STRM Linker</h1>
              <el-tag size="small" type="info">v1.0.0</el-tag>
            </div>

            <!-- 导航菜单 -->
            <div class="nav-section">
              <el-menu
                :default-active="$route.path"
                mode="horizontal"
                background-color="transparent"
                text-color="#303133"
                active-text-color="#409EFF"
                :ellipsis="false"
                router
              >
                <el-menu-item index="/">
                  <el-icon><House /></el-icon>
                  <span>首页</span>
                </el-menu-item>
                <el-menu-item index="/scan">
                  <el-icon><Search /></el-icon>
                  <span>扫描管理</span>
                </el-menu-item>
                <el-menu-item index="/scan-configs">
                  <el-icon><Files /></el-icon>
                  <span>扫描配置</span>
                </el-menu-item>
                <el-menu-item index="/schedule">
                  <el-icon><Timer /></el-icon>
                  <span>定时任务</span>
                </el-menu-item>
                <el-menu-item index="/logs">
                  <el-icon><Document /></el-icon>
                  <span>日志查看</span>
                </el-menu-item>
                <el-menu-item index="/settings">
                  <el-icon><Setting /></el-icon>
                  <span>设置</span>
                </el-menu-item>
              </el-menu>
            </div>

            <!-- 右侧操作区 -->
            <div class="actions-section">
              <!-- 系统状态指示器 -->
              <el-tooltip content="系统状态" placement="bottom">
                <el-badge :value="errorCount" :hidden="errorCount === 0" type="danger">
                  <el-button
                    :type="systemStatus === 'healthy' ? 'success' : 'danger'"
                    :icon="systemStatus === 'healthy' ? 'CircleCheck' : 'CircleClose'"
                    circle
                    size="small"
                    @click="checkSystemStatus"
                  />
                </el-badge>
              </el-tooltip>
              
              <!-- 主题切换 -->
              <el-tooltip content="切换主题" placement="bottom">
                <el-button
                  :icon="isDark ? 'Sunny' : 'Moon'"
                  circle
                  size="small"
                  @click="toggleTheme"
                />
              </el-tooltip>
            </div>
          </div>
        </el-header>

        <!-- 主要内容区域 -->
        <el-main class="app-main">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>

        <!-- 底部信息 -->
        <el-footer class="app-footer">
          <div class="footer-content">
            <div class="footer-left">
              <span>© 2024 STRM Linker - Emby/Jellyfin 字幕软链管理工具</span>
            </div>
            <div class="footer-right">
              <el-link href="/api/docs" target="_blank" type="primary">
                API 文档
              </el-link>
              <el-divider direction="vertical" />
              <el-link @click="showAbout" type="primary">关于</el-link>
            </div>
          </div>
        </el-footer>
      </el-container>

      <!-- 关于对话框 -->
      <el-dialog v-model="aboutVisible" title="关于 STRM Linker" width="500px">
        <div class="about-content">
          <div class="about-logo">
            <el-icon :size="64" color="#409EFF">
              <Link />
            </el-icon>
          </div>
          <h2>STRM Linker</h2>
          <p>版本: 1.0.0</p>
          <p>一个专为 Emby/Jellyfin 设计的字幕软链管理工具</p>
          
          <h3>主要功能</h3>
          <ul>
            <li>自动扫描 .strm 文件并创建对应的视频格式软链接</li>
            <li>实时文件监听，新文件自动处理</li>
            <li>灵活的定时任务配置</li>
            <li>完整的日志管理和查看</li>
            <li>直观的 Web 界面，支持 PC 和移动端</li>
          </ul>
          
          <h3>技术栈</h3>
          <p>
            <el-tag size="small">Vue 3</el-tag>
            <el-tag size="small">Element Plus</el-tag>
            <el-tag size="small">FastAPI</el-tag>
            <el-tag size="small">Python</el-tag>
          </p>
        </div>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="aboutVisible = false">关闭</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import { ElMessage, ElNotification } from 'element-plus'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import { systemApi } from '@/api'

// 国际化
const locale = zhCn

// 主题
const isDark = useDark()
const toggleTheme = useToggle(isDark)

// 系统状态
const systemStatus = ref('unknown')
const errorCount = ref(0)

// 关于对话框
const aboutVisible = ref(false)

// 检查系统状态
const checkSystemStatus = async () => {
  try {
    const response = await systemApi.getHealth()
    systemStatus.value = response.status
    
    // 检查各个服务状态
    const services = response.services || {}
    const failedServices = Object.entries(services)
      .filter(([, status]) => !status)
      .map(([name]) => name)
    
    if (failedServices.length > 0) {
      ElNotification.warning({
        title: '服务状态警告',
        message: `以下服务未运行: ${failedServices.join(', ')}`,
        duration: 5000
      })
    } else {
      ElMessage.success('系统运行正常')
    }
  } catch (error) {
    systemStatus.value = 'error'
    ElMessage.error('无法获取系统状态')
    console.error('检查系统状态失败:', error)
  }
}

// 显示关于对话框
const showAbout = () => {
  aboutVisible.value = true
}

// 组件挂载时检查系统状态
onMounted(() => {
  checkSystemStatus()
  
  // 定期检查系统状态
  setInterval(checkSystemStatus, 30000) // 每30秒检查一次
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  background: var(--el-bg-color-page);
}

.layout-container {
  min-height: 100vh;
}

/* 头部样式 */
.app-header {
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  padding: 0 24px;
  height: 64px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1200px;
  margin: 0 auto;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  flex-shrink: 0;
}

.app-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.nav-section {
  flex: 1;
  margin: 0 40px;
}

.nav-section .el-menu {
  border-bottom: none;
}

.actions-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 主要内容区域 */
.app-main {
  padding: 24px;
  min-height: calc(100vh - 124px);
  max-width: 1200px;
  margin: 0 auto;
}

/* 底部样式 */
.app-footer {
  background: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-light);
  padding: 16px 24px;
  height: auto;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 页面切换动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.55, 0, 0.1, 1);
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translate3d(30px, 0, 0);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translate3d(-30px, 0, 0);
}

/* 关于对话框 */
.about-content {
  text-align: center;
}

.about-logo {
  margin-bottom: 16px;
}

.about-content h2 {
  margin: 16px 0 8px;
  color: var(--el-text-color-primary);
}

.about-content h3 {
  margin: 24px 0 12px;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.about-content p {
  margin: 8px 0;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

.about-content ul {
  text-align: left;
  margin: 12px 0;
  padding-left: 24px;
}

.about-content li {
  margin: 8px 0;
  color: var(--el-text-color-regular);
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }
  
  .logo-section .app-title {
    display: none;
  }
  
  .nav-section {
    margin: 0 16px;
  }
  
  .nav-section .el-menu-item span {
    display: none;
  }
  
  .app-main {
    padding: 16px;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>
