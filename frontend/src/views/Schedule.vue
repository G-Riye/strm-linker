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
      <el-form :model="taskForm" label-width="100px">
        <el-form-item label="任务名称" required>
          <el-input v-model="taskForm.task_id" />
        </el-form-item>
        <el-form-item label="扫描目录" required>
          <el-input v-model="taskForm.directory" />
        </el-form-item>
        <el-form-item label="执行时间" required>
          <el-input v-model="taskForm.cron" placeholder="如：0 3 * * * (每天3点)" />
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
  directory: '',
  cron: ''
})

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

const addTask = async () => {
  try {
    await configApi.addScheduledTask({
      ...taskForm,
      target_formats: ['mp4', 'mkv'],
      schedule_type: 'cron',
      schedule_params: { hour: 3, minute: 0 },
      recursive: true
    })
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

onMounted(loadTasks)
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
