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
            <el-button @click="loadWatchlist" size="small" type="primary">
              <el-icon v-if="!loadingWatchlist"><Refresh /></el-icon>
              <span v-if="!loadingWatchlist">刷新</span>
            </el-button>
          </div>
        </template>
        
        <div class="watchlist-grid" v-loading="loadingWatchlist">
          <div 
            v-for="item in watchlistData" 
            :key="item.crypto_symbol"
            class="watchlist-item"
            @click="openKlineDialog(item)"
          >
            <div class="item-info">
              <span class="item-name">{{ item.crypto_name }}</span>
              <span class="item-price">${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}</span>
            </div>
            <div class="item-change" :class="getChangeClass(item.change_24h)">
              {{ formatChange(item.change_24h) }}
            </div>
          </div>
          <el-empty v-if="!loadingWatchlist && watchlistData.length === 0" description="暂无关注数据" />
        </div>
      </el-card>
    </el-main>

    <div class="kline-dialog-overlay" v-if="klineDialogVisible" @click.self="closeKlineDialog">
      <div class="kline-dialog-content">

        <div class="kline-header-toolbar">
          
          <div class="header-main">
            <div class="symbol-info">
              <h2>
                {{ selectedSymbol }}
                <span class="main-interval-text">
                  {{ selectedInterval === '1d' ? '1天' : (intervalLabelMap[selectedInterval] || selectedInterval) }}
                </span>
              </h2>
            </div>
            
            <button class="close-btn" @click="closeKlineDialog">×</button>
          </div>

          <div class="realtime-data-bar" v-if="realtimeObj">
            <div class="data-item"><span class="label">时间</span><span class="value">{{ realtimeObj.time }}</span></div>
            <div class="data-item"><span class="label">开</span><span class="value">{{ realtimeObj.open }}</span></div>
            <div class="data-item"><span class="label">高</span><span class="value">{{ realtimeObj.high }}</span></div>
            <div class="data-item"><span class="label">低</span><span class="value">{{ realtimeObj.low }}</span></div>
            <div class="data-item"><span class="label">收</span><span class="value" :class="realtimeObj.changePercent >= 0 ? 'text-up' : 'text-down'">{{ realtimeObj.close }}</span></div>
            <div class="data-item"><span class="label">涨跌幅</span><span class="value" :class="realtimeObj.changePercent >= 0 ? 'text-up' : 'text-down'">{{ realtimeObj.changePercent }}%</span></div>
            <div class="data-item"><span class="label">振幅</span><span class="value">{{ realtimeObj.amplitude }}%</span></div>
            <div class="data-item"><span class="label">成交量</span><span class="value">{{ realtimeObj.volume }}</span></div>
          </div>

          <div class="header-bottom">
            <div class="custom-interval-selector">
              <span 
                v-for="interval in ['1m', '5m', '15m', '1h', '4h', '1d', '1w', '1M']" 
                :key="interval"
                class="interval-btn"
                :class="{ active: selectedInterval === interval }"
                @click="changeInterval(interval)"
              >
                {{ intervalLabelMap[interval] || interval }}
              </span>
            </div>
          </div>
          
        </div>

        <div class="kline-chart-container" @touchend.capture="clearTooltip" @touchcancel.capture="clearTooltip" @mouseleave="clearTooltip">
          <v-chart 
            ref="chartRef"
            class="chart" 
            :option="chartOption" 
            style="height: 100%; width: 100%;"
            :notMerge="true"
            :autoresize="true"
            @datazoom="onDataZoom"
          />
          <div v-if="loading" class="loading-overlay">
            <div class="loading-spinner"></div>
          </div>
          <div v-if="!loading && klineData.length === 0" class="empty-placeholder">
            <span>暂无K线数据</span>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
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

// 获取图表实例引用
const chartRef = ref(null)

// 2. 清理面板的函数
const clearTooltip = () => {
  // 设置极短延迟，确保覆盖掉图表引擎自身的渲染结算
  setTimeout(() => {
    // 顶部数据条回退到最新数据
    hoverIndex.value = null;
    
    // 强制派发隐藏动作，抹除十字准星和悬浮窗
    if (chartRef.value) {
      chartRef.value.dispatchAction({
        type: 'hideTip'
      });
    }
  }, 10); 
};
const loading = ref(false)
const loadingWatchlist = ref(false)
const selectedSymbol = ref('')
const selectedInterval = ref('1d')
const selectedLimit = ref(100)
const klineData = ref<any[]>([])
const watchlistData = ref<any[]>([])
const klineDialogVisible = ref(false)
const selectedCryptoName = ref('')
const savedDataZoom = ref<{ start: number; end: number } | null>(null)

