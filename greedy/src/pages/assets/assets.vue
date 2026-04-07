<template>
	<view class="assets-page">
		<view class="assets-container">
			<!-- 未登录态 -->
			<view v-if="!isLoggedIn" class="guest-state">
				<text class="guest-title">请登录后查看资产</text>
				<view class="guest-login-btn" @tap="goToLogin">
					<text class="btn-text">立即登录</text>
				</view>
			</view>

			<!-- 已登录态 -->
			<view v-else>
				<!-- 首次加载骨架屏 -->
				<view v-if="loading && assets.length === 0" class="skeleton-state">
					<view class="skeleton-card skeleton-dashboard"></view>
					<view class="skeleton-card skeleton-list-item"></view>
					<view class="skeleton-card skeleton-list-item"></view>
				</view>

				<!-- 已加载完成 -->
				<view v-else>
					<!-- 仪表盘概览卡片 -->
					<view v-if="dashboardLoaded" class="overview-card">
						<text class="overview-label">总估值 (USD)</text>
						<text class="overview-value">${{ formatNumber(dashboard.total_value) }}</text>
						<view class="pnl-row">
							<view class="pnl-item">
								<text class="pnl-label">累计盈亏</text>
								<text :class="['pnl-value', dashboard.total_profit_loss >= 0 ? 'profit' : 'loss']">
									{{ dashboard.total_profit_loss >= 0 ? '+' : '' }}${{ formatNumber(dashboard.total_profit_loss) }}
								</text>
							</view>
							<view class="pnl-divider"></view>
							<view class="pnl-item">
								<text class="pnl-label">盈亏比例</text>
								<text :class="['pnl-value', dashboard.total_profit_loss_percentage >= 0 ? 'profit' : 'loss']">
									{{ dashboard.total_profit_loss_percentage >= 0 ? '+' : '' }}{{ dashboard.total_profit_loss_percentage.toFixed(2) }}%
								</text>
							</view>
						</view>
					</view>

					<!-- 添加资产按钮 -->
					<view class="holdings-header">
						<text class="header-title">持有资产</text>
						<view class="header-actions">
							<text class="header-count">共 {{ assets.length }} 个</text>
							<view class="add-btn pc-only" @tap="toggleForm">
								<text class="btn-text">+ 添加资产</text>
							</view>
						</view>
					</view>

					<!-- 添加/编辑资产表单 -->
					<view v-if="showForm" class="add-form-card">
						<view class="form-header">
							<text class="form-title">{{ editingId ? '编辑资产' : '添加资产' }}</text>
							<text class="form-close" @tap="toggleForm">×</text>
						</view>

						<view class="form-group">
							<text class="form-label">交易对</text>
							<input
								class="form-input"
								type="text"
								placeholder="如 btc / BTC / BTCUSDT 均可，自动补全 USDT"
								v-model="form.crypto_symbol"
								@blur="onSymbolBlur"
							/>
						</view>

						<view class="form-row-group">
							<view class="form-group form-half">
								<text class="form-label">买入价格 (USD)</text>
								<input
									class="form-input"
									type="digit"
									placeholder="如 65000"
									v-model="form.buy_price"
								/>
							</view>
							<view class="form-group form-half">
								<text class="form-label">持有数量</text>
								<input
									class="form-input"
									type="digit"
									placeholder="如 0.5"
									v-model="form.quantity"
								/>
							</view>
						</view>

						<view class="form-group">
							<text class="form-label">备注（可选）</text>
							<input
								class="form-input"
								type="text"
								placeholder="如 长期持有"
								v-model="form.notes"
							/>
						</view>

						<view class="form-submit-btn" @tap="submitAsset">
							<text class="btn-text">{{ submitting ? '提交中...' : (editingId ? '保存修改' : '确认添加') }}</text>
						</view>
					</view>

					<!-- 资产列表 -->
					<scroll-view scroll-y class="holdings-scroll">
						<view class="holdings-list">
							<view
								v-for="item in assets"
								:key="item.id"
								class="holding-card"
							>
								<view class="holding-left">
									<view class="coin-icon" :style="{ backgroundColor: getCoinColor(item.crypto_symbol) }">
										<text class="coin-abbreviation">{{ getShortSymbol(item.crypto_symbol) }}</text>
									</view>
									<view class="coin-detail">
										<text class="coin-name">{{ item.crypto_name }}</text>
										<text class="coin-amount">{{ item.quantity }} {{ getShortSymbol(item.crypto_symbol) }}</text>
										<text class="coin-buy-price">成本 ${{ formatNumber(item.buy_price) }}</text>
									</view>
								</view>
								<view class="holding-right">
									<text class="coin-total-value">${{ formatNumber(item.total_value) }}</text>
									<view class="price-pnl-row">
										<text class="coin-current-price">现 ${{ formatNumber(item.current_price) }}</text>
										<text :class="['coin-pnl', getItemPnl(item) >= 0 ? 'profit' : 'loss']">
											{{ getItemPnl(item) >= 0 ? '+' : '' }}${{ formatNumber(getItemPnl(item)) }}
										</text>
									</view>
									<view class="action-btns">
										<view class="edit-btn-wrap" @tap.stop="openEdit(item)">
											<text class="edit-btn-text">编辑</text>
										</view>
										<view class="delete-btn-wrap" @tap.stop="confirmDelete(item)">
											<text class="delete-btn-text">删除</text>
										</view>
									</view>
								</view>
							</view>

							<view v-if="assets.length === 0" class="empty-state">
								<text class="empty-text">暂无持仓记录</text>
								<text class="empty-hint">点击上方按钮添加你的第一个资产</text>
							</view>
						</view>
					</scroll-view>

					<!-- 移动端底部按钮 -->
					<view class="add-btn mobile-only" @tap="onMobileBtnTap">
						<text class="btn-text">{{ showForm ? '返回' : '+ 添加资产' }}</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dashboardApi, assetsApi, type AssetItem } from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'

