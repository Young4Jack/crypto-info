<template>
  <div class="page-container">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>📈 K线图</h1>
          <p>实时查看关注币种的K线走势</p>
        </div>
        <div class="header-right">
          <el-button @click="goToLogin" type="primary" plain>系统登录</el-button>
        </div>
      </div> 
    </el-header>

    <el-main class="page-main">
      <!-- 关注列表 -->
      <el-card class="watchlist-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">🔥 关注列表</span>
            <el-button @click="loadWatchlist" size="small" text bg>刷新</el-button>
          </div>
        </template>
        
        <div class="watchlist-grid" v-loading="loadingWatchlist">
          <div 
            v-for="item in watchlistData" 
            :key="item.crypto_symbol"
            class="watchlist-item"
            @click="openKlineDialog(item)"
          >
            <div class="item-left">
              <el-tag effect="dark" round size="small" class="symbol-tag">{{ item.crypto_symbol }}</el-tag>
              <span class="item-name">{{ item.crypto_name }}</span>
            </div>
            <div class="item-right">
              <div class="price-text">${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}</div>
            </div>
          </div>
          <el-empty v-if="!loadingWatchlist && watchlistData.length === 0" description="暂无关注数据" />
        </div>
      </el-card>

      <!-- 提示信息 -->
      <el-card class="tip-card" shadow="never">
        <div class="tip-content">
          <div class="tip-icon">👆</div>
          <div class="tip-text">点击上方币种查看K线图</div>
        </div>
      </el-card>
    </el-main>

    <!-- K线弹窗 -->
    <el-dialog 
      v-model="klineDialogVisible" 
      :title="`${selectedSymbol} - K线图`"
      width="90%"
      top="5vh"
      :close-on-click-modal="true"
      @close="closeKlineDialog"
    >
      <div class="kline-dialog-content">
        <!-- 控制面板 -->
        <div class="dialog-control-row">
          <div class="dialog-control-item">
            <label>时间周期：</label>
              <el-radio-group v-model="selectedInterval" @change="loadKlineData">
                <el-radio-button label="1m">1分钟</el-radio-button>
                <el-radio-button label="5m">5分钟</el-radio-button>
                <el-radio-button label="15m">15分钟</el-radio-button>
                <el-radio-button label="1h">1小时</el-radio-button>
                <el-radio-button label="4h">4小时</el-radio-button>
                <el-radio-button label="1d">1天</el-radio-button>
                <el-radio-button label="1w">1周</el-radio-button>
                <el-radio-button label="1M">1月</el-radio-button>
              </el-radio-group>
          </div>
          
          <div class="dialog-control-item">
            <label>数据数量：</label>
            <el-select v-model="selectedLimit" @change="loadKlineData" style="width: 120px">
              <el-option label="100条" :value="100" />
              <el-option label="200条" :value="200" />
              <el-option label="500条" :value="500" />
              <el-option label="1000条" :value="1000" />
            </el-select>
          </div>
          
          <div class="dialog-control-item">
            <el-button @click="loadKlineData" :loading="loading" type="primary" size="small">
              🔄 刷新
            </el-button>
          </div>
        </div>

        <!-- K线图 -->
        <div class="dialog-chart-container" v-loading="loading">
          <v-chart 
            v-if="klineData.length > 0" 
            :option="chartOption" 
            autoresize 
            style="height: 400px;"
          />
          <el-empty v-else-if="!loading" description="暂无K线数据" />
        </div>

        <!-- 数据统计 -->
        <div class="dialog-stats" v-if="klineData.length > 0">
          <div class="stat-item">
            <span class="stat-label">最高价</span>
            <span class="stat-value text-up">${{ latestKline.high?.toFixed(2) || '0.00' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">最低价</span>
            <span class="stat-value text-down">${{ latestKline.low?.toFixed(2) || '0.00' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">开盘价</span>
            <span class="stat-value">${{ latestKline.open?.toFixed(2) || '0.00' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">收盘价</span>
            <span class="stat-value">${{ latestKline.close?.toFixed(2) || '0.00' }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { klinesApi, watchlistApi, systemSettingsApi } from '../api'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CandlestickChart, BarChart, LineChart } from 'echarts/charts'
import { 
  TitleComponent, 
  TooltipComponent, 
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

use([
  CandlestickChart, 
  BarChart, 
  LineChart,
  TitleComponent, 
  TooltipComponent, 
  LegendComponent,
  GridComponent,
  DataZoomComponent,
  ToolboxComponent,
  CanvasRenderer
])

const router = useRouter()

const loading = ref(false)
const loadingWatchlist = ref(false)
const selectedSymbol = ref('')
const selectedInterval = ref('1h')
const selectedLimit = ref(200)
const klineData = ref<any[]>([])
const watchlistData = ref<any[]>([])
const klineDialogVisible = ref(false)
const selectedCryptoName = ref('')

let refreshTimer: ReturnType<typeof setInterval> | null = null
let priceRefreshTimer: ReturnType<typeof setInterval> | null = null
let refreshInterval = 5 // 默认5秒

// 计算属性
const intervalLabel = computed(() => {
  const labels: Record<string, string> = {
    '1m': '1分钟',
    '5m': '5分钟',
    '15m': '15分钟',
    '1h': '1小时',
    '4h': '4小时', 
    '1d': '1天'
  }
  return labels[selectedInterval.value] || selectedInterval.value
})

const latestKline = computed(() => {
  if (klineData.value.length === 0) return {}
  return klineData.value[klineData.value.length - 1]
})

// 图表配置
const chartOption = computed(() => {
  if (klineData.value.length === 0) return {}

  const dates = klineData.value.map(k => {
    const date = new Date(k.open_time)
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  })
  
  const ohlcData = klineData.value.map(k => [k.open, k.close, k.low, k.high])
  const volumeData = klineData.value.map(k => k.volume)

  return {
    title: {
      text: `${selectedSymbol.value} ${intervalLabel.value} K线图`,
      left: 'center',
      textStyle: {
        color: '#303133',
        fontSize: 16,
        fontWeight: 600
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      },
      formatter: (params: any) => {
        const kline = params[0]
        if (!kline) return ''
        
        const data = klineData.value[kline.dataIndex]
        return `
          <div style="font-family: Monaco, monospace;">
            <div><strong>${dates[kline.dataIndex]}</strong></div>
            <div>开盘: <span style="color: #409eff;">$${data.open.toFixed(2)}</span></div>
            <div>收盘: <span style="color: ${data.close >= data.open ? '#f56c6c' : '#67c23a'};">$${data.close.toFixed(2)}</span></div>
            <div>最高: <span style="color: #f56c6c;">$${data.high.toFixed(2)}</span></div>
            <div>最低: <span style="color: #67c23a;">$${data.low.toFixed(2)}</span></div>
            <div>成交量: ${data.volume.toFixed(2)}</div>
          </div>
        `
      }
    },
    legend: {
      data: ['K线', '成交量'],
      top: 30
    },
    grid: [
      {
        left: '10%',
        right: '10%',
        top: '15%',
        height: '50%'
      },
      {
        left: '10%',
        right: '10%',
        top: '70%',
        height: '20%'
      }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { onZero: false },
        splitLine: { show: false },
        axisLabel: { 
          fontSize: 11,
          color: '#909399'
        }
      },
      {
        type: 'category',
        gridIndex: 1,
        data: dates,
        axisLabel: { show: false },
        axisLine: { onZero: false },
        splitLine: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitArea: { show: true },
        axisLabel: {
          formatter: '${value}',
          fontSize: 11,
          color: '#909399'
        }
      },
      {
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: { show: false },
        axisLine: { show: false },
        splitLine: { show: false }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 50,
        end: 100
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlcData,
        xAxisIndex: 0,
        yAxisIndex: 0,
        itemStyle: {
          color: '#f56c6c',      // 阳线颜色
          color0: '#67c23a',     // 阴线颜色
          borderColor: '#f56c6c',
          borderColor0: '#67c23a'
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumeData,
        itemStyle: {
          color: (params: any) => {
            const kline = klineData.value[params.dataIndex]
            return kline && kline.close >= kline.open ? '#f56c6c' : '#67c23a'
          },
          opacity: 0.6
        }
      }
    ]
  }
})

// 加载关注列表
const loadWatchlist = async () => {
  loadingWatchlist.value = true
  try {
    const response = await watchlistApi.getPublic()
    watchlistData.value = response.data
  } catch (error) {
    console.error('加载关注列表失败:', error)
    ElMessage.error('加载关注列表失败')
  } finally {
    loadingWatchlist.value = false
  }
}

// 选择币种
const selectSymbol = (symbol: string) => {
  selectedSymbol.value = symbol
  loadKlineData()
}

// 打开K线弹窗
const openKlineDialog = async (item: any) => {
  selectedSymbol.value = item.crypto_symbol
  selectedCryptoName.value = item.crypto_name
  klineDialogVisible.value = true
  await loadKlineData()
}

// 关闭K线弹窗
const closeKlineDialog = () => {
  klineDialogVisible.value = false
  selectedSymbol.value = ''
  selectedCryptoName.value = ''
  klineData.value = []
}

// 关闭K线
const closeKline = () => {
  selectedSymbol.value = ''
  klineData.value = []
}

// 加载K线数据
const loadKlineData = async () => {
  if (!selectedSymbol.value) {
    ElMessage.warning('请先选择币种')
    return
  }

  loading.value = true
  try {
    const response = await klinesApi.getKlines(selectedSymbol.value, selectedInterval.value, selectedLimit.value)
    console.log('K线API响应:', response)
    
    if (response.data && response.data.success) {
      klineData.value = response.data.data.klines || []
      if (klineData.value.length > 0) {
        ElMessage.success(`成功加载 ${klineData.value.length} 条K线数据`)
      } else {
        ElMessage.warning('K线数据为空')
      }
    } else {
      console.error('API响应格式错误:', response)
      ElMessage.error(response.data?.error || '获取K线数据失败')
    }
  } catch (error: any) {
    console.error('获取K线数据失败:', error)
    if (error.response?.status === 404) {
      ElMessage.error('K线API不存在，请重启后端服务')
    } else {
      ElMessage.error('获取K线数据失败: ' + (error.message || '未知错误'))
    }
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}

// 自动刷新（使用动态间隔）
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    if (selectedSymbol.value) {
      loadKlineData()
    }
  }, refreshInterval * 1000) // 使用配置的刷新间隔
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// 价格实时刷新（使用动态间隔）
const startPriceRefresh = () => {
  priceRefreshTimer = setInterval(() => {
    loadWatchlistBackground()
  }, refreshInterval * 1000) // 使用动态获取的刷新间隔
}

const stopPriceRefresh = () => {
  if (priceRefreshTimer) {
    clearInterval(priceRefreshTimer)
    priceRefreshTimer = null
  }
}

// 后台加载关注列表（不显示loading）
const loadWatchlistBackground = async () => {
  try {
    const response = await watchlistApi.getPublic()
    watchlistData.value = response.data
  } catch (error) {
    console.error('后台刷新价格失败:', error)
  }
}

// 加载系统设置获取刷新间隔
const loadPublicSettings = async (): Promise<number> => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      // 返回后端配置的时间，保底 5 秒
      return response.data.refresh_interval || 5
    }
  } catch (error) {
    console.error('加载配置失败，使用默认 5 秒')
  }
  return 5
}

onMounted(async () => {
  loadWatchlist()
  
  // 获取动态刷新间隔
  refreshInterval = await loadPublicSettings()
  
  startAutoRefresh()
  startPriceRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  stopPriceRefresh()
})
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 30px;
}

.page-header { 
  background: white; 
  padding: 15px 25px; 
  box-shadow: 0 1px 4px rgba(0,21,41,0.04); 
  border-bottom: 1px solid #f0f0f0; 
}
.header-content { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  max-width: 1200px; 
  margin: 0 auto; 
  width: 100%; 
}
.header-left h1 { 
  margin: 0; 
  font-size: 22px; 
  color: #409eff; 
  font-weight: bold; 
  letter-spacing: 0.5px; 
}
.header-left p { 
  margin: 6px 0 0; 
  color: #909399; 
  font-size: 13px; 
}

.page-main { 
  padding: 20px 25px; 
  max-width: 1200px; 
  margin: 0 auto; 
  width: 100%; 
}

.watchlist-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02);
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  color: #303133;
  font-size: 15px;
}

