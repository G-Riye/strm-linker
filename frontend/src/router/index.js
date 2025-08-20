import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'

// 路由组件
import Home from '@/views/Home.vue'
import Scan from '@/views/Scan.vue'
import Schedule from '@/views/Schedule.vue'
import Logs from '@/views/Logs.vue'
import Settings from '@/views/Settings.vue'

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
    meta: {
      title: '首页',
      icon: 'House'
    }
  },
  {
    path: '/scan',
    name: 'Scan',
    component: Scan,
    meta: {
      title: '扫描管理',
      icon: 'Search'
    }
  },
  {
    path: '/schedule',
    name: 'Schedule',
    component: Schedule,
    meta: {
      title: '定时任务',
      icon: 'Timer'
    }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs,
    meta: {
      title: '日志查看',
      icon: 'Document'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '设置',
      icon: 'Setting'
    }
  },
  // 404 页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 路由切换时滚动到顶部
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  const title = to.meta?.title
  if (title) {
    document.title = `${title} - STRM Linker`
  } else {
    document.title = 'STRM Linker - 字幕软链管理工具'
  }
  
  // 这里可以添加权限验证等逻辑
  // 目前直接允许所有路由
  next()
})

// 全局后置守卫
router.afterEach((to, from) => {
  // 路由切换完成后的处理
  // 可以在这里添加统计代码等
})

// 路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
  ElMessage.error('页面加载失败')
})

export default router
