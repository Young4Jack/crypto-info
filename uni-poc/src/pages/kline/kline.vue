<template>
  <view class="page-container" :class="{ 'dark-mode': isDarkMode }">
    <view class="page-header">
      <view class="header-content">
        <view class="header-left">
          <text class="header-h1">📈 K线图</text>
          <text class="header-p">实时查看关注币种的K线走势</text>
        </view>
        <view class="header-right">
          <button class="dark-mode-btn" @click="toggleDarkMode">{{ isDarkMode ? '☀️' : '🌙' }}</button>
        </view>
      </view>
    </view>

    <view class="page-main">
      <view class="watchlist-card">
        <view class="el-card__header">
          <view class="card-header">
            <text class="card-title">🔥 关注列表</text>
            <button class="refresh-btn" @click="loadWatchlist" :disabled="loadingWatchlist">
              <text v-if="!loadingWatchlist">刷新</text>
              <text v-else>加载中...</text>
            </button>
          </view>
        </view>
        <view class="el-card__body">
          <view class="watchlist-grid">
            <view
              v-for="item in watchlistData"
              :key="item.crypto_symbol"
              class="watchlist-item"
              @click="openKlineDialog(item)"
            >
              <view class="item-left">
                <text class="item-symbol">{{ item.crypto_symbol }}</text>
                <text class="item-name">{{ item.crypto_name }}</text>
              </view>
              <view class="item-right">
                <text class="item-price">${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}</text>
                <text class="item-change" :class="getChangeClass(item.change_24h)">
                  {{ formatChange(item.change_24h) }}
                </text>
              </view>
            </view>
            <view v-if="!loadingWatchlist && watchlistData.length === 0" class="empty-placeholder">
              <text>暂无关注数据</text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <view class="kline-dialog-overlay" v-if="klineDialogVisible" @click="closeKlineDialog">
      <view class="kline-dialog-content" @click.stop>
        <view class="kline-header-toolbar">
          <view class="header-main">
            <view class="symbol-info">
              <text class="symbol-h2">
                {{ selectedSymbol }}
                <text class="main-interval-text">
                  {{ selectedInterval === '1d' ? '1天' : (intervalLabelMap[selectedInterval] || selectedInterval) }}
                </text>
              </text>
            </view>
            <button class="close-btn" @click="closeKlineDialog">×</button>
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

          <scroll-view class="header-bottom" scroll-x>
            <view class="custom-interval-selector">
              <text
                v-for="interval in ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']"
                :key="interval"
                class="interval-btn"
                :class="{ active: selectedInterval === interval }"
                @click="changeInterval(interval)"
              >
                {{ intervalLabelMap[interval] || interval }}
              </text>
            </view>
          </scroll-view>
        </view>

        <view class="kline-chart-container">
          <view id="klineChart" class="chart"></view>
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
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { klinesApi, watchlistApi, systemSettingsApi } from '../../api/index'
import * as echarts from 'echarts'

const loading = ref(false)
const loadingWatchlist = ref(false)
const selectedSymbol = ref('')
const selectedInterval = ref('1d')
const selectedLimit = ref(100)
const klineData = ref<any[]>([])
const watchlistData = ref<any[]>([])
const klineDialogVisible = ref(false)
const selectedCryptoName = ref('')
const isDarkMode = ref(false)
const savedDataZoom = ref<{ start: number; end: number } | null>(null)
let chartInstance: any = null

let klineWs: WebSocket | null = null
let priceRefreshTimer: any = null
let refreshInterval = 5

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

const hoverIndex = ref<number | null>(null)

