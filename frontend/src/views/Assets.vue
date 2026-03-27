<template>
  <div class="assets-container">
    <el-container>
      <el-header class="assets-header">
        <div class="header-left">
          <h1>资产管理</h1>
        </div>
        <div class="header-right">
          <span>欢迎，{{ authStore.user?.username || '用户' }}</span>
          <el-button @click="goToDashboard">返回仪表盘</el-button>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      
      <el-main class="assets-main">
        <!-- 添加资产表单 -->
        <el-card class="create-asset-card">
          <template #header>
            <div class="card-header">
              <span>添加新资产</span>
            </div>
          </template>
          
          <el-form
            ref="createFormRef"
            :model="createForm"
            :rules="createRules"
            label-width="120px"
            @submit.prevent="handleCreateAsset"
          >
            <el-row :gutter="20">
              <el-col :span="6">
                <el-form-item label="交易对" prop="crypto_symbol">
                  <el-input
                    v-model="createForm.crypto_symbol"
                    placeholder="请输入交易对，如：BTCUSDT"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <el-form-item label="买入价格" prop="buy_price">
                  <el-input-number
                    v-model="createForm.buy_price"
                    :precision="2"
                    :min="0"
                    placeholder="请输入买入价格"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <el-form-item label="持有数量" prop="quantity">
                  <el-input-number
                    v-model="createForm.quantity"
                    :precision="8"
                    :min="0"
                    placeholder="请输入持有数量"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="6">
                <el-form-item>
                  <el-button
                    type="primary"
                    :loading="createLoading"
                    @click="handleCreateAsset"
                  >
                    添加资产
                  </el-button>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row>
              <el-col :span="24">
                <el-form-item label="备注" prop="notes">
                  <el-input
                    v-model="createForm.notes"
                    placeholder="请输入备注（可选）"
                    type="textarea"
                    :rows="2"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>
        
        <!-- 资产列表 -->
        <el-card class="assets-list-card">
          <template #header>
            <div class="card-header">
              <span>我的资产</span>
              <div class="header-actions">
                <span class="total-value">总资产价值: ${{ totalValue.toLocaleString() }}</span>
                <el-button @click="loadAssets" :loading="loading">刷新</el-button>
              </div>
            </div>
          </template>
          
          <el-table
            :data="assets"
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="crypto_symbol" label="交易对" width="120">
              <template #default="{ row }">
                <el-tag>{{ row.crypto_symbol }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="crypto_name" label="币种名称" width="150" />
            
            <el-table-column prop="buy_price" label="买入价格" width="150">
              <template #default="{ row }">
                <span class="price">${{ row.buy_price.toLocaleString() }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="quantity" label="持有数量" width="150">
              <template #default="{ row }">
                <span class="quantity">{{ row.quantity }}</span>
              </template>
            </el-table-column>
            
            <el-table-column label="总价值" width="180">
              <template #default="{ row }">
                <span class="total-value">${{ row.total_value.toLocaleString() }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="notes" label="备注" min-width="150">
              <template #default="{ row }">
                <span class="notes">{{ row.notes || '-' }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="添加时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="handleEditAsset(row)"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  @click="handleDeleteAsset(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div v-if="!loading && assets.length === 0" class="empty-state">
            <p>暂无资产记录</p>
            <p>请添加您的数字货币资产开始跟踪</p>
          </div>
        </el-card>
      </el-main>
    </el-container>
    
    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑资产"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="买入价格" prop="buy_price">
          <el-input-number
            v-model="editForm.buy_price"
            :precision="2"
            :min="0"
            placeholder="请输入买入价格"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="持有数量" prop="quantity">
          <el-input-number
            v-model="editForm.quantity"
            :precision="8"
            :min="0"
            placeholder="请输入持有数量"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="备注" prop="notes">
          <el-input
            v-model="editForm.notes"
            placeholder="请输入备注"
            type="textarea"
            :rows="2"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveEdit">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { cryptocurrenciesApi, assetsApi } from '../api'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const createLoading = ref(false)
const cryptocurrencies = ref<any[]>([])
const assets = ref<any[]>([])

const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const editDialogVisible = ref(false)
const editingAssetId = ref<number | null>(null)

const createForm = reactive({
  crypto_symbol: '',
  buy_price: null as number | null,
  quantity: null as number | null,
  notes: ''
})

const editForm = reactive({
  buy_price: null as number | null,
  quantity: null as number | null,
  notes: ''
})

const createRules: FormRules = {
  crypto_symbol: [
    { required: true, message: '请选择或输入币种', trigger: 'change' }
  ],
  buy_price: [
    { required: true, message: '请输入买入价格', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '价格必须大于0', trigger: 'blur' }
  ],
  quantity: [
    { required: true, message: '请输入持有数量', trigger: 'blur' },
    { type: 'number', min: 0.00000001, message: '数量必须大于0', trigger: 'blur' }
  ]
}

const editRules: FormRules = {
  buy_price: [
    { required: true, message: '请输入买入价格', trigger: 'blur' },
    { type: 'number', min: 0.01, message: '价格必须大于0', trigger: 'blur' }
  ],
  quantity: [
    { required: true, message: '请输入持有数量', trigger: 'blur' },
    { type: 'number', min: 0.00000001, message: '数量必须大于0', trigger: 'blur' }
  ]
}

const totalValue = computed(() => {
  return assets.value.reduce((sum, asset) => sum + asset.total_value, 0)
})

const loadCryptocurrencies = async () => {
  try {
    const response = await cryptocurrenciesApi.getAll()
    cryptocurrencies.value = response.data
  } catch (error) {
    console.error('加载币种失败:', error)
    ElMessage.error('加载币种失败')
  }
}

const loadAssets = async () => {
  loading.value = true
  try {
    const response = await assetsApi.getAll()
    assets.value = response.data
  } catch (error) {
    console.error('加载资产失败:', error)
    ElMessage.error('加载资产失败')
  } finally {
    loading.value = false
  }
}

const handleCreateAsset = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await assetsApi.create({
          crypto_symbol: createForm.crypto_symbol,
          buy_price: createForm.buy_price!,
          quantity: createForm.quantity!,
          notes: createForm.notes || undefined
        })
        
        ElMessage.success('资产添加成功')
        
        createForm.crypto_symbol = ''
        createForm.buy_price = null
        createForm.quantity = null
        createForm.notes = ''
        createFormRef.value?.resetFields()
        
        await loadAssets()
      } catch (error) {
        console.error('添加资产失败:', error)
        ElMessage.error('添加资产失败')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleEditAsset = (asset: any) => {
  editingAssetId.value = asset.id
  editForm.buy_price = asset.buy_price
  editForm.quantity = asset.quantity
  editForm.notes = asset.notes || ''
  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  if (!editFormRef.value || !editingAssetId.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await assetsApi.update(editingAssetId.value!, {
          buy_price: editForm.buy_price!,
          quantity: editForm.quantity!,
          notes: editForm.notes || undefined
        })
        
        ElMessage.success('资产更新成功')
        editDialogVisible.value = false
        
        await loadAssets()
      } catch (error) {
        console.error('更新资产失败:', error)
        ElMessage.error('更新资产失败')
      }
    }
  })
}

const handleDeleteAsset = async (asset: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${asset.crypto_name} 的资产记录吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await assetsApi.delete(asset.id)
    
    ElMessage.success('资产已删除')
    
    await loadAssets()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除资产失败:', error)
      ElMessage.error('删除资产失败')
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
  loadCryptocurrencies()
  loadAssets()
})
</script>

<style scoped>
.assets-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.assets-header {
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

.assets-main {
  padding: 20px;
}

.create-asset-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.total-value {
  font-weight: bold;
  color: #e6a23c;
  font-size: 16px;
}

.price {
  font-weight: bold;
  color: #409eff;
}

.quantity {
  font-weight: bold;
  color: #67c23a;
}

.notes {
  color: #666;
  font-size: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-state p {
  margin: 10px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>