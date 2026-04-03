<template>
  <div class="page-container" :class="{ 'dark-mode': isDarkMode }">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>{{ siteTitle }}</h1>
          <p>欢迎回来，{{ authStore.user?.username || 'Jack' }}</p>
        </div>
        <div class="header-right">
          <el-button @click="toggleDarkMode" class="dark-mode-btn" :type="isDarkMode ? 'warning' : 'default'" plain>
            {{ isDarkMode ? '☀️' : '🌙' }}
          </el-button>
          <el-button-group class="action-buttons">
            <el-button @click="goToHome">返回主页</el-button>
            <el-button type="primary" @click="goToAlerts" plain>预警管理</el-button>
            <el-button type="success" @click="goToAssets" plain>资产管理</el-button>
            <el-button type="info" @click="goToWatchlist" plain>关注列表</el-button>
            <el-button type="warning" @click="goToSettings" plain>系统设置</el-button>
            <el-button type="danger" @click="handleLogout">退出登录</el-button>
          </el-button-group>
        </div>
      </div>
    </el-header>
      
    <el-main class="page-main">
      <el-row :gutter="20" class="top-dashboard-row">
        
        <el-col :xs="24" :md="8" class="chart-col">
          <el-card class="content-card chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">📊 资产配置</span>
              </div>
            </template>
            <div class="chart-container-small">
              <v-chart :option="allocationChartOption" autoresize />
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :md="16">
          <el-row :gutter="20">
            <el-col :xs="12" :sm="12" :md="12">
              <el-card class="stat-card" shadow="hover">
                <div class="stat-content">
                  <div class="stat-number">${{ dashboardData.total_value?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) || '0.00' }}</div>
                  <div class="stat-label">资产总值</div>
                </div>
              </el-card>
            </el-col>
            
            <el-col :xs="12" :sm="12" :md="12">
              <el-card class="stat-card" shadow="hover" :class="{ 'profit-border': dashboardData.total_profit_loss >= 0, 'loss-border': dashboardData.total_profit_loss < 0 }">
                <div class="stat-content">
                  <div :class="['stat-number', dashboardData.total_profit_loss >= 0 ? 'text-up' : 'text-down']">
                    {{ dashboardData.total_profit_loss > 0 ? '+' : '' }}${{ dashboardData.total_profit_loss?.toLocaleString(undefined, {maximumFractionDigits: 0}) || '0' }}
                  </div>
                  <div class="stat-label">总盈亏金额</div>
                </div>
              </el-card>
            </el-col>

            <el-col :xs="12" :sm="12" :md="12">
              <el-card class="stat-card" shadow="hover" :class="{ 'profit-border': dashboardData.total_profit_loss >= 0, 'loss-border': dashboardData.total_profit_loss < 0 }">
                <div class="stat-content">
                  <div :class="['stat-number', dashboardData.total_profit_loss >= 0 ? 'text-up' : 'text-down']">
                    {{ dashboardData.total_profit_loss_percentage?.toFixed(2) || '0.00' }}%
                  </div>
                  <div class="stat-label">总盈亏比</div>
                </div>
              </el-card>
            </el-col>
            
            <el-col :xs="12" :sm="12" :md="12">
              <el-card class="stat-card" shadow="hover">
                <div class="stat-content">
                  <div class="stat-number active-alerts-num">{{ dashboardData.active_alerts_count || 0 }}</div>
                  <div class="stat-label">运行中的预警引擎</div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">💰 资产详情</span>
                <el-button @click="goToAssets" size="small" text bg>查看全部</el-button>
              </div>
            </template>
            <div class="data-list" v-if="dashboardData.asset_allocation?.length > 0">
              <div v-for="asset in dashboardData.asset_allocation" :key="asset.crypto_symbol" class="list-item asset-item">
                <div class="item-left">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ asset.crypto_symbol }}</el-tag>
                  <span class="item-name">{{ asset.crypto_name }}</span>
                </div>
                <div class="item-right text-right">
                  <div class="primary-text">${{ asset.holding_value?.toLocaleString(undefined, {maximumFractionDigits: 0}) || '0' }}</div>
                  <div :class="['secondary-text', asset.profit_loss >= 0 ? 'text-up' : 'text-down']">
                    {{ asset.profit_loss > 0 ? '+' : '' }}${{ asset.profit_loss?.toLocaleString(undefined, {maximumFractionDigits: 0}) || '0' }}
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无资产数据" :image-size="60" />
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">🔥 关注列表</span>
                <el-button @click="goToWatchlist" size="small" text bg>管理关注</el-button>
              </div>
            </template>
            <div class="data-list" v-if="watchlist.length > 0">
              <div v-for="item in watchlist" :key="item.id" class="list-item watchlist-item">
                <div class="item-left">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ item.crypto_symbol }}</el-tag>
                  <span class="item-name">{{ item.crypto_name }}</span>
                </div>
                <div class="item-right text-right">
                  <div class="price-text">${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}</div>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无关注数据" :image-size="60" />
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">⚠️ 预警监控</span>
                <el-button @click="goToAlerts" size="small" text bg>管理规则</el-button>
              </div>
            </template>
            <div class="data-list" v-if="alerts.length > 0">
              <div v-for="alert in alerts" :key="alert.id" class="list-item alert-item">
                <div class="item-left">
                  <el-tag :type="alert.is_active ? 'success' : 'info'" effect="dark" round size="small" class="symbol-tag">
                    {{ alert.crypto_symbol }}
                  </el-tag>
                  <span class="item-name">{{ alert.crypto_name }}</span>
                </div>
                <div class="item-right text-right">
                  <div class="primary-text">
                    <span :class="alert.alert_type === 'above' ? 'text-up' : 'text-down'">
                      {{ alert.alert_type === 'above' ? '高于↑' : '低于↓' }}
                    </span>
                    <span class="price-target">${{ alert.threshold_price }}</span>
                  </div>
                  <div class="secondary-text" style="color:#909399; font-size: 12px;">
                    {{ alert.is_active ? '监控中' : '已停用' }}
                  </div>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无预警记录" :image-size="60" />
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { dashboardApi, systemSettingsApi } from '../api'
import { useDarkMode } from '../composables/useDarkMode'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const router = useRouter()
const authStore = useAuthStore()
const { isDarkMode, toggleDarkMode } = useDarkMode()