const realtimeObj = computed(() => {
  if (klineData.value.length === 0) return null
  const currentIndex = hoverIndex.value !== null ? hoverIndex.value : (klineData.value.length - 1)
  if (currentIndex < 0 || currentIndex >= klineData.value.length) return null
  const data = klineData.value[currentIndex]

  const date = new Date(data.open_time)
  const Y = date.getFullYear()
  const M = String(date.getMonth() + 1).padStart(2, '0')
  const D = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const m = String(date.getMinutes()).padStart(2, '0')

  let timeStr = ''
  if (['1d', '1w', '1M'].includes(selectedInterval.value)) {
    timeStr = `${Y}-${M}-${D}`
  } else {
    timeStr = `${M}-${D} ${h}:${m}`
  }

  const open = parseFloat(data.open)
  const close = parseFloat(data.close)
  const changePercent = open ? (((close - open) / open) * 100).toFixed(2) : '0.00'

  return {
    time: timeStr,
    open: open.toFixed(2),
    high: parseFloat(data.high).toFixed(2),
    low: parseFloat(data.low).toFixed(2),
    close: close.toFixed(2),
    changePercent: changePercent,
    amplitude: open ? (((parseFloat(data.high) - parseFloat(data.low)) / open) * 100).toFixed(2) : '--',
    volume: parseFloat(data.volume).toFixed(2)
  }
})

const onDataZoom = (params: any) => {
  if (params.batch && params.batch.length > 0) {
    const { start, end } = params.batch[0]
    savedDataZoom.value = { start, end }
  } else if (params.start !== undefined && params.end !== undefined) {
    savedDataZoom.value = { start: params.start, end: params.end }
  }
}

