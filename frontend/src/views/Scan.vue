<template>
  <div class="scan-container">
    <!-- 页面标题 -->
    <div class="page-header mb-3">
      <h1>
        <el-icon><Search /></el-icon>
        扫描管理
      </h1>
      <p>选择目录并配置扫描参数，为 .strm 文件创建对应的视频格式软链接</p>
    </div>

    <!-- 扫描配置表单 -->
    <el-card class="mb-3">
      <template #header>
        <div class="card-header">
          <span>扫描配置</span>
        </div>
      </template>

      <el-form
        ref="scanForm"
        :model="scanConfig"
        :rules="scanRules"
        label-width="120px"
        @submit.prevent="handleScan"
      >
        <el-form-item label="扫描目录" prop="directory" required>
          <div class="directory-input">
            <el-input
              v-model="scanConfig.directory"
              placeholder="请输入或选择要扫描的目录路径"
              clearable
              @input="handleDirectoryInput"
            >
              <template #prepend>
                <el-button @click="showDirectoryBrowser = true">
                  <el-icon><Folder /></el-icon>
                  浏览
                </el-button>
              </template>
            </el-input>
            
            <!-- 路径建议下拉列表 -->
            <div v-if="pathSuggestions.length > 0" class="path-suggestions">
              <ul>
                <li
                  v-for="suggestion in pathSuggestions"
                  :key="suggestion.path"
                  @click="selectPathSuggestion(suggestion.path)"
                  class="suggestion-item"
                >
                  <el-icon><Folder /></el-icon>
                  <span>{{ suggestion.name }}</span>
                  <el-tag v-if="suggestion.has_strm_files" size="small" type="success">
                    含 STRM
                  </el-tag>
                </li>
              </ul>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="目标格式" prop="target_formats">
          <el-checkbox-group v-model="scanConfig.target_formats">
            <el-checkbox label="mp4">MP4</el-checkbox>
            <el-checkbox label="mkv">MKV</el-checkbox>
            <el-checkbox label="avi">AVI</el-checkbox>
            <el-checkbox label="mov">MOV</el-checkbox>
            <el-checkbox label="wmv">WMV</el-checkbox>
            <el-checkbox label="flv">FLV</el-checkbox>
            <el-checkbox label="webm">WebM</el-checkbox>
          </el-checkbox-group>
          <div class="form-tip">
            选择要创建软链接的视频格式，建议至少选择 MP4 和 MKV
          </div>
        </el-form-item>

        <el-form-item label="扫描选项">
          <el-checkbox v-model="scanConfig.recursive">
            递归扫描子目录
          </el-checkbox>
          <el-checkbox v-model="scanConfig.dry_run">
            预览模式（只显示结果，不实际创建文件）
          </el-checkbox>
        </el-form-item>

        <el-form-item label="自定义视频扩展名">
          <el-select
            v-model="scanConfig.custom_video_extensions"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入或选择自定义视频扩展名"
            style="width: 100%"
          >
            <el-option
              v-for="ext in commonVideoExtensions"
              :key="ext"
              :label="ext"
              :value="ext"
            />
          </el-select>
          <div class="form-tip">
            添加自定义视频扩展名，支持更多格式的 STRM 文件
          </div>
        </el-form-item>

        <el-form-item label="自定义元数据扩展名">
          <el-select
            v-model="scanConfig.custom_metadata_extensions"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入或选择自定义元数据扩展名"
            style="width: 100%"
          >
            <el-option
              v-for="ext in commonMetadataExtensions"
              :key="ext"
              :label="ext"
              :value="ext"
            />
          </el-select>
          <div class="form-tip">
            添加自定义元数据扩展名，支持更多格式的元数据文件
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleScan" :loading="scanning">
            <el-icon><Search /></el-icon>
            {{ scanning ? '扫描中...' : '开始扫描' }}
          </el-button>
          <el-button @click="resetForm">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
          <el-button type="danger" @click="handleCleanup" :loading="cleaning">
            <el-icon><Delete /></el-icon>
            清理损坏软链接
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 扫描结果 -->
    <el-card v-if="scanResult" class="mb-3">
      <template #header>
        <div class="card-header">
          <span>扫描结果</span>
          <el-tag :type="scanResult.success ? 'success' : 'danger'">
            {{ scanResult.success ? '成功' : '失败' }}
          </el-tag>
        </div>
      </template>

      <div class="scan-result">
        <el-row :gutter="16" class="mb-2">
          <el-col :xs="12" :sm="6">
            <el-statistic title="扫描目录" :value="scanResult.directory" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-statistic title="发现文件" :value="scanResult.total_files" suffix="个" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-statistic title="处理文件" :value="scanResult.processed" suffix="个" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-statistic title="创建软链" :value="scanResult.created_links" suffix="个" />
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :xs="12" :sm="6">
            <el-statistic title="跳过文件" :value="scanResult.skipped" suffix="个" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-statistic title="错误数量" :value="scanResult.errors?.length || 0" suffix="个" />
          </el-col>
          <el-col :xs="12" :sm="6">
            <el-statistic title="耗时" :value="scanResult.duration?.toFixed(2)" suffix="秒" />
          </el-col>
        </el-row>

        <!-- 错误详情 -->
        <div v-if="scanResult.errors && scanResult.errors.length > 0" class="mt-3">
          <h4>错误详情：</h4>
          <el-alert
            v-for="(error, index) in scanResult.errors"
            :key="index"
            :title="error.file"
            :description="error.error"
            type="error"
            show-icon
            class="mb-1"
          />
        </div>
      </div>
    </el-card>

    <!-- 目录浏览器对话框 -->
    <DirectoryBrowser
      v-model="showDirectoryBrowser"
      @select="handleDirectorySelect"
      :initial-path="scanConfig.directory"
    />
  </div>
