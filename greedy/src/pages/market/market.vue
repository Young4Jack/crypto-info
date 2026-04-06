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

			<!-- 加载/错误状态 -->
			<view v-if="loading && coinList.length === 0" class="loading-state">
				<text class="loading-text">加载中...</text>
			</view>

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
					@tap="isManageMode ? null : handleCoinClick(coin.symbol)"
				>
					<view class="coin-main">
						<view class="coin-left">
							<text class="coin-name">{{ coin.symbol }}</text>
							<text class="coin-pair">{{ coin.name }}</text>
						</view>
						<view class="coin-right">
							<text class="price-value">${{ coin.price }}</text>
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
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { klinesApi, watchlistApi, type WatchlistItem } from '@/api'

interface CoinItem {
	id: number
	symbol: string
	name: string
	price: string
	change: number
	is_public: boolean
	notes: string
}

const coinList = ref<CoinItem[]>([])
const loading = ref(false)
const error = ref('')
const isLoggedIn = ref(false)
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

const formatPrice = (price: number): string => {
	if (price >= 1000) return price.toFixed(2)
	if (price >= 1) return price.toFixed(4)
	return price.toFixed(6)
}

const fetchData = async () => {
	loading.value = true
	error.value = ''
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

		// 已登录：以 watchlist 为主数据源（确保有 id），用 klines 补充价格
		const [klinesRes, watchlistRes] = await Promise.all([
			klinesApi.getWatchlistKlines('1d', 2),
			watchlistApi.getList(),
		])

		// 构建 klines 映射（补充价格和涨跌幅）
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

		// 以 watchlist 为主遍历
		const list: CoinItem[] = []
		for (const wl of (watchlistRes.data || [])) {
			const symUpper = wl.crypto_symbol.toUpperCase()
			const kline = klinesMap.get(symUpper)
			list.push({
				id: wl.id,
				symbol: wl.crypto_symbol,
				name: wl.crypto_name || wl.crypto_symbol.replace('USDT', ''),
				price: kline?.price || '--',
				change: kline?.change ?? 0,
				is_public: wl.is_public,
				notes: wl.notes || '',
			})
		}
		coinList.value = list
	} catch (e: any) {
		error.value = e?.message || '加载失败，请检查网络'
	} finally {
		loading.value = false
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
	color: #1a1a2e;
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
	background-color: #f5f7fa;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.action-icon-wrap:active {
	background-color: #e8eaed;
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
	color: #606266;
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
	background-color: #1a1a2e;
	box-shadow: 0 2rpx 8rpx rgba(26, 26, 46, 0.2);
}

.manage-toggle:active {
	opacity: 0.8;
	transform: scale(0.96);
}

.manage-text {
	font-size: 24rpx;
	color: #ffffff;
	font-weight: 600;
	letter-spacing: 2rpx;
}

/* 状态区 */
.loading-state,
.error-state,
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 120rpx 0;
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

.empty-text {
	font-size: 30rpx;
	color: #909399;
}

.empty-hint {
	font-size: 24rpx;
	color: #c0c4cc;
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
	background-color: #ffffff;
	border-radius: 12rpx;
	padding: 28rpx 24rpx;
	box-shadow: 0 1rpx 4rpx rgba(0, 0, 0, 0.04);
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
	color: #1a1a2e;
}

.coin-pair {
	font-size: 22rpx;
	color: #999999;
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
	color: #1a1a2e;
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

/* 管理模式操作面板 */
.manage-panel {
	margin-top: 16rpx;
	padding-top: 16rpx;
	border-top: 2rpx solid #f0f2f5;
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
	background-color: #ffffff;
	border-radius: 20rpx;
	overflow: hidden;
}

.modal-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 30rpx;
	border-bottom: 2rpx solid #f0f2f5;
}

.modal-title {
	font-size: 32rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.modal-close {
	font-size: 48rpx;
	color: #909399;
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
	border: 2rpx solid #dcdfe6;
	border-radius: 8rpx;
	font-size: 26rpx;
	color: #303133;
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
	background-color: #f0f2f5;
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
