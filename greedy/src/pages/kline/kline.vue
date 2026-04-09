<template>
	<view class="page-container" :class="{ 'dark-mode': isDarkMode }">
		<view class="page-header">
			<view class="header-main">
				<view class="back-btn" @tap="goBack">
					<text class="back-icon">←</text>
				</view>
				<view class="symbol-info">
					<text class="symbol-title">{{ baseCoin }}/USDT</text>
					<text class="symbol-period">{{ currentPeriodLabel }}</text>
				</view>
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
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { onLoad, onUnload } from '@dcloudio/uni-app'
import * as echarts from 'echarts'
import { klinesApi } from '@/api'
import { wsBase } from '@/utils/config'
import { formatPrice } from '@/utils/formatPrice'
import { useTheme } from '@/composables/useDarkMode'

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

// 使用全局主题状态，不再使用独立的深色模式按钮
const { isDarkMode } = useTheme()

const toggleDarkMode = () => {
	// 已移除独立切换按钮，主题由全局控制
}

const chartRef = ref<any>(null)
let chartInstance: any = null
const loading = ref(false)
const selectedSymbol = ref('')
const selectedInterval = ref('1d')
const selectedLimit = ref(100)
const klineData = ref<any[]>([])
const savedDataZoom = ref<{ start: number; end: number } | null>(null)
// @update: 追踪用户当前查看的K线索引，使上方信息列表跟随图表交互变化
const hoveredDataIndex = ref<number | null>(null)
// @update: 图例显隐由用户控制；setOption(true) 全量替换会丢失选中态，故持久化并在 option 中回写
const legendSelected = ref<Record<string, boolean>>({ K线: true, 成交量: true })

// 接收 URL 传入的币种参数
const currentCoin = ref('')

// 提取基础币种（如 BTCUSDT -> BTC）
const baseCoin = computed(() => {
	if (!currentCoin.value) return ''
	if (currentCoin.value.endsWith('USDT')) {
		return currentCoin.value.slice(0, -4)
	}
	return currentCoin.value
})

// 当前周期中文显示
const currentPeriodLabel = computed(() => {
	return intervalLabelMap[selectedInterval.value] || selectedInterval.value
})

let socketTask: UniApp.SocketTask | null = null

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

const clearTooltip = () => {
	hoveredDataIndex.value = null
	setTimeout(() => {
		if (chartInstance && chartInstance.dispatchAction) {
			chartInstance.dispatchAction({ type: 'hideTip' });
		}
	}, 10);
}

const goBack = () => {
	const pages = getCurrentPages()
	if (pages.length > 1) {
		uni.navigateBack()
	} else {
		uni.reLaunch({ url: '/pages/market/market' })
	}
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
		open: formatPrice(open),
		high: formatPrice(parseFloat(data.high)),
		low: formatPrice(parseFloat(data.low)),
		close: formatPrice(close),
		changePercent: changePercent,
		amplitude: open ? (((parseFloat(data.high) - parseFloat(data.low)) / open) * 100).toFixed(2) : '--',
		volume: parseFloat(data.volume).toFixed(2)
	};
});

