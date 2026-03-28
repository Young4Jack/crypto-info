<template>
  <div class="page-container">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>{{ siteTitle }}</h1>
          <p>欢迎回来，{{ authStore.user?.username || 'Jack' }}</p>
        </div>
        <div class="header-right">
          <el-button-group class="action-buttons">
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
      <el-row :gutter="20" class="stats-row">
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number">${{ dashboardData.total_value?.toLocaleString() || '0.00' }}</div>
              <div class="stat-label">资产总值</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="stat-card" shadow="hover" :class="{ 'profit-border': dashboardData.total_profit_loss >= 0, 'loss-border': dashboardData.total_profit_loss < 0 }">
            <div class="stat-content">
              <div :class="['stat-number', dashboardData.total_profit_loss >= 0 ? 'text-up' : 'text-down']">
                {{ dashboardData.total_profit_loss > 0 ? '+' : '' }}${{ dashboardData.total_profit_loss?.toLocaleString() || '0.00' }}
              </div>
              <div class="stat-label">总盈亏金额 ({{ dashboardData.total_profit_loss_percentage?.toFixed(2) || '0.00' }}%)</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="8">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number active-alerts-num">{{ dashboardData.active_alerts_count || 0 }}</div>
              <div class="stat-label">运行中的预警引擎</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="content-card chart-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">资产配置</span>
              </div>
            </template>
            <div class="chart-container">
              <v-chart :option="allocationChartOption" autoresize />
            </div>
          </el-card>
          
          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header">
                <span class="card-title">资产详情</span>
                <el-button @click="goToAssets" size="small" text bg>查看全部</el-button>
              </div>
            </template>
            <div class="data-list" v-if="dashboardData.asset_allocation?.length > 0">
              <div v-for="asset in dashboardData.asset_allocation" :key="asset.crypto_symbol" class="list-item asset-item">
                <div class="item-left">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ asset.crypto_symbol }}</el-tag>
                </div>
                <div class="item-right text-right">
                  <div class="primary-text">${{ asset.holding_value?.toLocaleString() || '0' }}</div>
                  <div :class="['secondary-text', asset.profit_loss >= 0 ? 'text-up' : 'text-down']">
                    {{ asset.profit_loss > 0 ? '+' : '' }}${{ asset.profit_loss?.toLocaleString() || '0' }}
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { dashboardApi, alertsApi, watchlistApi, systemSettingsApi } from '../api'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([PieChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const dashboardData = ref<any>({})
const alerts = ref<any[]>([])
const watchlist = ref<any[]>([])
const siteTitle = ref('Crypto-info')

const loadDashboardData = async () => {
  loading.value = true
  try {
    const response = await dashboardApi.getSummary()
    dashboardData.value = response.data
  } catch (error) {
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

const loadAlerts = async () => {
  try {
    const response = await alertsApi.getAll()
    alerts.value = response.data
  } catch (error) {
    console.error('加载预警记录失败:', error)
  }
}

const loadWatchlist = async () => {
  try {
    const response = await watchlistApi.getAll()
    watchlist.value = response.data
  } catch (error) {
    console.error('加载关注列表失败:', error)
  }
}

const allocationChartOption = computed(() => {
  const data = dashboardData.value.asset_allocation || []
  
  if (data.length === 0) {
    return {
      title: { text: '暂无资产数据', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14 } },
      series: []
    }
  }
  
  return {
    title: { show: false },
    tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: ${c} ({d}%)' },
    legend: { bottom: '0%', left: 'center', icon: 'circle', itemWidth: 10, itemHeight: 10, textStyle: { color: '#606266' } },
    series: [
      {
        name: '资产配置',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { show: false, position: 'center' },
        emphasis: {
          label: { show: true, fontSize: 16, fontWeight: 'bold' }
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

const loadPublicSettings = async () => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      siteTitle.value = response.data.site_title || 'Crypto-info'
    }
  } catch (error) {
    console.error('加载公开设置失败:', error)
  }
}

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  loadDashboardData()
  loadAlerts()
  loadWatchlist()
  loadPublicSettings()
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
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; }
.price-target { color: #1f2f3d; font-family: 'Monaco', monospace; margin-left: 4px; }
.text-up { color: #f56c6c; font-weight: bold; font-family: 'Monaco', monospace; }
.text-down { color: #67c23a; font-weight: bold; font-family: 'Monaco', monospace; }

.stats-row { margin-bottom: 24px; }

.stat-card {
  border-radius: 12px;
  border: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  margin-bottom: 15px;
}
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.08); }
.stat-content { padding: 20px 10px; text-align: center; }
.stat-number { font-size: 28px; font-weight: bold; color: #1f2f3d; margin-bottom: 8px; font-family: 'Monaco', monospace; }
.active-alerts-num { color: #e6a23c; }
.stat-label { font-size: 13px; color: #909399; font-weight: 500; }

.profit-border { border-bottom: 4px solid #f56c6c; }
.loss-border { border-bottom: 4px solid #67c23a; }

.content-card {
  border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02);
  margin-bottom: 20px;
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; color: #303133; font-size: 15px; }

.chart-container { height: 280px; width: 100%; }

/* 修改点：删除了 .scrollable-list 的 max-height 和 overflow 设置，仅保留容器边距基础结构 */
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
.primary-text { font-size: 14px; font-weight: bold; color: #303133; font-family: 'Monaco', monospace; }
.secondary-text { font-size: 12px; margin-top: 4px; }

@media (max-width: 768px) {
  .page-container { padding-bottom: 80px; }
  .page-main { padding: 12px; }
  
  .page-header { padding: 15px; }
  .header-content { flex-direction: column; align-items: flex-start; gap: 15px; }
  .header-right { width: 100%; }
  
  :deep(.action-buttons) { display: flex; flex-wrap: wrap; width: 100%; gap: 6px; }
  :deep(.action-buttons .el-button) { flex: 1 1 auto; margin: 0 !important; border-radius: 6px !important; }

  .stat-card { margin-bottom: 12px; }
  .stat-content { padding: 16px 10px; }
  .stat-number { font-size: 24px; }
  
  .content-card { margin-bottom: 15px; }
  .chart-container { height: 240px; }
  
  .list-item { padding: 10px 12px; }
  .primary-text { font-size: 13px; }
}
</style>