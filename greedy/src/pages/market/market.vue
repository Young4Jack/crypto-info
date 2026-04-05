<template>
	<view class="market-page">
		<view class="market-container">
			<view class="market-header">
				<text class="header-title">关注列表</text>
			</view>
			<view class="coin-list">
				<view
					v-for="coin in coinList"
					:key="coin.symbol"
					class="coin-card"
					@click="handleCoinClick(coin.symbol)"
				>
					<view class="coin-info">
						<text class="coin-name">{{ coin.name }}</text>
						<text class="coin-pair">{{ coin.pair }}</text>
					</view>
					<view class="coin-price">
						<text class="price-value">{{ coin.price }}</text>
						<text :class="['price-change', coin.change >= 0 ? 'up' : 'down']">
							{{ coin.change >= 0 ? '+' : '' }}{{ coin.change }}%
						</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
// @update: 实现关注列表页面，含响应式双列布局与路由跳转逻辑
interface CoinItem {
	symbol: string
	name: string
	pair: string
	price: string
	change: number
}

// 模拟关注列表数据
const coinList: CoinItem[] = [
	{ symbol: 'BTC', name: 'Bitcoin', pair: 'BTC/USDT', price: '67,234.50', change: 2.35 },
	{ symbol: 'ETH', name: 'Ethereum', pair: 'ETH/USDT', price: '3,456.78', change: -1.12 },
	{ symbol: 'SOL', name: 'Solana', pair: 'SOL/USDT', price: '178.92', change: 5.67 },
]

// 点击币种跳转 K 线详情页
const handleCoinClick = (symbol: string) => {
	uni.navigateTo({
		url: `/pages/kline/kline?coin=${symbol}`,
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}
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
	padding: 30rpx 0;
}

.header-title {
	font-size: 40rpx;
	font-weight: bold;
	color: #1a1a2e;
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
	color: #00c853;
}

.price-change.down {
	color: #ff1744;
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
