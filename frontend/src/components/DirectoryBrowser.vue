<template>
  <el-dialog
    v-model="visible"
    title="选择目录"
    width="70%"
    :close-on-click-modal="false"
    @open="handleDialogOpen"
  >
    <div class="directory-browser">
      <!-- 工具栏 -->
      <div class="toolbar mb-2">
        <div class="toolbar-left">
          <!-- 驱动器选择 (Windows) / 快速导航 (Linux) -->
          <el-select
            v-model="currentDrive"
            placeholder="选择驱动器"
            style="width: 200px"
            @change="handleDriveChange"
          >
            <el-option
              v-for="drive in systemDrives"
              :key="drive.path"
              :label="drive.name"
              :value="drive.path"
            />
          </el-select>
          
          <!-- 向上一级 -->
          <el-button
            :disabled="!canGoUp"
            @click="goUp"
          >
            <el-icon><ArrowUp /></el-icon>
            上一级
          </el-button>
          
          <!-- 刷新 -->
          <el-button @click="refresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        
        <div class="toolbar-right">
          <!-- 搜索 -->
          <el-input
            v-model="searchQuery"
            placeholder="搜索目录..."
            clearable
            style="width: 250px"
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <!-- 路径导航 -->
      <div class="path-navigation mb-2">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item
            v-for="(part, index) in pathParts"
            :key="index"
            class="path-part"
            @click="navigateToPath(index)"
          >
            {{ part.name }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <!-- 目录列表 -->
      <div class="directory-list">
        <el-table
          ref="directoryTable"
          :data="filteredDirectories"
          height="400px"
          highlight-current-row
          @current-change="handleCurrentChange"
          @row-dblclick="handleDoubleClick"
          v-loading="loading"
        >
          <el-table-column width="40" align="center">
            <template #default="scope">
              <el-icon v-if="scope.row.is_directory" color="#409EFF">
                <Folder />
              </el-icon>
              <el-icon v-else color="#909399">
                <Document />
              </el-icon>
            </template>
          </el-table-column>
          
          <el-table-column label="名称" prop="name" min-width="200">
            <template #default="scope">
              <div class="directory-name">
                <span>{{ scope.row.name }}</span>
                <el-tag
                  v-if="scope.row.has_strm_files === true"
                  size="small"
                  type="success"
                  class="ml-1"
                >
                  STRM
                </el-tag>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="修改时间" width="160" align="center">
            <template #default="scope">
              <span v-if="scope.row.modified_time" class="modified-time">
                {{ formatTime(scope.row.modified_time) }}
              </span>
            </template>
          </el-table-column>
          
          <el-table-column label="大小" width="100" align="right">
            <template #default="scope">
              <span v-if="!scope.row.is_directory && scope.row.size">
                {{ formatSize(scope.row.size) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 当前选择的路径 -->
      <div class="selected-path mt-2">
        <span>当前选择：</span>
        <el-input
          v-model="selectedPath"
          readonly
          style="width: 100%; max-width: 500px;"
        />
      </div>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :disabled="!selectedPath">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { browseApi } from '@/api'
import dayjs from 'dayjs'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  initialPath: {
    type: String,
    default: ''
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'select'])

// 响应式数据
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const loading = ref(false)
const currentPath = ref('')
const selectedPath = ref('')
const directories = ref([])
const systemDrives = ref([])
const currentDrive = ref('')
const searchQuery = ref('')

// 搜索防抖计时器
let searchTimer = null

// 计算属性
const canGoUp = computed(() => {
  return currentPath.value !== '' && currentPath.value !== '/' && !currentPath.value.match(/^[A-Z]:\\?$/i)
})

const pathParts = computed(() => {
  if (!currentPath.value) return []
  
  const parts = currentPath.value.split(/[/\\]/).filter(Boolean)
  const result = []
  
  if (currentPath.value.startsWith('/')) {
    result.push({ name: '/', path: '/' })
  }
  
  let fullPath = currentPath.value.startsWith('/') ? '' : ''
  
  parts.forEach((part, index) => {
    if (currentPath.value.includes('\\')) {
      // Windows 路径
      if (index === 0 && part.includes(':')) {
        fullPath = part + '\\'
        result.push({ name: part, path: fullPath })
      } else {
        fullPath += (fullPath.endsWith('\\') ? '' : '\\') + part
        result.push({ name: part, path: fullPath })
      }
    } else {
      // Unix 路径
      fullPath += '/' + part
      result.push({ name: part, path: fullPath })
    }
  })
  
  return result
})

const filteredDirectories = computed(() => {
  if (!searchQuery.value) {
    return directories.value.filter(item => item.is_directory)
  }
  
  const query = searchQuery.value.toLowerCase()
  return directories.value
    .filter(item => item.is_directory)
    .filter(item => item.name.toLowerCase().includes(query))
})

// 方法
const handleDialogOpen = async () => {
  await loadSystemDrives()
  
  if (props.initialPath) {
    await navigateToDirectory(props.initialPath)
  } else if (systemDrives.value.length > 0) {
    await navigateToDirectory(systemDrives.value[0].path)
  }
}

const loadSystemDrives = async () => {
  try {
    const response = await browseApi.getDrives()
    systemDrives.value = response.drives || []
    
    if (systemDrives.value.length > 0) {
      currentDrive.value = systemDrives.value[0].path
    }
  } catch (error) {
    console.error('获取系统驱动器失败:', error)
    ElMessage.error('获取系统驱动器失败')
  }
}

const navigateToDirectory = async (path) => {
  if (!path) return
  
  try {
    loading.value = true
    
    const response = await browseApi.browse({
      path: path,
      show_files: false,
      show_hidden: false,
      check_strm: true
    })
    
    currentPath.value = response.current_path
    directories.value = response.items || []
    selectedPath.value = currentPath.value
    
    // 更新当前驱动器选择
    if (systemDrives.value.length > 0) {
      const matchedDrive = systemDrives.value.find(drive => 
        currentPath.value.startsWith(drive.path)
      )
      if (matchedDrive) {
        currentDrive.value = matchedDrive.path
      }
    }
    
  } catch (error) {
    console.error('浏览目录失败:', error)
    ElMessage.error('浏览目录失败')
  } finally {
    loading.value = false
  }
}

const handleDriveChange = (drivePath) => {
  navigateToDirectory(drivePath)
}

const goUp = () => {
  if (!canGoUp.value) return
  
  const parentPath = currentPath.value.replace(/[/\\][^/\\]*$/, '') || '/'
  navigateToDirectory(parentPath)
}

const refresh = () => {
  navigateToDirectory(currentPath.value)
}

const navigateToPath = (index) => {
  if (index >= pathParts.value.length) return
  
  const targetPath = pathParts.value[index].path
  navigateToDirectory(targetPath)
}

const handleCurrentChange = (row) => {
  if (row && row.is_directory) {
    selectedPath.value = row.path
  }
}

const handleDoubleClick = (row) => {
  if (row.is_directory) {
    navigateToDirectory(row.path)
  }
}

const handleSearch = (query) => {
  // 防抖处理
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    // 搜索逻辑已在 computed 中处理
  }, 300)
}

const handleConfirm = () => {
  if (selectedPath.value) {
    emit('select', selectedPath.value)
    visible.value = false
  }
}

const handleCancel = () => {
  visible.value = false
}

// 工具函数
const formatTime = (timeStr) => {
  return dayjs(timeStr).format('YYYY-MM-DD HH:mm')
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}
</script>

<style scoped>
.directory-browser {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.path-navigation {
  padding: 8px 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.path-part {
  cursor: pointer;
  color: var(--el-color-primary);
}

.path-part:hover {
  text-decoration: underline;
}

.directory-list {
  flex: 1;
  overflow: hidden;
}

.directory-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.modified-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.selected-path {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selected-path span {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .toolbar-left {
    justify-content: center;
  }
  
  .toolbar-right {
    justify-content: center;
  }
  
  .selected-path {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}
</style>
