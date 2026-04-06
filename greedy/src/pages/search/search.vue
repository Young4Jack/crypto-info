<template>
	<view class="search-page">
		<view class="search-container">
			<!-- 搜索栏 -->
			<view class="search-bar">
				<input
					class="search-input"
					type="text"
					placeholder="输入币种名称或交易对，如 BTC / ETH"
					v-model="keyword"
					@confirm="onSearch"
				/>
				<view class="search-btn" @tap="onSearch">
					<text class="btn-text">搜索</text>
				</view>
			</view>

			<!-- 搜索结果 -->
			<view v-if="searchResults.length > 0" class="results-section">
				<text class="section-title">搜索结果</text>
				<view
					v-for="item in searchResults"
					:key="item.symbol"
					class="result-card"
				>
					<view class="result-info">
						<text class="result-name">{{ item.symbol }}</text>
						<text class="result-sub">{{ item.name }}</text>
					</view>
					<view
						:class="['add-btn', item.added ? 'added' : '']"
						@tap="toggleWatchlist(item)"
					>
						<text class="btn-text">{{ item.added ? '已添加' : '+ 添加' }}</text>
					</view>
				</view>
			</view>

			<!-- 空状态 -->
			<view v-else-if="hasSearched" class="empty-state">
				<text class="empty-text">未找到匹配的币种</text>
			</view>

			<!-- 初始提示 -->
			<view v-else class="empty-state">
				<text class="empty-text">输入关键词搜索并添加关注</text>
				<text class="empty-hint">支持输入币种名称或交易对</text>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { watchlistApi, klinesApi, type WatchlistItem } from '@/api'

const keyword = ref('')
const searchResults = ref<Array<{
	symbol: string
	name: string
	added: boolean
	loading: boolean
}>>([])
const hasSearched = ref(false)
const myWatchlist = ref<Set<string>>(new Set())

onShow(async () => {
	await loadMyWatchlist()
})

const loadMyWatchlist = async () => {
	try {
		const res = await watchlistApi.getList()
		const symbols = new Set<string>()
		;(res.data || []).forEach((item: WatchlistItem) => {
			symbols.add(item.crypto_symbol.toUpperCase())
		})
		myWatchlist.value = symbols
	} catch (e: any) {
		console.error('获取关注列表失败', e)
	}
}

const normalizeSymbol = (raw: string): string => {
	const s = raw.trim().toUpperCase()
	if (!s) return ''
	if (!s.endsWith('USDT')) return `${s}USDT`
	return s
}

const onSearch = async () => {
	const kw = keyword.value.trim().toUpperCase()
	if (!kw) {
		uni.showToast({ title: '请输入搜索关键词', icon: 'none' })
		return
	}

	hasSearched.value = true
	searchResults.value = []

	try {
		const res = await klinesApi.getWatchlistKlines('1d', 2)
		const body = res.data as any
		const raw = body?.data || body || {}

		const matched: typeof searchResults.value = []
		for (const symbol of Object.keys(raw)) {
			const item = raw[symbol]
			const symUpper = symbol.toUpperCase()
			const name = item?.name || symbol.replace('USDT', '')

			// 匹配逻辑：交易对完整匹配 或 名称包含关键词
			if (symUpper.includes(kw) || name.toUpperCase().includes(kw)) {
				matched.push({
					symbol,
					name,
					added: myWatchlist.value.has(symUpper),
					loading: false,
				})
			}
		}

		searchResults.value = matched
	} catch (e: any) {
		uni.showToast({ title: '搜索失败', icon: 'none' })
	}
}

const toggleWatchlist = async (item: typeof searchResults.value[number]) => {
	if (item.added) {
		uni.showToast({ title: '已在关注列表中', icon: 'none' })
		return
	}

	item.loading = true
	try {
		await watchlistApi.create({
			crypto_symbol: item.symbol,
			is_public: false,
		})
		item.added = true
		myWatchlist.value.add(item.symbol.toUpperCase())
		uni.showToast({ title: '添加成功', icon: 'success' })
	} catch (e: any) {
		uni.showToast({ title: e?.message || '添加失败', icon: 'none' })
	} finally {
		item.loading = false
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
	margin-bottom: 30rpx;
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

.search-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 0 32rpx;
}

.search-btn:active {
	opacity: 0.8;
}

.btn-text {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

.section-title {
	font-size: 28rpx;
	font-weight: 600;
	color: #1a1a2e;
	margin-bottom: 16rpx;
	display: block;
}

.results-section {
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
	padding: 24rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.result-info {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
}

.result-name {
	font-size: 30rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.result-sub {
	font-size: 24rpx;
	color: #909399;
}

.add-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 8rpx;
	padding: 12rpx 24rpx;
	min-width: 120rpx;
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
	.results-section {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20rpx;
	}
}
</style>