.watchlist-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.watchlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  cursor: pointer;
  transition: all 0.2s ease;
}

.watchlist-item:hover {
  background: #f0f2f5;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.watchlist-item.active {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.watchlist-item.active .symbol-tag {
  background: white;
  color: #409eff;
}

.watchlist-item.active .item-name {
  color: white;
}

.watchlist-item.active .price-text {
  color: white;
}

.item-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.symbol-tag {
  font-weight: bold;
  font-family: 'Monaco', monospace;
}

.item-name {
  font-size: 13px;
  color: #606266;
}

.price-text {
  color: #409eff;
  font-weight: 600;
  font-family: 'Monaco', monospace;
  font-size: 15px;
}

.kline-section {
  margin-top: 20px;
}

.control-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02);
  margin-bottom: 20px;
}

.control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: center;
}

.control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-item label {
  font-weight: 500;
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
}

.chart-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02);
  margin-bottom: 20px;
}

.data-count {
  font-size: 12px;
  color: #909399;
}

.chart-container {
  min-height: 500px;
}

.stat-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02);
  margin-bottom: 20px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.stat-content {
  padding: 15px 10px;
  text-align: center;
}

.stat-number {
  font-size: 20px;
  font-weight: bold;
  color: #1f2f3d;
  margin-bottom: 5px;
  font-family: 'Monaco', monospace;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.text-up {
  color: #f56c6c;
}

.text-down {
  color: #67c23a;
}

.tip-card {
  border-radius: 10px;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02);
}

