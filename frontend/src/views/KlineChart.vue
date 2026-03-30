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
      <!-- 控制面板 -->
      <el-card class="control-card" shadow="never">
        <div class="control-row">
          <div class="control-item">
            <label>选择币种：</label>
            <el-select v-model="selectedSymbol" placeholder="选择币种" @change="loadKlineData" style="width: 200px">
              <el-option
                v-for="symbol in watchlistSymbols"
                :key="symbol.crypto_symbol"
                :label="`${symbol.crypto_name} (${symbol.crypto_symbol})`"
                :value="symbol.crypto_symbol"
              />
            </el-select>
          </div>
          
          <div class="control-item">
            <label>时间周期：</label>
            <el-radio-group v-model="selectedInterval" @change="loadKlineData">
              <el-radio-button label="1h">1小时</el-radio-button>
              <el-radio-button label="4h">4小时</el-radio-button>
              <el-radio-button label="1d">1天</el-radio-button>
              <el-radio-button label="1w">1周</el-radio-button>
              <el-radio-button label="1M">1月</el-radio-button>
            </el-radio-group>
          </div>
          
          <div class="control-item">
            <el-button @click="loadKlineData" :loading="loading" type="primary">
              🔄 刷新数据
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- K线图 -->
      <el-card class="chart-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">
              {{ selectedSymbol }} - {{ intervalLabel }} K线图
            </span>
            <span class="data-count" v-if="klineData.length > 0">
              共 {{ klineData.length }} 条数据
            </span>
          </div>
        </template>
        
        <div class="chart-container" v-loading="loading">
          <v-chart 
            v-if="klineData.length > 0" 
            :option="chartOption" 
            autoresize 
            style="height: 500px;"
          />
          <el-empty v-else-if="!loading" description="暂无K线数据" />
        </div>
      </el-card>

      <!-- 数据统计 -->
      <el-row :gutter="20" v-if="klineData.length > 0">
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number text-up">${{ latestKline.high?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">最高价</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number text-down">${{ latestKline.low?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">最低价</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number">${{ latestKline.open?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">开盘价</div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <div class="stat-number">${{ latestKline.close?.toFixed(2) || '0.00' }}</div>
              <div class="stat-label">收盘价</div>
            </div>
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
import { klinesApi, watchlistApi } from '../api'
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
const selectedSymbol = ref('BTCUSDT')
const selectedInterval = ref('1h')
const klineData = ref<any[]>([])
const watchlistSymbols = ref<any[]>([])

// 计算属性
const intervalLabel = computed(() => {
  const labels: Record<string, string> = {
    '1h': '1小时',
    '4h': '4小时', 
    '1d': '1天',
    '1w': '1周',
    '1M': '1月'
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
  try {
    const response = await watchlistApi.getPublic()
    watchlistSymbols.value = response.data
    
    // 默认选择第一个
    if (watchlistSymbols.value.length > 0 && !selectedSymbol.value) {
      selectedSymbol.value = watchlistSymbols.value[0].crypto_symbol
      loadKlineData()
    }
  } catch (error) {
    console.error('加载关注列表失败:', error)
    ElMessage.error('加载关注列表失败')
  }
}

// 加载K线数据
const loadKlineData = async () => {
  if (!selectedSymbol.value) {
    ElMessage.warning('请先选择币种')
    return
  }

  loading.value = true
  try {
    const response = await klinesApi.getKlines(selectedSymbol.value, selectedInterval.value, 200)
    if (response.data.success) {
      klineData.value = response.data.data.klines
      ElMessage.success(`成功加载 ${klineData.value.length} 条K线数据`)
    } else {
      ElMessage.error('获取K线数据失败')
    }
  } catch (error) {
    console.error('获取K线数据失败:', error)
    ElMessage.error('获取K线数据失败')
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}

onMounted(() => {
  loadWatchlist()
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
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.header-left h1 {
  margin: 0;
  font-size: 22px;
  color: #1f2f3d;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.header-left p {
  margin: 6px 0 0;
  color: #909399;
  font-size: 13px;
}

.page-main {
  padding: 20px 25px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
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
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .header-left h1 {
    font-size: 18px;
  }
  
  .header-left p {
    font-size: 12px;
  }
  
  .header-right {
    width: 100%;
  }
  
  .control-card {
    margin-bottom: 12px;
  }
  
  .control-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .control-item {
    width: 100%;
    justify-content: space-between;
  }
  
  .control-item label {
    font-size: 12px;
  }
  
  .chart-card {
    margin-bottom: 12px;
  }
  
  .chart-container {
    min-height: 300px;
  }
  
  .chart-container :deep(.el-empty) {
    padding: 20px 0;
  }
  
  .stat-card {
    margin-bottom: 10px;
  }
  
  .stat-content {
    padding: 10px 8px;
  }
  
  .stat-number {
    font-size: 16px;
  }
  
  .stat-label {
    font-size: 11px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .card-title {
    font-size: 14px;
  }
  
  .data-count {
    font-size: 11px;
  }
}
</style>