const isLoggedIn = ref(false)
const loading = ref(false)
const submitting = ref(false)
const dashboardLoaded = ref(false)
const showForm = ref(false)
const editingId = ref<number | null>(null)

const { startAutoRefresh, stopAutoRefresh } = useAutoRefresh()

const dashboard = ref({
	total_value: 0,
	total_profit_loss: 0,
	total_profit_loss_percentage: 0,
})

const assets = ref<AssetItem[]>([])

const form = ref({
	crypto_symbol: '',
	buy_price: '',
	quantity: '',
	notes: '',
})

onShow(async () => {
	const token = uni.getStorageSync('token')
	if (!token) {
		isLoggedIn.value = false
		assets.value = []
		dashboardLoaded.value = false
		return
	}
	isLoggedIn.value = true
	// 资产列表优先加载，仪表盘数据异步后台加载不阻塞页面
	await fetchAssets()
	fetchDashboard()
	// 启动自动刷新
	startAutoRefresh(fetchAssets)
})

onUnmounted(() => {
	stopAutoRefresh()
})

const fetchDashboard = async () => {
	try {
		const res = await dashboardApi.getSummary()
		dashboard.value = {
			total_value: res.data.total_value || 0,
			total_profit_loss: res.data.total_profit_loss || 0,
			total_profit_loss_percentage: res.data.total_profit_loss_percentage || 0,
		}
		dashboardLoaded.value = true
	} catch (e: any) {
		console.error('获取仪表盘数据失败', e)
		dashboardLoaded.value = true
	}
}

const fetchAssets = async () => {
	loading.value = true
	try {
		const res = await assetsApi.getList()
		assets.value = res.data || []
	} catch (e: any) {
		console.error('获取资产列表失败', e)
	} finally {
		loading.value = false
	}
}

const normalizeSymbol = (raw: string): string => {
	const s = raw.trim().toUpperCase()
	if (!s) return ''
	if (!s.endsWith('USDT')) return `${s}USDT`
	return s
}

const onSymbolBlur = () => {
	if (form.value.crypto_symbol.trim()) {
		const normalized = normalizeSymbol(form.value.crypto_symbol)
		if (normalized && normalized !== form.value.crypto_symbol) {
			form.value.crypto_symbol = normalized
		}
	}
}

const toggleForm = () => {
	showForm.value = !showForm.value
	if (!showForm.value) {
		editingId.value = null
		resetForm()
	}
}

const onMobileBtnTap = () => {
	if (showForm.value) {
		editingId.value = null
		showForm.value = false
		resetForm()
	} else {
		toggleForm()
	}
}

const resetForm = () => {
	form.value = {
		crypto_symbol: '',
		buy_price: '',
		quantity: '',
		notes: '',
	}
}

