<template>
  <div class="scan-configs">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span>扫描配置管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建配置
          </el-button>
        </div>
      </template>

      <!-- 配置列表 -->
      <el-table :data="configs" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="配置名称" min-width="150">
          <template #default="{ row }">
            <el-tag type="primary">{{ row.name }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        
        <el-table-column prop="directory" label="扫描目录" min-width="250" show-overflow-tooltip />
        
        <el-table-column prop="recursive" label="递归扫描" width="100">
          <template #default="{ row }">
            <el-tag :type="row.recursive ? 'success' : 'info'">
              {{ row.recursive ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="自定义扩展名" min-width="200">
          <template #default="{ row }">
            <div class="extensions-info">
              <div v-if="row.custom_video_extensions?.length">
                <small>视频: {{ row.custom_video_extensions.join(', ') }}</small>
              </div>
              <div v-if="row.custom_metadata_extensions?.length">
                <small>元数据: {{ row.custom_metadata_extensions.join(', ') }}</small>
              </div>
              <div v-if="!row.custom_video_extensions?.length && !row.custom_metadata_extensions?.length">
                <small class="text-muted">无自定义扩展名</small>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" type="primary" @click="executeConfig(row.config_id)">
                <el-icon><VideoPlay /></el-icon>
                执行
              </el-button>
              <el-button size="small" type="success" @click="executeConfig(row.config_id, true)">
                <el-icon><View /></el-icon>
                预览
              </el-button>
              <el-button size="small" @click="editConfig(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteConfig(row.config_id)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑配置对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingConfig ? '编辑配置' : '新建配置'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="configFormRef"
        :model="configForm"
        :rules="configRules"
        label-width="120px"
      >
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="configForm.name" placeholder="请输入配置名称" />
        </el-form-item>
        
        <el-form-item label="配置描述" prop="description">
          <el-input
            v-model="configForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入配置描述"
          />
        </el-form-item>
        
        <el-form-item label="扫描目录" prop="directory">
          <el-input v-model="configForm.directory" placeholder="请输入扫描目录路径">
            <template #append>
              <el-button @click="browseDirectory">浏览</el-button>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item label="递归扫描" prop="recursive">
          <el-switch v-model="configForm.recursive" />
        </el-form-item>
        
        <el-form-item label="自定义视频扩展名">
          <el-select
            v-model="configForm.custom_video_extensions"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入或选择视频扩展名"
            style="width: 100%"
          >
            <el-option
              v-for="ext in commonVideoExtensions"
              :key="ext"
              :label="ext"
              :value="ext"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="自定义元数据扩展名">
          <el-select
            v-model="configForm.custom_metadata_extensions"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="请输入或选择元数据扩展名"
            style="width: 100%"
          >
            <el-option
              v-for="ext in commonMetadataExtensions"
              :key="ext"
              :label="ext"
              :value="ext"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveConfig" :loading="saving">
            {{ editingConfig ? '更新' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 执行结果对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="执行结果"
      width="800px"
      :close-on-click-modal="false"
    >
      <div v-if="executionResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="扫描目录">
            {{ executionResult.directory }}
          </el-descriptions-item>
          <el-descriptions-item label="处理文件数">
            {{ executionResult.processed }}
          </el-descriptions-item>
          <el-descriptions-item label="创建软链接数">
            {{ executionResult.created_links }}
          </el-descriptions-item>
          <el-descriptions-item label="跳过文件数">
            {{ executionResult.skipped }}
          </el-descriptions-item>
          <el-descriptions-item label="错误数量">
            {{ executionResult.errors?.length || 0 }}
          </el-descriptions-item>
          <el-descriptions-item label="执行时间">
            {{ executionResult.duration?.toFixed(2) }}秒
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="executionResult.errors?.length" class="mt-3">
          <h4>错误详情：</h4>
          <el-alert
            v-for="(error, index) in executionResult.errors"
            :key="index"
            :title="error.file"
            :description="error.error"
            type="error"
            show-icon
            class="mb-2"
          />
        </div>

        <div v-if="executionResult.details?.length" class="mt-3">
          <h4>处理详情：</h4>
          <el-collapse>
            <el-collapse-item
              v-for="(detail, index) in executionResult.details"
              :key="index"
              :title="detail.file"
            >
              <div v-if="detail.result">
                <p><strong>基础名称：</strong>{{ detail.result.base_name }}</p>
                <p><strong>视频格式：</strong>{{ detail.result.video_extension }}</p>
                <p><strong>创建链接数：</strong>{{ detail.result.links_created }}</p>
                <div v-if="detail.result.created_links?.length">
                  <p><strong>创建的链接：</strong></p>
                  <ul>
                    <li v-for="link in detail.result.created_links" :key="link">
                      {{ link }}
                    </li>
                  </ul>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, VideoPlay, View } from '@element-plus/icons-vue'
import { configApi } from '@/api'

// 响应式数据
const loading = ref(false)
const saving = ref(false)
const configs = ref([])
const showCreateDialog = ref(false)
const showResultDialog = ref(false)
const editingConfig = ref(null)
const executionResult = ref(null)

// 表单数据
const configFormRef = ref()
const configForm = reactive({
  name: '',
  description: '',
  directory: '',
  recursive: true,
  custom_video_extensions: [],
  custom_metadata_extensions: []
})

// 表单验证规则
const configRules = {
  name: [
    { required: true, message: '请输入配置名称', trigger: 'blur' }
  ],
  directory: [
    { required: true, message: '请输入扫描目录', trigger: 'blur' }
  ]
}

// 常用扩展名
const commonVideoExtensions = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'ts']
const commonMetadataExtensions = ['nfo', 'srt', 'ass', 'jpg', 'png', 'json', 'xml', 'txt']

// 加载配置列表
const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await configApi.getScanConfigs()
    configs.value = response.configs || []
  } catch (error) {
    console.error('加载配置列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 浏览目录
const browseDirectory = async () => {
  // 这里可以集成目录浏览功能
  ElMessage.info('目录浏览功能待实现')
}

// 保存配置
const saveConfig = async () => {
  if (!configFormRef.value) return
  
  try {
    await configFormRef.value.validate()
    saving.value = true
    
    if (editingConfig.value) {
      await configApi.updateScanConfig(editingConfig.value.config_id, configForm)
      ElMessage.success('配置更新成功')
    } else {
      await configApi.createScanConfig(configForm)
      ElMessage.success('配置创建成功')
    }
    
    showCreateDialog.value = false
    resetForm()
    loadConfigs()
  } catch (error) {
    console.error('保存配置失败:', error)
  } finally {
    saving.value = false
  }
}

// 编辑配置
const editConfig = (config) => {
  editingConfig.value = config
  Object.assign(configForm, {
    name: config.name,
    description: config.description,
    directory: config.directory,
    recursive: config.recursive,
    custom_video_extensions: config.custom_video_extensions || [],
    custom_metadata_extensions: config.custom_metadata_extensions || []
  })
  showCreateDialog.value = true
}

// 删除配置
const deleteConfig = async (configId) => {
  try {
    await ElMessageBox.confirm('确定要删除这个配置吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await configApi.deleteScanConfig(configId)
    ElMessage.success('配置删除成功')
    loadConfigs()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
    }
  }
}

// 执行配置
const executeConfig = async (configId, dryRun = false) => {
  try {
    const result = await configApi.executeScanConfig(configId, dryRun)
    executionResult.value = result
    showResultDialog.value = true
    ElMessage.success(dryRun ? '预览完成' : '执行完成')
  } catch (error) {
    console.error('执行配置失败:', error)
  }
}

// 重置表单
const resetForm = () => {
  editingConfig.value = null
  Object.assign(configForm, {
    name: '',
    description: '',
    directory: '',
    recursive: true,
    custom_video_extensions: [],
    custom_metadata_extensions: []
  })
  if (configFormRef.value) {
    configFormRef.value.resetFields()
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 监听对话框关闭
const handleDialogClose = () => {
  resetForm()
}

// 组件挂载时加载数据
onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.scan-configs {
  padding: 20px;
}

.config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.extensions-info {
  font-size: 12px;
}

.extensions-info small {
  display: block;
  margin-bottom: 2px;
}

.text-muted {
  color: #999;
}

.mt-3 {
  margin-top: 15px;
}

.mb-2 {
  margin-bottom: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
