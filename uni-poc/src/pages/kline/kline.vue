<template>
  <!-- @update: 弹窗打开时锁定页面滚动，避免穿透滑动底层关注列表（uni-app page-meta） -->
  <page-meta v-if="klineDialogVisible" page-style="overflow:hidden;" />
  <view class="page-container" :class="{ 'dark-mode': isDarkMode }">
    <view class="page-header">
      <view class="header-content">
        <view class="header-left">
          <text class="title">📈 K线图</text>
          <text class="subtitle">实时查看关注币种的K线走势</text>
        </view>
        <view class="header-right">
          <view class="dark-mode-btn" @tap="toggleDarkMode">
            <text>{{ isDarkMode ? '☀️' : '🌙' }}</text>
          </view>
          <view class="login-btn" @tap="goToLogin">
            <text>系统登录</text>
          </view>
        </view>
      </view> 
    </view>

    <view class="page-main">
      <view class="watchlist-card">
        <view class="card-header">
          <text class="card-title">🔥 关注列表</text>
          <view class="refresh-btn" @tap="loadWatchlist">
            <text v-if="loadingWatchlist">加载中...</text>
            <text v-else>↻ 刷新</text>
          </view>
        </view>
        
        <view class="watchlist-grid">
          <view 
            v-for="item in watchlistData" 
            :key="item.crypto_symbol"
            class="watchlist-item"
            @tap="openKlineDialog(item)"
          >
            <view class="item-left">
              <text class="item-symbol">{{ item.crypto_symbol }}</text>
              <text class="item-name">{{ item.crypto_name }}</text>
            </view>
            <view class="item-right">
              <text class="item-price">${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}</text>
              <view class="item-change" :class="getChangeClass(item.change_24h)">
                <text class="change-text">{{ formatChange(item.change_24h) }}</text>
              </view>
            </view>
          </view>
          
          <view v-if="!loadingWatchlist && watchlistData.length === 0" class="empty-status">
            <text>暂无关注数据</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 遮罩层单独拦截 touchmove（仅点击半透明区域时），内容区事件不冒泡到遮罩，避免影响图表手势 -->
    <view class="kline-dialog-overlay" v-if="klineDialogVisible">
      <view class="kline-dialog-mask" @tap="closeKlineDialog" @touchmove.stop.prevent="noopTouchHandler" />
      <view class="kline-dialog-content" @tap.stop>
        
        <view class="kline-header-toolbar">
          <view class="header-main">
            <view class="symbol-info">
              <text class="symbol-title">{{ selectedSymbol }}</text>
              <text class="main-interval-text">
                {{ selectedInterval === '1d' ? '1天' : (intervalLabelMap[selectedInterval] || selectedInterval) }}
              </text>
            </view>
            <view class="close-btn" @tap="closeKlineDialog">×</view>
          </view>

          <view class="realtime-data-bar" v-if="realtimeObj">
            <view class="data-item"><text class="label">时间</text><text class="value">{{ realtimeObj.time }}</text></view>
            <view class="data-item"><text class="label">开</text><text class="value">{{ realtimeObj.open }}</text></view>
            <view class="data-item"><text class="label">高</text><text class="value">{{ realtimeObj.high }}</text></view>
            <view class="data-item"><text class="label">低</text><text class="value">{{ realtimeObj.low }}</text></view>
            <view class="data-item"><text class="label">收</text><text class="value" :class="Number(realtimeObj.changePercent) >= 0 ? 'text-up' : 'text-down'">{{ realtimeObj.close }}</text></view>
            <view class="data-item"><text class="label">涨跌幅</text><text class="value" :class="Number(realtimeObj.changePercent) >= 0 ? 'text-up' : 'text-down'">{{ realtimeObj.changePercent }}%</text></view>
            <view class="data-item"><text class="label">振幅</text><text class="value">{{ realtimeObj.amplitude }}%</text></view>
            <view class="data-item"><text class="label">成交量</text><text class="value">{{ realtimeObj.volume }}</text></view>
          </view>

          <scroll-view scroll-x class="header-bottom" :show-scrollbar="false">
            <view class="custom-interval-selector">
              <view 
                v-for="interval in ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']" 
                :key="interval"
                class="interval-btn"
                :class="{ active: selectedInterval === interval }"
                @tap="changeInterval(interval)"
              >
                <text>{{ intervalLabelMap[interval] || interval }}</text>
              </view>
            </view>
          </scroll-view>
        </view>

        <view class="kline-chart-container" @touchend="clearTooltip" @touchcancel="clearTooltip">
          <l-echart ref="chartRef" class="chart"></l-echart>
          
          <view v-if="loading" class="loading-overlay">
            <view class="loading-spinner"></view>
          </view>
          <view v-if="!loading && klineData.length === 0" class="empty-placeholder">
            <text>暂无K线数据</text>
          </view>
        </view>

      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { klinesApi, watchlistApi, systemSettingsApi } from '@/api'