const openEdit = (item: AssetItem) => {
	editingId.value = item.id
	showForm.value = true
	form.value.crypto_symbol = item.crypto_symbol
	form.value.buy_price = String(item.buy_price)
	form.value.quantity = String(item.quantity)
	form.value.notes = item.notes || ''
	uni.pageScrollTo({ scrollTop: 0, duration: 200 })
}

const submitAsset = async () => {
	const symbol = normalizeSymbol(form.value.crypto_symbol)
	if (!symbol) {
		uni.showToast({ title: '请输入交易对', icon: 'none' })
		return
	}
	const buyPrice = parseFloat(form.value.buy_price)
	if (!buyPrice || buyPrice <= 0) {
		uni.showToast({ title: '请输入有效买入价格', icon: 'none' })
		return
	}
	const quantity = parseFloat(form.value.quantity)
	if (!quantity || quantity <= 0) {
		uni.showToast({ title: '请输入有效持有数量', icon: 'none' })
		return
	}

	submitting.value = true
	try {
		const payload = {
			crypto_symbol: symbol,
			buy_price: buyPrice,
			quantity: quantity,
			notes: form.value.notes.trim() || undefined,
		}
		if (editingId.value) {
			await assetsApi.update(editingId.value, payload)
			uni.showToast({ title: '资产已更新', icon: 'success' })
		} else {
			await assetsApi.create(payload)
			uni.showToast({ title: '资产添加成功', icon: 'success' })
		}
		showForm.value = false
		editingId.value = null
		resetForm()
		await Promise.all([fetchDashboard(), fetchAssets()])
	} catch (e: any) {
		uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
	} finally {
		submitting.value = false
	}
}

const confirmDelete = (item: AssetItem) => {
	uni.showModal({
		title: '确认删除',
		content: `确定删除 ${item.crypto_symbol} 的持仓记录吗？`,
		success: async (res) => {
			if (res.confirm) {
				await deleteAsset(item.id)
			}
		},
	})
}

const deleteAsset = async (id: number) => {
	try {
		await assetsApi.delete(id)
		uni.showToast({ title: '已删除', icon: 'success' })
		await Promise.all([fetchDashboard(), fetchAssets()])
	} catch (e: any) {
		uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
	}
}

const formatNumber = (n: number): string => {
	if (n == null || isNaN(n)) return '0.00'
	return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const getItemPnl = (item: AssetItem): number => {
	return (item.current_price - item.buy_price) * item.quantity
}

const getShortSymbol = (symbol: string): string => {
	return symbol.replace('USDT', '')
}

const COIN_COLORS: Record<string, string> = {
	BTC: '#f7931a',
	ETH: '#627eea',
	SOL: '#00ffa3',
	BNB: '#f3ba2f',
	XRP: '#00aae4',
	ADA: '#0033ad',
	DOGE: '#c2a633',
	DOT: '#e6007a',
	AVAX: '#e84142',
	MATIC: '#8247e5',
}

const getCoinColor = (symbol: string): string => {
	const short = getShortSymbol(symbol)
	return COIN_COLORS[short] || '#409eff'
}

const goToLogin = () => {
	uni.navigateTo({
		url: '/pages/login/login',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}
</script>

<style scoped>
.assets-page {
	min-height: 100vh;
	background-color: var(--page-bg);
	padding: 20rpx;
}

.assets-container {
	width: 100%;
	max-width: 1200px;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
}

.guest-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 200rpx 0;
	gap: 40rpx;
}

.guest-title {
	font-size: 32rpx;
	color: var(--text-tertiary);
}

.guest-login-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 20rpx 60rpx;
}

.btn-text {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

.overview-card {
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	border-radius: 24rpx;
	padding: 40rpx;
	margin-bottom: 30rpx;
	box-shadow: 0 8rpx 24rpx rgba(102, 126, 234, 0.3);
}

.overview-label {
	font-size: 26rpx;
	color: rgba(255, 255, 255, 0.85);
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
	color: var(--text-placeholder);
}

.pnl-value {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--card-bg);
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
	background-color: rgba(255, 255, 255, 0.25);
}

.holdings-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 10rpx 0 20rpx;
}

