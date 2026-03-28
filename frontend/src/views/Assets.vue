<template>
  <div class="page-container">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>我的资产</h1>
          <p>管理数字货币持仓组合与盈亏监控</p>
        </div>
        <div class="header-right">
          <el-button-group class="action-buttons">
            <el-button @click="goToDashboard">返回面板</el-button>
            <el-button @click="() => loadAssets(false)" :loading="loading">刷新价格</el-button>
            <el-button type="primary" :icon="Plus" @click="openAddDialog">添加资产</el-button>
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
              <el-input 
                v-model="inlineForm.crypto_symbol" 
                placeholder="如: BTCUSDT" 
                clearable 
                @change="inlineForm.crypto_symbol = formatSymbolInput(inlineForm.crypto_symbol)"
              />
            </el-form-item>
            
            <el-form-item label="持仓数量" prop="quantity" class="flex-item-small">
              <el-input-number v-model="inlineForm.quantity" :min="0" :precision="6" :controls="false" style="width: 100%" placeholder="数量" />
            </el-form-item>
            
            <el-form-item label="持仓均价 ($)" prop="buy_price" class="flex-item-small">
              <el-input-number v-model="inlineForm.buy_price" :min="0" :precision="4" :controls="false" style="width: 100%" placeholder="均价" />
            </el-form-item>
            
            <el-form-item label="备注说明 (可选)" prop="notes" class="flex-item-large">
              <el-input v-model="inlineForm.notes" placeholder="买入逻辑或来源" clearable />
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
            <el-table :data="assets" stripe hover style="width: 100%">
              <el-table-column label="交易对" min-width="110">
                <template #default="{ row }">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ row._symbol }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="_name" label="币种名称" min-width="110" show-overflow-tooltip />
              
              <el-table-column label="持仓数量" min-width="110" align="right">
                <template #default="{ row }">
                  <span class="crypto-amount">{{ formatNum(row._qty, 4) }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="平均持仓价" min-width="120" align="right">
                <template #default="{ row }">
                  <span class="base-price">${{ formatNum(row._bp, 4) }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="当前价格" min-width="120" align="right">
                <template #default="{ row }">
                  <span class="price-text">${{ formatNum(row._cp, 4) }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="当前市值" min-width="130" align="right">
                <template #default="{ row }">
                  <b class="market-value">${{ formatNum(row._currentValue, 2) }}</b>
                </template>
              </el-table-column>
              
              <el-table-column label="盈亏" min-width="140" align="right">
                <template #default="{ row }">
                  <span :class="row._profitLoss >= 0 ? 'text-up' : 'text-down'">
                    {{ row._profitLoss >= 0 ? '+' : '' }}{{ formatNum(row._profitLoss, 2) }}
                    ({{ formatNum(row._profitLossPercent, 2) }}%)
                  </span>
                </template>
              </el-table-column>
              
              <el-table-column label="操作" width="140" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button-group>
                    <el-button size="small" :icon="Edit" @click="openEditDialog(row)" />
                    <el-button size="small" type="danger" :icon="Delete" @click="handleDelete(row)" />
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="assets.length === 0" description="暂无资产记录，请在上方快捷添加" />
          </el-card>
        </div>

        <div class="mobile-view">
          <el-empty v-if="assets.length === 0" description="暂无资产记录，请在上方添加" />
          <div v-else class="card-list">
            <el-card v-for="item in assets" :key="item.id" shadow="hover" class="mobile-data-card">
              <div class="card-header-row">
                <div class="coin-info">
                  <el-tag effect="dark" round class="symbol-tag">{{ item._symbol }}</el-tag>
                  <span class="coin-name">{{ item._name }}</span>
                </div>
                <div :class="['p-l-badge', item._profitLoss >= 0 ? 'bg-profit' : 'bg-loss']">
                  {{ item._profitLoss >= 0 ? '+' : '' }}{{ formatNum(item._profitLossPercent, 2) }}%
                </div>
              </div>

              <el-divider class="compact-divider" />

              <div class="card-body">
                <div class="data-row main-data">
                  <span class="data-label">当前总市值</span>
                  <span class="market-value-large">${{ formatNum(item._currentValue, 2) }}</span>
                </div>
                
                <div class="data-grid">
                  <div class="data-item">
                    <span class="data-label">持仓数量</span>
                    <span class="data-value crypto-amount">{{ formatNum(item._qty, 4) }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">持仓均价</span>
                    <span class="data-value">${{ formatNum(item._bp, 4) }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">当前价格</span>
                    <span class="data-value price-text">${{ formatNum(item._cp, 4) }}</span>
                  </div>
                  <div class="data-item">
                    <span class="data-label">盈亏金额</span>
                    <span :class="['data-value', item._profitLoss >= 0 ? 'text-up' : 'text-down']">
                      {{ item._profitLoss >= 0 ? '+' : '' }}${{ formatNum(item._profitLoss, 2) }}
                    </span>
                  </div>
                </div>

                <div v-if="item.notes" class="notes-box">
                  <el-icon><Notebook /></el-icon>
                  <span>{{ item.notes }}</span>
                </div>
              </div>

              <el-divider class="compact-divider" />

              <div class="card-footer">
                <el-button size="default" :icon="Edit" @click="openEditDialog(item)" plain style="flex:1">修改数据</el-button>
                <el-button size="default" type="danger" :icon="Delete" @click="handleDelete(item)" plain style="flex:1">删除记录</el-button>
              </div>
            </el-card>
          </div>
        </div>

      </div>
    </el-main>

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '修改资产数据' : '添加新资产 (弹窗模式)'"
      class="responsive-dialog"
      @close="handleDialogClose"
    >
      <el-form :model="dialogForm" :rules="formRules" ref="dialogFormRef" label-position="top">
        <el-form-item label="交易对 (容错: 填 eth 自动转 ETHUSDT)" prop="crypto_symbol">
          <el-input 
            v-model="dialogForm.crypto_symbol" 
            placeholder="输入要添加的交易对" 
            clearable 
            :disabled="isEditing" 
            @change="dialogForm.crypto_symbol = formatSymbolInput(dialogForm.crypto_symbol)"
          />
        </el-form-item>
        
        <div class="form-row-2">
          <el-form-item label="持仓数量" prop="quantity">
            <el-input-number v-model="dialogForm.quantity" :min="0" :precision="6" :step="0.01" style="width: 100%" />
          </el-form-item>
          <el-form-item label="平均持仓均价 ($)" prop="buy_price">
            <el-input-number v-model="dialogForm.buy_price" :min="0" :precision="4" :step="1" style="width: 100%" />
          </el-form-item>
        </div>
        
        <el-form-item label="备注说明 (可选)" prop="notes">
          <el-input v-model="dialogForm.notes" type="textarea" placeholder="记录购买理由或来源" rows="2" clearable />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button v-if="!isEditing" type="success" @click="submitDialogForm(true)" :loading="submitLoading" plain>
            保存并继续添加
          </el-button>
          <el-button type="primary" @click="submitDialogForm(false)" :loading="submitLoading">
            {{ isEditing ? '保存修改' : '确认添加' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Edit, Delete, Notebook } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { assetsApi } from '../api'

const router = useRouter()
const loading = ref(false)
const submitLoading = ref(false)
const assets = ref<any[]>([])
let refreshTimer: ReturnType<typeof setInterval> | null = null

const inlineFormRef = ref<FormInstance>()
const dialogFormRef = ref<FormInstance>()

const inlineForm = reactive({ crypto_symbol: '', quantity: undefined as number|undefined, buy_price: undefined as number|undefined, notes: '' })
const dialogForm = reactive({ id: null as number|null, crypto_symbol: '', quantity: 0, buy_price: 0, notes: '' })

const dialogVisible = ref(false)
const isEditing = ref(false)

const formRules: FormRules = {
  crypto_symbol: [{ required: true, message: '请输入交易对', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入持仓数量', trigger: 'blur' }],
  buy_price: [{ required: true, message: '请输入持仓均价', trigger: 'blur' }]
}

const formatNum = (val: any, decimals: number) => {
  const num = Number(val)
  return isNaN(num) ? (0).toFixed(decimals) : num.toFixed(decimals)
}

// 核心修复 3：升级版智能输入容错清洗引擎 (解决把 btc 误判为后缀的 bug)
const formatSymbolInput = (rawSymbol: string) => {
  if (!rawSymbol) return ''
  let formatted = rawSymbol.trim().toUpperCase()
  if (!formatted) return ''
  
  // 计价货币白名单
  const quoteCurrencies = ['USDT', 'USDC', 'BTC', 'ETH', 'FDUSD']
  
  // 必须同时满足：1.以后缀结尾 2.字符串总长度大于后缀的长度 (防止输入 "BTC" 触发条件)
  const hasQuote = quoteCurrencies.some(quote => {
    return formatted.endsWith(quote) && formatted.length > quote.length
  })

  // 若不包含任何标准计价后缀，则补齐 USDT
  if (!hasQuote) {
    formatted += 'USDT'
  }
  return formatted
}

const loadAssets = async (isBackground = false) => {
  if (!isBackground) loading.value = true
  try {
    const response = await assetsApi.getAll()
    
    const uniqueData: any[] = []
    const seenSymbols = new Set()
    
    for (const item of response.data) {
      const rawSymbol = item.crypto_symbol || (item.crypto && item.crypto.symbol) || 'UNKNOWN'
      if (!seenSymbols.has(rawSymbol)) {
        seenSymbols.add(rawSymbol)
        uniqueData.push(item)
      }
    }

    assets.value = uniqueData.map((asset: any) => {
      const cp = Number(asset.current_price || (asset.crypto && asset.crypto.current_price) || 0)
      const qty = Number(asset.quantity || 0)
      const bp = Number(asset.buy_price || 0)
      const totalCost = bp * qty
      const currentValue = cp * qty
      const profitLoss = currentValue - totalCost
      const profitLossPercent = totalCost > 0 ? (profitLoss / totalCost) * 100 : 0
      
      return { 
        ...asset, 
        _symbol: asset.crypto_symbol || (asset.crypto && asset.crypto.symbol) || '未知',
        _name: asset.crypto_name || (asset.crypto && asset.crypto.name) || '-',
        _cp: cp, _qty: qty, _bp: bp,
        _totalCost: totalCost, _currentValue: currentValue,
        _profitLoss: profitLoss, _profitLossPercent: profitLossPercent
      }
    })
  } catch (error) {
    if (!isBackground) ElMessage.error('加载资产数据失败')
  } finally {
    if (!isBackground) loading.value = false
  }
}

const submitInlineForm = async () => {
  if (!inlineFormRef.value) return
  
  // 核心修复 4：提交前再次强制同步覆盖
  inlineForm.crypto_symbol = formatSymbolInput(inlineForm.crypto_symbol)

  await inlineFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        await assetsApi.create({
          crypto_symbol: inlineForm.crypto_symbol, // 直接提取已经同步变大写的字段
          quantity: Number(inlineForm.quantity),
          buy_price: Number(inlineForm.buy_price),
          notes: inlineForm.notes
        })
        ElMessage.success(`成功录入资产: ${inlineForm.crypto_symbol}`)
        inlineFormRef.value?.resetFields()
        loadAssets(true)
      } catch (error: any) {
        ElMessage.error(error.message || '录入失败，可能已存在记录')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const submitDialogForm = async (keepOpen = false) => {
  if (!dialogFormRef.value) return

  // 强制同步
  dialogForm.crypto_symbol = formatSymbolInput(dialogForm.crypto_symbol)

  await dialogFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        const payload = {
          crypto_symbol: dialogForm.crypto_symbol,
          quantity: Number(dialogForm.quantity),
          buy_price: Number(dialogForm.buy_price),
          notes: dialogForm.notes
        }

        if (isEditing.value && dialogForm.id) {
          await assetsApi.update(dialogForm.id, payload)
          ElMessage.success('资产数据更新成功')
          dialogVisible.value = false
        } else {
          await assetsApi.create(payload)
          ElMessage.success(`成功添加资产: ${payload.crypto_symbol}`)
          
          if (keepOpen) {
            dialogFormRef.value?.resetFields()
          } else {
            dialogVisible.value = false
          }
        }
        loadAssets(true)
      } catch (error: any) {
        ElMessage.error(error.message || '操作失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const openAddDialog = () => {
  isEditing.value = false
  dialogForm.id = null
  dialogForm.crypto_symbol = ''
  dialogForm.quantity = 0
  dialogForm.buy_price = 0
  dialogForm.notes = ''
  setTimeout(() => dialogFormRef.value?.clearValidate(), 0)
  dialogVisible.value = true
}

const openEditDialog = (row: any) => {
  isEditing.value = true
  dialogForm.id = row.id
  dialogForm.crypto_symbol = row._symbol
  dialogForm.quantity = row._qty
  dialogForm.buy_price = row._bp
  dialogForm.notes = row.notes || ''
  dialogVisible.value = true
}

const handleDialogClose = () => {
  dialogFormRef.value?.resetFields()
}

const handleDelete = (row: any) => {
  ElMessageBox.confirm(`确定要彻底删除 ${row._symbol} 的持仓记录吗？`, '危险操作', {
    confirmButtonText: '强制删除', cancelButtonText: '取消', type: 'error'
  }).then(async () => {
    try {
      await assetsApi.delete(row.id)
      ElMessage.success('资产记录已抹除')
      loadAssets(true)
    } catch (error) {
      ElMessage.error('删除资产失败')
    }
  }).catch(() => {})
}

const goToDashboard = () => router.push('/dashboard')

onMounted(() => {
  loadAssets(false)
  refreshTimer = setInterval(() => loadAssets(true), 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
/* =========================================
   UI 架构层：与 Watchlist/Alerts 绝对统一
   ========================================= */
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; width: 100%; }
.header-left h1 { margin: 0; font-size: 22px; color: #1f2f3d; font-weight: 600; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.page-main { padding: 20px 25px; max-width: 1400px; margin: 0 auto; width: 100%; }

.form-card { margin-bottom: 20px; border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); }
.table-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); overflow: hidden; }

/* 字体与颜色语义 (专为金融数据强化) */
.symbol-tag { font-weight: bold; font-family: 'Monaco', monospace; }
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; }
.market-value { color: #1f2f3d; font-size: 16px; font-family: 'Monaco', monospace; }
.crypto-amount { color: #5e6d82; font-family: 'Monaco', monospace; }
.base-price { color: #909399; font-family: 'Monaco', monospace; }
.text-up { color: #f56c6c; font-weight: bold; font-family: 'Monaco', monospace; }
.text-down { color: #67c23a; font-weight: bold; font-family: 'Monaco', monospace; }

/* =========================================
   PC端视图 (> 768px)
   ========================================= */
@media (min-width: 769px) {
  .desktop-view { display: block; }
  .mobile-view { display: none !important; }
  
  :deep(.el-table th.el-table__cell) { background-color: #fafafa; color: #606266; font-weight: 600; height: 50px; }
  
  .form-responsive-row { display: flex; gap: 20px; align-items: flex-end; }
  .flex-item-large { flex: 2; margin-bottom: 0; }
  .flex-item-small { flex: 1.2; margin-bottom: 0; }
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
  .flex-item-large, .flex-item-small { margin-bottom: 16px; }
  .flex-btn { margin-bottom: 4px; }

  /* 移动端高级卡片设计 */
  .card-list { display: flex; flex-direction: column; gap: 12px; }
  .mobile-data-card { 
    border-radius: 12px; border: none; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.03); 
    transition: transform 0.2s ease;
  }
  .mobile-data-card:active { transform: scale(0.98); }
  :deep(.mobile-data-card .el-card__body) { padding: 16px; }
  
  .card-header-row { display: flex; justify-content: space-between; align-items: center; }
  .coin-info { display: flex; align-items: center; gap: 10px; }
  .coin-name { font-weight: 600; font-size: 15px; color: #303133; }
  
  .p-l-badge { padding: 4px 10px; border-radius: 20px; color: white; font-size: 12px; font-weight: bold; font-family: 'Monaco', monospace;}
  .bg-profit { background-color: #f56c6c; } /* 国内习惯红涨绿跌 */
  .bg-loss { background-color: #67c23a; }

  .compact-divider { margin: 14px 0; border-color: #ebeef5; opacity: 0.6; }
  
  .card-body { display: flex; flex-direction: column; gap: 12px; }
  .data-label { font-size: 12px; color: #909399; margin-bottom: 4px; display: block; }
  .data-value { font-size: 15px; font-weight: 500; }

  .main-data { background: #f8f9fa; padding: 12px; border-radius: 8px; border: 1px solid #f0f2f5;}
  .market-value-large { font-size: 22px; font-weight: bold; color: #1f2f3d; font-family: 'Monaco', monospace;}

  .data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  
  .notes-box { display: flex; align-items: flex-start; gap: 6px; background: #fdfdfd; padding: 10px; border-radius: 6px; border: 1px dashed #e4e7ed; font-size: 13px; color: #5e6d82;}
  .notes-box .el-icon { margin-top: 2px; color: #a8abb2; }

  .card-footer { display: flex; gap: 12px; margin-top: 6px; }
  .card-footer .el-button { border-radius: 6px; }

  /* 对话框适配 */
  :deep(.responsive-dialog) { width: 95% !important; max-width: 400px; margin: 5vh auto !important; border-radius: 12px; }
  .form-row-2 { display: flex; flex-direction: column; gap: 0; }
  :deep(.dialog-footer) { display: flex; flex-wrap: wrap; gap: 10px; }
  :deep(.dialog-footer .el-button) { flex: 1 1 100%; margin-left: 0 !important; }
}
</style>