/** 桌面端 K 线/成交量双 grid 比例（与 ECharts 百分比布局一致） */
const DESKTOP_CHART_GRID = {
  MAIN_BOTTOM: '26%',
  VOL_HEIGHT: '16%',
  VOL_BOTTOM: '4%'
} as const
/** 移动端：抬高主图底部、加高成交量区与底边距，避免成交量柱被裁切 */
const MOBILE_CHART_GRID = {
  MAIN_BOTTOM: '34%',
  VOL_HEIGHT: '22%',
  VOL_BOTTOM: '11%'
} as const

// 遮罩层 touchmove 占位：用于 .prevent 阻止默认滚动穿透（函数体需存在）
const noopTouchHandler = () => {}

const isDarkMode = ref(false)
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  uni.setNavigationBarColor({
    frontColor: isDarkMode.value ? '#ffffff' : '#000000',
    backgroundColor: isDarkMode.value ? '#1a1a2e' : '#ffffff',
    animation: { duration: 200, timingFunc: 'easeIn' }
  })
}

const chartRef = ref<any>(null)
let chartInstance: any = null
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
// @update: 追踪用户当前查看的K线索引，使上方信息列表跟随图表交互变化
const hoveredDataIndex = ref<number | null>(null)
// @update: 图例显隐由用户控制；setOption(true) 全量替换会丢失选中态，故持久化并在 option 中回写
const legendSelected = ref<Record<string, boolean>>({ K线: true, 成交量: true })

let socketTask: UniApp.SocketTask | null = null;
let priceRefreshTimer: ReturnType<typeof setInterval> | null = null
let refreshInterval = 5

// 判断是否为移动端屏幕以动态调整 ECharts 的边距
const isMobile = ref(false)
try {
  isMobile.value = uni.getSystemInfoSync().windowWidth < 768
} catch(e) {}

const intervalLabelMap: Record<string, string> = {
  '1m': '1分钟', '5m': '5分钟', '15m': '15分钟', '30m': '30分钟',
  '1h': '1小时', '4h': '4小时', 
  '1d': '日线', '1w': '周线', '1M': '月线'
}

