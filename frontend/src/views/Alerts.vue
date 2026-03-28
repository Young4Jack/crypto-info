<template>
  <div class="page-container">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>预警管理</h1>
          <p>设定价格阈值，捕捉市场每一次关键异动</p>
        </div>
        <div class="header-right">
          <el-button-group class="action-buttons">
            <el-button @click="goToDashboard">返回面板</el-button>
            <el-button @click="() => loadAlerts(false)" :loading="loading">刷新状态</el-button>
            <el-button type="primary" :icon="Plus" @click="openAddDialog">创建预警</el-button>
          </el-button-group>
        </div>
      </div>
    </el-header>
      
    <el-main class="page-main">
      <el-card class="form-card" shadow="never">
        <el-form
          ref="inlineFormRef"
          :model="inlineForm"
          :rules="formRules"
          label-position="top"
          @submit.prevent="submitInlineForm"
        >
          <div class="form-responsive-row">
            <el-form-item label="交易对 (容错: 填 btc 自动转 BTCUSDT)" prop="crypto_symbol" class="flex-item-large">
              <el-input v-model="inlineForm.crypto_symbol" placeholder="输入监控币种" clearable />
            </el-form-item>
            
            <el-form-item label="触发条件" prop="alert_type" class="flex-item-small">
              <el-select v-model="inlineForm.alert_type" placeholder="选择条件" style="width: 100%">
                <el-option label="价格高于 ↑" value="above" />
                <el-option label="价格低于 ↓" value="below" />
                <el-option label="振幅预警 ↕" value="amplitude" />
                <el-option label="涨幅百分比 ↗" value="percent_up" />
                <el-option label="跌幅百分比 ↘" value="percent_down" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="持续预警" class="flex-item-small">
              <el-switch v-model="inlineForm.is_continuous" active-text="是" inactive-text="否" />
            </el-form-item>
            
            <el-form-item label="通知次数" class="flex-item-small">
              <el-input-number v-model="inlineForm.max_notifications" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
            
            <el-form-item label="间隔(分钟)" class="flex-item-small">
              <el-input-number v-model="inlineForm.interval_minutes" :min="1" :max="1440" style="width: 100%" />
            </el-form-item>
            
            <el-form-item label="目标价格 ($)" prop="threshold_price" class="flex-item-medium">
              <el-input-number v-model="inlineForm.threshold_price" :precision="4" :min="0" :controls="false" style="width: 100%" placeholder="目标触发价" />
            </el-form-item>
            
            <el-form-item label="&nbsp;" class="flex-btn">
              <el-button type="primary" :loading="submitLoading" @click="submitInlineForm" style="width: 100%;">
                快捷添加
              </el-button>
            </el-form-item>
          </div>
        </el-form>
      </el-card>
      
      <div class="view-wrapper" v-loading="loading">
        
        <div class="desktop-view">
          <el-card shadow="never" class="table-card">
            <el-table :data="alerts" stripe hover style="width: 100%">
              <el-table-column label="交易对" min-width="110">
                <template #default="{ row }">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ row._symbol }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="当前价格" min-width="120" align="right">
                <template #default="{ row }">
                  <span class="price-text">${{ formatNum(row._cp, 4) }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="触发条件" min-width="150" align="right">
                <template #default="{ row }">
                  <span class="condition-group">
                    <span :class="row.alert_type === 'above' ? 'text-up' : 'text-down'">
                      {{ row.alert_type === 'above' ? '高于 ↑' : '低于 ↓' }}
                    </span>
                    <b class="price-target">${{ formatNum(row.threshold_price, 4) }}</b>
                  </span>
                </template>
              </el-table-column>
              
              <el-table-column label="运行状态" min-width="110" align="center">
                <template #default="{ row }">
                  <el-switch
                    v-model="row.is_active"
                    style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
                    inline-prompt
                    active-text="监控中"
                    inactive-text="已停用"
                    @change="handleToggleActive(row)"
                  />
                </template>
              </el-table-column>
              
              <el-table-column label="最后触发" min-width="160">
                <template #default="{ row }">
                  <span class="time-text">{{ row.triggered_at ? formatTime(row.triggered_at) : '等待触发...' }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="操作" width="100" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" type="danger" plain @click="handleDeleteAlert(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="alerts.length === 0" description="暂无预警规则，请在上方快捷创建" />
          </el-card>
        </div>

        <div class="mobile-view">
          <el-empty v-if="alerts.length === 0" description="暂无预警规则，请在上方创建" />
          <div v-else class="card-list">
            <el-card v-for="item in alerts" :key="item.id" shadow="hover" :class="['mobile-data-card', !item.is_active && 'card-inactive']">
              <div class="card-header-row">
                <div class="coin-info">
                  <el-tag effect="dark" round class="symbol-tag">{{ item._symbol }}</el-tag>
                </div>
                <div class="status-indicator" @click="handleToggleActive(item)">
                  <span :class="['status-dot', item.is_active ? 'dot-active' : 'dot-inactive']"></span>
                  <span class="status-text">{{ item.is_active ? '监控中' : '已停用' }}</span>
                </div>
              </div>

              <el-divider class="compact-divider" />

              <div class="card-body">
                <div class="price-compare-box">
                  <div class="price-item">
                    <span class="price-label">当前价格</span>
                    <span class="price-value price-text">${{ formatNum(item._cp, 4) }}</span>
                  </div>
                  <div class="price-divider"></div>
                  <div class="price-item">
                    <span class="price-label">目标设定</span>
                    <span class="price-value">
                      <span :class="item.alert_type === 'above' ? 'text-up' : 'text-down'" style="font-size: 14px; margin-right: 4px;">
                        {{ item.alert_type === 'above' ? '高于↑' : '低于↓' }}
                      </span>
                      <span class="price-target">${{ formatNum(item.threshold_price, 4) }}</span>
                    </span>
                  </div>
                </div>
                
                <div class="trigger-info">
                  <span class="trigger-label">最新动态:</span>
                  <span class="trigger-time">{{ item.triggered_at ? formatTime(item.triggered_at) : '监控引擎待命...' }}</span>
                </div>
              </div>

              <el-divider class="compact-divider" />

              <div class="card-footer">
                <el-button size="default" :type="item.is_active ? 'warning' : 'success'" plain @click="handleToggleActive(item)" style="flex:1">
                  {{ item.is_active ? '暂停监控' : '恢复监控' }}
                </el-button>
                <el-button size="default" type="danger" plain @click="handleDeleteAlert(item)" style="flex:1">彻底删除</el-button>
              </div>
            </el-card>
          </div>
        </div>

      </div>
    </el-main>

    <el-dialog
      v-model="dialogVisible"
      title="创建新预警 (弹窗模式)"
      class="responsive-dialog"
      @close="handleDialogClose"
    >
      <el-form :model="dialogForm" :rules="formRules" ref="dialogFormRef" label-position="top">
        <el-form-item label="交易对 (容错: 填 eth 自动转 ETHUSDT)" prop="crypto_symbol">
          <el-input v-model="dialogForm.crypto_symbol" placeholder="输入要监控的交易对" clearable />
        </el-form-item>
        
        <div class="form-row-2">
          <el-form-item label="触发条件" prop="alert_type">
            <el-select v-model="dialogForm.alert_type" style="width: 100%">
              <el-option label="价格高于 ↑" value="above" />
              <el-option label="价格低于 ↓" value="below" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标价格 ($)" prop="threshold_price">
            <el-input-number v-model="dialogForm.threshold_price" :min="0" :precision="4" :step="1" style="width: 100%" />
          </el-form-item>
        </div>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="success" @click="submitDialogForm(true)" :loading="submitLoading" plain>
            保存并继续创建
          </el-button>
          <el-button type="primary" @click="submitDialogForm(false)" :loading="submitLoading">
            确认创建
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { alertsApi } from '../api'

const router = useRouter()
const loading = ref(false)
const submitLoading = ref(false)
const alerts = ref<any[]>([])
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 双输入渠道隔离
const inlineFormRef = ref<FormInstance>()
const dialogFormRef = ref<FormInstance>()

const inlineForm = reactive({ 
  crypto_symbol: '', 
  alert_type: 'above' as 'above'|'below'|'amplitude'|'percent_up'|'percent_down', 
  threshold_price: undefined as number|undefined,
  is_continuous: false,
  max_notifications: 1,
  interval_minutes: 5
})
const dialogForm = reactive({ 
  crypto_symbol: '', 
  alert_type: 'above' as 'above'|'below'|'amplitude'|'percent_up'|'percent_down', 
  threshold_price: undefined as number|undefined,
  is_continuous: false,
  max_notifications: 1,
  interval_minutes: 5
})
const dialogVisible = ref(false)

const formRules: FormRules = {
  crypto_symbol: [{ required: true, message: '请输入交易对', trigger: 'blur' }],
  threshold_price: [{ required: true, message: '请输入目标触发价格', trigger: 'blur' }]
}

// 格式化工具：数字安全与容错输入
const formatNum = (val: any, decimals: number) => {
  const num = Number(val)
  return isNaN(num) ? (0).toFixed(decimals) : num.toFixed(decimals)
}

const formatSymbolInput = (rawSymbol: string) => {
  let formatted = rawSymbol.trim().toUpperCase()
  if (!formatted) return ''
  if (!formatted.endsWith('USDT') && !formatted.endsWith('USDC') && !formatted.endsWith('BTC') && !formatted.endsWith('ETH')) {
    formatted += 'USDT'
  }
  return formatted
}

const loadAlerts = async (isBackground = false) => {
  if (!isBackground) loading.value = true
  try {
    const response = await alertsApi.getAll()
    
    alerts.value = response.data.map((alert: any) => {
      // 提取当前价格（兼容后端可能的嵌套结构，若后端暂无该字段则默认为0）
      const cp = Number(alert.current_price || (alert.crypto && alert.crypto.current_price) || 0)
      
      return {
        ...alert,
        _symbol: alert.crypto_symbol || (alert.crypto && alert.crypto.symbol) || '未知',
        _cp: cp
      }
    })
  } catch (error) {
    if (!isBackground) ElMessage.error('加载预警规则失败')
  } finally {
    if (!isBackground) loading.value = false
  }
}

// 提交处理：渠道一 (页面快捷录入)
const submitInlineForm = async () => {
  if (!inlineFormRef.value) return
  await inlineFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const formattedSymbol = formatSymbolInput(inlineForm.crypto_symbol)
        await alertsApi.create({
          crypto_symbol: formattedSymbol,
          alert_type: inlineForm.alert_type as 'above' | 'below',
          threshold_price: Number(inlineForm.threshold_price)
        })
        ElMessage.success(`预警创建成功: ${formattedSymbol}`)
        
        inlineForm.crypto_symbol = ''
        inlineForm.threshold_price = undefined
        inlineFormRef.value?.resetFields()
        
        loadAlerts(true)
      } catch (error: any) {
        ElMessage.error('创建失败，可能是参数错误')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

// 提交处理：渠道二 (弹窗录入)
const submitDialogForm = async (keepOpen = false) => {
  if (!dialogFormRef.value) return
  await dialogFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const formattedSymbol = formatSymbolInput(dialogForm.crypto_symbol)
        await alertsApi.create({
          crypto_symbol: formattedSymbol,
          alert_type: dialogForm.alert_type,
          threshold_price: Number(dialogForm.threshold_price)
        })
        ElMessage.success(`预警创建成功: ${formattedSymbol}`)
        
        if (keepOpen) {
          dialogForm.crypto_symbol = ''
          dialogForm.threshold_price = undefined
          dialogFormRef.value?.resetFields()
        } else {
          dialogVisible.value = false
        }
        loadAlerts(true)
      } catch (error: any) {
        ElMessage.error('创建失败，可能是参数错误')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const openAddDialog = () => {
  dialogForm.crypto_symbol = ''
  dialogForm.threshold_price = undefined
  setTimeout(() => dialogFormRef.value?.clearValidate(), 0)
  dialogVisible.value = true
}

const handleDialogClose = () => {
  dialogFormRef.value?.resetFields()
}

const handleToggleActive = async (alert: any) => {
  const originalState = alert.is_active
  alert.is_active = !originalState
  try {
    await alertsApi.update(alert.id, { is_active: alert.is_active })
    ElMessage.success(`已${alert.is_active ? '启动' : '暂停'}监控引擎`)
  } catch (error) {
    alert.is_active = originalState
    ElMessage.error('状态更新失败')
  }
}

const handleDeleteAlert = async (alert: any) => {
  try {
    await ElMessageBox.confirm(`确定删除 ${alert._symbol} 的预警设定吗？`, '危险操作', {
      confirmButtonText: '强制删除', cancelButtonText: '取消', type: 'error'
    })
    await alertsApi.delete(alert.id)
    ElMessage.success('预警已抹除')
    loadAlerts(true)
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  const dateStr = timeStr.endsWith('Z') || timeStr.includes('+') ? timeStr : timeStr + 'Z'
  return new Date(dateStr).toLocaleString('zh-CN', { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const goToDashboard = () => router.push('/dashboard')

onMounted(() => {
  loadAlerts(false)
  refreshTimer = setInterval(() => loadAlerts(true), 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
/* =========================================
   UI 架构层：与 Assets/Watchlist 绝对统一
   ========================================= */
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; width: 100%; }
.header-left h1 { margin: 0; font-size: 22px; color: #1f2f3d; font-weight: 600; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.page-main { padding: 20px 25px; max-width: 1400px; margin: 0 auto; width: 100%; }

.form-card { margin-bottom: 20px; border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); }
.table-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); overflow: hidden; }

/* 字体与颜色语义 */
.symbol-tag { font-weight: bold; font-family: 'Monaco', monospace; }
.text-up { color: #f56c6c; font-weight: bold; }
.text-down { color: #67c23a; font-weight: bold; }
.price-target { color: #1f2f3d; font-size: 16px; font-family: 'Monaco', monospace; margin-left: 5px; }
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; }
.condition-group { display: flex; align-items: center; justify-content: flex-end; }
.time-text { color: #909399; font-size: 13px; }

/* =========================================
   PC端视图 (> 768px)
   ========================================= */
@media (min-width: 769px) {
  .desktop-view { display: block; }
  .mobile-view { display: none !important; }
  
  :deep(.el-table th.el-table__cell) { background-color: #fafafa; color: #606266; font-weight: 600; height: 50px; }
  
  .form-responsive-row { display: flex; gap: 24px; align-items: flex-end; }
  .flex-item-large { flex: 2; margin-bottom: 0; }
  .flex-item-medium { flex: 1.5; margin-bottom: 0; }
  .flex-item-small { flex: 1; margin-bottom: 0; }
  .flex-btn { width: 120px; margin-bottom: 0; }
  
  .form-row-2 { display: flex; gap: 20px; }
  .form-row-2 > .el-form-item { flex: 1; }
}

/* =========================================
   移动端视图 (<= 768px)
   ========================================= */
@media (max-width: 768px) {
  .desktop-view { display: none !important; }
  .mobile-view { display: block; }
  
  .page-container { padding-bottom: 80px; }
  .page-main { padding: 12px; }
  
  .page-header { padding: 15px; }
  .header-content { flex-direction: column; align-items: flex-start; gap: 15px; }
  .header-right { width: 100%; }
  
  :deep(.action-buttons) { display: flex; flex-wrap: wrap; width: 100%; gap: 8px; }
  :deep(.action-buttons .el-button) { flex: 1 1 auto; margin: 0 !important; border-radius: 6px !important; }

  .form-responsive-row { display: flex; flex-direction: column; gap: 0; }
  .flex-item-large, .flex-item-medium, .flex-item-small { margin-bottom: 16px; }
  .flex-btn { margin-bottom: 4px; }

  /* 移动端高级卡片设计 */
  .card-list { display: flex; flex-direction: column; gap: 12px; }
  .mobile-data-card { 
    border-radius: 12px; border: none; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.03); 
    transition: all 0.3s ease;
  }
  .card-inactive { opacity: 0.6; filter: grayscale(50%); }
  :deep(.mobile-data-card .el-card__body) { padding: 16px; }
  
  .card-header-row { display: flex; justify-content: space-between; align-items: center; }
  
  /* 仿 iOS 状态指示器 */
  .status-indicator { display: flex; align-items: center; gap: 6px; background: #f4f4f5; padding: 4px 10px; border-radius: 20px; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot-active { background-color: #13ce66; box-shadow: 0 0 4px #13ce66; }
  .dot-inactive { background-color: #909399; }
  .status-text { font-size: 12px; color: #606266; font-weight: 500; }
  
  .compact-divider { margin: 14px 0; border-color: #ebeef5; opacity: 0.6; }
  
  /* 移动端专属：价格对比框 */
  .price-compare-box {
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #f0f2f5;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
  }
  .price-item { display: flex; flex-direction: column; gap: 4px; }
  .price-label { font-size: 12px; color: #909399; }
  .price-value { font-size: 18px; font-weight: bold; font-family: 'Monaco', monospace; display: flex; align-items: center;}
  .price-divider { width: 1px; height: 30px; background-color: #ebeef5; margin: 0 10px; }
  
  .trigger-info { margin-top: 12px; font-size: 12px; display: flex; justify-content: space-between; align-items: center; }
  .trigger-label { color: #a8abb2; }
  .trigger-time { color: #606266; font-weight: 500; }
  
  .card-footer { display: flex; gap: 12px; margin-top: 6px; }
  .card-footer .el-button { border-radius: 6px; }

  /* 对话框适配 */
  :deep(.responsive-dialog) { width: 95% !important; max-width: 400px; margin: 5vh auto !important; border-radius: 12px; }
  .form-row-2 { display: flex; flex-direction: column; gap: 0; }
  :deep(.dialog-footer) { display: flex; flex-wrap: wrap; gap: 10px; }
  :deep(.dialog-footer .el-button) { flex: 1 1 100%; margin-left: 0 !important; }
}
</style>