<template>
	<view class="assets-page">
		<view class="assets-container">
			<!-- 总资产概览卡片 -->
			<view class="overview-card">
				<text class="overview-label">总估值 (USD)</text>
				<text class="overview-value">{{ totalValue }}</text>
				<view class="pnl-row">
					<view class="pnl-item">
						<text class="pnl-label">今日盈亏</text>
						<text :class="['pnl-value', dailyPnl >= 0 ? 'profit' : 'loss']">
							{{ dailyPnl >= 0 ? '+' : '' }}${{ dailyPnlAbs }}
						</text>
					</view>
					<view class="pnl-divider"></view>
					<view class="pnl-item">
						<text class="pnl-label">盈亏比例</text>
						<text :class="['pnl-value', dailyPnlPercent >= 0 ? 'profit' : 'loss']">
							{{ dailyPnlPercent >= 0 ? '+' : '' }}{{ dailyPnlPercent }}%
						</text>
					</view>
				</view>
			</view>

			<!-- 持有资产列表 -->
			<view class="holdings-header">
				<text class="header-title">持有资产</text>
				<text class="header-count">共 {{ holdings.length }} 个</text>
			</view>
			<scroll-view scroll-y class="holdings-scroll">
				<view class="holdings-list">
					<view
						v-for="item in holdings"
						:key="item.symbol"
						class="holding-card"
					>
						<view class="holding-left">
							<view class="coin-icon" :style="{ backgroundColor: item.color }">
								<text class="coin-abbreviation">{{ item.symbol }}</text>
							</view>
							<view class="coin-detail">
								<text class="coin-name">{{ item.name }}</text>
								<text class="coin-amount">{{ item.amount }} {{ item.symbol }}</text>
							</view>
						</view>
						<view class="holding-right">
							<text class="coin-price">${{ item.price }}</text>
							<text class="coin-total-value">${{ item.totalValue }}</text>
						</view>
					</view>
				</view>
			</scroll-view>
		</view>
	</view>
</template>

<script setup lang="ts">
// @update: 实现资产列表页面，含总资产概览卡片与持有资产滚动列表
interface HoldingItem {
	symbol: string
	name: string
	amount: number
	price: string
	totalValue: string
	color: string
}

// 模拟总资产数据
const totalValue = '$12,500.00'
const dailyPnl = 285.40
const dailyPnlPercent = 2.33

// 计算属性：盈亏绝对值
const dailyPnlAbs = dailyPnl.toFixed(2)

// 模拟持有资产列表
const holdings: HoldingItem[] = [
	{ symbol: 'BTC', name: 'Bitcoin', amount: 0.15, price: '67,234.50', totalValue: '10,085.18', color: '#f7931a' },
	{ symbol: 'ETH', name: 'Ethereum', amount: 0.8, price: '3,456.78', totalValue: '2,765.42', color: '#627eea' },
	{ symbol: 'SOL', name: 'Solana', amount: 10, price: '178.92', totalValue: '1,789.20', color: '#00ffa3' },
	{ symbol: 'BNB', name: 'BNB', amount: 2.5, price: '580.30', totalValue: '1,450.75', color: '#f3ba2f' },
	{ symbol: 'XRP', name: 'Ripple', amount: 500, price: '0.6234', totalValue: '311.70', color: '#00aae4' },
	{ symbol: 'ADA', name: 'Cardano', amount: 1000, price: '0.4521', totalValue: '452.10', color: '#0033ad' },
]
</script>

<style scoped>
.assets-page {
	display: flex;
	justify-content: center;
	min-height: 100vh;
	background-color: #f5f7fa;
	padding: 20rpx;
}

.assets-container {
	width: 100%;
	max-width: 1200px;
	display: flex;
	flex-direction: column;
	height: 100%;
}

/* 总资产概览卡片 */
.overview-card {
	background: linear-gradient(135deg, #409eff 0%, #2c7be5 100%);
	border-radius: 24rpx;
	padding: 40rpx;
	margin-bottom: 30rpx;
	box-shadow: 0 8rpx 24rpx rgba(64, 158, 255, 0.25);
}

.overview-label {
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.8);
	margin-bottom: 12rpx;
}

.overview-value {
	font-size: 56rpx;
	font-weight: bold;
	color: #ffffff;
	font-family: 'Monaco', monospace;
	display: block;
	margin-bottom: 30rpx;
}

.pnl-row {
	display: flex;
	align-items: center;
	gap: 30rpx;
}

.pnl-item {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
	flex: 1;
}

.pnl-label {
	font-size: 22rpx;
	color: rgba(255, 255, 255, 0.7);
}

.pnl-value {
	font-size: 30rpx;
	font-weight: 600;
	color: #ffffff;
	font-family: 'Monaco', monospace;
}

.pnl-value.profit {
	color: #a8ffb2;
}

.pnl-value.loss {
	color: #ffb3b3;
}

.pnl-divider {
	width: 2rpx;
	height: 50rpx;
	background-color: rgba(255, 255, 255, 0.2);
}

/* 持有资产列表头部 */
.holdings-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 10rpx 0 20rpx;
}

.header-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.header-count {
	font-size: 24rpx;
	color: #909399;
}

/* 滚动容器 */
.holdings-scroll {
	flex: 1;
	height: 0;
}

.holdings-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	padding-bottom: 20rpx;
}

.holding-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background-color: #ffffff;
	border-radius: 16rpx;
	padding: 24rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.holding-left {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.coin-icon {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
}

.coin-abbreviation {
	font-size: 22rpx;
	font-weight: bold;
	color: #ffffff;
}

.coin-detail {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.coin-name {
	font-size: 28rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.coin-amount {
	font-size: 22rpx;
	color: #909399;
}

.holding-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 6rpx;
}

.coin-price {
	font-size: 24rpx;
	color: #606266;
	font-family: 'Monaco', monospace;
}

.coin-total-value {
	font-size: 28rpx;
	font-weight: 600;
	color: #1a1a2e;
	font-family: 'Monaco', monospace;
}

/* PC 端响应式 */
@media (min-width: 768px) {
	.holdings-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20rpx;
	}
}
</style>