const formatChange = (change: number | undefined | null) => {
  if (change === undefined || change === null || isNaN(change)) return '--'
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

const getChangeClass = (change: number | undefined | null) => {
  if (change === undefined || change === null || isNaN(change)) return ''
  return change >= 0 ? 'change-up' : 'change-down'
}

const clearTooltip = () => {
  hoveredDataIndex.value = null
  setTimeout(() => {
    if (chartInstance && chartInstance.dispatchAction) {
      chartInstance.dispatchAction({ type: 'hideTip' });
    }
  }, 10); 
}

const goToLogin = () => {
  uni.navigateTo({ url: '/pages/login/login' })
}

const realtimeObj = computed(() => {
  if (klineData.value.length === 0) return null;
  // 当用户正在交互时取对应索引，否则取最新一根K线
  const idx = hoveredDataIndex.value !== null 
    ? hoveredDataIndex.value 
    : klineData.value.length - 1;
  const data = klineData.value[idx]; 
  
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

// 图表配置 (完美还原 Vue 代码)
const chartOption = computed(() => {
  const dark = isDarkMode.value
  const bgColor = dark ? '#1a1a2e' : '#ffffff'
  const textColor = dark ? '#a0a0b0' : '#909399'
  const borderColor = dark ? '#2a2a3e' : '#ebeef5'
  const splitAreaColor = dark ? 'rgba(255,255,255,0.03)' : 'rgba(245,247,250,0.5)'
  const tooltipBg = dark ? '#2a2a3e' : '#ffffff'
  const tooltipBorder = dark ? '#3a3a5e' : '#ebeef5'
  const tooltipLabel = dark ? '#8080a0' : '#909399'
  
  // 原版红绿颜色
  const upColor = '#f56c6c'
  const downColor = '#67c23a'

  if (klineData.value.length === 0) {
    return { backgroundColor: bgColor, title: { text: '' }, series: [] }
  }

  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    const interval = selectedInterval.value
    if (['1m', '5m', '15m', '30m'].includes(interval)) {
      return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    } else if (['1h', '2h', '4h', '6h', '12h'].includes(interval)) {
      return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:00`
    } else if (['1d', '3d', '1w'].includes(interval)) {
      return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
    } else if (interval === '1M') {
      return `${date.getFullYear()}/${date.getMonth() + 1}`
    }
    return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`
  }

  const dates = klineData.value.map(k => formatTime(k.open_time))
  const ohlcData = klineData.value.map(k => [parseFloat(k.open), parseFloat(k.close), parseFloat(k.low), parseFloat(k.high)])
  
  // 核心修复：彻底解决 RenderJS 函数失效导致成交量发白的问题
  const volumeData = klineData.value.map(k => {
    const isUp = parseFloat(k.close) >= parseFloat(k.open);
    return {
      value: parseFloat(k.volume),
      itemStyle: { color: isUp ? upColor : downColor, opacity: 0.6 }
    }
  });

  // 动态边距计算：电脑端为 8%，移动端为 2% 防止过窄
  const sideMargin = isMobile.value ? '2%' : '8%'
  const gridSpec = isMobile.value ? MOBILE_CHART_GRID : DESKTOP_CHART_GRID

  return {
    backgroundColor: bgColor,
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { color: dark ? '#4a4a6e' : '#dcdfe6' } },
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: dark ? '#d0d0e0' : '#303133', fontSize: 12 },
      // 还原原版富文本悬浮窗
      formatter: (params: any) => {
        const kline = params[0]
        if (!kline) return ''
        const dataIndex = kline.dataIndex
        const data = klineData.value[dataIndex]
        if(!data) return ''

        const timeStr = formatTime(data.open_time)
        const openVal = parseFloat(data.open)
        const closeVal = parseFloat(data.close)
        const highVal = parseFloat(data.high)
        const lowVal = parseFloat(data.low)
        const volVal = parseFloat(data.volume)
        
        const change = openVal ? (((closeVal - openVal) / openVal) * 100).toFixed(2) : '0.00'
        const amplitude = openVal ? (((highVal - lowVal) / openVal) * 100).toFixed(2) : '0.00'
        const color = closeVal >= openVal ? upColor : downColor
        const sign = closeVal >= openVal ? '+' : ''
        
        return `
          <div style="font-family: Monaco, monospace; font-size: 12px; min-width: 140px;">
            <div style="color: ${tooltipLabel}; margin-bottom: 8px; font-weight: bold;">${timeStr}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>开盘</span> <span>${openVal.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最高</span> <span style="color: ${upColor};">${highVal.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最低</span> <span style="color: ${downColor};">${lowVal.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>收盘</span> <span style="color: ${color}; font-weight: bold;">${closeVal.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid ${tooltipBorder}; margin-top: 6px; padding-top: 6px;">
              <span>涨跌幅</span> <span style="color: ${color};">${sign}${change}%</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px;"><span>振幅</span> <span>${amplitude}%</span></div>
            <div style="display: flex; justify-content: space-between; margin-top: 4px;"><span>成交量</span> <span>${volVal.toFixed(2)}</span></div>
          </div>
        `
      }
    },
    legend: {
      data: ['K线', '成交量'],
      selected: { ...legendSelected.value },
      left: 'center',
      top: 0,
      textStyle: { fontSize: 11, color: textColor }
    },
    grid: [
      { left: sideMargin, right: sideMargin, top: 30, bottom: gridSpec.MAIN_BOTTOM },
      { left: sideMargin, right: sideMargin, height: gridSpec.VOL_HEIGHT, bottom: gridSpec.VOL_BOTTOM }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLine: { onZero: false, lineStyle: { color: borderColor } }, splitLine: { show: false }, axisLabel: { fontSize: 11, color: textColor } },
      { type: 'category', gridIndex: 1, data: dates, axisLabel: { show: false }, axisLine: { onZero: false, lineStyle: { color: borderColor } }, splitLine: { show: false } }
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitArea: { show: true, areaStyle: { color: [splitAreaColor, 'transparent'] } }, axisLabel: { fontSize: 11, color: textColor }, splitLine: { lineStyle: { color: borderColor } } },
      { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false }, axisLine: { show: false }, splitLine: { show: false } }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: savedDataZoom.value ? savedDataZoom.value.start : 70, end: savedDataZoom.value ? savedDataZoom.value.end : 100 }
    ],
    series: [
      {
        name: 'K线', type: 'candlestick', data: ohlcData, xAxisIndex: 0, yAxisIndex: 0,
        itemStyle: { color: upColor, color0: downColor, borderColor: upColor, borderColor0: downColor }
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumeData
      }
    ]
  }
})