// 图表配置
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
			// @update: App端不支持HTML，使用纯文本；H5端使用富文本格式
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
				const amplitude = openVal ? (((highVal - lowVal) / openVal) * 100).toFixed(2) : '--'
				const color = closeVal >= openVal ? upColor : downColor
				const sign = closeVal >= openVal ? '+' : ''

				// #ifdef H5
				// H5端使用富文本格式
				return `
					<div style="font-family: Monaco, monospace; font-size: 12px; min-width: 140px;">
						<div style="color: ${tooltipLabel}; margin-bottom: 8px; font-weight: bold;">${timeStr}</div>
						<div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>开盘</span> <span>${formatPrice(openVal)}</span></div>
						<div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最高</span> <span style="color: ${upColor};">${formatPrice(highVal)}</span></div>
						<div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>最低</span> <span style="color: ${downColor};">${formatPrice(lowVal)}</span></div>
						<div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>收盘</span> <span style="color: ${color}; font-weight: bold;">${formatPrice(closeVal)}</span></div>
						<div style="display: flex; justify-content: space-between; border-top: 1px solid ${tooltipBorder}; margin-top: 6px; padding-top: 6px;">
							<span>涨跌幅</span> <span style="color: ${color};">${sign}${change}%</span>
						</div>
						<div style="display: flex; justify-content: space-between; margin-top: 4px;"><span>振幅</span> <span>${amplitude}%</span></div>
						<div style="display: flex; justify-content: space-between; margin-top: 4px;"><span>成交量</span> <span>${volVal.toFixed(2)}</span></div>
					</div>
				`
				// #endif

				// #ifndef H5
				// App端：不用 div 标签，只用 span + br 实现多行
				return `
					<span style="font-family: Monaco, monospace; font-size: 12px; color: ${dark ? '#d0d0e0' : '#303133'};">
						<span style="color: ${tooltipLabel}; font-weight: bold;">${timeStr}</span><br/>
						<span>开盘: ${formatPrice(openVal)}</span><br/>
						<span>最高: <span style="color: ${upColor};">${formatPrice(highVal)}</span></span><br/>
						<span>最低: <span style="color: ${downColor};">${formatPrice(lowVal)}</span></span><br/>
						<span>收盘: <span style="color: ${color}; font-weight: bold;">${formatPrice(closeVal)}</span></span><br/>
						<span style="border-top: 1px solid ${tooltipBorder};">涨跌幅: <span style="color: ${color};">${sign}${change}%</span></span><br/>
						<span>振幅: ${amplitude}%</span><br/>
						<span>成交量: ${volVal.toFixed(2)}</span>
					</span>
				`
				// #endif
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

// 增量合并更新：保留用户图例选中、dataZoom 等交互状态
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
		if (chartInstance) scheduleChartResize()
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

	// 从全局配置读取 WebSocket 地址
	let wsUrl = `${wsBase.value}/api/klines/ws/${symbol}`

	// 兜底：如果 wsBase 为空，使用相对路径（走 Vite 代理）
	if (!wsBase.value) {
		// #ifdef H5
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
		wsUrl = `${protocol}//${window.location.host}/api/klines/ws/${symbol}`
		// #endif
		// #ifndef H5
		wsUrl = `wss://your-api-domain.com/api/klines/ws/${symbol}`
		// #endif
	}

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

// 接收 URL 参数 coin
onLoad((options) => {
	if (options && options.coin) {
		currentCoin.value = options.coin
		selectedSymbol.value = options.coin
	}
})

onMounted(async () => {
	if (!selectedSymbol.value) return
	// 页面挂载后初始化图表并加载数据
	setTimeout(() => {
		if (chartRef.value && !chartInstance) {
			chartRef.value.init(echarts, (chart: any) => {
				chartInstance = chart
				bindChartInteractionOnce(chart)
				chart.setOption(chartOption.value, true)
				scheduleChartResize()
			})
		}
	}, 150)

	await loadKlineData()
	connectWebSocket(selectedSymbol.value)
})

onUnmounted(() => {
	if (socketTask) socketTask.close({})
})
</script>

<style scoped>
/* ==========================================
   页面主框架
========================================== */
.page-container {
	min-height: 100vh;
	background-color: #f5f7fa;
	display: flex;
	flex-direction: column;
	padding-top: var(--status-bar-height, 0px);
}

.page-header {
	background: #ffffff;
	padding: 16px 24px 0;
	box-shadow: 0 1px 4px rgba(0,21,41,0.04);
	border-bottom: 1px solid #f0f0f0;
	flex-shrink: 0;
}

.header-main {
	display: flex;
	justify-content: space-between;
	align-items: center;
	width: 100%;
	padding-bottom: 8px;
}

.back-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 48rpx;
	height: 48rpx;
	cursor: pointer;
}

.back-icon {
	font-size: 36rpx;
	color: #409eff;
}

.symbol-info {
	display: flex;
	align-items: baseline;
	gap: 16rpx;
}

.symbol-title {
	font-size: 40rpx;
	color: #1f2937;
	font-weight: bold;
	font-family: 'Monaco', monospace;
}

.symbol-period {
	font-size: 24rpx;
	color: #909399;
	padding: 4rpx 12rpx;
	background: #f0f2f5;
	border-radius: 6rpx;
	font-weight: 500;
}

.dark-mode-btn {
	padding: 12rpx 24rpx;
	border: 2rpx solid #e4e7ed;
	border-radius: 8rpx;
	cursor: pointer;
}