let klineWs: WebSocket | null = null;
let priceRefreshTimer: ReturnType<typeof setInterval> | null = null
let refreshInterval = 5 // 默认5秒

const intervalLabelMap: Record<string, string> = {
  '1m': '1分钟', '5m': '5分钟', '15m': '15分钟',
  '1h': '1小时', '4h': '4小时', 
  '1d': '日线', '1w': '周线', '1M': '月线'
}

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

// 格式化涨跌幅
const formatChange = (change: number | undefined | null) => {
  if (change === undefined || change === null || isNaN(change)) return '--'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

// 获取涨跌幅样式类
const getChangeClass = (change: number | undefined | null) => {
  if (change === undefined || change === null || isNaN(change)) return ''
  return change >= 0 ? 'change-up' : 'change-down'
}

// 计算最新K线的涨跌幅
const latestChange = computed(() => {
  if (klineData.value.length === 0) return null
  const kline = klineData.value[klineData.value.length - 1]
  if (!kline.open || !kline.close) return null
  return ((kline.close - kline.open) / kline.open) * 100
})

// 新增一个响应式变量，用于记录当前鼠标指着的 K 线索引
const hoverIndex = ref(null);

// 修改顶部数据的数据源计算逻辑
const realtimeObj = computed(() => {
  if (klineData.value.length === 0) return null;
  
  // 核心判断：如果鼠标停留在图表上，就取 hoverIndex 的数据；否则取最新一根（最后一条）数据
  const currentIndex = hoverIndex.value !== null ? hoverIndex.value : (klineData.value.length - 1);
  const data = klineData.value[currentIndex]; 
  
  // 处理时间格式
  const date = new Date(data.open_time);
  const Y = date.getFullYear();
  const M = String(date.getMonth() + 1).padStart(2, '0');
  const D = String(date.getDate()).padStart(2, '0');
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');

  let timeStr = '';
  if (['1d', '1w', '1M'].includes(selectedInterval.value)) {
    timeStr = `${Y}-${M}-${D}`;
  } else {
    timeStr = `${M}-${D} ${h}:${m}`;
  }
  
  const open = parseFloat(data.open);
  const close = parseFloat(data.close);
  const changePercent = open ? (((close - open) / open) * 100).toFixed(2) : '0.00';

  return {
    time: timeStr,
    open: open.toFixed(2),
    high: parseFloat(data.high).toFixed(2),
    low: parseFloat(data.low).toFixed(2),
    close: close.toFixed(2),
    changePercent: changePercent,
    amplitude: open ? (((parseFloat(data.high) - parseFloat(data.low)) / open) * 100).toFixed(2) : '--',
    volume: parseFloat(data.volume).toFixed(2)
  };
});

// 格式化时间
const formatInfoTime = (timestamp: number | undefined) => {
  if (!timestamp) return '--'
  const date = new Date(timestamp)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${minutes}`
}

// 格式化振幅
const formatAmplitude = (kline: any) => {
  if (!kline.high || !kline.low || !kline.open) return '--'
  const amplitude = ((kline.high - kline.low) / kline.open) * 100
  return `${amplitude.toFixed(2)}%`
}

// 保存用户的缩放状态
const onDataZoom = (params: any) => {
  if (params.batch && params.batch.length > 0) {
    const { start, end } = params.batch[0]
    savedDataZoom.value = { start, end }
  } else if (params.start !== undefined && params.end !== undefined) {
    savedDataZoom.value = { start: params.start, end: params.end }
  }
}

// 图表配置
const chartOption = computed(() => {
  if (klineData.value.length === 0) {
    return {
      title: {
        text: '', left: 'center', top: 'center',
        textStyle: { color: '#ccc', fontSize: 14 }
      },
      series: []
    }
  }

  // 根据周期格式化时间
  const formatTime = (timestamp) => {
    const date = new Date(timestamp)
    const interval = selectedInterval.value
    
    if (interval === '1m' || interval === '5m' || interval === '15m' || interval === '30m') {
      return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    } else if (interval === '1h' || interval === '2h' || interval === '4h' || interval === '6h' || interval === '12h') {
      return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:00`
    } else if (interval === '1d' || interval === '3d' || interval === '1w') {
      return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
    } else if (interval === '1M') {
      return `${date.getFullYear()}/${date.getMonth() + 1}`
    }
    return date.toLocaleDateString('zh-CN')
  }

  const dates = klineData.value.map(k => formatTime(k.open_time))
  const ohlcData = klineData.value.map(k => [k.open, k.close, k.low, k.high])
  const volumeData = klineData.value.map(k => k.volume)

  return {
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      triggerOn: 'mousemove',
      // 新增以下两行：
      confine: true,        // 强制将 tooltip 限制在可视范围内，如果上方空间不够，它会自动翻转显示在手指下方
      appendToBody: true,   // 将 tooltip 的 DOM 节点直接挂载到 <body> 层，彻底打破外部容器的 overflow 遮挡限制
      
      axisPointer: { type: 'cross' },
      formatter: (params) => {
        const kline = params[0]
        if (!kline) return ''

        hoverIndex.value = kline.dataIndex;

        const data = klineData.value[kline.dataIndex]
        const timeStr = formatTime(data.open_time)
        const change = (((data.close - data.open) / data.open) * 100).toFixed(2)
        const amplitude = (((data.high - data.low) / data.open) * 100).toFixed(2)
        const color = data.close >= data.open ? '#f56c6c' : '#67c23a'
        const sign = data.close >= data.open ? '+' : ''
        
        return `
          <div style="font-family: Monaco, monospace; font-size: 12px; min-width: 140px;">
            <div style="color: #909399; margin-bottom: 8px; font-weight: bold;">${timeStr}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>开盘</span> <span>${data.open.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最高</span> <span style="color: #f56c6c;">${data.high.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最低</span> <span style="color: #67c23a;">${data.low.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>收盘</span> <span style="color: ${color}; font-weight: bold;">${data.close.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid #ebeef5; margin-top: 6px; padding-top: 6px;">
              <span>涨跌幅</span> <span style="color: ${color};">${sign}${change}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px;"><span>振幅</span> <span>${amplitude}%</span></div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px;"><span>成交量</span> <span>${data.volume.toFixed(2)}</span></div>
          </div>
        `
      }
    },
    legend: {
      data: ['K线', '成交量'],
      left: 'center',  // 强制绝对水平居中
      top: 0,          // 紧贴顶部
      textStyle: { fontSize: 11 }
    },
    grid: [
      {
        left: '8%', right: '8%',
        top: 30,
        bottom: '26%'  // 强制主图(K线)距离画布底部留出 26% 的绝对空间
      },
      {
        left: '8%', right: '8%',
        height: '16%', // 成交量图的高度占比
        bottom: '4%'   // 强制副图(成交量)锚定在距离画布最底边 4% 的位置
      }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLine: { onZero: false }, splitLine: { show: false }, axisLabel: { fontSize: 11, color: '#909399' } },
      { type: 'category', gridIndex: 1, data: dates, axisLabel: { show: false }, axisLine: { onZero: false }, splitLine: { show: false } }
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitArea: { show: true }, axisLabel: { formatter: '${value}', fontSize: 11, color: '#909399' } },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false }, axisLine: { show: false }, splitLine: { show: false } }
    ],
    dataZoom: [
      {
        type: 'inside', xAxisIndex: [0, 1],
        start: savedDataZoom.value ? savedDataZoom.value.start : 80,
        end: savedDataZoom.value ? savedDataZoom.value.end : 100
      }
    ],
    series: [
      {
        name: 'K线', type: 'candlestick', data: ohlcData, xAxisIndex: 0, yAxisIndex: 0,
        itemStyle: { color: '#f56c6c', color0: '#67c23a', borderColor: '#f56c6c', borderColor0: '#67c23a' }
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumeData,
        itemStyle: {
          color: (params) => {
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
    // 并行获取关注列表和涨跌幅数据
    const [watchlistRes, klinesRes] = await Promise.all([
      watchlistApi.getPublic(),
      klinesApi.getWatchlistKlines('1d', 2)
    ])
    
    const data = watchlistRes.data
    //console.log('K线API完整响应:', klinesRes)
    //console.log('K线API data:', klinesRes.data)
    
    const klinesData = klinesRes.data?.data || {}
    //console.log('涨跌幅数据:', klinesData)
    
    // 合并涨跌幅数据
    for (const item of data) {
      const symbolData = klinesData[item.crypto_symbol]
      const symbolKlines = symbolData?.klines || []
      
      // 使用最新一条K线的涨跌幅（与弹出框一致）
      if (symbolKlines.length > 0) {
        const latestKline = symbolKlines[symbolKlines.length - 1]
        const open = parseFloat(latestKline.open)
        const close = parseFloat(latestKline.close)
        if (open && close) {
          item.change_24h = ((close - open) / open) * 100
        } else {
          item.change_24h = null
        }
      } else {
        item.change_24h = null
      }
    }
    
    watchlistData.value = data
  } catch (error) {
    console.error('加载关注列表失败:', error)
    // 降级：只加载关注列表
    try {
      const response = await watchlistApi.getPublic()
      watchlistData.value = response.data
    } catch (e) {
      ElMessage.error('加载关注列表失败')
    }
  } finally {
    loadingWatchlist.value = false
  }
}

// 打开K线弹窗
const openKlineDialog = async (item: any) => {
  selectedSymbol.value = item.crypto_symbol
  selectedCryptoName.value = item.crypto_name
  klineDialogVisible.value = true
  
  await loadKlineData()
  // 移除周期限制，无论什么周期均连接 WebSocket 以更新实时现价
  connectWebSocket(selectedSymbol.value)
}

// 关闭K线弹窗
const closeKlineDialog = () => {
  if (klineWs) {
    klineWs.close()
    klineWs = null
  }
  klineDialogVisible.value = false
  selectedSymbol.value = ''
  selectedCryptoName.value = ''
  klineData.value = []
}

// 加载K线数据
const loadKlineData = async (silent = false) => {
  if (!selectedSymbol.value) {
    ElMessage.warning('请先选择币种')
    return
  }

  if (!silent) {
    loading.value = true
  }
  
  try {
    const response = await klinesApi.getKlines(selectedSymbol.value, selectedInterval.value, selectedLimit.value)
    
    if (response.data && response.data.success) {
      klineData.value = response.data.data.klines || []
      if (klineData.value.length === 0 && !silent) {
        ElMessage.warning('K线数据为空')
      }
    } else {
      if (!silent) {
        ElMessage.error(response.data?.error || '获取K线数据失败')
      }
    }
  } catch (error: any) {
    if (!silent) {
      if (error.response?.status === 404) {
        ElMessage.error('K线API不存在，请重启后端服务')
      } else {
        ElMessage.error('获取K线数据失败: ' + (error.message || '未知错误'))
      }
    }
  } finally {
    loading.value = false
  }
}

// 周期切换核心逻辑
const changeInterval = async (newInterval: string) => {
  if (selectedInterval.value === newInterval) return; 
  selectedInterval.value = newInterval;
  
  if (klineWs) {
    klineWs.close();
    klineWs = null;
  }
  await loadKlineData();
  // 移除周期限制，切换后重新连接
  connectWebSocket(selectedSymbol.value);
}

// 建立WebSocket连接并处理实时数据（包含防崩溃与强制重绘）
const connectWebSocket = (symbol: string) => {
  if (klineWs) klineWs.close();
  
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.hostname;
  const wsUrl = `${protocol}//${host}:${__BACKEND_PORT__}/api/klines/ws/${symbol}`;

  klineWs = new WebSocket(wsUrl);


  klineWs.onmessage = (event) => {
    try {
      if (!event.data || event.data === 'undefined') return;
      const newKline = JSON.parse(event.data);
      if (!newKline || typeof newKline.close === 'undefined') return;
      if (klineData.value.length === 0) return;
      
      const lastIndex = klineData.value.length - 1;
      const lastKline = klineData.value[lastIndex];
      const currentPrice = parseFloat(newKline.close);

      // 解构生成新数组，强制触发 Vue 和 ECharts 的深度响应式渲染
      const newData = [...klineData.value];

      // 无论当前处于1d还是1h周期，强制更新最后一根K线的收盘价与极值
      newData[lastIndex] = { 
        ...lastKline, 
        close: currentPrice,
        high: Math.max(lastKline.high, currentPrice),
        low: Math.min(lastKline.low, currentPrice)
      };

      // 仅当周期为1m且产生新的分钟线时，才向图表追加新柱子
      if (selectedInterval.value === '1m' && newKline.open_time > lastKline.open_time) {
        newData.push(newKline);
        if (newData.length > selectedLimit.value) newData.shift();
      }

      // 内存地址覆盖
      klineData.value = newData;
    } catch (error) {
      // 拦截非标准 JSON，防止前端线程崩溃
    }
  };
};

const goToLogin = () => {
  router.push('/login')
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
    // 只获取关注列表，不获取涨跌幅（涨跌幅按天变化，不需要实时更新）
    const response = await watchlistApi.getPublic()
    const newData = response.data
    
    // 保留现有的涨跌幅数据
    for (const newItem of newData) {
      const existingItem = watchlistData.value.find(item => item.crypto_symbol === newItem.crypto_symbol)
      if (existingItem && existingItem.change_24h !== undefined) {
        newItem.change_24h = existingItem.change_24h
      }
    }
    
    watchlistData.value = newData
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
  
  startPriceRefresh()
})

onUnmounted(() => {
  // stopAutoRefresh() // <- 删掉这行
  stopPriceRefresh()
  if (klineWs) {
    klineWs.close()
  }
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
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.watchlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
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

.item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.item-price {
  font-size: 16px;
  font-weight: bold;
  color: #409eff;
  font-family: 'Monaco', monospace;
}

.item-change {
  font-size: 14px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: 'Monaco', monospace;
}

.change-up {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.1);
}

.change-down {
  color: #67c23a;
  background: rgba(103, 194, 58, 0.1);
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
  margin-bottom: 0;
  position: relative;
}

.empty-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 1;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  z-index: 10;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.kline-info-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 12px;
  margin-top: 5px;
}

.info-symbol {
  font-weight: bold;
  color: #303133;
  font-size: 13px;
}

.info-time {
  color: #909399;
  font-size: 11px;
}

.info-item {
  color: #606266;
}

.info-value {
  font-weight: 600;
  font-family: 'Monaco', monospace;
  margin-left: 1px;
}

.text-up {
  color: #f56c6c;
}

.text-down {
  color: #67c23a;
}

.change-up {
  color: #f56c6c;
  font-weight: 600;
}

.change-down {
  color: #67c23a;
  font-weight: 600;
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
  
  :deep(.el-dialog) {
    width: 100% !important;
    margin: 0 !important;
    max-width: 100% !important;
    border-radius: 0 !important;
  }
  
  :deep(.el-dialog__header) {
    padding: 10px 12px !important;
    margin: 0 !important;
  }
  
  :deep(.el-dialog__body) {
    padding: 0 8px 10px !important;
  }
  
  .kline-dialog-content {
    overflow-x: hidden;
  }
  
  .dialog-chart-container {
    width: 100%;
    overflow: hidden;
    margin: 0;
    padding: 0;
  }
  
  .dialog-chart-container :deep(canvas) {
    width: 100% !important;
  }
  
  .dialog-control-row {
    padding: 8px !important;
    margin-bottom: 8px !important;
  }
  
  .dialog-stats {
    padding: 8px !important;
    margin: 0 !important;
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
  
  .watchlist-card :deep(.el-card__header) {
    padding: 8px 12px;
  }
  
  .card-title {
    font-size: 13px;
  }
  
  .card-header {
    min-height: auto;
  }
  
  .watchlist-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  
  .watchlist-item {
    padding: 10px 12px;
  }
  
  .item-name {
    font-size: 12px;
  }
  
  .item-price {
    font-size: 13px;
  }
  
  .item-change {
    font-size: 11px;
    padding: 2px 5px;
  }
  
  .dialog-control-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    padding: 12px;
  }
  
  .dialog-control-item {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: nowrap;
    gap: 8px;
  }
  
  .dialog-control-item:first-child {
    justify-content: space-between;
  }
  
  .dialog-control-item label {
    font-size: 12px;
    min-width: 60px;
    flex-shrink: 0;
  }
  
  .dialog-control-item .el-radio-group {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    -ms-overflow-style: none;
    flex: 1;
  }
  
  .dialog-control-item .el-radio-group::-webkit-scrollbar {
    display: none;
  }
  
  .dialog-control-item .el-radio-group :deep(.el-radio-button) {
    flex-shrink: 0;
  }
  
  .dialog-control-item .el-radio-group :deep(.el-radio-button__inner) {
    font-size: 12px;
    white-space: nowrap;
  }
  
  .dialog-control-item .el-radio-group::-webkit-scrollbar {
    display: none;
  }
  
  .dialog-control-item .el-radio-group :deep(.el-radio-button) {
    flex-shrink: 0;
    margin-right: 0 !important;
  }
  
  .dialog-control-item .el-radio-group :deep(.el-radio-button__inner) {
    padding: 6px 10px;
    font-size: 12px;
    white-space: nowrap;
    border-radius: 4px;
    border: 1px solid #dcdfe6;
  }
  
  .dialog-control-item:last-child {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
  }
  
  .dialog-control-item .el-select {
    width: 100px !important;
    flex-shrink: 0;
  }
  
  .dialog-control-item .refresh-btn {
    flex-shrink: 0;
    min-width: 70px;
    padding: 8px 16px;
    font-size: 12px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
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

/* ==========================================
   K线弹窗亮色主题样式
========================================== */
.kline-dialog-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.kline-dialog-content {
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  background-color: #ffffff;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0,0,0,0.1);
  overflow: hidden;
}

/* 头部信息区 */
.kline-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  background-color: #ffffff;
  border-bottom: 1px solid #ebeef5;
  position: relative;
}

.symbol-info h2 {
  color: #303133;
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  font-family: 'Monaco', monospace;
}

.crypto-name {
  color: #909399;
  font-size: 13px;
  margin-top: 2px;
  display: block;
}

.price-info {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-left: 40px;
}

.current-price {
  font-size: 26px;
  font-weight: bold;
  font-family: 'Monaco', monospace;
  color: #303133;
}

.change-percent {
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  position: absolute;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #909399;
  font-size: 28px;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #409eff;
}

/* 控制工具栏 */
.kline-toolbar {
  padding: 0 24px;
  background-color: #f8f9fa;
  border-bottom: 1px solid #ebeef5;
}

.interval-selector {
  display: flex;
  gap: 24px;
}

.interval-btn {
  color: #606266;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 12px 0;
  position: relative;
  transition: color 0.2s;
}

.interval-btn:hover {
  color: #303133;
}

.interval-btn.active {
  color: #409eff;
}

.interval-btn.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #409eff;
}

/* 核心绘图区 */
.kline-chart-container {
  flex: 1;
  position: relative;
  background-color: #ffffff;
  padding: 10px 0;
}

.empty-placeholder {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  background: #ffffff;
  z-index: 1;
}

.loading-overlay {
  background: rgba(255, 255, 255, 0.8);
}

/* ========== 头部重构样式 ========== */
.kline-header-toolbar {
  padding: 16px 24px 0;
  background-color: #ffffff;
  border-bottom: 1px solid #ebeef5;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-middle {
  margin-top: 4px;
}

.header-bottom {
  margin-top: 16px;
  overflow-x: auto;
  white-space: nowrap;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none; /* Firefox */
}
.header-bottom::-webkit-scrollbar {
  display: none; /* Chrome/Safari */
}

.custom-interval-selector {
  display: flex;
  gap: 24px;
  padding-bottom: 8px;
}

.interval-btn {
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  font-weight: 500;
  padding-bottom: 4px;
  transition: all 0.2s;
}

.interval-btn:hover {
  color: #303133;
}

.interval-btn.active {
  color: #409eff;
  font-weight: bold;
  border-bottom: 2px solid #409eff;
}

/* 覆盖原有的绝对定位 close-btn */
.kline-header-toolbar .close-btn {
  position: static;
  transform: none;
}

/* --- K线弹窗重构样式追加 --- */

/* 头部主区域弹性布局：横向排列，垂直居中 */
.header-main {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px; /* 元素之间的间距 */
  width: 100%;
}

/* 占据剩余空间，将关闭按钮挤到最右边 */
.flex-spacer {
  flex: 1;
}

/* 现代化圆形关闭按钮 */
.kline-header-toolbar .close-btn {
  background: #f0f2f5;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  color: #909399;
  transition: all 0.2s ease;
}

.kline-header-toolbar .close-btn:hover {
  background: #e4e7ed;
  color: #f56c6c; /* 悬浮时变红警告 */
}

/* 实时数据条：背景卡片化与网格间距 */
.realtime-data-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 15px;
  padding: 10px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

/* 单个数据项：标签置灰，数值加粗，采用等宽字体对齐 */
.data-item {
  display: flex;
  gap: 6px;
  font-size: 13px;
  font-family: 'Monaco', monospace;
}

.data-item .label {
  color: #909399;
}

.data-item .value {
  color: #303133;
  font-weight: 600;
}

/* ==========================================
   强制修复弹窗头部排版错位 (新手专属补丁)
========================================== */

/* 1. 强制左右分开布局 */
.header-main {
  display: flex !important;
  justify-content: space-between !important; /* 让币种在左边，价格在右边 */
  align-items: center !important;
  width: 100% !important;
  padding-bottom: 10px;
}

/* 2. 左侧币种名称对齐 */
.symbol-info {
  display: flex !important;
  align-items: baseline !important;
  gap: 10px;
}
.symbol-info h2 {
  margin: 0;
  font-size: 24px;
  color: #1f2937;
  font-family: 'Monaco', monospace;
}

/* 3. 右侧容器（把价格和关闭按钮捆绑在一起） */
.header-right {
  display: flex !important;
  align-items: center !important;
  gap: 20px !important;
}

/* 4. 清除恶心的背景色，只留文字颜色 */
.price-info {
  display: flex !important;
  align-items: baseline !important;
  gap: 10px !important;
  background: transparent !important; /* 强制透明背景 */
  padding: 0 !important;
}

.current-price {
  font-size: 26px !important;
  font-weight: bold;
  font-family: 'Monaco', monospace;
}
.change-percent {
  font-size: 16px !important;
  font-weight: bold;
}

/* 文字颜色翻转，根据你的截图是红涨绿跌 */
.text-up { color: #f56c6c !important; }
.text-down { color: #2ebd85 !important; }

/* 5. 修复关闭按钮，干掉绝对定位 */
.kline-header-toolbar .close-btn {
  position: static !important; /* 清除错位元凶 */
  transform: none !important;
  background: #f4f4f5 !important;
  border: none !important;
  border-radius: 50% !important;
  width: 32px !important;
  height: 32px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  cursor: pointer !important;
  font-size: 18px !important;
  color: #909399 !important;
}
.kline-header-toolbar .close-btn:hover {
  background: #f56c6c !important;
  color: #fff !important;
}

/* ==========================================
   排版修复：左右对齐与单行周期栏
========================================== */
.header-main {
  display: flex !important;
  justify-content: space-between !important; /* 强制左(币种)右(关闭按钮)两端对齐 */
  align-items: center !important;
  width: 100% !important;
  padding-bottom: 8px;
}

/* 修复关闭按钮样式 */
.kline-header-toolbar .close-btn {
  position: static !important;
  transform: none !important;
  font-size: 28px !important;
  color: #909399 !important;
  background: transparent !important;
  border: none !important;
  cursor: pointer !important;
  padding: 0 5px !important;
}

.kline-header-toolbar .close-btn:hover {
  color: #f56c6c !important;
}

/* 强制周期栏保持单行（溢出时可滑动） */
.header-bottom {
  width: 100% !important;
  overflow-x: auto !important;
  white-space: nowrap !important;
}

.custom-interval-selector {
  display: flex !important;
  flex-wrap: nowrap !important; /* 绝对禁止换行 */
  gap: 16px !important;
}

.main-interval-text {
  font-size: 16px;
  color: #606266;
  margin-left: 8px;
  font-weight: normal; /* 不加粗，以区分主币种 */
}

.kline-chart-container {
  flex: 1;
  position: relative;
  background-color: #ffffff;
  padding: 10px 0;
  /* 新增下面两行，锁死高度，防止 Canvas 溢出 */
  min-height: 0 !important; 
  overflow: hidden; 
}
</style>