.tip-content {
  text-align: center;
  padding: 40px 20px;
}

.tip-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.tip-text {
  font-size: 16px;
  color: #909399;
}

/* K线弹窗样式 */
.kline-dialog-content {
  min-height: 500px;
}

.dialog-control-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.dialog-control-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialog-control-item label {
  font-weight: 500;
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
}

.dialog-chart-container {
  min-height: 400px;
  margin-bottom: 20px;
}

.dialog-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
  font-weight: 500;
}

.stat-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  font-family: 'Monaco', monospace;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-container {
    padding-bottom: 40px;
  }
  
  .page-main {
    padding: 8px;
  }
  
  .page-header {
    padding: 12px;
  }
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: nowrap;
  }
  
  .header-left h1 {
    font-size: 18px;
  }
  
  .header-left p {
    font-size: 12px;
  }
  
  .header-right {
    flex-shrink: 0;
  }
  
  .watchlist-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .watchlist-item {
    padding: 10px 12px;
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  
  .item-left {
    gap: 6px;
    width: 100%;
  }
  
  .item-right {
    width: 100%;
    justify-content: flex-start;
  }
  
  .symbol-tag {
    font-size: 11px;
    padding: 2px 6px;
  }
  
  .item-name {
    font-size: 12px;
    color: #909399;
  }
  
  .price-text {
    font-size: 14px;
    font-weight: 600;
  }
  
  .dialog-control-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .dialog-control-item {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .dialog-control-item label {
    font-size: 12px;
    min-width: 60px;
  }
  
  .dialog-control-item .el-radio-group {
    flex-wrap: wrap;
    gap: 4px;
  }
  
  .dialog-control-item .el-radio-button {
    margin-bottom: 4px;
  }
  
  .dialog-control-item .el-select {
    width: 100px !important;
  }
  
  .dialog-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .stat-item {
    padding: 8px;
  }
  
  .stat-value {
    font-size: 16px;
  }
}
</style>