// 增量合并更新：保留用户图例选中、dataZoom 等交互状态（避免 setOption 第二个参数 true 导致图例被刷回）
watch(
  () => chartOption.value,
  (newVal) => {
    if (klineData.value.length === 0 || !chartInstance) return
    chartInstance.setOption(newVal, { lazyUpdate: true })
  },
  { deep: true }
)

const bindChartInteractionOnce = (chart: any) => {
  chart.off('datazoom')
  chart.off('legendselectchanged')
  chart.off('showTip')
  chart.on('showTip', (params: any) => {
    if (params.dataIndex !== undefined) {
      hoveredDataIndex.value = params.dataIndex
    }
  })
  chart.on('datazoom', (params: any) => {
    if (params.batch && params.batch.length > 0) {
      savedDataZoom.value = { start: params.batch[0].start, end: params.batch[0].end }
    }
  })
  chart.on('legendselectchanged', (e: any) => {
    if (e?.selected) legendSelected.value = { ...legendSelected.value, ...e.selected }
  })
}

const scheduleChartResize = () => {
  nextTick(() => {
    setTimeout(() => {
      try {
        chartRef.value?.resize?.()
      } catch (e) {}
    }, 200)
  })
}

const loadWatchlist = async () => {
  loadingWatchlist.value = true
  try {
    const watchlistRes = await watchlistApi.getAllWatchlist()
    const data = watchlistRes.data
    for (const item of data) item.change_24h = null
    data.sort((a: any, b: any) => (a.sort_order || 0) - (b.sort_order || 0))
    watchlistData.value = data
    
    klinesApi.getWatchlistKlines('1d', 2).then(klinesRes => {
      const klinesData = klinesRes.data?.data || {}
      for (const item of watchlistData.value) {
        const symbolData = klinesData[item.crypto_symbol]
        const symbolKlines = symbolData?.klines || []
        if (symbolKlines.length > 0) {
          const latestKline = symbolKlines[symbolKlines.length - 1]
          const open = parseFloat(latestKline.open)
          const close = parseFloat(latestKline.close)
          if (open && close) item.change_24h = ((close - open) / open) * 100
        }
      }
    }).catch(() => {})
  } catch (error) {
    uni.showToast({ title: '加载关注列表失败', icon: 'none' })
  } finally {
    loadingWatchlist.value = false
  }
}

const openKlineDialog = async (item: any) => {
  selectedSymbol.value = item.crypto_symbol
  selectedCryptoName.value = item.crypto_name
  legendSelected.value = { K线: true, 成交量: true }
  klineDialogVisible.value = true

  // 给予弹窗动画和 DOM 挂载时间，避免 canvas 高度为 0；初始化后 resize 一次
  setTimeout(() => {
    if (chartRef.value && !chartInstance) {
      chartRef.value.init(echarts, (chart: any) => {
        chartInstance = chart
        bindChartInteractionOnce(chart)
        chart.setOption(chartOption.value, true)
        scheduleChartResize()
      })
    } else if (chartInstance) {
      scheduleChartResize()
    }
  }, 150)

  await loadKlineData()
  connectWebSocket(selectedSymbol.value)
}

const closeKlineDialog = () => {
  if (socketTask) {
    socketTask.close({})
    socketTask = null
  }
  klineDialogVisible.value = false
  selectedSymbol.value = ''
  selectedCryptoName.value = ''
  klineData.value = []
  hoveredDataIndex.value = null
  legendSelected.value = { K线: true, 成交量: true }
  chartInstance = null
}