const chartOption = computed(() => {
  const dark = isDarkMode.value
  const bgColor = dark ? '#1a1a2e' : '#ffffff'
  const textColor = dark ? '#a0a0b0' : '#909399'
  const borderColor = dark ? '#2a2a3e' : '#ebeef5'
  const splitAreaColor = dark ? 'rgba(255,255,255,0.03)' : 'rgba(245,247,250,0.5)'
  const tooltipBg = dark ? '#2a2a3e' : '#ffffff'
  const tooltipBorder = dark ? '#3a3a5e' : '#ebeef5'
  const tooltipText = dark ? '#d0d0e0' : '#303133'
  const tooltipLabel = dark ? '#8080a0' : '#909399'

  if (klineData.value.length === 0) {
    return {
      backgroundColor: bgColor,
      title: { text: '', left: 'center', top: 'center', textStyle: { color: textColor, fontSize: 14 } },
      series: []
    }
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
    return date.toLocaleDateString('zh-CN')
  }

  const dates = klineData.value.map(k => formatTime(k.open_time))
  const ohlcData = klineData.value.map(k => [k.open, k.close, k.low, k.high])
  const volumeData = klineData.value.map(k => k.volume)

  return {
    backgroundColor: bgColor,
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      triggerOn: 'mousemove',
      confine: true,
      appendToBody: true,
      backgroundColor: tooltipBg,
      borderColor: tooltipBorder,
      textStyle: { color: tooltipText },
      axisPointer: { type: 'cross', lineStyle: { color: dark ? '#4a4a6e' : '#dcdfe6' } },
      formatter: (params: any) => {
        const kline = params[0]
        if (!kline) return ''

        hoverIndex.value = kline.dataIndex
        const data = klineData.value[kline.dataIndex]
        const timeStr = formatTime(data.open_time)
        const change = data.open ? (((data.close - data.open) / data.open) * 100).toFixed(2) : '0.00'
        const amplitude = data.open ? (((data.high - data.low) / data.open) * 100).toFixed(2) : '0.00'
        const color = data.close >= data.open ? '#f56c6c' : '#67c23a'
        const sign = data.close >= data.open ? '+' : ''

        return `
          <div style="font-family: Monaco, monospace; font-size: 12px; min-width: 140px;">
            <div style="color: ${tooltipLabel}; margin-bottom: 8px; font-weight: bold;">${timeStr}</div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>开盘</span> <span>${data.open.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最高</span> <span style="color: #f56c6c;">${data.high.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最低</span> <span style="color: #67c23a;">${data.low.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>收盘</span> <span style="color: ${color}; font-weight: bold;">${data.close.toFixed(4)}</span></div>
            <div style="display: flex; justify-content: space-between; border-top: 1px solid ${tooltipBorder}; margin-top: 6px; padding-top: 6px;">
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
      left: 'center',
      top: 0,
      textStyle: { fontSize: 11, color: textColor }
    },
    grid: [
      { left: '8%', right: '8%', top: 30, bottom: '26%' },
      { left: '8%', right: '8%', height: '16%', bottom: '4%' }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLine: { onZero: false, lineStyle: { color: borderColor } }, splitLine: { show: false }, axisLabel: { fontSize: 11, color: textColor } },
      { type: 'category', gridIndex: 1, data: dates, axisLabel: { show: false }, axisLine: { onZero: false, lineStyle: { color: borderColor } }, splitLine: { show: false } }
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitArea: { show: true, areaStyle: { color: [splitAreaColor, 'transparent'] } }, axisLabel: { formatter: '${value}', fontSize: 11, color: textColor }, splitLine: { lineStyle: { color: borderColor } } },
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

const loadWatchlist = async () => {
  loadingWatchlist.value = true
  try {
    const watchlistRes = await watchlistApi.getAllWatchlist()
    const data = watchlistRes.data

    for (const item of data) {
      item.change_24h = null
    }

    data.sort((a: any, b: any) => (a.sort_order || 0) - (b.sort_order || 0))
    watchlistData.value = data

    klinesApi.getWatchlistKlines('1d', 2).then(klinesRes => {
      const klinesData = (klinesRes.data as any)?.data || {}

      for (const item of watchlistData.value) {
        const symbolData = klinesData[item.crypto_symbol]
        const symbolKlines = symbolData?.klines || []

        if (symbolKlines.length > 0) {
          const latestKline = symbolKlines[symbolKlines.length - 1]
          const open = parseFloat(latestKline.open)
          const close = parseFloat(latestKline.close)
          if (open && close) {
            item.change_24h = ((close - open) / open) * 100
          }
        }
      }
    }).catch(err => {
      console.error('后台加载涨跌幅失败:', err)
    })
  } catch (error) {
    console.error('加载关注列表失败:', error)
    try {
      const response = await watchlistApi.getAllWatchlist()
      const data = response.data
      data.sort((a: any, b: any) => (a.sort_order || 0) - (b.sort_order || 0))
      watchlistData.value = data
    } catch (e) {
      uni.showToast({ title: '加载关注列表失败', icon: 'none' })
    }
  } finally {
    loadingWatchlist.value = false
  }
}

const openKlineDialog = async (item: any) => {
  selectedSymbol.value = item.crypto_symbol
  selectedCryptoName.value = item.crypto_name
  klineDialogVisible.value = true

  await loadKlineData()
  connectWebSocket(selectedSymbol.value)
}

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

const loadKlineData = async (silent = false) => {
  if (!selectedSymbol.value) {
    uni.showToast({ title: '请先选择币种', icon: 'none' })
    return
  }

  if (!silent) {
    loading.value = true
  }

  try {
    const response = await klinesApi.getKlines(selectedSymbol.value, selectedInterval.value, selectedLimit.value)

    if (response.data && (response.data as any).success) {
      klineData.value = (response.data as any).data.klines || []
      if (klineData.value.length === 0 && !silent) {
        uni.showToast({ title: 'K线数据为空', icon: 'none' })
      }
    } else {
      if (!silent) {
        uni.showToast({ title: (response.data as any)?.error || '获取K线数据失败', icon: 'none' })
      }
    }
  } catch (error: any) {
    if (!silent) {
      uni.showToast({ title: '获取K线数据失败', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

const changeInterval = async (newInterval: string) => {
  if (selectedInterval.value === newInterval) return
  selectedInterval.value = newInterval

  if (klineWs) {
    klineWs.close()
    klineWs = null
  }
  await loadKlineData()
  connectWebSocket(selectedSymbol.value)
}

const connectWebSocket = (symbol: string) => {
  if (klineWs) klineWs.close()

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = window.location.host
  const wsUrl = `${protocol}//${host}/api/klines/ws/${symbol}`
  klineWs = new WebSocket(wsUrl)

  klineWs.onopen = () => {
    console.log(`WebSocket 已连接: ${symbol}`)
  }

  klineWs.onmessage = (event) => {
    try {
      if (!event.data || event.data === 'undefined') return
      const newKline = JSON.parse(event.data)
      if (!newKline || typeof newKline.close === 'undefined') return
      if (klineData.value.length === 0) return

      const lastIndex = klineData.value.length - 1
      const lastKline = klineData.value[lastIndex]
      const currentPrice = parseFloat(newKline.close)

      const newData = [...klineData.value]

      newData[lastIndex] = {
        ...lastKline,
        close: currentPrice,
        high: Math.max(lastKline.high, currentPrice),
        low: Math.min(lastKline.low, currentPrice)
      }

      if (selectedInterval.value === '1m' && newKline.open_time > lastKline.open_time) {
        newData.push(newKline)
        if (newData.length > selectedLimit.value) newData.shift()
      }

      klineData.value = newData
    } catch (error) {
      // 忽略解析错误
    }
  }

  klineWs.onerror = (error) => {
    console.error('WebSocket 连接错误:', error)
  }

  klineWs.onclose = (event) => {
    console.log(`WebSocket 已断开: ${symbol}, code: ${event.code}`)
    klineWs = null
  }
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
  } catch (error) {
    console.error('后台刷新价格失败:', error)
  }
}

const loadPublicSettings = async (): Promise<number> => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      return (response.data as any).refresh_interval || 5
    }
  } catch (error) {
    console.error('加载配置失败，使用默认 5 秒')
  }
  return 5
}

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  uni.setStorageSync('kline_dark_mode_override', isDarkMode.value.toString())
}

