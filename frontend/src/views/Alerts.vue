<template>
  <div class="page-container" :class="{ 'dark-mode': isDarkMode }">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>预警管理</h1>
          <p>设定价格阈值，捕捉市场每一次关键异动</p>
        </div>
        <div class="header-right">
          <el-button @click="toggleDarkMode" class="dark-mode-btn" :type="isDarkMode ? 'warning' : 'default'" plain>
            {{ isDarkMode ? '☀️' : '🌙' }}
          </el-button>
          <el-button-group class="action-buttons">
            <el-button @click="goToDashboard">返回面板</el-button>
            <el-button @click="goToHome">返回主页</el-button>
            <el-button @click="() => loadAlerts(false)" :loading="loading">刷新状态</el-button>
            <el-button v-if="!isSortMode" type="warning" :icon="Sort" @click="enterSortMode">排序模式</el-button>
            <template v-else>
              <el-button type="success" :icon="Check" @click="saveSortOrder">保存排序</el-button>
              <el-button @click="cancelSortMode">取消</el-button>
            </template>
            <el-button type="danger" :icon="Delete" @click="handleDeleteAll">全部删除</el-button>
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
              <el-input 
                v-model="inlineForm.crypto_symbol" 
                placeholder="输入监控币种" 
                clearable 
                @change="inlineForm.crypto_symbol = formatSymbolInput(inlineForm.crypto_symbol)"
              />
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
            
            <el-form-item :label="['above', 'below'].includes(inlineForm.alert_type) ? '目标价格 ($)' : '触发阈值 (%)'" prop="threshold_price" class="flex-item-medium">
              <el-input-number v-model="inlineForm.threshold_price" :precision="['above', 'below'].includes(inlineForm.alert_type) ? 4 : 2" :min="0" :controls="false" style="width: 100%" :placeholder="['above', 'below'].includes(inlineForm.alert_type) ? '目标触发价' : '填入百分比，如 5'" />
            </el-form-item>
            
            <el-form-item label="通知渠道" class="flex-item-medium">
              <el-select v-model="inlineForm.notification_channel" placeholder="默认" clearable style="width: 100%" @change="inlineForm.notification_group = ''">
                <el-option label="使用默认" value="" />
                <el-option v-for="ch in channels" :key="ch.name" :label="ch.name" :value="ch.name" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="通知频道" class="flex-item-medium">
              <el-select v-model="inlineForm.notification_group" :placeholder="inlineForm.notification_channel ? '默认频道' : '使用默认'" clearable style="width: 100%">
                <el-option label="使用默认" value="" />
                <el-option v-for="g in (channels.find(c => c.name === inlineForm.notification_channel)?.groups || [])" :key="g" :label="g" :value="g" />
              </el-select>
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
            <div v-if="isSortMode" class="sort-mode-hint">
              <el-icon><Rank /></el-icon>
              <span>拖拽行调整顺序，完成后点击"保存排序"</span>
            </div>
            <el-table 
              :data="alerts" 
              stripe 
              hover 
              style="width: 100%"
              :row-class-name="sortModeRowClass"
            >
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
              <el-table-column label="交易对" min-width="110">
                <template #default="{ row }">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ row._symbol }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="币种名称" min-width="110">
                <template #default="{ row }">
                  <span style="color: #606266; font-weight: 500;">{{ row.crypto_name }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="当前价格" min-width="110" align="right">
                <template #default="{ row }">
                  <span class="price-text">${{ formatNum(row._cp, 4) }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="触发条件" min-width="130" align="right">
                <template #default="{ row }">
                  <span class="condition-group">
                    <span :class="getConditionText(row).class">{{ getConditionText(row).text }}</span>
                    <b class="price-target">{{ getConditionText(row).val }}</b>
                  </span>
                </template>
              </el-table-column>
              
              <el-table-column label="持续" min-width="70" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.is_continuous ? 'success' : 'info'" size="small">{{ row.is_continuous ? '是' : '否' }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column label="进度" min-width="80" align="center">
                <template #default="{ row }">
                  <span>{{ row.notified_count }} / {{ row.max_notifications }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="间隔" min-width="70" align="center">
                <template #default="{ row }">
                  <span>{{ row.interval_minutes }}m</span>
                </template>
              </el-table-column>
              
              <el-table-column label="创建时间" min-width="150">
                <template #default="{ row }">
                  <span class="time-text">{{ row.created_at ? formatTime(row.created_at) : '-' }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="最后触发" min-width="150">
                <template #default="{ row }">
                  <span class="time-text">{{ row.last_triggered_at ? formatTime(row.last_triggered_at) : '等待触发...' }}</span>
                </template>
              </el-table-column>
              
              <el-table-column label="运行状态" min-width="110" align="center" fixed="right">
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
              
              <el-table-column label="操作" width="140" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button size="small" type="primary" plain @click="openEditDialog(row)">编辑</el-button>
                  <el-button size="small" type="danger" plain @click="handleDeleteAlert(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="alerts.length === 0" description="暂无预警规则，请在上方快捷创建" />
          </el-card>
        </div>

        <div class="mobile-view">
          <el-empty v-if="alerts.length === 0" description="暂无预警规则，请在上方创建" />
          <div v-else class="card-list" :class="{ 'sort-mode': isSortMode }">
            <el-card v-for="item in alerts" :key="item.id" shadow="hover" :class="['mobile-data-card', !item.is_active && 'card-inactive', isSortMode && 'draggable-card']">
              <div v-if="isSortMode" class="mobile-sort-handle">
                <el-icon><Rank /></el-icon>
              </div>
              <div class="card-header-row">
                <div class="coin-info">
                  <el-tag effect="dark" round class="symbol-tag">{{ item._symbol }}</el-tag>
                  <span style="font-size: 13px; color: #909399; margin-left: 6px;">{{ item.crypto_name }}</span>
                </div>
                <div class="header-right-group">
                  <span class="sort-order-mini" @click.stop="startEditSort(item)">
                    <el-icon class="sort-icon"><Rank /></el-icon>
                    <span class="sort-num">{{ item.sort_order ?? 0 }}</span>
                  </span>
                  <div class="status-indicator" @click="handleToggleActiveMobile(item)">
                    <span :class="['status-dot', item.is_active ? 'dot-active' : 'dot-inactive']"></span>
                    <span class="status-text">{{ item.is_active ? '监控中' : '已停用' }}</span>
                  </div>
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
                      <span :class="getConditionText(item).class" style="font-size: 14px; margin-right: 4px;">
                        {{ getConditionText(item).text }}
                      </span>
                      <span class="price-target" style="font-size: 16px;">{{ getConditionText(item).val }}</span>
                    </span>
                  </div>
                </div>
                
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">持续预警:</span>
                    <span class="detail-value">{{ item.is_continuous ? '是' : '否' }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">间隔频率:</span>
                    <span class="detail-value">{{ item.interval_minutes }}分钟</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">推送进度:</span>
                    <span class="detail-value">{{ item.notified_count }} / {{ item.max_notifications }}次</span>
                  </div>
                </div>
                
                <div class="trigger-info">
                  <span class="trigger-label">创建时间:</span>
                  <span class="trigger-time">{{ item.created_at ? formatTime(item.created_at) : '-' }}</span>
                </div>
                <div class="trigger-info" style="margin-top: 4px;">
                  <span class="trigger-label">最后触发:</span>
                  <span class="trigger-time">{{ item.last_triggered_at ? formatTime(item.last_triggered_at) : '等待触发...' }}</span>
                </div>
              </div>

              <el-divider class="compact-divider" />

              <div class="card-footer">
                <el-button size="default" type="primary" plain @click="openEditDialog(item)" style="flex:1">编辑</el-button>
                <el-button size="default" :type="item.is_active ? 'warning' : 'success'" plain @click="handleToggleActiveMobile(item)" style="flex:1">
                  {{ item.is_active ? '暂停' : '启动' }}
                </el-button>
                <el-button size="default" type="danger" plain @click="handleDeleteAlert(item)" style="flex:1">删除</el-button>
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
              <el-tag effect="dark" round size="small">{{ sortEditItem?._symbol }}</el-tag>
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
      title="创建新预警 (弹窗模式)"
      class="responsive-dialog"
      @close="handleDialogClose"
    >
      <el-form :model="dialogForm" :rules="formRules" ref="dialogFormRef" label-position="top">
        <el-form-item label="交易对 (容错: 填 eth 自动转 ETHUSDT)" prop="crypto_symbol">
          <el-input 
            v-model="dialogForm.crypto_symbol" 
            placeholder="输入要监控的交易对" 
            clearable 
            @change="dialogForm.crypto_symbol = formatSymbolInput(dialogForm.crypto_symbol)"
          />
        </el-form-item>
        
        <div class="form-row-2">
          <el-form-item label="触发条件" prop="alert_type">
            <el-select v-model="dialogForm.alert_type" style="width: 100%">
              <el-option label="价格高于 ↑" value="above" />
              <el-option label="价格低于 ↓" value="below" />
              <el-option label="振幅预警 ↕" value="amplitude" />
              <el-option label="涨幅百分比 ↗" value="percent_up" />
              <el-option label="跌幅百分比 ↘" value="percent_down" />
            </el-select>
          </el-form-item>
          <el-form-item :label="['above', 'below'].includes(dialogForm.alert_type) ? '目标价格 ($)' : '触发阈值 (%)'" prop="threshold_price">
            <el-input-number v-model="dialogForm.threshold_price" :precision="['above', 'below'].includes(dialogForm.alert_type) ? 4 : 2" :min="0" :controls="false" style="width: 100%" />
          </el-form-item>
        </div>

        <div class="form-row-2">
          <el-form-item label="持续预警">
            <el-switch v-model="dialogForm.is_continuous" active-text="是" inactive-text="否" />
          </el-form-item>
          <el-form-item label="通知次数">
            <el-input-number v-model="dialogForm.max_notifications" :min="1" :max="100" style="width: 100%" />
          </el-form-item>
        </div>

        <div class="form-row-2">
          <el-form-item label="间隔(分钟)">
            <el-input-number v-model="dialogForm.interval_minutes" :min="1" :max="1440" style="width: 100%" />
          </el-form-item>
          <el-form-item label="通知渠道">
            <el-select v-model="dialogForm.notification_channel" placeholder="默认" clearable style="width: 100%" @change="dialogForm.notification_group = ''">
              <el-option label="使用默认" value="" />
              <el-option v-for="ch in channels" :key="ch.name" :label="ch.name" :value="ch.name" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="通知频道">
          <el-select v-model="dialogForm.notification_group" :placeholder="dialogForm.notification_channel ? '默认频道' : '使用默认'" clearable style="width: 100%">
            <el-option label="使用默认" value="" />
            <el-option v-for="g in (channels.find(c => c.name === dialogForm.notification_channel)?.groups || [])" :key="g" :label="g" :value="g" />
          </el-select>
        </el-form-item>
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

    <el-dialog
      v-model="editDialogVisible"
      title="修改预警规则"
      class="responsive-dialog"
    >
      <el-form :model="editForm" :rules="formRules" ref="editFormRef" label-position="top">
        <el-form-item label="交易对 (锁定)">
          <el-input v-model="editForm.crypto_symbol" disabled />
        </el-form-item>
        
        <el-form-item label="触发条件" prop="alert_type">
          <el-select v-model="editForm.alert_type" style="width: 100%">
            <el-option label="价格高于 ↑" value="above" />
            <el-option label="价格低于 ↓" value="below" />
            <el-option label="振幅预警 ↕" value="amplitude" />
            <el-option label="涨幅百分比 ↗" value="percent_up" />
            <el-option label="跌幅百分比 ↘" value="percent_down" />
          </el-select>
        </el-form-item>
        
        <div class="form-row-2">
          <el-form-item label="持续预警">
            <el-switch v-model="editForm.is_continuous" active-text="是" inactive-text="否" />
          </el-form-item>
          <el-form-item label="通知次数">
            <el-input-number v-model="editForm.max_notifications" :min="1" :max="100" style="width: 100%" />
          </el-form-item>
        </div>

        <div class="form-row-2">
          <el-form-item label="间隔(分钟)">
            <el-input-number v-model="editForm.interval_minutes" :min="1" :max="1440" style="width: 100%" />
          </el-form-item>
          <el-form-item :label="['above', 'below'].includes(editForm.alert_type) ? '目标价格 ($)' : '触发阈值 (%)'" prop="threshold_price">
            <el-input-number v-model="editForm.threshold_price" :precision="['above', 'below'].includes(editForm.alert_type) ? 4 : 2" :min="0" :controls="false" style="width: 100%" />
          </el-form-item>
        </div>
        
        <div class="form-row-2">
          <el-form-item label="通知渠道">
            <el-select v-model="editForm.notification_channel" placeholder="默认" clearable style="width: 100%" @change="editForm.notification_group = ''">
              <el-option label="使用默认" value="" />
              <el-option v-for="ch in channels" :key="ch.name" :label="ch.name" :value="ch.name" />
            </el-select>
          </el-form-item>
          <el-form-item label="通知频道">
            <el-select v-model="editForm.notification_group" :placeholder="editForm.notification_channel ? '默认频道' : '使用默认'" clearable style="width: 100%">
              <el-option label="使用默认" value="" />
              <el-option v-for="g in (channels.find(c => c.name === editForm.notification_channel)?.groups || [])" :key="g" :label="g" :value="g" />
            </el-select>
          </el-form-item>
        </div>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEditForm" :loading="submitLoading">
            保存修改并重置状态
          </el-button>
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
import { alertsApi, systemSettingsApi, notificationChannelsApi } from '../api'
import { useDarkMode } from '../composables/useDarkMode'
import Sortable from 'sortablejs'
import { formatTimeWithTimezoneSync, getTimezone } from '../utils/timezone'

const router = useRouter()
const { isDarkMode, toggleDarkMode } = useDarkMode()
const loading = ref(false)
const submitLoading = ref(false)
const alerts = ref<any[]>([])
let refreshTimer: ReturnType<typeof setInterval> | null = null
const isSortMode = ref(false)
let sortableInstance: Sortable | null = null
const timezone = ref('Asia/Shanghai')
const sortDialogVisible = ref(false)
const sortEditItem = ref<any>(null)
const sortEditValue = ref(0)
const channels = ref<{ name: string; groups: string[]; default_group: string }[]>([])

const inlineFormRef = ref<FormInstance>()
const dialogFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

type AlertType = 'above' | 'below' | 'amplitude' | 'percent_up' | 'percent_down'

const inlineForm = reactive({ 
  crypto_symbol: '', 
  alert_type: 'above' as AlertType, 
  threshold_price: undefined as number|undefined,
  is_continuous: false,
  max_notifications: 1,
  interval_minutes: 5,
  notification_channel: '',
  notification_group: ''
})

const dialogForm = reactive({ 
  crypto_symbol: '', 
  alert_type: 'above' as 'above'|'below'|'amplitude'|'percent_up'|'percent_down', 
  threshold_price: undefined as number|undefined,
  is_continuous: false,
  max_notifications: 1,
  interval_minutes: 5,
  notification_channel: '',
  notification_group: ''
})

const editForm = reactive({
  id: 0,
  crypto_symbol: '',
  alert_type: 'above' as 'above'|'below'|'amplitude'|'percent_up'|'percent_down',
  threshold_price: 0 as number,
  is_continuous: false,
  max_notifications: 1,
  interval_minutes: 5,
  notification_channel: '',
  notification_group: ''
})

const dialogVisible = ref(false)
const editDialogVisible = ref(false)

const formRules: FormRules = {
  crypto_symbol: [{ required: true, message: '请输入交易对', trigger: 'blur' }],
  threshold_price: [{ required: true, message: '请输入目标触发数据', trigger: 'blur' }]
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

const getConditionText = (row: any) => {
  const type = row.alert_type
  const val = row.threshold_value !== null ? row.threshold_value : row.threshold_price
  if (type === 'above') return { text: '高于 ↑', val: `$${formatNum(val, 4)}`, class: 'text-up' }
  if (type === 'below') return { text: '低于 ↓', val: `$${formatNum(val, 4)}`, class: 'text-down' }
  if (type === 'amplitude') return { text: '振幅 ↕', val: `${formatNum(val, 2)}%`, class: 'text-amplitude' }
  if (type === 'percent_up') return { text: '涨幅 ↗', val: `${formatNum(val, 2)}%`, class: 'text-up' }
  if (type === 'percent_down') return { text: '跌幅 ↘', val: `${formatNum(val, 2)}%`, class: 'text-down' }
  return { text: '未知', val: String(val), class: '' }
}

const loadAlerts = async (isBackground = false) => {
  if (!isBackground) loading.value = true
  try {
    const response = await alertsApi.getAll()
    alerts.value = response.data.map((alert: any) => {
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

const submitInlineForm = async () => {
  if (!inlineFormRef.value) return
  // 核心修复 4：提交前再次强制同步覆盖
  inlineForm.crypto_symbol = formatSymbolInput(inlineForm.crypto_symbol)
  
  await inlineFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        await alertsApi.create({
          crypto_symbol: inlineForm.crypto_symbol,
          alert_type: inlineForm.alert_type,
          threshold_price: Number(inlineForm.threshold_price),
          is_continuous: inlineForm.is_continuous,
          max_notifications: Number(inlineForm.max_notifications),
          interval_minutes: Number(inlineForm.interval_minutes),
          notification_channel: inlineForm.notification_channel || undefined,
          notification_group: inlineForm.notification_group || undefined
        })
        ElMessage.success(`预警创建成功: ${inlineForm.crypto_symbol}`)
        
        inlineForm.crypto_symbol = ''
        inlineForm.threshold_price = undefined
        inlineForm.is_continuous = false
        inlineForm.max_notifications = 1
        inlineForm.interval_minutes = 5
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

const submitDialogForm = async (keepOpen = false) => {
  if (!dialogFormRef.value) return
  // 强制同步
  dialogForm.crypto_symbol = formatSymbolInput(dialogForm.crypto_symbol)

  await dialogFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        await alertsApi.create({
          crypto_symbol: dialogForm.crypto_symbol,
          alert_type: dialogForm.alert_type,
          threshold_price: Number(dialogForm.threshold_price),
          is_continuous: dialogForm.is_continuous,
          max_notifications: Number(dialogForm.max_notifications),
          interval_minutes: Number(dialogForm.interval_minutes),
          notification_channel: dialogForm.notification_channel || undefined,
          notification_group: dialogForm.notification_group || undefined
        })
        ElMessage.success(`预警创建成功: ${dialogForm.crypto_symbol}`)
        
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

const openEditDialog = (row: any) => {
  editForm.id = row.id
  editForm.crypto_symbol = row._symbol
  editForm.alert_type = row.alert_type
  editForm.threshold_price = row.threshold_value !== null ? row.threshold_value : row.threshold_price
  editForm.is_continuous = row.is_continuous
  editForm.max_notifications = row.max_notifications
  editForm.interval_minutes = row.interval_minutes
  editForm.notification_channel = row.notification_channel || ''
  editForm.notification_group = row.notification_group || ''
  editDialogVisible.value = true
}

const submitEditForm = async () => {
  if (!editFormRef.value) return
  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        await alertsApi.update(editForm.id, {
          alert_type: editForm.alert_type,
          threshold_price: Number(editForm.threshold_price),
          is_continuous: editForm.is_continuous,
          max_notifications: Number(editForm.max_notifications),
          interval_minutes: Number(editForm.interval_minutes),
          is_active: true,
          notification_channel: editForm.notification_channel || undefined,
          notification_group: editForm.notification_group || undefined
        })
        ElMessage.success('预警规则已更新并重新激活')
        editDialogVisible.value = false
        loadAlerts(true)
      } catch (error: any) {
        ElMessage.error('修改失败')
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const openAddDialog = () => {
  dialogForm.crypto_symbol = ''
  dialogForm.threshold_price = undefined
  dialogForm.notification_channel = ''
  dialogForm.notification_group = ''
  setTimeout(() => dialogFormRef.value?.clearValidate(), 0)
  dialogVisible.value = true
}

const handleDialogClose = () => {
  dialogFormRef.value?.resetFields()
}

const handleToggleActive = async (alert: any) => {
  const newState = alert.is_active 
  try {
    await alertsApi.update(alert.id, { is_active: newState })
    ElMessage.success(`引擎已${newState ? '重置并激活' : '暂停'}`)
    loadAlerts(true) 
  } catch (error) {
    alert.is_active = !newState
    ElMessage.error('状态更新失败')
  }
}

const handleToggleActiveMobile = async (alert: any) => {
  alert.is_active = !alert.is_active
  await handleToggleActive(alert)
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
  return formatTimeWithTimezoneSync(timeStr, timezone.value, { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
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
        const item = alerts.value.splice(oldIndex, 1)[0]
        alerts.value.splice(newIndex, 0, item)
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
        const item = alerts.value.splice(oldIndex, 1)[0]
        alerts.value.splice(newIndex, 0, item)
      }
    })
  }
}

const saveSortOrder = async () => {
  try {
    const items = alerts.value.map((item, index) => ({
      id: item.id,
      sort_order: index
    }))
    await alertsApi.updateSortOrder(items)
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
    const items = alerts.value.map((item) => ({
      id: item.id,
      sort_order: item.sort_order ?? 0
    }))
    await alertsApi.updateSortOrder(items)
  } catch (error) {
    ElMessage.error('保存排序失败')
  }
}

const saveSortEdit = async () => {
  if (!sortEditItem.value) return
  try {
    sortEditItem.value.sort_order = sortEditValue.value
    const items = alerts.value.map((item) => ({
      id: item.id,
      sort_order: item.sort_order ?? 0
    }))
    await alertsApi.updateSortOrder(items)
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
  loadAlerts(false)
}

const handleDeleteAll = async () => {
  try {
    await ElMessageBox.confirm('确定要删除所有预警规则吗？此操作不可恢复。', '警告', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await alertsApi.deleteAll()
    ElMessage.success('已删除所有预警规则')
    loadAlerts(false)
  } catch (error) {}
}

const sortModeRowClass = (_: { row: any; rowIndex: number }) => {
  return isSortMode.value ? 'sort-mode-row' : ''
}

onMounted(async () => {
  // 先加载时区配置
  timezone.value = await getTimezone()
  
  // 加载通知渠道列表
  try {
    const resp = await notificationChannelsApi.getAll()
    channels.value = resp.data || []
  } catch (error) {}
  
  // 再调用你的基础拉取方法
  loadAlerts(false) 

  // 拉取配置时间
  const intervalSeconds = await loadPublicSettings()

  // 启动计时器
  refreshTimer = setInterval(() => {
    loadAlerts(true)
  }, intervalSeconds * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
/* 1. 基础容器与公共排版 */
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; width: 100%; }
.header-left h1 { margin: 0; font-size: 22px; color: #1f2f3d; font-weight: 600; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.page-main { padding: 20px 25px; max-width: 1400px; margin: 0 auto; width: 100%; }

/* 2. 组件卡片与业务特有字体 */
.form-card { margin-bottom: 20px; border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); }
.table-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); overflow: hidden; }

.symbol-tag { font-weight: bold; font-family: 'Monaco', monospace; }
.text-up { color: #f56c6c; font-weight: bold; }
.text-down { color: #67c23a; font-weight: bold; }
.text-amplitude { color: #e6a23c; font-weight: bold; }
.price-target { color: #1f2f3d; font-size: 16px; font-family: 'Monaco', monospace; margin-left: 5px; }
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; }
.condition-group { display: flex; align-items: center; justify-content: flex-end; }
.time-text { color: #909399; font-size: 13px; }

/* 3. 排序模式专有样式 */
.sort-mode-hint { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: #fff7e6; border-bottom: 1px solid #ffe58f; color: #d48806; font-size: 13px; font-weight: 500; }
.drag-handle { cursor: grab; font-size: 18px; color: #909399; }
.drag-handle:active { cursor: grabbing; }
:deep(.sort-mode-row) { cursor: grab; }
:deep(.sortable-ghost) { opacity: 0.4; background: #f0f9ff !important; }
:deep(.sortable-chosen) { background: #ecf5ff !important; }
:deep(.sortable-drag) { opacity: 0.8; background: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }

/* 4. 桌面端视图 (> 768px) */
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

/* 5. 移动端视图 (全局唯一定义 <= 768px) */
@media (max-width: 768px) {
  .desktop-view { display: none !important; }
  .mobile-view { display: block; }
  .page-container { padding-bottom: 80px; }
  .page-main { padding: 12px; }

  /* 标准化导航栏 */
  .page-header { padding: 15px; position: relative; }
  .header-content { display: block; }
  .header-left { width: calc(100% - 50px); margin-bottom: 12px; }
  .header-left h1 { font-size: 18px; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .header-left p { display: block; font-size: 12px; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .header-right { display: block; width: 100%; }
  .dark-mode-btn { position: absolute; top: 15px; right: 15px; font-size: 16px; width: 36px; height: 36px; padding: 0; display: inline-flex; align-items: center; justify-content: center; z-index: 10; }
  
  /* 标准化两行三列导航区 */
  :deep(.action-buttons) { display: grid !important; grid-template-columns: repeat(3, 1fr) !important; gap: 8px !important; width: 100%; }
  :deep(.action-buttons::before), :deep(.action-buttons::after) { display: none !important; }
  :deep(.action-buttons .el-button) { width: 100% !important; margin: 0 !important; border-radius: 6px !important; float: none !important; justify-content: center; padding: 8px 0 !important; font-size: 12px !important; height: auto !important; }

  /* 表单折叠排版 */
  .form-responsive-row { display: flex; flex-direction: column; gap: 0; }
  .flex-item-large, .flex-item-medium, .flex-item-small { margin-bottom: 16px; }
  .flex-btn { margin-bottom: 4px; }
  .form-row-2 { display: flex; flex-direction: column; gap: 0; }

  /* 预警业务卡片排版 */
  .card-list { display: flex; flex-direction: column; gap: 12px; }
  .mobile-data-card { border-radius: 12px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.03); transition: all 0.3s ease; }
  .card-inactive { opacity: 0.6; filter: grayscale(50%); }
  :deep(.mobile-data-card .el-card__body) { padding: 16px; }
  .card-header-row { display: flex; justify-content: space-between; align-items: center; }
  
  .status-indicator { display: flex; align-items: center; gap: 6px; background: #f4f4f5; padding: 4px 10px; border-radius: 20px; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; }
  .dot-active { background-color: #13ce66; box-shadow: 0 0 4px #13ce66; }
  .dot-inactive { background-color: #909399; }
  .status-text { font-size: 12px; color: #606266; font-weight: 500; }
  
  .compact-divider { margin: 14px 0; border-color: #ebeef5; opacity: 0.6; }
  
  .price-compare-box { background: #f8f9fa; border-radius: 8px; border: 1px solid #f0f2f5; display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; margin-bottom: 12px; }
  .price-item { display: flex; flex-direction: column; gap: 4px; }
  .price-label { font-size: 12px; color: #909399; }
  .price-value { font-size: 18px; font-weight: bold; font-family: 'Monaco', monospace; display: flex; align-items: center;}
  .price-divider { width: 1px; height: 30px; background-color: #ebeef5; margin: 0 10px; }
  
  .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; background: #fff; border-radius: 8px; }
  .detail-item { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; border-bottom: 1px dashed #f0f2f5;}
  .detail-label { color: #909399; }
  .detail-value { color: #303133; font-weight: 500; }
  
  .trigger-info { font-size: 12px; display: flex; justify-content: space-between; align-items: center; }
  .trigger-label { color: #a8abb2; }
  .trigger-time { color: #606266; font-weight: 500; }
  
  .card-footer { display: flex; gap: 8px; margin-top: 6px; }
  .card-footer .el-button { border-radius: 6px; padding: 8px; }
  
  :deep(.responsive-dialog) { width: 95% !important; max-width: 400px; margin: 5vh auto !important; border-radius: 12px; }
  :deep(.dialog-footer) { display: flex; flex-wrap: wrap; gap: 10px; }
  :deep(.dialog-footer .el-button) { flex: 1 1 100%; margin-left: 0 !important; }

  /* 移动端排序样式 */
  .mobile-sort-handle { display: flex; justify-content: center; align-items: center; padding: 8px; background: #fff7e6; border-radius: 8px 8px 0 0; color: #d48806; font-size: 20px; cursor: grab; }
  .header-right-group { display: flex; align-items: center; gap: 6px; }
  .sort-order-mini { display: inline-flex; align-items: center; gap: 3px; padding: 3px 8px; background: #f0f5ff; border: 1px solid #adc6ff; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
  .sort-order-mini:active { background: #d6e4ff; transform: scale(0.95); }
  .sort-order-mini .sort-icon { font-size: 13px; color: #597ef7; }
  .sort-order-mini .sort-num { font-size: 13px; font-weight: 600; color: #597ef7; font-family: 'Monaco', monospace; min-width: 12px; text-align: center; }
  .sort-dialog-content { padding: 8px 0; }
  .sort-dialog-coin { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; }
  .sort-dialog-name { font-size: 14px; color: #606266; }
  .sort-dialog-input { display: flex; align-items: center; justify-content: space-between; }
  .sort-dialog-label { font-size: 14px; color: #606266; }
  .sort-dialog-number { width: 120px; }
  .card-list.sort-mode { cursor: default; }
  .draggable-card { cursor: grab; transition: transform 0.2s, box-shadow 0.2s; }
  .draggable-card:active { cursor: grabbing; }
}

/* 6. 夜间模式 (统一管理) */
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
.page-container.dark-mode :deep(.el-input__wrapper), .page-container.dark-mode :deep(.el-select .el-input__wrapper) { background: #16162a; }
.page-container.dark-mode .draggable-card { background: #16162a; border-color: #2a2a3e; }
.page-container.dark-mode .draggable-card:hover { background: #1e1e36; }
.page-container.dark-mode .alert-status-active { background: rgba(103,194,58,0.15); color: #67c23a; }
.page-container.dark-mode .alert-status-triggered { background: rgba(245,108,108,0.15); color: #f56c6c; }
</style>