</template>

<script setup>
import { ref, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi, browseApi } from '@/api'
import DirectoryBrowser from '@/components/DirectoryBrowser.vue'

// 表单引用
const scanForm = ref()

// 扫描配置
const scanConfig = reactive({
  directory: '',
  target_formats: ['mp4', 'mkv'],
  recursive: true,
  dry_run: false,
  custom_video_extensions: [],
  custom_metadata_extensions: []
})

// 常用扩展名
const commonVideoExtensions = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'ts']
const commonMetadataExtensions = ['nfo', 'srt', 'ass', 'jpg', 'png', 'json', 'xml', 'txt']

// 表单验证规则
const scanRules = {
  directory: [
    { required: true, message: '请选择扫描目录', trigger: 'blur' }
  ],
  target_formats: [
    { type: 'array', min: 1, message: '请至少选择一种目标格式', trigger: 'change' }
  ]
}

// 状态
const scanning = ref(false)
const cleaning = ref(false)
const scanResult = ref(null)
const showDirectoryBrowser = ref(false)

// 路径自动补全
const pathSuggestions = ref([])
let suggestionTimer = null

// 处理目录输入
const handleDirectoryInput = async (value) => {
  if (!value || value.length < 2) {
    pathSuggestions.value = []
    return
  }

  // 防抖处理
  clearTimeout(suggestionTimer)
  suggestionTimer = setTimeout(async () => {
    try {
      const response = await browseApi.autocomplete({ partial_path: value, limit: 8 })
      pathSuggestions.value = response.suggestions || []
    } catch (error) {
      pathSuggestions.value = []
    }
  }, 300)
}

// 选择路径建议
const selectPathSuggestion = (path) => {
  scanConfig.directory = path
  pathSuggestions.value = []
}

// 处理目录选择
const handleDirectorySelect = (path) => {
  scanConfig.directory = path
  pathSuggestions.value = []
}

// 执行扫描
const handleScan = async () => {
  try {
    const valid = await scanForm.value.validate()
    if (!valid) return

    scanning.value = true
    scanResult.value = null

    const result = await configApi.scan(scanConfig)
    scanResult.value = result

    if (result.success) {
      ElMessage.success(`扫描完成！处理了 ${result.processed} 个文件，创建了 ${result.created_links} 个软链接`)
    } else {
      ElMessage.error('扫描过程中发生错误，请查看详细信息')
    }

  } catch (error) {
    ElMessage.error(`扫描失败: ${error.message}`)
  } finally {
    scanning.value = false
  }
}

// 清理损坏的软链接
const handleCleanup = async () => {
  if (!scanConfig.directory) {
    ElMessage.warning('请先选择目录')
    return
  }

  try {
    cleaning.value = true
    
    const result = await configApi.cleanup(scanConfig.directory, scanConfig.recursive)
    
    if (result.success) {
      ElMessage.success(`清理完成！删除了 ${result.removed_count} 个损坏的软链接`)
    }

  } catch (error) {
    ElMessage.error(`清理失败: ${error.message}`)
  } finally {
    cleaning.value = false
  }
}

// 重置表单
const resetForm = () => {
  scanForm.value.resetFields()
  scanResult.value = null
  pathSuggestions.value = []
  // 重置自定义扩展名
  scanConfig.custom_video_extensions = []
  scanConfig.custom_metadata_extensions = []
}
</script>

<style scoped>
.scan-container {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header h1 {
  margin: 0 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--el-text-color-primary);
}

.page-header p {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.directory-input {
  position: relative;
  width: 100%;
}

.path-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  box-shadow: var(--el-box-shadow-light);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.path-suggestions ul {
  list-style: none;
  margin: 0;
  padding: 4px 0;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.suggestion-item:hover {
  background: var(--el-fill-color-light);
}

.suggestion-item span {
  flex: 1;
  color: var(--el-text-color-primary);
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
}

.scan-result {
  margin-top: 16px;
}

.scan-result h4 {
  margin: 0 0 12px;
  color: var(--el-text-color-primary);
}

/* 响应式布局 */
@media (max-width: 768px) {
  .directory-input .el-input-group__prepend {
    padding: 0 8px;
  }
  
  .directory-input .el-input-group__prepend .el-button {
    font-size: 12px;
    padding: 0 8px;
  }
}
</style>
