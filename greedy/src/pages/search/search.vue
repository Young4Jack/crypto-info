<template>
	<view class="search-page">
		<view class="search-container">
			<!-- 搜索栏 -->
			<view class="search-bar">
				<input
					class="search-input"
					type="text"
					placeholder="输入币种代码，例如 BTCUSDT"
					v-model="keyword"
					@confirm="onSearch"
					@blur="onBlur"
				/>
				<view class="search-btn" @tap="onSearch">
					<text class="btn-text">搜索</text>
				</view>
			</view>

			<!-- 搜索中 -->
			<view v-if="searching" class="loading-state">
				<text class="loading-text">查询中...</text>
			</view>

			<!-- 结果展示卡片 -->
			<view v-else-if="searchResult" class="result-section">
				<view class="result-card">
					<view class="result-info">
						<text class="result-symbol">{{ searchResult.symbol }}</text>
						<text class="result-name">{{ searchResult.display_name }}</text>
						<text class="result-price">${{ formatPrice(searchResult.price) }}</text>
					</view>
					<view
						:class="['add-btn', isAdded ? 'added' : '']"
						@tap="addToWatchlist"
					>
						<text class="btn-text">{{ isAdded ? '已添加' : '+ 添加' }}</text>
					</view>
				</view>
			</view>

			<!-- 未找到或错误提示 -->
			<view v-else-if="hasSearched && !searchResult" class="empty-state">
				<text class="empty-text">未找到该币种数据</text>
				<text class="empty-hint">请检查币种代码是否正确</text>
			</view>

			<!-- 初始提示 -->
			<view v-else class="empty-state">
				<text class="empty-text">输入币种代码查询实时价格</text>
				<text class="empty-hint">支持 BTC / eth / SOLUSDT 等格式</text>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { priceSearchApi, watchlistApi, type PriceSearchResult } from '@/api'

const keyword = ref('')
const searching = ref(false)
const hasSearched = ref(false)
const searchResult = ref<PriceSearchResult | null>(null)
const isAdded = ref(false)

const onBlur = () => {
	const normalized = normalizeSymbol(keyword.value)
	if (normalized && normalized !== keyword.value) {
		keyword.value = normalized
	}
}

const normalizeSymbol = (raw: string): string => {
	const s = raw.trim().toUpperCase()
	if (!s) return ''
	if (!s.endsWith('USDT')) return `${s}USDT`
	return s
}

const formatPrice = (price: number): string => {
	if (price >= 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
	if (price >= 1) return price.toFixed(4)
	return price.toFixed(6)
}

const onSearch = async () => {
	const symbol = normalizeSymbol(keyword.value)
	if (!symbol) {
		uni.showToast({ title: '请输入币种代码', icon: 'none' })
		return
	}

	keyword.value = symbol
	searching.value = true
	hasSearched.value = true
	searchResult.value = null
	isAdded.value = false

	try {
		const res = await priceSearchApi.search(symbol)
		searchResult.value = res.data
	} catch (e: any) {
		console.error('价格查询失败', e)
	} finally {
		searching.value = false
	}
}

const addToWatchlist = async () => {
	if (isAdded.value) {
		uni.showToast({ title: '已在关注列表中', icon: 'none' })
		return
	}

	const token = uni.getStorageSync('token')
	if (!token) {
		uni.showToast({ title: '请先登录', icon: 'none' })
		return
	}

	if (!searchResult.value) return

	try {
		await watchlistApi.create({
			crypto_symbol: searchResult.value.symbol,
			is_public: true,
			notes: '',
		})
		isAdded.value = true
		uni.showToast({ title: '添加成功', icon: 'success' })
	} catch (e: any) {
		uni.showToast({ title: e?.message || '添加失败', icon: 'none' })
	}
}
</script>

<style scoped>
.search-page {
	min-height: 100vh;
	background-color: #f5f7fa;
	padding: 20rpx;
}

.search-container {
	width: 100%;
	max-width: 1200px;
	margin: 0 auto;
}

.search-bar {
	display: flex;
	gap: 16rpx;
	margin-bottom: 40rpx;
}

.search-input {
	flex: 1;
	height: 80rpx;
	padding: 0 24rpx;
	border: 2rpx solid #dcdfe6;
	border-radius: 12rpx;
	font-size: 28rpx;
	color: #303133;
	background-color: #ffffff;
	box-sizing: border-box;
}

.search-input:focus {
	border-color: #409eff;
}

.search-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 0 40rpx;
	min-width: 140rpx;
}

.search-btn:active {
	opacity: 0.8;
}

.btn-text {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

.loading-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 150rpx 0;
}

.loading-text {
	font-size: 28rpx;
	color: #909399;
}

.result-section {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
}

.result-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background-color: #ffffff;
	border-radius: 16rpx;
	padding: 32rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.result-info {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.result-symbol {
	font-size: 36rpx;
	font-weight: 700;
	color: #1a1a2e;
}

.result-name {
	font-size: 24rpx;
	color: #909399;
}

.result-price {
	font-size: 32rpx;
	font-weight: 600;
	color: #409eff;
	font-variant-numeric: tabular-nums;
}

.add-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 8rpx;
	padding: 14rpx 28rpx;
	min-width: 140rpx;
}

.add-btn.added {
	background-color: #e6f7ec;
}

.add-btn.added .btn-text {
	color: #00c853;
}

.add-btn:active {
	opacity: 0.8;
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 150rpx 0;
	gap: 12rpx;
}

.empty-text {
	font-size: 30rpx;
	color: #909399;
}

.empty-hint {
	font-size: 24rpx;
	color: #c0c4cc;
}

@media (min-width: 768px) {
	.result-section {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20rpx;
	}
}
</style>
