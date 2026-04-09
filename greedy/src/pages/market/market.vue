<template>
	<view class="market-page">
		<view class="market-container">
			<!-- 页面头部 -->
			<view class="market-header">
				<text class="header-title">自选</text>
				<view class="header-actions">
					<!-- 刷新按钮（始终可见） -->
					<view class="header-action-btn" @tap="fetchData">
						<view class="action-icon-wrap">
							<text class="action-icon" :class="{ 'icon-spin': loading }">⟳</text>
						</view>
					</view>
					<!-- 搜索按钮（仅登录态可见） -->
					<view v-if="isLoggedIn" class="header-action-btn" @tap="goToSearch">
						<view class="action-icon-wrap action-icon-primary">
							<text class="action-icon">＋</text>
						</view>
					</view>
					<!-- 管理模式切换（仅登录态可见） -->
					<view v-if="isLoggedIn" class="manage-toggle" @tap="toggleManageMode">
						<text class="manage-text">{{ isManageMode ? '完成' : '管理' }}</text>
					</view>
				</view>
			</view>

			<!-- 首次加载骨架屏 -->
			<view v-if="loading && coinList.length === 0" class="skeleton-state">
				<view class="skeleton-card"></view>
				<view class="skeleton-card"></view>
				<view class="skeleton-card"></view>
			</view>

			<!-- 错误状态 -->
			<view v-else-if="error" class="error-state">
				<text class="error-text">{{ error }}</text>
				<view class="retry-btn" @tap="fetchData">
					<text>重试</text>
				</view>
			</view>

			<!-- 列表 -->
			<view v-else class="coin-list">
				<view
					v-for="coin in coinList"
					:key="coin.id"
					class="coin-card"
					:class="{ 'price-flash-up': coin.priceFlash === 'up', 'price-flash-down': coin.priceFlash === 'down' }"
					@tap="isManageMode ? null : handleCoinClick(coin.symbol)"
				>
					<view class="coin-main">
						<view class="coin-left">
							<text class="coin-name">{{ coin.symbol }}</text>
							<text class="coin-pair">{{ coin.name }}</text>
						</view>
						<view class="coin-right">
							<text class="price-value">{{ coin.price }}</text>
							<text :class="['price-change', coin.change >= 0 ? 'up' : 'down']">
								{{ coin.change >= 0 ? '+' : '' }}{{ coin.change }}%
							</text>
						</view>
					</view>

					<!-- 管理模式操作面板 -->
					<view v-if="isManageMode" class="manage-panel" @tap.stop>
						<view class="manage-row">
							<switch
								:checked="coin.is_public"
								color="#409EFF"
								@change="togglePublic(coin, $event)"
							/>
							<text class="manage-switch-label">{{ coin.is_public ? '已公开' : '私有' }}</text>
							<view class="manage-spacer"></view>
							<view class="manage-btn manage-btn-edit" @tap="openEdit(coin)">
								<text class="manage-btn-text">编辑</text>
							</view>
							<view class="manage-btn manage-btn-del" @tap="confirmDelete(coin)">
								<text class="manage-btn-text">删除</text>
							</view>
						</view>
					</view>
				</view>

				<view v-if="coinList.length === 0" class="empty-state">
					<text class="empty-text">暂无数据</text>
					<text v-if="isLoggedIn" class="empty-hint">点击右上角 ＋ 添加关注</text>
				</view>
			</view>

			<!-- 编辑备注弹窗 -->
			<view v-if="showEditModal" class="modal-overlay" @tap="closeEditModal">
				<view class="modal-content" @tap.stop>
					<view class="modal-header">
						<text class="modal-title">编辑备注</text>
						<text class="modal-close" @tap="closeEditModal">×</text>
					</view>
					<view class="modal-body">
						<text class="modal-symbol">{{ editingCoin?.symbol }}</text>
						<textarea
							class="modal-textarea"
							placeholder="输入备注信息"
							v-model="editNotes"
							maxlength="200"
						/>
					</view>
					<view class="modal-footer">
						<view class="modal-btn modal-btn-cancel" @tap="closeEditModal">
							<text class="btn-text">取消</text>
						</view>
						<view class="modal-btn modal-btn-confirm" @tap="saveEdit">
							<text class="btn-text">保存</text>
						</view>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { onShow, onHide, onPullDownRefresh } from '@dcloudio/uni-app'
import { klinesApi, watchlistApi, type WatchlistItem } from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { formatPrice } from '@/utils/formatPrice'

