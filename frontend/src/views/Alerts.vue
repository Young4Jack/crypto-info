<template>
  <div class="alerts-container">
    <el-container>
      <el-header class="alerts-header">
        <div class="header-left">
          <h1>预警管理</h1>
        </div>
        <div class="header-right">
          <span>欢迎，{{ authStore.user?.username || '用户' }}</span>
          <el-button @click="goToDashboard">返回仪表盘</el-button>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      
      <el-main class="alerts-main">
        <el-card class="create-alert-card">
          <template #header>
            <div class="card-header">
              <span>创建新预警</span>
            </div>
          </template>
          
          <el-form
            ref="createFormRef"
            :model="createForm"
            :rules="createRules"
            label-width="120px"
            @submit.prevent="handleCreateAlert"
          >
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="交易对" prop="crypto_symbol">
                  <el-input
                    v-model="createForm.crypto_symbol"
                    placeholder="请输入交易对，如：BTCUSDT"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <el-form-item label="触发条件" prop="alert_type">
                  <el-select
                    v-model="createForm.alert_type"
                    placeholder="请选择条件"
                    style="width: 100%"
                  >
                    <el-option label="价格高于" value="above" />
                    <el-option label="价格低于" value="below" />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <el-form-item label="目标价格" prop="threshold_price">
                  <el-input-number
                    v-model="createForm.threshold_price"
                    :precision="2"
                    :min="0"
                    placeholder="请输入价格"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="4">
                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="createLoading"
                    @click="handleCreateAlert"
                  >
                    创建预警
                  </el-button>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>
        
        <el-card class="alerts-list-card">
          <template #header>
            <div class="card-header">
              <span>我的预警规则</span>
              <el-button @click="loadAlerts" :loading="loading">刷新</el-button>
            </div>
          </template>
          
          <el-table
            :data="alerts"
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="crypto_symbol" label="交易对" width="120">
              <template #default="{ row }">
                <el-tag>{{ row.crypto_symbol }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="crypto_name" label="币种名称" width="150" />
            
            <el-table-column prop="alert_type" label="触发条件" width="120">
              <template #default="{ row }">
                <el-tag :type="row.alert_type === 'above' ? 'danger' : 'success'">
                  {{ row.alert_type === 'above' ? '价格高于' : '价格低于' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="threshold_price" label="目标价格" width="150">
              <template #default="{ row }">
                <span class="price">{{ row.threshold_price }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'">
                  {{ row.is_active ? '激活' : '已禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="triggered_at" label="触发时间" width="180">
              <template #default="{ row }">
                {{ row.triggered_at ? formatTime(row.triggered_at) : '未触发' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="handleEditAlert(row)"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  :type="row.is_active ? 'warning' : 'success'"
                  @click="handleToggleActive(row)"
                >
                  {{ row.is_active ? '禁用' : '启用' }}
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDeleteAlert(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-if="!loading && alerts.length === 0" class="empty-state">
            <p>暂无预警规则</p>
            <p>请创建新的预警规则开始监控价格</p>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { cryptocurrenciesApi, alertsApi } from '../api'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const createLoading = ref(false)
const cryptocurrencies = ref<any[]>([])
const alerts = ref<any[]>([])

const createFormRef = ref<FormInstance>()

const createForm = reactive({
  crypto_symbol: '',
  alert_type: '' as 'above' | 'below' | '',
  threshold_price: null as number | null
})

const createRules: FormRules = {
  crypto_symbol: [
    { required: true, message: '请选择或输入币种', trigger: 'change' }
  ],
  alert_type: [
    { required: true, message: '请选择触发条件', trigger: 'change' }
  ],
  threshold_price: [
    { required: true, message: '请输入目标价格', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '价格必须大于0', trigger: 'blur' }
  ]
}

const loadCryptocurrencies = async () => {
  try {
    const response = await cryptocurrenciesApi.getAll()
    cryptocurrencies.value = response.data
  } catch (error) {
    console.error('加载币种失败:', error)
    ElMessage.error('加载币种失败')
  }
}

const loadAlerts = async () => {
  loading.value = true
  try {
    const response = await alertsApi.getAll()
    alerts.value = response.data
  } catch (error) {
    console.error('加载预警规则失败:', error)
    ElMessage.error('加载预警规则失败')
  } finally {
    loading.value = false
  }
}

const handleCreateAlert = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await alertsApi.create({
          crypto_symbol: createForm.crypto_symbol,
          alert_type: createForm.alert_type as 'above' | 'below',
          threshold_price: createForm.threshold_price!
        })
        
        ElMessage.success('预警规则创建成功')
        
        createForm.crypto_symbol = ''
        createForm.alert_type = ''
        createForm.threshold_price = null
        createFormRef.value?.resetFields()
        
        await loadAlerts()
      } catch (error) {
        console.error('创建预警规则失败:', error)
        ElMessage.error('创建预警规则失败')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleEditAlert = (_alert: any) => {
  // TODO: 实现编辑功能
  ElMessage.info('编辑功能开发中')
}

const handleToggleActive = async (alert: any) => {
  try {
    await alertsApi.update(alert.id, {
      is_active: !alert.is_active
    })
    
    ElMessage.success(`预警规则已${alert.is_active ? '禁用' : '启用'}`)
    
    await loadAlerts()
  } catch (error) {
    console.error('更新预警规则状态失败:', error)
    ElMessage.error('更新预警规则状态失败')
  }
}

const handleDeleteAlert = async (alert: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除预警规则吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await alertsApi.delete(alert.id)
    
    ElMessage.success('预警规则已删除')
    
    await loadAlerts()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除预警规则失败:', error)
      ElMessage.error('删除预警规则失败')
    }
  }
}

const formatTime = (timeStr: string) => {
  // 解析ISO格式时间字符串，确保正确处理时区
  const date = new Date(timeStr)
  // 使用toLocaleString并指定时区，确保显示正确的时间
  return date.toLocaleString('zh-CN', {
    timeZone: 'Asia/Shanghai'
  })
}

const goToDashboard = () => {
  router.push('/dashboard')
}

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  loadCryptocurrencies()
  loadAlerts()
})
</script>

<style scoped>
.alerts-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.alerts-header {
  background: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  margin: 0;
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.alerts-main {
  padding: 20px;
}

.create-alert-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.price {
  font-weight: bold;
  color: #e6a23c;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-state p {
  margin: 10px 0;
}
</style>