const initChart = () => {
  nextTick(() => {
    const chartDom = document.getElementById('klineChart')
    if (!chartDom) return
    if (chartInstance) {
      chartInstance.dispose()
    }
    chartInstance = echarts.init(chartDom)
    chartInstance.setOption(chartOption.value, true)
  })
}

watch(chartOption, (newVal) => {
  if (chartInstance) {
    chartInstance.setOption(newVal, true)
  }
}, { deep: true })

watch(klineDialogVisible, (val) => {
  if (val) {
    nextTick(() => {
      initChart()
    })
  } else {
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
  }
})

onMounted(async () => {
  const override = uni.getStorageSync('kline_dark_mode_override')
  if (override !== null) {
    isDarkMode.value = override === 'true'
  }

  loadWatchlist()
  refreshInterval = await loadPublicSettings()
  startPriceRefresh()
})

onUnmounted(() => {
  stopPriceRefresh()
  if (klineWs) {
    klineWs.close()
  }
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
/* ==========================================
   基础与电脑端样式
========================================== */
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; width: 100%; }
.header-left { display: flex; flex-direction: column; }
.header-h1 { margin: 0; font-size: 22px; color: #409eff; font-weight: bold; letter-spacing: 0.5px; }
.header-p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.header-right { display: flex; align-items: center; }
.dark-mode-btn { font-size: 16px; min-width: 36px; height: 32px; padding: 0; display: inline-flex; align-items: center; justify-content: center; }
.page-main { padding: 20px 25px; max-width: 1200px; margin: 0 auto; width: 100%; }

.watchlist-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); margin-bottom: 20px; background: #fff; }
.el-card__header { padding: 18px 20px; border-bottom: 1px solid #f0f2f5; }
.el-card__body { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; color: #303133; font-size: 15px; }
.refresh-btn { font-size: 12px; padding: 4px 12px; border-radius: 4px; background: #409eff; color: #fff; border: none; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; margin: 0; line-height: 1; outline: none; }
.refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.watchlist-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.watchlist-item { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: #f8f9fa; border-radius: 10px; border: 1px solid #f0f2f5; cursor: pointer; transition: all 0.2s ease; }
.watchlist-item:hover { background: #fff; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

.item-left { display: flex; flex-direction: column; gap: 2px; }
.item-symbol { font-size: 15px; font-weight: 700; color: #1a1a2e; letter-spacing: 0.5px; }
.item-name { font-size: 12px; color: #909399; }
.item-right { display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
.item-price { font-size: 15px; font-weight: bold; color: #409eff; font-family: 'Monaco', monospace; }
.item-change { font-size: 13px; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-family: 'Monaco', monospace; }

.change-up { color: #f56c6c; background: rgba(245, 108, 108, 0.1); }
.change-down { color: #67c23a; background: rgba(103, 194, 58, 0.1); }
.text-up { color: #f56c6c; }
.text-down { color: #67c23a; }

.empty-placeholder { text-align: center; padding: 40px; color: #909399; grid-column: 1 / -1; }

/* ==========================================
   K线弹窗亮色主题与排版修复
========================================== */
.kline-dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0, 0, 0, 0.5); display: flex; justify-content: center; align-items: center; z-index: 2000; }
.kline-dialog-content { width: 90vw; max-width: 1200px; height: 80vh; background-color: #ffffff; border-radius: 12px; display: flex; flex-direction: column; box-shadow: 0 10px 40px rgba(0,0,0,0.1); overflow: hidden; min-height: 500px; }

.kline-header-toolbar { padding: 16px 24px 0; background-color: #ffffff; border-bottom: 1px solid #ebeef5; }
.header-main { display: flex !important; justify-content: space-between !important; align-items: center !important; width: 100% !important; padding-bottom: 8px; }

.symbol-info { display: flex !important; align-items: baseline !important; gap: 10px; }
.symbol-h2 { margin: 0; font-size: 24px; color: #1f2937; font-family: 'Monaco', monospace; font-weight: bold; }
.main-interval-text { font-size: 16px; color: #606266; margin-left: 8px; font-weight: normal; }

.close-btn { position: static !important; transform: none !important; background: #f4f4f5 !important; border: none !important; border-radius: 50% !important; width: 32px !important; height: 32px !important; display: flex !important; align-items: center !important; justify-content: center !important; cursor: pointer !important; font-size: 18px !important; color: #909399 !important; transition: all 0.2s ease; }
.close-btn:hover { background: #f56c6c !important; color: #fff !important; }

.realtime-data-bar { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 15px; padding: 10px 16px; background: #f8f9fa; border-radius: 8px; border: 1px solid #ebeef5; }
.data-item { display: flex; gap: 6px; font-size: 13px; font-family: 'Monaco', monospace; }
.data-item .label { color: #909399; }
.data-item .value { color: #303133; font-weight: 600; }

.header-bottom { width: 100% !important; overflow-x: auto !important; white-space: nowrap !important; margin-top: 16px; scrollbar-width: none; }
.header-bottom::-webkit-scrollbar { display: none; }
.custom-interval-selector { display: flex !important; flex-wrap: nowrap !important; gap: 16px !important; padding-bottom: 8px; }
.interval-btn { font-size: 14px; color: #909399; cursor: pointer; font-weight: 500; padding-bottom: 4px; transition: all 0.2s; }
.interval-btn:hover { color: #303133; }
.interval-btn.active { color: #409eff; font-weight: bold; border-bottom: 2px solid #409eff; }

.kline-chart-container { flex: 1; position: relative; background-color: #ffffff; padding: 10px 0; min-height: 0 !important; overflow: hidden; }
.chart { width: 100%; height: 100%; }
.loading-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; display: flex; align-items: center; justify-content: center; background: rgba(255, 255, 255, 0.8); z-index: 10; }
.loading-spinner { width: 32px; height: 32px; border: 3px solid #f3f3f3; border-top: 3px solid #409eff; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* ==========================================
   夜间模式
========================================== */
.page-container.dark-mode { background-color: #0f0f1a; }
.page-container.dark-mode .page-header { background: #1a1a2e; border-bottom-color: #2a2a3e; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.page-container.dark-mode .header-h1 { color: #60a5fa; }
.page-container.dark-mode .header-p { color: #8080a0; }
.page-container.dark-mode .watchlist-card { background: #1a1a2e; border-color: #2a2a3e; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.3); }
.page-container.dark-mode .el-card__header { background: #1a1a2e; border-bottom-color: #2a2a3e; }
.page-container.dark-mode .el-card__body { background: #1a1a2e; }
.page-container.dark-mode .card-title { color: #d0d0e0; }
.page-container.dark-mode .watchlist-item { background: #16162a; border-color: #2a2a3e; }
.page-container.dark-mode .watchlist-item:hover { background: #1e1e36; }
.page-container.dark-mode .item-name { color: #d0d0e0; }
.page-container.dark-mode .item-symbol { color: #e0e0f0; }
.page-container.dark-mode .item-price { color: #60a5fa; }
.page-container.dark-mode .kline-dialog-overlay { background: rgba(0, 0, 0, 0.7); }
.page-container.dark-mode .kline-dialog-content { background-color: #1a1a2e; }
.page-container.dark-mode .kline-header-toolbar { background-color: #1a1a2e; border-bottom-color: #2a2a3e; }
.page-container.dark-mode .symbol-h2 { color: #e0e0f0; }
.page-container.dark-mode .main-interval-text { color: #a0a0b0; }
.page-container.dark-mode .close-btn { background: #2a2a3e !important; color: #a0a0b0 !important; }
.page-container.dark-mode .close-btn:hover { background: #3a3a5e !important; color: #f56c6c !important; }
.page-container.dark-mode .realtime-data-bar { background: #16162a; border-color: #2a2a3e; }
.page-container.dark-mode .data-item .label { color: #8080a0; }
.page-container.dark-mode .data-item .value { color: #d0d0e0; }
.page-container.dark-mode .header-bottom { border-bottom-color: #2a2a3e; }
.page-container.dark-mode .interval-btn { color: #8080a0; }
.page-container.dark-mode .interval-btn:hover { color: #d0d0e0; }
.page-container.dark-mode .interval-btn.active { color: #60a5fa; border-bottom-color: #60a5fa; }
.page-container.dark-mode .kline-chart-container { background-color: #1a1a2e; }
.page-container.dark-mode .loading-overlay { background: rgba(26, 26, 46, 0.8); }
.page-container.dark-mode .empty-placeholder { background: #1a1a2e; color: #8080a0; }

/* ==========================================
   移动端响应式
========================================== */
@media (max-width: 768px) {
  .page-container { padding-bottom: 40px; }
  .page-main { padding: 8px; }
  .page-header { padding: 6px 12px; }

  .header-content { display: flex; flex-direction: row; justify-content: space-between; align-items: center !important; flex-wrap: nowrap; gap: 0; }
  .header-left { flex: 1; min-width: 0; }
  .header-h1 { font-size: 16px; margin: 0; line-height: 1.1; }
  .header-p { font-size: 11px; margin: 2px 0 0; line-height: 1; color: #909399; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .header-right { flex-shrink: 0; width: auto; display: flex; justify-content: flex-end; align-items: center; gap: 8px; }
  .dark-mode-btn { font-size: 16px; min-width: 36px; height: 32px; padding: 0; display: inline-flex; align-items: center; justify-content: center; }

  .watchlist-card { margin-bottom: 12px; }
  .el-card__header { padding: 4px 12px !important; border-bottom: 1px solid #f0f2f5 !important; }
  .card-header { min-height: 24px !important; display: flex; align-items: center; justify-content: space-between; }
  .card-title { font-size: 13px; line-height: 1; }
  .refresh-btn { height: 24px !important; padding: 0 8px !important; font-size: 12px !important; }
  .el-card__body { padding: 8px; }

  .watchlist-grid { grid-template-columns: 1fr; gap: 6px; }
  .watchlist-item { padding: 8px 10px; }
  .item-symbol { font-size: 14px; }
  .item-name { font-size: 12px; }
  .item-price { font-size: 14px; }
  .item-change { font-size: 11px; padding: 2px 5px; }

  .kline-dialog-overlay { align-items: flex-end !important; }
  .kline-dialog-content { width: 100% !important; height: 95vh !important; border-radius: 12px 12px 0 0 !important; margin-bottom: 0 !important; }
  .kline-header-toolbar { padding: 12px 16px 0; }
  .symbol-h2 { font-size: 20px; }
  .main-interval-text { font-size: 14px; }
  .realtime-data-bar { gap: 10px; padding: 8px 12px; }
  .data-item { font-size: 12px; }
}
</style>