const loading = ref(false)
const dashboardData = ref<any>({})
const alerts = ref<any[]>([])
const watchlist = ref<any[]>([])
const siteTitle = ref('Crypto-info')

let refreshTimer: ReturnType<typeof setInterval> | null = null

const loadDashboardData = async (isBackground = false) => {
  if (!isBackground) loading.value = true
  try {
    const response = await dashboardApi.getSummary()
    dashboardData.value = response.data
    if (response.data.watchlist) {
      watchlist.value = response.data.watchlist
    }
    if (response.data.alerts) {
      alerts.value = response.data.alerts
    }
  } catch (error) {
    if (!isBackground) ElMessage.error('加载仪表盘数据失败')
  } finally {
    if (!isBackground) loading.value = false
  }
}

const fetchAllData = (isBackground = false) => {
  loadDashboardData(isBackground)
}

const allocationChartOption = computed(() => {
  const data = dashboardData.value.asset_allocation || []
  
  if (data.length === 0) {
    return {
      title: { text: '暂无配置', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 13 } },
      series: []
    }
  }
  
  return {
    title: { show: false }, 
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: ${c} ({d}%)' },
    legend: { 
      orient: 'horizontal', 
      bottom: '0%', 
      left: 'center', 
      icon: 'circle', 
      itemWidth: 8, 
      itemHeight: 8, 
      textStyle: { color: '#606266', fontSize: 11 } 
    },
    series: [
      {
        name: '资产配置',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'], 
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold', formatter: '{b}\n${c}' }
        },
        labelLine: { show: false },
        data: data.map((item: any) => ({
          value: item.holding_value,
          name: item.crypto_symbol
        }))
      }
    ]
  }
})

const goToAlerts = () => router.push('/alerts')
const goToAssets = () => router.push('/assets')
const goToWatchlist = () => router.push('/watchlist')
const goToSettings = () => router.push('/settings')