.header-bottom {
	width: 100%;
	white-space: nowrap;
	margin-top: 16rpx;
	box-sizing: border-box;
}

.custom-interval-selector {
	display: flex;
	flex-wrap: nowrap;
	gap: 32rpx;
	padding-bottom: 16rpx;
}

.interval-btn {
	font-size: 28rpx;
	color: #909399;
	font-weight: 500;
	padding-bottom: 8rpx;
	transition: all 0.2s;
	flex-shrink: 0;
}

.interval-btn.active text {
	color: #409eff;
	font-weight: bold;
	border-bottom: 4rpx solid #409eff;
	padding-bottom: 8rpx;
}

/* 实时数据栏 */
.realtime-data-bar {
	display: flex;
	flex-wrap: wrap;
	gap: 32rpx;
	margin-top: 20rpx;
	padding: 20rpx 32rpx;
	background: #f8f9fa;
	border-radius: 16rpx;
	border: 2rpx solid #ebeef5;
}

.data-item {
	display: flex;
	gap: 12rpx;
	font-size: 24rpx;
	font-family: 'Monaco', monospace;
}

.data-item .label {
	color: #909399;
}

.data-item .value {
	color: #303133;
	font-weight: 600;
}

.text-up {
	color: #f56c6c !important;
}

.text-down {
	color: #67c23a !important;
}

/* 图表容器 */
.kline-chart-container {
	flex: 1;
	width: 100%;
	min-height: 0;
	position: relative;
	background-color: #ffffff;
	padding: 20rpx 0;
	box-sizing: border-box;
}

.chart {
	width: 100%;
	height: 100%;
	display: block;
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
}

.loading-overlay {
	position: absolute;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background: rgba(255, 255, 255, 0.8);
	display: flex;
	justify-content: center;
	align-items: center;
	z-index: 10;
}

.loading-spinner {
	width: 64rpx;
	height: 64rpx;
	border: 6rpx solid #f3f3f3;
	border-top: 6rpx solid #409eff;
	border-radius: 50%;
	animation: spin 1s linear infinite;
}

@keyframes spin {
	0% { transform: rotate(0deg); }
	100% { transform: rotate(360deg); }
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
	color: #909399;
	z-index: 1;
	background: #ffffff;
}

/* ==========================================
   夜间模式
========================================== */
.page-container.dark-mode {
	background-color: #0f0f1a;
}

.page-container.dark-mode .page-header {
	background: #1a1a2e;
	border-bottom-color: #2a2a3e;
	box-shadow: 0 1px 4px rgba(0,0,0,0.3);
}

.page-container.dark-mode .symbol-title {
	color: #e0e0f0;
}

.page-container.dark-mode .symbol-period {
	color: #8080a0;
	background: #2a2a3e;
}

.page-container.dark-mode .back-icon {
	color: #60a5fa;
}

.page-container.dark-mode .realtime-data-bar {
	background: #16162a;
	border-color: #2a2a3e;
}

.page-container.dark-mode .data-item .label {
	color: #8080a0;
}

.page-container.dark-mode .data-item .value {
	color: #d0d0e0;
}

.page-container.dark-mode .interval-btn {
	color: #8080a0;
}

.page-container.dark-mode .interval-btn.active text {
	color: #60a5fa;
	border-bottom-color: #60a5fa;
}

.page-container.dark-mode .kline-chart-container {
	background-color: #1a1a2e;
}

.page-container.dark-mode .loading-overlay {
	background: rgba(26, 26, 46, 0.8);
}

.page-container.dark-mode .empty-placeholder {
	background: #1a1a2e;
	color: #8080a0;
}

/* ==========================================
   移动端响应式
========================================== */
@media (max-width: 768px) {
	.page-header {
		padding: 16rpx 16rpx 0;
	}

	.symbol-title {
		font-size: 32rpx;
	}

	.symbol-pair {
		font-size: 20rpx;
	}

	.custom-interval-selector {
		gap: 24rpx;
	}

	.interval-btn {
		font-size: 24rpx;
	}

	.realtime-data-bar {
		padding: 20rpx;
		gap: 16rpx 24rpx;
		margin-top: 20rpx;
	}

	.data-item {
		font-size: 22rpx;
	}

	/* 移动端隐藏日间模式切换按钮 */
	.dark-mode-btn {
		display: none;
	}
}
</style>
