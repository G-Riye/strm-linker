<template>
  <div class="schedule-container">
    <div class="page-header mb-3">
      <h1>
        <el-icon><Timer /></el-icon>
        定时任务
      </h1>
      <p>管理自动扫描任务，设置定时执行规则</p>
    </div>

    <!-- 任务列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务列表</span>
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加任务
          </el-button>
        </div>
      </template>

      <el-table :data="tasks" v-loading="loading">
        <el-table-column label="任务名称" prop="task_id" />
        <el-table-column label="目录" prop="directory" />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.enabled ? 'success' : 'info'">
              {{ scope.row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="下次执行" prop="next_run" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="runTask(scope.row.task_id)">
              立即执行
            </el-button>
            <el-button size="small" type="danger" @click="removeTask(scope.row.task_id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加任务对话框 -->
    <el-dialog v-model="showAddDialog" title="添加定时任务" width="600px">
      <el-form :model="taskForm" label-width="120px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.task_id" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="使用扫描配置">
          <el-switch v-model="taskForm.useScanConfig" />
        </el-form-item>
        
        <el-form-item v-if="taskForm.useScanConfig" label="选择配置" required>
          <el-select v-model="taskForm.scan_config_id" placeholder="请选择扫描配置" style="width: 100%">
            <el-option
              v-for="config in scanConfigs"
              :key="config.config_id"
              :label="config.name"
              :value="config.config_id"
            >
              <span>{{ config.name }}</span>
              <small style="color: #999; margin-left: 10px;">{{ config.directory }}</small>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="!taskForm.useScanConfig" label="扫描目录" required>
          <el-input v-model="taskForm.directory" placeholder="请输入扫描目录路径" />
        </el-form-item>
        
        <el-form-item v-if="!taskForm.useScanConfig" label="递归扫描">
          <el-switch v-model="taskForm.recursive" />
        </el-form-item>
        
        <el-form-item v-if="!taskForm.useScanConfig" label="自定义视频扩展名">
          <el-select
            v-model="taskForm.custom_video_extensions"
            multiple
            filterable
            allow-create
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
        
        <el-form-item v-if="!taskForm.useScanConfig" label="自定义元数据扩展名">
          <el-select
            v-model="taskForm.custom_metadata_extensions"
            multiple
            filterable
            allow-create
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
        
        <el-form-item label="调度类型" required>
          <el-radio-group v-model="taskForm.schedule_type">
            <el-radio label="cron">Cron 表达式</el-radio>
            <el-radio label="interval">时间间隔</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item v-if="taskForm.schedule_type === 'cron'" label="Cron 表达式" required>
          <el-input v-model="taskForm.cron_expression" placeholder="如：0 3 * * * (每天3点)" />
        </el-form-item>
        
        <el-form-item v-if="taskForm.schedule_type === 'interval'" label="时间间隔" required>
          <el-row :gutter="10">
            <el-col :span="8">
              <el-input-number v-model="taskForm.interval_hours" :min="0" :max="24" placeholder="小时" />
            </el-col>
            <el-col :span="8">
              <el-input-number v-model="taskForm.interval_minutes" :min="0" :max="59" placeholder="分钟" />
            </el-col>
            <el-col :span="8">
              <el-input-number v-model="taskForm.interval_seconds" :min="0" :max="59" placeholder="秒" />
            </el-col>
          </el-row>
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="taskForm.enabled" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addTask">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { configApi } from '@/api'

const loading = ref(false)
const tasks = ref([])
const showAddDialog = ref(false)
const taskForm = reactive({
  task_id: '',
  useScanConfig: false,
  scan_config_id: '',
  directory: '',
  recursive: true,
  custom_video_extensions: [],
  custom_metadata_extensions: [],
  schedule_type: 'cron',
  cron_expression: '',
  interval_hours: 0,
  interval_minutes: 0,
  interval_seconds: 0,
  enabled: true
})

const scanConfigs = ref([])
const commonVideoExtensions = ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'ts']
const commonMetadataExtensions = ['nfo', 'srt', 'ass', 'jpg', 'png', 'json', 'xml', 'txt']

const loadTasks = async () => {
  try {
    loading.value = true
    tasks.value = await configApi.getScheduledTasks()
  } catch (error) {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

const loadScanConfigs = async () => {
  try {
    const response = await configApi.getScanConfigs()
    scanConfigs.value = response.configs || []
  } catch (error) {
    console.error('加载扫描配置失败:', error)
  }
}

const addTask = async () => {
  try {
    // 构建调度参数
    let scheduleParams = {}
    if (taskForm.schedule_type === 'cron') {
      // 解析 cron 表达式
      const cronParts = taskForm.cron_expression.split(' ')
      if (cronParts.length >= 5) {
        scheduleParams = {
          minute: cronParts[0],
          hour: cronParts[1],
          day: cronParts[2],
          month: cronParts[3],
          day_of_week: cronParts[4]
        }
      } else {
        ElMessage.error('Cron 表达式格式不正确')
        return
      }
    } else {
      scheduleParams = {
        hours: taskForm.interval_hours,
        minutes: taskForm.interval_minutes,
        seconds: taskForm.interval_seconds
      }
    }

    const taskData = {
      task_id: taskForm.task_id,
      target_formats: ['mp4', 'mkv'],
      schedule_type: taskForm.schedule_type,
      schedule_params: scheduleParams,
      enabled: taskForm.enabled
    }

    // 根据是否使用扫描配置来设置参数
    if (taskForm.useScanConfig) {
      taskData.scan_config_id = taskForm.scan_config_id
    } else {
      taskData.directory = taskForm.directory
      taskData.recursive = taskForm.recursive
      taskData.custom_video_extensions = taskForm.custom_video_extensions
      taskData.custom_metadata_extensions = taskForm.custom_metadata_extensions
    }

    await configApi.addScheduledTask(taskData)
    ElMessage.success('任务添加成功')
    showAddDialog.value = false
    loadTasks()
  } catch (error) {
    ElMessage.error('添加任务失败')
  }
}

const runTask = async (taskId) => {
  try {
    await configApi.runTaskNow(taskId)
    ElMessage.success('任务已启动')
  } catch (error) {
    ElMessage.error('启动任务失败')
  }
}

const removeTask = async (taskId) => {
  try {
    await configApi.removeScheduledTask(taskId)
    ElMessage.success('任务删除成功')
    loadTasks()
  } catch (error) {
    ElMessage.error('删除任务失败')
  }
}

onMounted(() => {
  loadTasks()
  loadScanConfigs()
})
</script>

<style scoped>
.schedule-container {
  max-width: 1000px;
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
</style>