interface CoinItem {
	id: number
	symbol: string
	name: string
	price: string
	change: number
	is_public: boolean
	notes: string
	priceFlash?: 'up' | 'down' | null
}

const coinList = ref<CoinItem[]>([])
const loading = ref(false)
const error = ref('')
const isLoggedIn = ref(false)

const { startAutoRefresh, stopAutoRefresh } = useAutoRefresh()

const isManageMode = ref(false)

const showEditModal = ref(false)
const editingCoin = ref<CoinItem | null>(null)
const editNotes = ref('')

const calcChange = (klines: any[]): number => {
	if (klines.length === 0) return 0
	const today = klines[klines.length - 1]
	const open = parseFloat(today?.open ?? 0)
	const close = parseFloat(today?.close ?? 0)
	if (!open) return 0
	return parseFloat((((close - open) / open) * 100).toFixed(2))
}

// 仅获取价格数据（后台刷新用）
const fetchPricesOnly = async () => {
	try {
		const klinesRes = await klinesApi.getWatchlistKlines('1d', 2)
		const klinesMap = new Map<string, { price: string; change: number }>()
		const body = klinesRes.data as any
		const raw = body?.data || body || {}
		for (const symbol of Object.keys(raw)) {
			const item = raw[symbol]
			const klines = item?.klines || []
			if (klines.length === 0) continue
			const price = parseFloat(klines[klines.length - 1]?.close ?? 0)
			const change = calcChange(klines)
			klinesMap.set(symbol.toUpperCase(), {
				price: formatPrice(price),
				change,
			})
		}

		// 仅更新价格，触发闪烁效果
		for (const coin of coinList.value) {
			const kline = klinesMap.get(coin.symbol.toUpperCase())
			if (kline && coin.price !== kline.price) {
				const oldPrice = parseFloat(coin.price) || 0
				const newPrice = parseFloat(kline.price)
				if (coin.price !== '--') {
					coin.priceFlash = newPrice > oldPrice ? 'up' : 'down'
					setTimeout(() => {
						coin.priceFlash = null
					}, 500)
				}
				coin.price = kline.price
				coin.change = kline.change
			}
		}
	} catch {
		// 价格获取失败静默处理
	}
}

const fetchData = async (isBackground = false) => {
	if (!isBackground) {
		loading.value = true
		error.value = ''
	}
	try {
		// 未登录：仅获取公开 K 线数据
		if (!isLoggedIn.value) {
			const klinesRes = await klinesApi.getWatchlistKlines('1d', 2)
			const body = klinesRes.data as any
			const raw = body?.data || body || {}
			const list: CoinItem[] = []

			for (const symbol of Object.keys(raw)) {
				const item = raw[symbol]
				const klines = item?.klines || []
				if (klines.length === 0) continue
				const price = parseFloat(klines[klines.length - 1]?.close ?? 0)
				const change = calcChange(klines)
				list.push({
					id: 0,
					symbol,
					name: item?.name || symbol.replace('USDT', ''),
					price: formatPrice(price),
					change,
					is_public: false,
					notes: '',
				})
			}
			coinList.value = list
			return
		}

		// 已登录：仅首次加载时获取 watchlist 列表
		if (!isBackground && coinList.value.length === 0) {
			const watchlistRes = await watchlistApi.getList()
			const raw = watchlistRes.data || []
			const list: CoinItem[] = raw.map((wl: any) => ({
				id: wl.id,
				symbol: wl.crypto_symbol,
				name: wl.crypto_name || wl.crypto_symbol.replace('USDT', ''),
				price: '--',
				change: 0,
				is_public: wl.is_public,
				notes: wl.notes || '',
			}))
			coinList.value = list
		}

		// 始终获取最新价格
		await fetchPricesOnly()

		if (!isBackground) {
			loading.value = false
		}
	} catch (e: any) {
		if (!isBackground) {
			error.value = e?.message || '加载失败，请检查网络'
		}
	} finally {
		if (!isBackground && loading.value) {
			loading.value = false
		}
	}
}

