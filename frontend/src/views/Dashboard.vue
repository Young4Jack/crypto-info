<template>
  <div class="dashboard-container">
    <el-container>
      <el-header class="dashboard-header" height="auto">
        <div class="header-left">
          <h1>{{ siteTitle }}</h1>
        </div>
        <div class="header-right">
          <span class="welcome-text">欢迎，{{ authStore.user?.username || '用户' }}</span>
          <el-button-group>
            <el-button type="primary" @click="goToAlerts" size="small">预警管理</el-button>
            <el-button type="success" @click="goToAssets" size="small">资产管理</el-button>
            <el-button type="info" @click="goToWatchlist" size="small">关注列表</el-button>
            <el-button type="warning" @click="goToSettings" size="small">系统设置</el-button>
            <el-button type="danger" @click="handleLogout" size="small">退出登录</el-button>
          </el-button-group>
        </div>
      </el-header>
      
      <el-main class="dashboard-main">
        <!-- 资产配置 -->
        <el-row :gutter="20" class="stats-row">
          <el-col :xs="24" :sm="12" :md="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">${{ dashboardData.total_value?.toLocaleString() || '0' }}</div>
                <div class="stat-label">资产总值</div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8">
            <el-card class="stat-card" :class="{ 'profit': dashboardData.total_profit_loss > 0, 'loss': dashboardData.total_profit_loss < 0 }">
              <div class="stat-content">
                <div class="stat-number">
                  {{ dashboardData.total_profit_loss > 0 ? '+' : '' }}${{ dashboardData.total_profit_loss?.toLocaleString() || '0' }}
                </div>
                <div class="stat-label">盈利/亏损 ({{ dashboardData.total_profit_loss_percentage?.toFixed(2) || '0' }}%)</div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ dashboardData.active_alerts_count || 0 }}</div>
                <div class="stat-label">活跃预警数</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 新的三列布局 -->
        <el-row :gutter="20">
          <!-- 第一列：资产配置和资产详情 -->
          <el-col :xs="24" :sm="24" :md="8">
            <!-- 资产配置 -->
            <el-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>资产配置</span>
                </div>
              </template>
              <div class="chart-container">
                <v-chart :option="allocationChartOption" autoresize />
              </div>
            </el-card>
            
            <!-- 资产详情 -->
            <el-card class="table-card">
              <template #header>
                <div class="card-header">
                  <span>资产详情</span>
                  <el-button @click="goToAssets" size="small">查看全部</el-button>
                </div>
              </template>
              <div class="assets-list" v-if="dashboardData.asset_allocation?.length > 0">
                <div v-for="asset in dashboardData.asset_allocation" :key="asset.crypto_symbol" class="asset-item">
                  <div class="asset-info">
                    <div class="asset-left">
                      <el-tag type="primary" size="small">{{ asset.crypto_symbol }}</el-tag>
                      <span class="asset-name">{{ asset.crypto_name }}</span>
                    </div>
                    <div class="asset-right">
                      <span class="asset-price">${{ asset.current_price?.toLocaleString() || '0' }}</span>
                      <span class="asset-quantity">{{ asset.quantity }} 个</span>
                      <span class="asset-value">${{ asset.holding_value?.toLocaleString() || '0' }}</span>
                      <span :class="{ 'profit': asset.profit_loss > 0, 'loss': asset.profit_loss < 0 }">
                        {{ asset.profit_loss > 0 ? '+' : '' }}${{ asset.profit_loss?.toLocaleString() || '0' }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">
                <p>暂无资产数据</p>
              </div>
            </el-card>
          </el-col>
          
          <!-- 第二列：关注列表 -->
          <el-col :xs="24" :sm="24" :md="8">
            <el-card class="watchlist-card">
              <template #header>
                <div class="card-header">
                  <span>🔥 关注列表</span>
                  <el-button @click="goToWatchlist" size="small">查看全部</el-button>
                </div>
              </template>
              <div class="watchlist-list" v-if="watchlist.length > 0">
                <div v-for="item in watchlist" :key="item.id" class="watchlist-item">
                  <div class="watchlist-info">
                    <div class="watchlist-left">
                      <el-tag type="primary" size="small">{{ item.crypto_symbol }}</el-tag>
                      <span class="watchlist-name">{{ item.crypto_name }}</span>
                    </div>
                    <div class="watchlist-right">
                      <span class="watchlist-price">${{ item.current_price ? item.current_price.toFixed(2) : '0.00' }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">
                <p>暂无关注数据</p>
              </div>
            </el-card>
          </el-col>
          
          <!-- 第三列：预警记录 -->
          <el-col :xs="24" :sm="24" :md="8">
            <el-card class="alerts-card">
              <template #header>
                <div class="card-header">
                  <span>⚠️ 预警记录</span>
                  <el-button @click="goToAlerts" size="small">查看全部</el-button>
                </div>
              </template>
              <div class="alerts-list" v-if="alerts.length > 0">
                <div v-for="alert in alerts" :key="alert.id" class="alert-item">
                  <div class="alert-info">
                    <div class="alert-left">
                      <el-tag :type="alert.alert_type === 'above' ? 'danger' : 'success'" size="small">
                        {{ alert.crypto_symbol }}
                      </el-tag>
                      <span class="alert-price">${{ alert.threshold_price }}</span>
                    </div>
                    <div class="alert-right">
                      <span class="alert-status">{{ alert.is_active ? '激活' : '已触发' }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state">
                <p>暂无预警记录</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
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

 // 注册 ECharts 组件
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
    console.error('加载仪表盘数据失败:', error)
    ElMessage.error('加载仪表盘数据失败')
  } finally {
    loading.value = false
  }
}

const loadAlerts = async () => {
  try {
    const response = await alertsApi.getAll()
    alerts.value = response.data // 显示所有预警记录
  } catch (error) {
    console.error('加载预警记录失败:', error)
  }
}

const loadWatchlist = async () => {
  try {
    const response = await watchlistApi.getAll()
    watchlist.value = response.data // 显示所有关注列表
  } catch (error) {
    console.error('加载关注列表失败:', error)
  }
}

// 饼图配置
const allocationChartOption = computed(() => {
  const data = dashboardData.value.asset_allocation || []
  
  if (data.length === 0) {
    return {
      title: {
        text: '暂无资产数据',
        left: 'center',
        top: 'center',
        textStyle: {
          color: '#999'
        }
      }
    }
  }
  
  return {
    title: {
      text: '资产配置',
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ${c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '资产配置',
        type: 'pie',
        radius: '50%',
        data: data.map((item: any) => ({
          value: item.holding_value,
          name: `${item.crypto_name} (${item.crypto_symbol})`
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
})

const goToAlerts = () => {
  router.push('/alerts')
}

const goToAssets = () => {
  router.push('/assets')
}

const goToWatchlist = () => {
  router.push('/watchlist')
}

const goToSettings = () => {
  router.push('/settings')
}

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
.dashboard-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.dashboard-header {
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

.dashboard-main {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-card.profit {
  border-left: 4px solid #67c23a;
}

.stat-card.loss {
  border-left: 4px solid #f56c6c;
}

.stat-content {
  padding: 20px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.chart-card, .table-card, .alerts-card, .news-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
}

.price {
  font-weight: bold;
  color: #409eff;
}

.profit {
  color: #67c23a;
  font-weight: bold;
}

.loss {
  color: #f56c6c;
  font-weight: bold;
}

.crypto-name {
  font-weight: 500;
  color: var(--text-primary);
}

.alerts-list, .news-list {
  max-height: 400px;
  overflow-y: auto;
}

.alert-item {
  padding: 15px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border-left: 4px solid #409eff;
  transition: all 0.3s ease;
}

.alert-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-left-color: #67c23a;
}

.alert-item:last-child {
  margin-bottom: 0;
}

.alert-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-price {
  font-weight: bold;
  color: #409eff;
  font-size: 16px;
}

.alert-status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.alert-status[data-status="active"] {
  background-color: #e1f3d8;
  color: #67c23a;
}

.alert-status[data-status="triggered"] {
  background-color: #fdf6ec;
  color: #e6a23c;
}

/* 资产详情样式 */
.assets-list {
  max-height: 400px;
  overflow-y: auto;
}

.asset-item {
  padding: 15px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border-left: 4px solid #409eff;
  transition: all 0.3s ease;
}

.asset-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-left-color: #67c23a;
}

.asset-item:last-child {
  margin-bottom: 0;
}

.asset-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.asset-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 14px;
}

.asset-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.asset-price {
  font-weight: bold;
  color: #409eff;
  font-size: 14px;
}

.asset-quantity {
  color: #666;
  font-size: 12px;
}

.asset-value {
  font-weight: bold;
  color: #409eff;
  font-size: 14px;
}

/* 关注列表样式 */
.watchlist-list {
  /* 移除滚动条限制，直接铺下来 */
}

.watchlist-item {
  padding: 15px;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 8px;
  border-left: 4px solid #67c23a;
  transition: all 0.3s ease;
}

.watchlist-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-left-color: #409eff;
}

.watchlist-item:last-child {
  margin-bottom: 0;
}

.watchlist-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watchlist-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.watchlist-name {
  font-weight: 500;
  color: var(--text-primary);
  font-size: 14px;
}

.watchlist-price {
  font-weight: bold;
  color: #67c23a;
  font-size: 16px;
}

.news-item {
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.news-item:last-child {
  border-bottom: none;
}

.news-title {
  font-weight: bold;
  margin-bottom: 5px;
  color: #333;
}

.news-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap; /* 允许元素换行 */
    justify-content: center;
  }

  /* 解除按钮组的强制在一行排列，允许其在移动端自动换行 */
  :deep(.el-button-group) {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 5px;
  }
  
  :deep(.el-button-group > .el-button) {
    float: none;
    border-radius: 4px !important; /* 取消首尾按钮的特殊圆角，让折行后的按钮更美观 */
    margin: 2px;
  }

  .dashboard-container {
    min-height: 100vh;
    background-color: #f5f5f5;
  }
  
  .dashboard-header {
    background: white;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    gap: 15px;
  }
  
  .header-left h1 {
    margin: 0;
    color: #409eff;
    font-size: 1.5rem;
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .dashboard-main {
    padding: 15px;
  }
  
  .stats-row {
    margin-bottom: 15px;
  }
  
  .stat-card {
    text-align: center;
    transition: all 0.3s;
    margin-bottom: 10px;
  }
  
  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .stat-card.profit {
    border-left: 4px solid #67c23a;
  }
  
  .stat-card.loss {
    border-left: 4px solid #f56c6c;
  }
  
  .stat-content {
    padding: 15px;
  }
  
  .stat-number {
    font-size: 24px;
    font-weight: bold;
    color: #409eff;
    margin-bottom: 8px;
  }
  
  .stat-label {
    font-size: 12px;
    color: #666;
  }
  
  .chart-card, .table-card, .alerts-card, .news-card {
    margin-bottom: 15px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .chart-container {
    height: 250px;
  }
  
  .price {
    font-weight: bold;
    color: #409eff;
    font-size: 12px;
  }
  
  .profit {
    color: #67c23a;
    font-weight: bold;
    font-size: 12px;
  }
  
  .loss {
    color: #f56c6c;
    font-weight: bold;
    font-size: 12px;
  }
  
  .crypto-name {
    font-weight: 500;
    color: var(--text-primary);
    font-size: 12px;
  }
  
  .alerts-list, .news-list {
    max-height: 200px;
    overflow-y: auto;
  }
  
  .alert-item {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
  }
  
  .alert-item:last-child {
    border-bottom: none;
  }
  
  .alert-info {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  
  .alert-price {
    font-weight: bold;
    color: #409eff;
    font-size: 12px;
  }
  
  .alert-status {
    margin-left: auto;
    color: #666;
    font-size: 10px;
  }
  
  .news-item {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
  }
  
  .news-item:last-child {
    border-bottom: none;
  }
  
  .news-title {
    font-weight: bold;
    margin-bottom: 3px;
    color: #333;
    font-size: 12px;
  }
  
  .news-meta {
    display: flex;
    justify-content: space-between;
    font-size: 10px;
    color: #999;
  }
  
  .empty-state {
    text-align: center;
    padding: 30px;
    color: #999;
    font-size: 12px;
  }
}
</style>
