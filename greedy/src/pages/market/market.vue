<template>
	<view class="market-page">
		<view class="market-container">
			<view class="market-header">
				<text class="header-title">关注列表</text>
				<view class="refresh-btn" @tap="fetchWatchlist">
					<text>{{ loading ? '加载中...' : '↻ 刷新' }}</text>
				</view>
			</view>

			<view v-if="loading && coinList.length === 0" class="loading-state">
				<text class="loading-text">加载中...</text>
			</view>

			<view v-else-if="error" class="error-state">
				<text class="error-text">{{ error }}</text>
				<view class="retry-btn" @tap="fetchWatchlist">
					<text>重试</text>
				</view>
			</view>

			<view v-else class="coin-list">
				<view
					v-for="coin in coinList"
					:key="coin.symbol"
					class="coin-card"
					@click="handleCoinClick(coin.symbol)"
				>
					<view class="coin-info">
						<text class="coin-name">{{ coin.symbol }}</text>
						<text class="coin-pair">{{ coin.name }}</text>
					</view>
                    <view class="coin-price">
                        <text class="price-value">${{ coin.price }}</text>
                        <text :class="['price-change', coin.change >= 0 ? 'up' : 'down']">
                            {{ coin.change >= 0 ? '+' : '' }}{{ coin.change }}%
                        </text>
                    </view>
				</view>

				<view v-if="coinList.length === 0" class="empty-state">
					<text>暂无关注数据</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { klinesApi } from '@/api'

// @update: 使用 /api/klines/watchlist/all 获取实时价格+涨跌幅
interface CoinItem {
	symbol: string
	name: string
	price: string
	change: number
}

const coinList = ref<CoinItem[]>([])
const loading = ref(false)
const error = ref('')

// 用 1d K 线的开盘价计算日涨跌幅
// 1d 的 open = 北京时间 8:00（UTC 0:00）的开盘价
// close = 当前最新价
const calcChange = (klines: any[]): number => {
	if (klines.length === 0) return 0
	const today = klines[klines.length - 1]
	const open = parseFloat(today?.open ?? 0)
	const close = parseFloat(today?.close ?? 0)
	if (!open) return 0
	return parseFloat((((close - open) / open) * 100).toFixed(2))
}

// 格式化价格显示
const formatPrice = (price: number): string => {
	if (price >= 1000) return price.toFixed(2)
	if (price >= 1) return price.toFixed(4)
	return price.toFixed(6)
}

// 请求 K 线关注列表（含价格和涨跌幅）
const fetchWatchlist = async () => {
	loading.value = true
	error.value = ''
	try {
		const res = await klinesApi.getWatchlistKlines('1d', 2)
		const body = res.data as any
		// 返回结构: { BTCUSDT: { name, klines: [...] }, ... }
		const raw = body?.data || body || {}
		const list: CoinItem[] = []

		for (const symbol of Object.keys(raw)) {
			const item = raw[symbol]
			const klines = item?.klines || []
			if (klines.length === 0) continue

			const price = parseFloat(klines[klines.length - 1]?.close ?? 0)
			const change = calcChange(klines)

			list.push({
				symbol,
				name: item?.name || symbol.replace('USDT', ''),
				price: formatPrice(price),
				change,
			})
		}
		coinList.value = list
	} catch (e: any) {
		error.value = e?.message || '加载失败，请检查网络'
	} finally {
		loading.value = false
	}
}

// 点击币种跳转 K 线详情页
const handleCoinClick = (symbol: string) => {
	uni.navigateTo({
		url: `/pages/kline/kline?coin=${symbol}`,
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

// 页面显示时拉取数据
onShow(() => {
	fetchWatchlist()
})
</script>

<style scoped>
.market-page {
	display: flex;
	justify-content: center;
	min-height: 100vh;
	background-color: #f5f7fa;
	padding: 20rpx;
}

.market-container {
	width: 100%;
	max-width: 1200px;
}

.market-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 30rpx 0;
}

.header-title {
	font-size: 40rpx;
	font-weight: bold;
	color: #1a1a2e;
}

.refresh-btn {
	padding: 12rpx 24rpx;
	border: 2rpx solid #409eff;
	border-radius: 8rpx;
	font-size: 24rpx;
	color: #409eff;
}

.loading-state,
.error-state,
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 100rpx 0;
	gap: 20rpx;
}

.loading-text,
.error-text {
	font-size: 28rpx;
	color: #909399;
}

.error-text {
	color: #f56c6c;
}

.retry-btn {
	padding: 16rpx 40rpx;
	background-color: #409eff;
	border-radius: 8rpx;
}

.retry-btn text {
	color: #ffffff;
	font-size: 26rpx;
}

.coin-list {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.coin-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background-color: #ffffff;
	border-radius: 16rpx;
	padding: 30rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.06);
	transition: transform 0.15s, box-shadow 0.15s;
}

.coin-card:active {
	transform: scale(0.98);
}

.coin-info {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
}

.coin-name {
	font-size: 32rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.coin-pair {
	font-size: 24rpx;
	color: #999999;
}

.coin-price {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 8rpx;
}

.price-value {
	font-size: 32rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.price-change {
	font-size: 24rpx;
	font-weight: 500;
}

.price-change.up {
	color: #f56c6c;
}

.price-change.down {
	color: #00c853;
}

/* PC 端双列 Grid 布局 */
@media (min-width: 768px) {
	.coin-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 24rpx;
	}
}
</style>