const goToHome = () => router.push('/')
// 🚀 修复点：将其改造为返回配置刷新间隔时间的异步函数
const loadPublicSettings = async (): Promise<number> => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      siteTitle.value = response.data.site_title || 'Crypto-info'
      // 提取后端的 refresh_interval 设置，如果后端没返回，保底给 5 秒
      // console.log('真实接收到的后端刷新频率:', response.data.refresh_interval)
      return response.data.refresh_interval || 5
    }
  } catch (error) {
    console.error('加载公开设置失败:', error)
  }
  return 5 // 发生异常时保底给 5 秒
}

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(async () => {
  // 1. 挂载时立即执行一次请求渲染画面
  fetchAllData(false)
  
  // 2. 等待拉取后端设置（例如拿到了你配置的 8）
  const intervalSeconds = await loadPublicSettings()
  
  // 3. 使用后端的设置动态计算毫秒数 (8 * 1000 = 8000ms)，启动循环引擎
  refreshTimer = setInterval(() => {
    fetchAllData(true)
  }, intervalSeconds * 1000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; width: 100%; }
.header-left h1 { margin: 0; font-size: 22px; color: #1f2f3d; font-weight: 600; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.page-main { padding: 20px 25px; max-width: 1400px; margin: 0 auto; width: 100%; }

.symbol-tag { font-weight: bold; font-family: 'Monaco', monospace; }
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; transition: color 0.3s ease; }
.price-target { color: #1f2f3d; font-family: 'Monaco', monospace; margin-left: 4px; }
.text-up { color: #f56c6c; font-weight: bold; font-family: 'Monaco', monospace; }
.text-down { color: #67c23a; font-weight: bold; font-family: 'Monaco', monospace; }

/* Dashboard 专属核心指标卡片 */
.stat-card {
  border-radius: 12px;
  border: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  margin-bottom: 20px; 
}
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }
.stat-content { padding: 20px 10px; text-align: center; }
.stat-number { font-size: 24px; font-weight: bold; color: #1f2f3d; margin-bottom: 8px; font-family: 'Monaco', monospace; transition: all 0.3s; }
.active-alerts-num { color: #e6a23c; }
.stat-label { font-size: 12px; color: #909399; font-weight: 500; }

.profit-border { border-bottom: 4px solid #f56c6c; }
.loss-border { border-bottom: 4px solid #67c23a; }

/* 内容卡片统一设计 */
.content-card {
  border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02);
  margin-bottom: 20px;
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; color: #303133; font-size: 15px; }

.data-list { padding-right: 5px; }

.list-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 15px; margin-bottom: 10px;
  background: #f8f9fa; border-radius: 8px; border: 1px solid #f0f2f5;
  transition: background-color 0.2s ease;
}
.list-item:hover { background: #f0f2f5; }
.list-item:last-child { margin-bottom: 0; }

.item-left { display: flex; align-items: center; gap: 10px; }
.item-name { font-size: 13px; color: #606266; }
.text-right { text-align: right; }
.primary-text { font-size: 14px; font-weight: bold; color: #303133; font-family: 'Monaco', monospace; transition: color 0.3s ease; }
.secondary-text { font-size: 12px; margin-top: 4px; transition: color 0.3s ease; }

/* =========================================
   🚀 修复点：大屏幕下的 Flex 等高拉伸
   ========================================= */
@media (min-width: 992px) {
  .top-dashboard-row {
    display: flex;
    align-items: stretch; /* 强制左右两侧高度拉平 */
  }
  
  .chart-col {
    display: flex;
    flex-direction: column;
  }
  
  .chart-card {
    flex: 1; /* 让卡片填满整个列 */
    display: flex;
    flex-direction: column;
    margin-bottom: 20px; /* 对齐右侧边距 */
  }
  
  .chart-card :deep(.el-card__body) {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
  }
  
  .chart-container-small {
    height: 100%;
    min-height: 180px;
    width: 100%;
  }
}

/* 移动端视图 (xs <= 768px) */
@media (max-width: 768px) {
  .page-container { padding-bottom: 80px; }
  .page-main { padding: 12px; }
  
  .page-header { padding: 15px; }
  .header-content { flex-direction: column; gap: 8px; }
  .header-left { display: flex; align-items: center; justify-content: space-between; }
  .header-left h1 { font-size: 18px; margin: 0; white-space: nowrap; }
  .header-left p { display: none; }
  .header-right { display: flex; flex-direction: column; gap: 8px; }
  .dark-mode-btn { font-size: 16px; min-width: 36px; padding: 0; flex-shrink: 0; align-self: flex-end; }
  :deep(.action-buttons) { display: grid !important; grid-template-columns: repeat(2, 1fr) !important; gap: 6px !important; width: 100%; }
  :deep(.action-buttons .el-button) { margin: 0 !important; border-radius: 6px !important; justify-content: center; }

  .stat-card { margin-bottom: 12px; }
  .stat-content { padding: 16px 10px; }
  .stat-number { font-size: 20px; }
  
  .content-card { margin-bottom: 15px; }
  
  /* 手机端图表高度回退 */
  .chart-container-small { height: 220px; width: 100%; }
  
  .list-item { padding: 10px 12px; }
  .primary-text { font-size: 13px; }
}

/* 夜间模式 */
.page-container.dark-mode { background-color: #0f0f1a; }
.page-container.dark-mode .page-header { background: #1a1a2e; border-bottom-color: #2a2a3e; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.page-container.dark-mode .header-left h1 { color: #60a5fa; }
.page-container.dark-mode .header-left p { color: #8080a0; }
.page-container.dark-mode .content-card { background: #1a1a2e; border: none; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
.page-container.dark-mode .card-header { color: #d0d0e0; }
.page-container.dark-mode .stat-card { background: #16162a; }
.page-container.dark-mode .stat-number { color: #e0e0f0; }
.page-container.dark-mode .stat-label { color: #8080a0; }
.page-container.dark-mode .list-item { background: #16162a; border-color: #2a2a3e; }
.page-container.dark-mode .primary-text { color: #d0d0e0; }
.page-container.dark-mode .secondary-text { color: #8080a0; }
.page-container.dark-mode :deep(.el-card__header) { background: #1a1a2e; border-bottom-color: #2a2a3e; }
.page-container.dark-mode :deep(.el-card__body) { background: #1a1a2e; }
.page-container.dark-mode :deep(.el-table) { background: #1a1a2e; color: #d0d0e0; }
.page-container.dark-mode :deep(.el-table tr) { background: #1a1a2e; }
.page-container.dark-mode :deep(.el-table td), .page-container.dark-mode :deep(.el-table th.is-leaf) { background: #1a1a2e; border-color: #2a2a3e; color: #d0d0e0; }
.page-container.dark-mode :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background: #16162a; }
</style>