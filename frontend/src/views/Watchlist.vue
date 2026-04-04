<template>
  <div class="page-container" :class="{ 'dark-mode': isDarkMode }">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>关注列表</h1>
          <p>实时监控您感兴趣的数字货币行情</p>
        </div>
        <div class="header-right">
          <el-button @click="toggleDarkMode" class="dark-mode-btn" :type="isDarkMode ? 'warning' : 'default'" plain>
            {{ isDarkMode ? '☀️' : '🌙' }}
          </el-button>
          <el-button-group class="action-buttons">
            <el-button @click="goToDashboard">返回面板</el-button>
            <el-button @click="goToHome">返回主页</el-button>
            <el-button @click="() => loadWatchlist(false)" :loading="loading">刷新行情</el-button>
            <el-button v-if="!isSortMode" type="warning" :icon="Sort" @click="enterSortMode">排序模式</el-button>
            <template v-else>
              <el-button type="success" :icon="Check" @click="saveSortOrder">保存排序</el-button>
              <el-button @click="cancelSortMode">取消</el-button>
            </template>
            <el-button type="danger" :icon="Delete" @click="handleDeleteAll">全部删除</el-button>
            <el-button type="primary" :icon="Plus" @click="dialogVisible = true">添加关注</el-button>
          </el-button-group>
        </div>
      </div>
    </el-header>
      
    <el-main class="page-main">
      <el-card class="form-card" shadow="never">
        <el-form
          ref="createFormRef"
          :model="createForm"
          :rules="createRules"
          label-position="top"
          @submit.prevent="handleCreateWatchlist('page', false)"
        >
          <div class="form-responsive-row">
            <el-form-item label="交易对 (容错输入: 填 btc 会自动转为 BTCUSDT)" prop="crypto_symbol" class="flex-item">
              <el-input 
                v-model="createForm.crypto_symbol" 
                placeholder="输入要关注的币种或交易对" 
                clearable 
                @change="createForm.crypto_symbol = formatSymbolInput(createForm.crypto_symbol)"
              />
            </el-form-item>
            
            <el-form-item label="备注说明 (可选)" prop="notes" class="flex-item">
              <el-input v-model="createForm.notes" placeholder="输入关注理由或预期" clearable />
            </el-form-item>
            
            <el-form-item label="&nbsp;" class="flex-btn">
              <el-button type="primary" :loading="createLoading" @click="handleCreateWatchlist('page', false)" style="width: 100%;">
                页面内添加
              </el-button>
            </el-form-item>
          </div>
        </el-form>
      </el-card>
      
      <div class="view-wrapper" v-loading="loading">
        <div class="desktop-view">
          <el-card shadow="never" class="table-card">
            <div v-if="isSortMode" class="sort-mode-hint">
              <el-icon><Rank /></el-icon>
              <span>拖拽行调整顺序，完成后点击"保存排序"</span>
            </div>
            <el-table :data="watchlist" stripe hover style="width: 100%">
              <el-table-column v-if="isSortMode" label="排序" width="60" align="center">
                <template #default>
                  <el-icon class="drag-handle"><Rank /></el-icon>
                </template>
              </el-table-column>
              <el-table-column label="排序" width="80" align="center">
                <template #default="{ row }">
                  <el-input-number 
                    v-model="row.sort_order" 
                    :min="0" 
                    :max="9999" 
                    size="small" 
                    controls-position="right"
                    style="width: 70px"
                    @change="handleSortOrderChange(row)"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="crypto_symbol" label="交易对" min-width="120">
                <template #default="{ row }">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ row.crypto_symbol }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="crypto_name" label="币种名称" min-width="120" />
              <el-table-column prop="current_price" label="当前价格" min-width="120" align="right">
                <template #default="{ row }">
                  <span class="price-text">${{ row.current_price ? row.current_price.toFixed(4) : '0.0000' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="备注" min-width="180" show-overflow-tooltip>
                <template #default="{ row }">
                  <span class="notes-text">{{ row.notes || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column label="公开" width="80" align="center">
                <template #default="{ row }">
                  <el-switch
                    v-model="row.is_public"
                    @change="handleTogglePublic(row)"
                    size="small"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="添加时间" min-width="160">
                <template #default="{ row }">
                  <span class="time-text">{{ formatTime(row.created_at) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button-group>
                    <el-button size="small" @click="handleEditWatchlist(row)">编辑</el-button>
                    <el-button size="small" type="danger" @click="handleDeleteWatchlist(row)">删除</el-button>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="watchlist.length === 0" description="暂无关注项，请在上方添加" />
          </el-card>
        </div>

        <div class="mobile-view">
          <el-empty v-if="watchlist.length === 0" description="暂无关注项，请在上方添加" />
          <div v-else class="card-list" :class="{ 'sort-mode': isSortMode }">
            <el-card v-for="item in watchlist" :key="item.id" shadow="hover" class="mobile-data-card" :class="isSortMode && 'draggable-card'">
              <div v-if="isSortMode" class="mobile-sort-handle">
                <el-icon><Rank /></el-icon>
              </div>
              <div class="card-header-row">
                <div class="coin-info">
                  <el-tag effect="dark" round class="symbol-tag">{{ item.crypto_symbol }}</el-tag>
                  <span class="coin-name">{{ item.crypto_name }}</span>
                </div>
                <div class="header-right-group">
                  <span class="sort-order-mini" @click.stop="startEditSort(item)">
                    <el-icon class="sort-icon"><Rank /></el-icon>
                    <span class="sort-num">{{ item.sort_order ?? 0 }}</span>
                  </span>
                  <div class="price-highlight">
                    ${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}
                  </div>
                </div>
              </div>
              <el-divider class="compact-divider" />
              <div class="card-body">
                <div class="public-toggle-row">
                  <span class="public-toggle-label">公开显示</span>
                  <el-switch
                    v-model="item.is_public"
                    @change="handleTogglePublic(item)"
                    size="small"
                  />
                </div>
                <div v-if="item.notes" class="notes-box">
                  <span class="notes-label">备注：</span>{{ item.notes }}
                </div>
                <div class="time-box">
                  收录于 {{ formatTime(item.created_at) }}
                </div>
              </div>
              <el-divider class="compact-divider" />
              <div class="card-footer">
                <el-button size="default" @click="handleEditWatchlist(item)" plain style="flex:1">修改备注</el-button>
                <el-button size="default" type="danger" @click="handleDeleteWatchlist(item)" plain style="flex:1">取消关注</el-button>
              </div>
            </el-card>
          </div>
        </div>

        <el-dialog
          v-model="sortDialogVisible"
          title="修改排序序号"
          class="responsive-dialog"
          width="280px"
        >
          <div class="sort-dialog-content">
            <div class="sort-dialog-coin">
              <el-tag effect="dark" round size="small">{{ sortEditItem?.crypto_symbol }}</el-tag>
              <span class="sort-dialog-name">{{ sortEditItem?.crypto_name }}</span>
            </div>
            <div class="sort-dialog-input">
              <span class="sort-dialog-label">排序序号</span>
              <el-input-number 
                v-model="sortEditValue" 
                :min="0" 
                :max="9999" 
                size="large"
                controls-position="right"
                class="sort-dialog-number"
              />
            </div>
          </div>
          <template #footer>
            <el-button @click="sortDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveSortEdit">保存</el-button>
          </template>
        </el-dialog>
      </div>
    </el-main>

    <el-dialog
      v-model="dialogVisible"
      title="添加新关注 (弹窗模式)"
      class="responsive-dialog"
      @close="handleDialogClose"
    >
      <el-form :model="createForm" :rules="createRules" ref="dialogFormRef" label-position="top">
        <el-form-item label="交易对 (容错输入: 填 eth 自动转为 ETHUSDT)" prop="crypto_symbol">
          <el-input 
            v-model="createForm.crypto_symbol" 
            placeholder="输入要关注的币种或交易对" 
            clearable 
            @change="createForm.crypto_symbol = formatSymbolInput(createForm.crypto_symbol)"
          />
        </el-form-item>
        
        <el-form-item label="备注说明 (可选)" prop="notes">
          <el-input v-model="createForm.notes" type="textarea" placeholder="输入关注理由或预期" rows="3" clearable />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="success" @click="handleCreateWatchlist('dialog', true)" :loading="createLoading" plain>保存并继续添加</el-button>
          <el-button type="primary" @click="handleCreateWatchlist('dialog', false)" :loading="createLoading">确认添加</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Sort, Check, Rank, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { watchlistApi, systemSettingsApi } from '../api'
import { useDarkMode } from '../composables/useDarkMode'
import Sortable from 'sortablejs'
import { formatTimeWithTimezoneSync, getTimezone } from '../utils/timezone'

const router = useRouter()
const { isDarkMode, toggleDarkMode } = useDarkMode()
const loading = ref(false)
const createLoading = ref(false)
const watchlist = ref<any[]>([])
let refreshTimer: ReturnType<typeof setInterval> | null = null
const isSortMode = ref(false)
let sortableInstance: Sortable | null = null
const timezone = ref('Asia/Shanghai')
const sortDialogVisible = ref(false)
const sortEditItem = ref<any>(null)
const sortEditValue = ref(0)

const dialogVisible = ref(false)
const createFormRef = ref<FormInstance>()
const dialogFormRef = ref<FormInstance>()

const createForm = reactive({ crypto_symbol: '', notes: '' })
const createRules: FormRules = {
  crypto_symbol: [{ required: true, message: '请输入交易对或币种名称', trigger: 'blur' }]
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

const loadWatchlist = async (isBackground = false) => {
  if (!isBackground) loading.value = true
  try {
    const response = await watchlistApi.getAll()
    const uniqueData = []
    const seen = new Set()
    for (const item of response.data) {
      if (!seen.has(item.crypto_symbol)) {
        seen.add(item.crypto_symbol)
        uniqueData.push(item)
      }
    }
    watchlist.value = uniqueData
  } catch (error) {
    if (!isBackground) ElMessage.error('加载关注列表失败')
  } finally {
    if (!isBackground) loading.value = false
  }
}

// 🚀 修复点：将其改造为返回配置刷新间隔时间的异步函数
const loadPublicSettings = async (): Promise<number> => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      // console.log('真实接收到的后端刷新频率:', response.data.refresh_interval)
      return response.data.refresh_interval || 5
    }
  } catch (error) {
    console.error('获取系统刷新频率失败，启用默认值', error)
  }
  return 5
}

const handleCreateWatchlist = async (source: 'page' | 'dialog', keepOpen = false) => {
  const targetFormRef = source === 'page' ? createFormRef.value : dialogFormRef.value
  
  if (!targetFormRef) return
  
  // 核心修复 4：提交前再次强制同步覆盖
  createForm.crypto_symbol = formatSymbolInput(createForm.crypto_symbol)

  await targetFormRef.validate(async (valid) => {
    if (valid) {
      createLoading.value = true
      try {
        await watchlistApi.create({
          crypto_symbol: createForm.crypto_symbol, // 直接提取已经同步变大写的字段
          notes: createForm.notes || undefined
        })
        ElMessage.success(`关注项 ${createForm.crypto_symbol} 添加成功`)
        
        // 状态重置
        createForm.crypto_symbol = ''
        createForm.notes = ''
        targetFormRef.resetFields()
        
        // 判断是否需要关闭弹窗
        if (source === 'dialog' && !keepOpen) {
          dialogVisible.value = false
        }
        
        loadWatchlist(true)
      } catch (error) {
        ElMessage.error('添加失败，可能是已存在该关注项')
      } finally {
        createLoading.value = false
      }
    }
  })
}

const handleDialogClose = () => {
  createForm.crypto_symbol = ''
  createForm.notes = ''
  dialogFormRef.value?.resetFields()
}

const handleEditWatchlist = (item: any) => {
  ElMessageBox.prompt('请输入新的备注', '编辑关注项', {
    confirmButtonText: '保存',
    cancelButtonText: '取消',
    inputValue: item.notes || '',
    inputPlaceholder: '请输入备注'
  }).then(async ({ value }) => {
    try {
      await watchlistApi.update(item.id, { notes: value })
      ElMessage.success('更新成功')
      loadWatchlist(true)
    } catch (error) {
      ElMessage.error('更新失败')
    }
  }).catch(() => {})
}

const handleTogglePublic = async (item: any) => {
  try {
    await watchlistApi.update(item.id, { is_public: item.is_public })
    ElMessage.success('已更新')
  } catch (error) {
    ElMessage.error('更新失败')
    item.is_public = !item.is_public
  }
}

const handleDeleteWatchlist = async (item: any) => {
  try {
    await ElMessageBox.confirm(`确定不再关注 ${item.crypto_symbol} 吗？`, '确认操作', {
      confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning'
    })
    await watchlistApi.delete(item.id)
    ElMessage.success('已取消关注')
    loadWatchlist(true)
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('操作失败')
  }
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '-'
  return formatTimeWithTimezoneSync(timeStr, timezone.value, { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

const goToDashboard = () => router.push('/dashboard')

const goToHome = () => router.push('/')

const enterSortMode = () => {
  isSortMode.value = true
  nextTick(() => {
    initSortable()
  })
}

const initSortable = () => {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
  
  const el = document.querySelector('.desktop-view .el-table__body-wrapper tbody') as HTMLElement
  if (el) {
    sortableInstance = Sortable.create(el, {
      animation: 150,
      handle: '.drag-handle',
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      dragClass: 'sortable-drag',
      onEnd: (evt) => {
        const { oldIndex, newIndex } = evt
        if (oldIndex === undefined || newIndex === undefined || oldIndex === newIndex) return
        const item = watchlist.value.splice(oldIndex, 1)[0]
        watchlist.value.splice(newIndex, 0, item)
      }
    })
  }
  
  const mobileEl = document.querySelector('.mobile-view .card-list') as HTMLElement
  if (mobileEl) {
    sortableInstance = Sortable.create(mobileEl, {
      animation: 150,
      handle: '.mobile-sort-handle',
      ghostClass: 'sortable-ghost',
      chosenClass: 'sortable-chosen',
      dragClass: 'sortable-drag',
      onEnd: (evt) => {
        const { oldIndex, newIndex } = evt
        if (oldIndex === undefined || newIndex === undefined || oldIndex === newIndex) return
        const item = watchlist.value.splice(oldIndex, 1)[0]
        watchlist.value.splice(newIndex, 0, item)
      }
    })
  }
}

const saveSortOrder = async () => {
  try {
    const items = watchlist.value.map((item, index) => ({
      id: item.id,
      sort_order: index
    }))
    await watchlistApi.updateSortOrder(items)
    ElMessage.success('排序已保存')
    isSortMode.value = false
    if (sortableInstance) {
      sortableInstance.destroy()
      sortableInstance = null
    }
  } catch (error) {
    ElMessage.error('保存排序失败')
  }
}

const startEditSort = (item: any) => {
  sortEditItem.value = item
  sortEditValue.value = item.sort_order ?? 0
  sortDialogVisible.value = true
}

const handleSortOrderChange = async (_row: any) => {
  try {
    const items = watchlist.value.map((item) => ({
      id: item.id,
      sort_order: item.sort_order ?? 0
    }))
    await watchlistApi.updateSortOrder(items)
  } catch (error) {
    ElMessage.error('保存排序失败')
  }
}

const saveSortEdit = async () => {
  if (!sortEditItem.value) return
  try {
    sortEditItem.value.sort_order = sortEditValue.value
    const items = watchlist.value.map((item) => ({
      id: item.id,
      sort_order: item.sort_order ?? 0
    }))
    await watchlistApi.updateSortOrder(items)
    ElMessage.success('排序已更新')
    sortDialogVisible.value = false
  } catch (error) {
    ElMessage.error('保存排序失败')
  }
}

const cancelSortMode = () => {
  isSortMode.value = false
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
  loadWatchlist(false)
}

const handleDeleteAll = async () => {
  try {
    await ElMessageBox.confirm('确定要删除所有关注项吗？此操作不可恢复。', '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await watchlistApi.deleteAll()
    ElMessage.success('已删除所有关注项')
    loadWatchlist(false)
  } catch (error) {}
}

onMounted(async () => {
  timezone.value = await getTimezone()
  loadWatchlist(false)
  const intervalSeconds = await loadPublicSettings()
  
  refreshTimer = setInterval(() => {
    loadWatchlist(true)
  }, intervalSeconds * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; width: 100%; }
.header-left h1 { margin: 0; font-size: 22px; color: #1f2f3d; font-weight: 600; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.page-main { padding: 20px 25px; max-width: 1400px; margin: 0 auto; width: 100%; }

.form-card { margin-bottom: 20px; border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); }
.table-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); overflow: hidden; }

.symbol-tag { font-weight: bold; font-family: 'Monaco', monospace; }
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; }
.notes-text { color: #5e6d82; }
.time-text { color: #909399; font-size: 13px; }

.sort-mode-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #fff7e6;
  border-bottom: 1px solid #ffe58f;
  color: #d48806;
  font-size: 13px;
  font-weight: 500;
}

.drag-handle {
  cursor: grab;
  font-size: 18px;
  color: #909399;
}

.drag-handle:active {
  cursor: grabbing;
}

:deep(.sort-mode-row) {
  cursor: grab;
}

:deep(.sortable-ghost) {
  opacity: 0.4;
  background: #f0f9ff !important;
}

:deep(.sortable-chosen) {
  background: #ecf5ff !important;
}

:deep(.sortable-drag) {
  opacity: 0.8;
  background: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

@media (min-width: 769px) {
  .desktop-view { display: block; }
  .mobile-view { display: none !important; }
  
  :deep(.el-table th.el-table__cell) { background-color: #fafafa; color: #606266; font-weight: 600; height: 50px; }
  
  .form-responsive-row { display: flex; gap: 24px; align-items: flex-end; }
  .flex-item { flex: 1; margin-bottom: 0; }
  .flex-btn { width: 140px; margin-bottom: 0; }
}

@media (max-width: 768px) {
  .desktop-view { display: none !important; }
  .mobile-view { display: block; }
  
  .page-container { padding-bottom: 80px; }
  .page-main { padding: 12px; }
  
  /* 1. 顶部容器改为相对定位，打断原有的 Flex 弹性流 */
  .page-header { padding: 15px; position: relative; }
  .header-content { display: block; }
  
  /* 2. 左侧标题区限制宽度，防止文字挤占右侧按钮空间 */
  .header-left { width: calc(100% - 50px); margin-bottom: 12px; }
  .header-left h1 { font-size: 18px; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  /* 恢复副标题显示，并强制单行超出显示省略号 */
  .header-left p { display: block; font-size: 12px; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  
  /* 3. 剥离暗黑模式按钮，使用绝对定位固定在右上角 */
  .header-right { display: block; width: 100%; }
  .dark-mode-btn { position: absolute; top: 15px; right: 15px; font-size: 16px; width: 36px; height: 36px; padding: 0; display: inline-flex; align-items: center; justify-content: center; z-index: 10; }

  /* 4. 按钮组重构为 CSS Grid 网格布局，强制一行三列 */
  :deep(.action-buttons) { display: grid !important; grid-template-columns: repeat(3, 1fr) !important; gap: 8px !important; width: 100%; }
  /* 抹除 Element Plus 按钮组默认的清除浮动伪元素，防止高度塌陷或间距异常 */
  :deep(.action-buttons::before), :deep(.action-buttons::after) { display: none !important; }
  /* 重置子按钮：清除浮动、独立赋予圆角、缩小字号以适应三列排版 */
  :deep(.action-buttons .el-button) { width: 100% !important; margin: 0 !important; border-radius: 6px !important; float: none !important; justify-content: center; padding: 8px 0 !important; font-size: 12px !important; height: auto !important; }
  .form-responsive-row { display: flex; flex-direction: column; gap: 0; }
  .flex-item { margin-bottom: 16px; }
  .flex-btn { margin-bottom: 4px; }

  .card-list { display: flex; flex-direction: column; gap: 12px; }
  .mobile-data-card { 
    border-radius: 12px; 
    border: none; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.03); 
    transition: transform 0.2s ease;
  }
  .mobile-data-card:active { transform: scale(0.98); }
  :deep(.mobile-data-card .el-card__body) { padding: 16px; }
  
  .card-header-row { display: flex; justify-content: space-between; align-items: center; }
  .coin-info { display: flex; align-items: center; gap: 10px; }
  .coin-name { font-weight: 600; font-size: 15px; color: #303133; }
  .price-highlight { font-size: 18px; font-weight: 700; color: #409eff; font-family: 'Monaco', monospace; }
  
  .compact-divider { margin: 14px 0; border-color: #ebeef5; opacity: 0.6; }
  
  .notes-box { background: #f8f9fa; padding: 10px 12px; border-radius: 6px; font-size: 13px; margin-bottom: 12px; color: #5e6d82; line-height: 1.4; }
  .notes-label { color: #909399; font-weight: 500; }
  .time-box { font-size: 12px; color: #a8abb2; text-align: right; }
  
  .card-footer { display: flex; gap: 12px; margin-top: 6px; }
  .card-footer .el-button { border-radius: 6px; }

  :deep(.responsive-dialog) {
    width: 95% !important;
    max-width: 400px;
    margin: 10vh auto !important;
    border-radius: 12px;
  }
  :deep(.dialog-footer) {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }
  :deep(.dialog-footer .el-button) {
    flex: 1 1 100%;
    margin-left: 0 !important;
  }
  
  .mobile-sort-handle {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 8px;
    background: #fff7e6;
    border-radius: 8px 8px 0 0;
    color: #d48806;
    font-size: 20px;
    cursor: grab;
  }
  
  .header-right-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  
  .sort-order-mini {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    padding: 3px 8px;
    background: #f0f5ff;
    border: 1px solid #adc6ff;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .sort-order-mini:active {
    background: #d6e4ff;
    transform: scale(0.95);
  }
  
  .sort-order-mini .sort-icon {
    font-size: 13px;
    color: #597ef7;
  }
  
  .sort-order-mini .sort-num {
    font-size: 13px;
    font-weight: 600;
    color: #597ef7;
    font-family: 'Monaco', monospace;
    min-width: 12px;
    text-align: center;
  }
  
  .sort-dialog-content {
    padding: 8px 0;
  }
  
  .sort-dialog-coin {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
  }
  
  .sort-dialog-name {
    font-size: 14px;
    color: #606266;
  }
  
  .sort-dialog-input {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .sort-dialog-label {
    font-size: 14px;
    color: #606266;
  }
  
  .sort-dialog-number {
    width: 120px;
  }
  
  .public-toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px dashed #ebeef5;
    margin-bottom: 8px;
  }
  
  .public-toggle-label {
    font-size: 13px;
    color: #606266;
    font-weight: 500;
  }
  
  .card-list.sort-mode {
    cursor: default;
  }
  
  .draggable-card {
    cursor: grab;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .draggable-card:active {
    cursor: grabbing;
  }
}

/* 夜间模式 */
.page-container.dark-mode { background-color: #0f0f1a; }
.page-container.dark-mode .page-header { background: #1a1a2e; border-bottom-color: #2a2a3e; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.page-container.dark-mode .header-left h1 { color: #60a5fa; }
.page-container.dark-mode .header-left p { color: #8080a0; }
.page-container.dark-mode .form-card { background: #1a1a2e; border: none; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
.page-container.dark-mode .card-header { color: #d0d0e0; }
.page-container.dark-mode :deep(.el-card__header) { background: #1a1a2e; border-bottom-color: #2a2a3e; }
.page-container.dark-mode :deep(.el-card__body) { background: #1a1a2e; }
.page-container.dark-mode :deep(.el-table) { background: #1a1a2e; color: #d0d0e0; }
.page-container.dark-mode :deep(.el-table td), .page-container.dark-mode :deep(.el-table th.is-leaf) { background: #1a1a2e; border-color: #2a2a3e; color: #d0d0e0; }
.page-container.dark-mode :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background: #16162a; }
.page-container.dark-mode :deep(.el-input__wrapper) { background: #16162a; }
.page-container.dark-mode :deep(.el-select .el-input__wrapper) { background: #16162a; }
.page-container.dark-mode .draggable-card { background: #16162a; border-color: #2a2a3e; }
.page-container.dark-mode .draggable-card:hover { background: #1e1e36; }
</style>