.header-title {
	font-size: 32rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.header-actions {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.header-count {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

.add-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 16rpx 32rpx;
}

.add-btn:active {
	opacity: 0.8;
}

.pc-only {
	display: none;
}

.mobile-only {
	display: flex;
	margin-top: 24rpx;
}

.add-form-card {
	background-color: var(--card-bg);
	border-radius: 16rpx;
	padding: 30rpx;
	margin-bottom: 24rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.form-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
}

.form-title {
	font-size: 32rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.form-close {
	font-size: 48rpx;
	color: var(--text-tertiary);
	line-height: 1;
}

.form-group {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
	margin-bottom: 24rpx;
}

.form-label {
	font-size: 26rpx;
	font-weight: 500;
	color: var(--text-primary);
}

.form-input {
	width: 100%;
	height: 80rpx;
	padding: 0 20rpx;
	border: 2rpx solid var(--border-color);
	border-radius: 8rpx;
	font-size: 28rpx;
	color: var(--text-primary);
	box-sizing: border-box;
}

.form-row-group {
	display: flex;
	gap: 20rpx;
}

.form-half {
	flex: 1;
}

.form-submit-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 8rpx;
	height: 80rpx;
}

.form-submit-btn:active {
	opacity: 0.85;
}

.holdings-scroll {
	flex: 1;
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
	background-color: var(--card-bg);
	border-radius: 16rpx;
	padding: 24rpx;
	box-shadow: var(--card-shadow);
}

.holding-left {
	display: flex;
	align-items: center;
	gap: 20rpx;
	flex: 1;
	min-width: 0;
}

.coin-icon {
	width: 72rpx;
	height: 72rpx;
	border-radius: 50%;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}

.coin-abbreviation {
	font-size: 20rpx;
	font-weight: bold;
	color: #ffffff;
}

.coin-detail {
	display: flex;
	flex-direction: column;
	gap: 4rpx;
	min-width: 0;
}

.coin-name {
	font-size: 28rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.coin-amount {
	font-size: 22rpx;
	color: var(--text-tertiary);
}

.coin-buy-price {
	font-size: 20rpx;
	color: var(--text-tertiary);
}

.holding-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 6rpx;
	flex-shrink: 0;
}

.coin-current-price {
	font-size: 20rpx;
	color: var(--text-secondary);
	font-family: 'Monaco', monospace;
}

.coin-total-value {
	font-size: 32rpx;
	font-weight: 700;
	color: var(--text-primary);
	font-family: 'Monaco', monospace;
	margin-bottom: 4rpx;
}

.price-pnl-row {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 4rpx;
}

.coin-pnl {
	font-size: 24rpx;
	font-weight: 600;
	font-family: 'Monaco', monospace;
}

.coin-pnl.profit {
	color: #00c853;
}

.coin-pnl.loss {
	color: #f56c6c;
}

.action-btns {
	display: flex;
	gap: 8rpx;
	margin-top: 4rpx;
}

.edit-btn-wrap {
	padding: 4rpx 12rpx;
	border-radius: 6rpx;
	background-color: #ecf5ff;
}

.edit-btn-text {
	font-size: 20rpx;
	color: #409eff;
}

.edit-btn-wrap:active {
	opacity: 0.6;
}

.delete-btn-wrap {
	margin-top: 0;
	padding: 4rpx 12rpx;
	border-radius: 6rpx;
	background-color: #fef0f0;
}

.delete-btn-text {
	font-size: 20rpx;
	color: #f56c6c;
}

.delete-btn-wrap:active {
	opacity: 0.6;
}

.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 100rpx 0;
}

.empty-text {
	font-size: 30rpx;
	color: var(--text-tertiary);
	margin-bottom: 12rpx;
}

.empty-hint {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

.skeleton-state {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	padding: 20rpx 0;
}

.skeleton-card {
	background: linear-gradient(90deg, var(--border-color) 25%, var(--text-placeholder) 50%, var(--border-color) 75%);
	background-size: 200% 100%;
	animation: skeleton-loading 1.5s ease-in-out infinite;
	border-radius: 16rpx;
}

.skeleton-dashboard {
	height: 260rpx;
}

.skeleton-list-item {
	height: 160rpx;
}

@keyframes skeleton-loading {
	0% { background-position: 200% 0; }
	100% { background-position: -200% 0; }
}

@media (min-width: 768px) {
	.pc-only {
		display: flex;
	}

	.mobile-only {
		display: none;
	}

	.holdings-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20rpx;
	}
}
</style>