const handleCoinClick = (symbol: string) => {
	uni.navigateTo({
		url: `/pages/kline/kline?coin=${symbol}`,
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const goToSearch = () => {
	uni.navigateTo({
		url: '/pages/search/search',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const goToLogin = () => {
	uni.navigateTo({
		url: '/pages/login/login',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const toggleManageMode = () => {
	isManageMode.value = !isManageMode.value
}

const togglePublic = async (coin: CoinItem, event: any) => {
	if (!coin.id) {
		uni.showToast({ title: '关注项不存在', icon: 'none' })
		return
	}
	const value = event.detail?.value ?? event.value ?? false
	try {
		await watchlistApi.update(coin.id, { is_public: value })
		coin.is_public = value
	} catch (e: any) {
		uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
	}
}

const confirmDelete = (coin: CoinItem) => {
	if (!coin.id) {
		uni.showToast({ title: '关注项不存在', icon: 'none' })
		return
	}
	uni.showModal({
		title: '确认删除',
		content: `确定将 ${coin.symbol} 从自选列表中移除吗？`,
		success: async (res) => {
			if (res.confirm) {
				await deleteCoin(coin)
			}
		},
	})
}

const deleteCoin = async (coin: CoinItem) => {
	try {
		await watchlistApi.delete(coin.id)
		coinList.value = coinList.value.filter((c) => c.id !== coin.id)
		uni.showToast({ title: '已移除', icon: 'success' })
	} catch (e: any) {
		uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
	}
}

const openEdit = (coin: CoinItem) => {
	if (!coin.id) {
		uni.showToast({ title: '关注项不存在', icon: 'none' })
		return
	}
	editingCoin.value = coin
	editNotes.value = coin.notes || ''
	showEditModal.value = true
}

const closeEditModal = () => {
	showEditModal.value = false
	editingCoin.value = null
	editNotes.value = ''
}

const saveEdit = async () => {
	if (!editingCoin.value) return
	try {
		await watchlistApi.update(editingCoin.value.id, { notes: editNotes.value.trim() })
		editingCoin.value.notes = editNotes.value.trim()
		uni.showToast({ title: '已更新', icon: 'success' })
		closeEditModal()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
	}
}

onShow(async () => {
	const token = uni.getStorageSync('token')
	isLoggedIn.value = !!token
	await fetchData()
	// 启动自动刷新
	startAutoRefresh(fetchData)
})

onHide(() => {
	stopAutoRefresh()
})

onUnmounted(() => {
	stopAutoRefresh()
})

onPullDownRefresh(async () => {
	await fetchData()
	uni.stopPullDownRefresh()
})
</script>

<style scoped>
.market-page {
 	display: flex;
 	justify-content: center;
 	min-height: 100vh;
 	background-color: var(--page-bg);
 	padding: 20rpx;
 	box-sizing: border-box;
 	overflow-x: hidden;
}

.market-container {
 	width: 100%;
 	max-width: 1200px;
 	box-sizing: border-box;
}

/* 页面头部 */
.market-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 20rpx 0 24rpx;
}

.header-title {
	font-size: 44rpx;
	font-weight: 700;
	color: var(--text-primary);
	letter-spacing: 2rpx;
}

.header-actions {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.header-action-btn {
	display: flex;
	align-items: center;
	justify-content: center;
}

.header-action-btn:active {
	transform: scale(0.92);
}

.action-icon-wrap {
	display: flex;
	align-items: center;
	justify-content: center;
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	background-color: var(--page-bg);
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.action-icon-wrap:active {
	background-color: var(--text-placeholder);
}

.action-icon-primary {
	background-color: #409eff;
	box-shadow: 0 4rpx 12rpx rgba(64, 158, 255, 0.3);
}

.action-icon-primary:active {
	background-color: #3a8ee6;
}

.action-icon {
	font-size: 40rpx;
	font-weight: 300;
	color: var(--text-secondary);
	line-height: 1;
}

.action-icon-primary .action-icon {
	color: #ffffff;
	font-weight: 500;
}

.icon-spin {
	animation: spin 0.6s linear infinite;
}

@keyframes spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}

.manage-toggle {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 10rpx 28rpx;
	border-radius: 32rpx;
	background-color: var(--text-primary);
	box-shadow: 0 2rpx 8rpx rgba(26, 26, 46, 0.2);
}

.manage-toggle:active {
	opacity: 0.8;
	transform: scale(0.96);
}

.manage-text {
	font-size: 24rpx;
	color: var(--page-bg);
	font-weight: 600;
	letter-spacing: 2rpx;
}

/* 状态区 */
.error-state,
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 120rpx 0;
	gap: 20rpx;
}

/* 骨架屏 */
.skeleton-state {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	padding: 20rpx 0;
}

.skeleton-card {
	height: 120rpx;
	background: linear-gradient(90deg, var(--border-color) 25%, var(--text-placeholder) 50%, var(--border-color) 75%);
	background-size: 200% 100%;
	animation: skeleton-loading 1.5s ease-in-out infinite;
	border-radius: 12rpx;
}

@keyframes skeleton-loading {
	0% { background-position: 200% 0; }
	100% { background-position: -200% 0; }
}

.error-text {
	font-size: 28rpx;
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

.empty-text {
    font-size: 30rpx;
    color: var(--text-tertiary);
}

.empty-hint {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

/* 卡片列表 */
.coin-list {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}

.coin-card {
	display: flex;
	flex-direction: column;
	background-color: var(--card-bg);
	border-radius: 12rpx;
	padding: 28rpx 24rpx;
	box-shadow: var(--card-shadow);
}

.coin-card:active {
	transform: scale(0.99);
}

.coin-main {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.coin-left {
	display: flex;
	flex-direction: column;
	gap: 6rpx;
	flex: 1;
	min-width: 0;
}

.coin-name {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.coin-pair {
	font-size: 22rpx;
	color: var(--text-tertiary);
}

.coin-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 6rpx;
	flex-shrink: 0;
}

.price-value {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--text-primary);
	font-variant-numeric: tabular-nums;
}

.price-change {
	font-size: 22rpx;
	font-weight: 500;
	font-variant-numeric: tabular-nums;
}

.price-change.up {
	color: #f56c6c;
}

.price-change.down {
	color: #00c853;
}

@keyframes flashUp {
	0% { background-color: transparent; }
	50% { background-color: rgba(0, 200, 83, 0.2); }
	100% { background-color: transparent; }
}

@keyframes flashDown {
	0% { background-color: transparent; }
	50% { background-color: rgba(245, 108, 108, 0.2); }
	100% { background-color: transparent; }
}

.price-flash-up {
	animation: flashUp 0.5s ease;
}

.price-flash-down {
	animation: flashDown 0.5s ease;
}

/* 管理模式操作面板 */
.manage-panel {
	margin-top: 16rpx;
	padding-top: 16rpx;
	border-top: 2rpx solid var(--border-color);
}

.manage-row {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.manage-switch-label {
	font-size: 22rpx;
	color: #606266;
	min-width: 64rpx;
}

.manage-spacer {
	flex: 1;
}

.manage-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 8rpx 20rpx;
	border-radius: 6rpx;
}

.manage-btn:active {
	opacity: 0.7;
}

.manage-btn-edit {
	background-color: #ecf5ff;
}

.manage-btn-edit .manage-btn-text {
	color: #409eff;
}

.manage-btn-del {
	background-color: #fef0f0;
}

.manage-btn-del .manage-btn-text {
	color: #f56c6c;
}

.manage-btn-text {
	font-size: 22rpx;
	font-weight: 500;
}

/* 弹窗 */
.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.5);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 999;
}

.modal-content {
	width: 600rpx;
	background-color: var(--card-bg);
	border-radius: 20rpx;
	overflow: hidden;
}

.modal-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 30rpx;
	border-bottom: 2rpx solid var(--border-color);
}

.modal-title {
	font-size: 32rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.modal-close {
	font-size: 48rpx;
	color: var(--text-tertiary);
	line-height: 1;
}

.modal-body {
	padding: 30rpx;
}

.modal-symbol {
	font-size: 28rpx;
	font-weight: 600;
	color: #409eff;
	margin-bottom: 16rpx;
	display: block;
}

.modal-textarea {
	width: 100%;
	height: 160rpx;
	padding: 16rpx;
	border: 2rpx solid var(--border-color);
	border-radius: 8rpx;
	font-size: 26rpx;
	color: var(--text-primary);
	box-sizing: border-box;
}

.modal-footer {
	display: flex;
	gap: 16rpx;
	padding: 20rpx 30rpx 30rpx;
}

.modal-btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 72rpx;
	border-radius: 8rpx;
}

.modal-btn:active {
	opacity: 0.8;
}

.modal-btn-cancel {
	background-color: var(--border-color);
}

.modal-btn-cancel .btn-text {
	color: #606266;
}

.modal-btn-confirm {
	background-color: #409eff;
}

.modal-btn-confirm .btn-text {
	color: #ffffff;
}

.btn-text {
	font-size: 28rpx;
	font-weight: 500;
}

/* PC 端双列 Grid */
@media (min-width: 768px) {
	.coin-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 16rpx;
	}
}
</style>