const loadKlineData = async (silent = false) => {
  if (!selectedSymbol.value) return
  if (!silent) loading.value = true
  try {
    const response = await klinesApi.getKlines(selectedSymbol.value, selectedInterval.value, selectedLimit.value)
    if (response.data && response.data.success) {
      klineData.value = response.data.data.klines || []
    }
  } catch (error: any) {
    if (!silent) uni.showToast({ title: '获取K线失败', icon: 'none' })
  } finally {
    loading.value = false
    // 数据到达后容器高度已确定，再 resize 一次避免成交量区域高度为 0 或未撑满
    if (klineDialogVisible.value && chartInstance) scheduleChartResize()
  }
}

const changeInterval = async (newInterval: string) => {
  if (selectedInterval.value === newInterval) return; 
  selectedInterval.value = newInterval;
  hoveredDataIndex.value = null;
  if (socketTask) {
    socketTask.close({})
    socketTask = null;
  }
  await loadKlineData();
  connectWebSocket(selectedSymbol.value);
}

const connectWebSocket = (symbol: string) => {
  if (socketTask) socketTask.close({});
  
  let wsHost = '127.0.0.1:8080' 
  let wsProtocol = 'ws:'
  // #ifdef H5
  wsHost = window.location.host;
  wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // #endif
  // #ifndef H5
  wsHost = 'your-api-domain.com'; 
  wsProtocol = 'wss:';
  // #endif

  const wsUrl = `${wsProtocol}//${wsHost}/api/klines/ws/${symbol}`;
  
  socketTask = uni.connectSocket({
    url: wsUrl,
    complete: () => {}
  });

  socketTask.onMessage((res) => {
    try {
      if (!res.data || res.data === 'undefined') return;
      const newKline = JSON.parse(res.data as string);
      if (!newKline || typeof newKline.close === 'undefined' || klineData.value.length === 0) return;
      
      const lastIndex = klineData.value.length - 1;
      const lastKline = klineData.value[lastIndex];
      const currentPrice = parseFloat(newKline.close);
      const newData = [...klineData.value];

      newData[lastIndex] = { 
        ...lastKline, 
        close: currentPrice,
        high: Math.max(lastKline.high, currentPrice),
        low: Math.min(lastKline.low, currentPrice)
      };

      if (selectedInterval.value === '1m' && newKline.open_time > lastKline.open_time) {
        newData.push(newKline);
        if (newData.length > selectedLimit.value) newData.shift();
      }

      klineData.value = newData;
    } catch (error) {}
  });

  socketTask.onClose(() => {
    socketTask = null;
  });
}

const startPriceRefresh = () => {
  priceRefreshTimer = setInterval(() => {
    loadWatchlistBackground()
  }, refreshInterval * 1000)
}

const stopPriceRefresh = () => {
  if (priceRefreshTimer) {
    clearInterval(priceRefreshTimer)
    priceRefreshTimer = null
  }
}

const loadWatchlistBackground = async () => {
  try {
    const response = await watchlistApi.getAllWatchlist()
    const newData = response.data
    for (const newItem of newData) {
      const existingItem = watchlistData.value.find(item => item.crypto_symbol === newItem.crypto_symbol)
      if (existingItem && existingItem.change_24h !== undefined) {
        newItem.change_24h = existingItem.change_24h
      }
    }
    watchlistData.value = newData
  } catch (error) {}
}

const loadPublicSettings = async (): Promise<number> => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) return response.data.refresh_interval || 5
  } catch (error) {}
  return 5
}

onMounted(async () => {
  loadWatchlist()
  refreshInterval = await loadPublicSettings()
  startPriceRefresh()
})

onUnmounted(() => {
  stopPriceRefresh()
  if (socketTask) socketTask.close({})
})
</script>

