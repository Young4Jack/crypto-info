<template>
  <div class="watchlist-container">
    <el-container>
      <el-header class="watchlist-header">
        <div class="header-left">
          <h1>关注列表</h1>
        </div>
        <div class="header-right">
          <span>欢迎，{{ authStore.user?.username || '用户' }}</span>
          <el-button @click="goToDashboard">返回仪表盘</el-button>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      
      <el-main class="watchlist-main">
        <el-card class="create-watchlist-card">
          <template #header>
            <div class="card-header">
              <span>添加关注</span>
            </div>
          </template>
          
          <el-form
            ref="createFormRef"
            :model="createForm"
            :rules="createRules"
            label-width="120px"
            @submit.prevent="handleCreateWatchlist"
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
              
              <el-col :span="8">
                <el-form-item label="备注" prop="notes">
                  <el-input
                    v-model="createForm.notes"
                    placeholder="请输入备注（可选）"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="createLoading"
                    @click="handleCreateWatchlist"
                  >
                    添加关注
                  </el-button>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>
        
        <el-card class="watchlist-list-card">
          <template #header>
            <div class="card-header">
              <span>我的关注</span>
              <el-button @click="loadWatchlist" :loading="loading">刷新</el-button>
            </div>
          </template>
          
          <el-table
            :data="watchlist"
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="crypto_symbol" label="交易对" width="120">
              <template #default="{ row }">
                <el-tag>{{ row.crypto_symbol }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="crypto_name" label="币种名称" width="120" />
            
            <el-table-column prop="current_price" label="当前价格" width="120">
              <template #default="{ row }">
                <span class="price">${{ row.current_price ? row.current_price.toFixed(2) : '0.00' }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="notes" label="备注" min-width="120">
              <template #default="{ row }">
                <span class="notes">{{ row.notes || '-' }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="添加时间" width="150">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="handleEditWatchlist(row)"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDeleteWatchlist(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-if="!loading && watchlist.length === 0" class="empty-state">
            <p>暂无关注项</p>
            <p>请添加新的关注项开始监控价格</p>
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
import { watchlistApi } from '../api'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const createLoading = ref(false)
const watchlist = ref<any[]>([])

const createFormRef = ref<FormInstance>()

const createForm = reactive({
  crypto_symbol: '',
  notes: ''
})

const createRules: FormRules = {
  crypto_symbol: [
    { required: true, message: '请输入交易对', trigger: 'change' }
  ]
}

const loadWatchlist = async () => {
  loading.value = true
  try {
    const response = await watchlistApi.getAll()
    watchlist.value = response.data
  } catch (error) {
    console.error('加载关注列表失败:', error)
    ElMessage.error('加载关注列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreateWatchlist = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await watchlistApi.create({
          crypto_symbol: createForm.crypto_symbol,
          notes: createForm.notes || undefined
        })
        
        ElMessage.success('关注项添加成功')
        
        createForm.crypto_symbol = ''
        createForm.notes = ''
        createFormRef.value?.resetFields()
        
        await loadWatchlist()
      } catch (error) {
        console.error('添加关注项失败:', error)
        ElMessage.error('添加关注项失败')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleEditWatchlist = (item: any) => {
  // 显示编辑对话框
  ElMessageBox.prompt('请输入新的备注', '编辑关注项', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputValue: item.notes || '',
    inputPlaceholder: '请输入备注'
  }).then(async ({ value }) => {
    try {
      await watchlistApi.update(item.id, { notes: value })
      ElMessage.success('关注项更新成功')
      await loadWatchlist()
    } catch (error) {
      console.error('更新关注项失败:', error)
      ElMessage.error('更新关注项失败')
    }
  }).catch(() => {
    // 用户取消
  })
}

const handleDeleteWatchlist = async (item: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除关注项 ${item.crypto_symbol} 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await watchlistApi.delete(item.id)
    
    ElMessage.success('关注项已删除')
    
    await loadWatchlist()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除关注项失败:', error)
      ElMessage.error('删除关注项失败')
    }
  }
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString('zh-CN')
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
  loadWatchlist()
})
</script>

<style scoped>
.watchlist-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.watchlist-header {
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

.watchlist-main {
  padding: 15px;
}

.create-watchlist-card {
  margin-bottom: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notes {
  color: #666;
  font-size: 12px;
}

.price {
  color: #e6a23c;
  font-weight: bold;
  font-size: 12px;
}

.empty-state {
  text-align: center;
  padding: 30px;
  color: #999;
}

.empty-state p {
  margin: 8px 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .watchlist-header {
    padding: 10px 15px;
    flex-direction: column;
    gap: 10px;
  }
  
  .header-left h1 {
    font-size: 1.2rem;
  }
  
  .header-right {
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .watchlist-main {
    padding: 10px;
  }
  
  .create-watchlist-card {
    margin-bottom: 10px;
  }
  
  .el-form-item {
    margin-bottom: 10px;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-table-column {
    min-width: 80px;
  }
  
  .empty-state {
    padding: 20px;
    font-size: 12px;
  }
}
</style>