<style scoped>
/* ==========================================
   页面主框架 (还原 Vue Web 版样式)
========================================== */
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; display: flex; flex-direction: column; }
.page-header { background: #ffffff; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; width: 100%; }
.header-left { display: flex; flex-direction: column; }
.title { font-size: 22px; color: #409eff; font-weight: bold; letter-spacing: 0.5px; }
.subtitle { font-size: 13px; color: #909399; margin-top: 6px; }
.header-right { display: flex; align-items: center; gap: 10px; }
.dark-mode-btn { padding: 6px 12px; border: 1px solid #e4e7ed; border-radius: 4px; }
.login-btn { padding: 8px 16px; background: rgba(64,158,255,0.1); color: #409eff; border: 1px solid #b3d8ff; border-radius: 4px; font-size: 14px; }

.page-main { padding: 20px 25px; flex: 1; max-width: 1200px; margin: 0 auto; width: 100%; box-sizing: border-box; }
.watchlist-card { background: #ffffff; border-radius: 10px; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); margin-bottom: 20px; overflow: hidden; }
.card-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; border-bottom: 1px solid #ebeef5; }
.card-title { font-weight: 600; color: #303133; font-size: 15px; }
.refresh-btn { font-size: 13px; color: #409eff; padding: 4px 8px; }

.watchlist-grid { padding: 15px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.watchlist-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: #f8f9fa; border-radius: 10px; border: 1px solid #f0f2f5; transition: all 0.2s ease; }
.item-left { display: flex; flex-direction: column; gap: 2px; }
.item-symbol { font-size: 15px; font-weight: 700; color: #1a1a2e; letter-spacing: 0.5px; }
.item-name { font-size: 12px; color: #909399; }
.item-right { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.item-price { font-size: 15px; font-weight: bold; color: #409eff; font-family: 'Monaco', monospace; }
.item-change { font-size: 13px; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-family: 'Monaco', monospace; }

.change-up { background: rgba(245, 108, 108, 0.1); }
.change-up .change-text { color: #f56c6c; }
.change-down { background: rgba(103, 194, 58, 0.1); }
.change-down .change-text { color: #67c23a; }
.text-up { color: #f56c6c !important; }
.text-down { color: #67c23a !important; }

.empty-status { text-align: center; color: #909399; font-size: 14px; padding: 30px 0; grid-column: 1 / -1; }

/* ==========================================
   K线弹窗 - 严格遵守 Vue 原版布局
========================================== */
/* 背景色移到 mask，便于内容浮在遮罩之上且单独拦截 mask 的 touchmove */
.kline-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.kline-dialog-mask {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
}

.kline-dialog-content {
  position: relative;
  z-index: 1;
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  min-height: 500px;
  background-color: #ffffff;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.kline-header-toolbar { padding: 16px 24px 0; background-color: #ffffff; border-bottom: 1px solid #ebeef5; flex-shrink: 0; }
.header-main { display: flex; justify-content: space-between; align-items: center; width: 100%; padding-bottom: 8px; }

.symbol-info { display: flex; align-items: baseline; gap: 10px; }
.symbol-title { font-size: 24px; color: #1f2937; font-weight: bold; font-family: 'Monaco', monospace; }
.main-interval-text { font-size: 16px; color: #606266; font-weight: normal; }

.close-btn { 
  background: #f4f4f5; border-radius: 50%; width: 32px; height: 32px; 
  display: flex; align-items: center; justify-content: center; 
  color: #909399; font-size: 20px; font-weight: bold; cursor: pointer; transition: all 0.2s ease;
}

/* 完美还原 Vue 版包裹效果 */
.realtime-data-bar { 
  display: flex; flex-wrap: wrap; gap: 16px; margin-top: 15px; 
  padding: 10px 16px; background: #f8f9fa; border-radius: 8px; border: 1px solid #ebeef5; 
}
.data-item { display: flex; gap: 6px; font-size: 13px; font-family: 'Monaco', monospace; }
.data-item .label { color: #909399; }
.data-item .value { color: #303133; font-weight: 600; }

.header-bottom { width: 100%; white-space: nowrap; margin-top: 16px; box-sizing: border-box; }
.custom-interval-selector { display: flex; flex-wrap: nowrap; gap: 16px; padding-bottom: 8px; }
.interval-btn { font-size: 14px; color: #909399; font-weight: 500; padding-bottom: 4px; transition: all 0.2s; flex-shrink: 0; }
.interval-btn.active text { color: #409eff; font-weight: bold; border-bottom: 2px solid #409eff; padding-bottom: 4px; }

.kline-chart-container { 
  flex: 1; 
  width: 100%; 
  min-height: 0; /* 这是 Flex 解决重叠问题的关键 */
  position: relative; 
  background-color: #ffffff; 
  padding: 10px 0; 
  box-sizing: border-box; 
}

.chart { 
  width: 100%; height: 100%; display: block; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
}

.loading-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255, 255, 255, 0.8); display: flex; justify-content: center; align-items: center; z-index: 10; }
.loading-spinner { width: 32px; height: 32px; border: 3px solid #f3f3f3; border-top: 3px solid #409eff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.empty-placeholder { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; color: #909399; z-index: 1; background: #ffffff;}

/* ==========================================
   夜间模式
========================================== */
.page-container.dark-mode { background-color: #0f0f1a; }
.page-container.dark-mode .page-header { background: #1a1a2e; border-bottom-color: #2a2a3e; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.page-container.dark-mode .title { color: #60a5fa; }
.page-container.dark-mode .subtitle { color: #8080a0; }
.page-container.dark-mode .watchlist-card { background: #1a1a2e; border-color: #2a2a3e; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.3); }
.page-container.dark-mode .card-title { color: #d0d0e0; }
.page-container.dark-mode .card-header { border-bottom-color: #2a2a3e; }
.page-container.dark-mode .watchlist-item { background: #16162a; border-color: #2a2a3e; }
.page-container.dark-mode .item-name { color: #8080a0; }
.page-container.dark-mode .item-symbol { color: #e0e0f0; }
.page-container.dark-mode .item-price { color: #60a5fa; }

.page-container.dark-mode .kline-dialog-mask { background: rgba(0, 0, 0, 0.7); }
.page-container.dark-mode .kline-dialog-content { background-color: #1a1a2e; }
.page-container.dark-mode .kline-header-toolbar { background-color: #1a1a2e; border-bottom-color: #2a2a3e; }
.page-container.dark-mode .symbol-title { color: #e0e0f0; }
.page-container.dark-mode .main-interval-text { color: #a0a0b0; }
.page-container.dark-mode .close-btn { background: #2a2a3e; color: #a0a0b0; }
.page-container.dark-mode .realtime-data-bar { background: #16162a; border-color: #2a2a3e; }
.page-container.dark-mode .data-item .label { color: #8080a0; }
.page-container.dark-mode .data-item .value { color: #d0d0e0; }
.page-container.dark-mode .interval-btn { color: #8080a0; }
.page-container.dark-mode .interval-btn.active text { color: #60a5fa; border-bottom-color: #60a5fa; }
.page-container.dark-mode .kline-chart-container { background-color: #1a1a2e; }
.page-container.dark-mode .loading-overlay { background: rgba(26, 26, 46, 0.8); }
.page-container.dark-mode .empty-placeholder { background: #1a1a2e; color: #8080a0; }

/* ==========================================
   移动端响应式 (1:1 原版适配)
========================================== */
@media (max-width: 768px) {
  .page-container { padding-bottom: 40px; }
  .page-main { padding: 8px; }
  .page-header { padding: 6px 12px; }
  
  .header-content { flex-direction: row; flex-wrap: nowrap; gap: 0; }
  .title { font-size: 16px; }
  .subtitle { font-size: 11px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  
  .watchlist-grid { grid-template-columns: 1fr; gap: 6px; }
  .watchlist-item { padding: 8px 10px; }

  /* 移动端：非满屏居中卡片；上下多留空白（与 max-height 中的 80px 对应：40+40） */
  .kline-dialog-overlay {
    padding: 40px 16px;
    padding-bottom: calc(40px + env(safe-area-inset-bottom, 0px));
    box-sizing: border-box;
  }
  .kline-dialog-content {
    width: 100%;
    max-width: 100%;
    height: 82vh;
    max-height: calc(100vh - 80px - env(safe-area-inset-bottom, 0px));
    min-height: 400px;
    border-radius: 20px;
    border: 1px solid rgba(0, 0, 0, 0.06);
    box-shadow:
      0 4px 6px -1px rgba(0, 0, 0, 0.06),
      0 12px 40px -4px rgba(0, 0, 0, 0.12);
  }
  .page-container.dark-mode .kline-dialog-content {
    border-color: rgba(255, 255, 255, 0.08);
    box-shadow:
      0 4px 6px -1px rgba(0, 0, 0, 0.25),
      0 12px 40px -4px rgba(0, 0, 0, 0.45);
  }

  .kline-header-toolbar { padding: 12px 16px 0; }
  .realtime-data-bar { padding: 10px; gap: 8px 12px; margin-top: 10px; }
  .data-item { font-size: 12px; }
  
  .custom-interval-selector { gap: 12px; }
  .interval-btn { font-size: 13px; padding-bottom: 2px; }
}
</style>