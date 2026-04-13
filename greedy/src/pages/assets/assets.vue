<template>
	<view class="assets-page" @touchstart="onTouchStart" @touchend="onTouchEnd">
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
					<!-- Dashboard 骨架屏 -->
					<view v-if="!dashboardLoaded" class="skeleton-dashboard"></view>

					<!-- 仪表盘概览卡片 -->
					<view v-if="dashboardLoaded" class="overview-card">
						<text class="overview-label">总估值</text>
						<view class="value-row">
							<text class="overview-value">{{ formatInteger (dashboard.total_value) }}</text>
							<text class="cost-label">成本: {{ formatInteger (dashboard.total_cost) }}</text>
						</view>
						<view class="pnl-row">
							<view class="pnl-item">
								<text class="pnl-label">累计盈亏</text>
								<text :class="['pnl-value', dashboard.total_profit_loss >= 0 ? 'profit' : 'loss']">
									{{ dashboard.total_profit_loss >= 0 ? '+' : '' }}{{ formatInteger (dashboard.total_profit_loss) }}
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
					<view class="assets-header">
						<text class="header-title">持有资产</text>
						<view class="header-actions">
							<text class="header-count">共 {{ assets.length }} 个</text>
							<!-- 刷新按钮 -->
							<view class="header-action-btn" @tap="refreshAll">
								<view class="action-icon-wrap">
									<text class="action-icon" :class="{ 'icon-spin': loading }">⟳</text>
								</view>
							</view>
							<!-- 添加资产按钮 -->
							<view class="header-action-btn" @tap="toggleForm">
								<view class="action-icon-wrap action-icon-primary">
									<text class="action-icon">＋</text>
								</view>
							</view>
							<!-- 管理按钮 -->
							<view class="manage-toggle" @tap="toggleManageMode">
								<text class="manage-text">{{ isManageMode ? '完成' : '管理' }}</text>
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
								<view class="holding-main">
									<view class="holding-left">
										<view class="coin-icon" :style="{ backgroundColor: getCoinColor(item.crypto_symbol) }">
											<text class="coin-abbreviation">{{ getShortSymbol(item.crypto_symbol) }}</text>
										</view>
										<view class="coin-detail">
											<view class="coin-name-row">
												<text class="coin-name">{{ item.crypto_name }}</text>
												<text class="coin-add-time">{{ formatDate(item.created_at) }}</text>
											</view>
											<text class="coin-amount">
												{{ item.quantity }}<text v-if="item.notes"> ({{ item.notes }})</text>
											</text>
											<view class="coin-pnl-inline" :class="getItemPnl(item) >= 0 ? 'profit' : 'loss'">
												<text class="coin-pnl-inline-text" :class="getItemPnl(item) >= 0 ? 'profit' : 'loss'">
													{{ getItemPnl(item) >= 0 ? '+' : '' }}{{ formatInteger(getItemPnl(item)) }} ({{ getItemPnlPercent(item) }}%)
												</text>
											</view>
										</view>
									</view>
									<view class="holding-right">
										<view class="price-row">
											<view class="price-item">
												<text class="price-item-label">买入价</text>
												<text class="price-item-value">{{ formatNumber(item.buy_price) }}</text>
											</view>
											<view class="price-item">
												<text class="price-item-label">成本</text>
												<text class="price-item-value">{{ formatInteger(item.cost_value) }}</text>
											</view>
										</view>
										<view class="price-row">
											<view class="price-item">
												<text class="price-item-label">现价</text>
												<text class="price-item-value">{{ formatNumber(item.current_price) }}</text>
											</view>
											<view class="price-item">
												<text class="price-item-label">现值</text>
												<text class="price-item-value">{{ formatInteger(item.total_value) }}</text>
											</view>
										</view>
									</view>
								</view>
								<!-- 管理模式操作按钮 -->
								<view v-if="isManageMode" class="item-actions">
									<view class="action-btn edit" @tap.stop="openEdit(item)">
										<text>编辑</text>
									</view>
									<view class="action-btn delete" @tap.stop="confirmDelete(item)">
										<text>删除</text>
									</view>
								</view>
							</view>

							<view v-if="assets.length === 0" class="empty-state">
								<text class="empty-text">暂无持仓记录</text>
								<text class="empty-hint">点击上方按钮添加你的第一个资产</text>
							</view>
						</view>
					</scroll-view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { onShow, onHide, onPullDownRefresh } from '@dcloudio/uni-app'
import { dashboardApi, assetsApi, type AssetItem } from '@/api'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useSwipeTab } from '@/composables/useSwipeTab'
import { formatPrice } from '@/utils/formatPrice'

const isLoggedIn = ref(false)
const loading = ref(false)
const submitting = ref(false)
const dashboardLoaded = ref(false)
const showForm = ref(false)
const editingId = ref<number | null>(null)
const isManageMode = ref(false)

const { startAutoRefresh, stopAutoRefresh } = useAutoRefresh()

const { onTouchStart, onTouchEnd, switchToNextTab, switchToPrevTab } = useSwipeTab(
  () => switchToNextTab(),
  () => switchToPrevTab()
)

const dashboard = ref({
	total_value: 0,
	total_cost: 0,
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

// 刷新全部数据（资产列表 + 仪表盘）
const refreshAll = async (isBackground = false) => {
	if (!isBackground) {
		loading.value = true
	}
	await Promise.all([fetchDashboard(), fetchAssets(isBackground)])
	if (!isBackground) {
		loading.value = false
	}
}

onShow(async () => {
	const token = uni.getStorageSync('token')
	if (!token) {
		isLoggedIn.value = false
		assets.value = []
		dashboardLoaded.value = false
		return
	}
	isLoggedIn.value = true
	// 并发加载资产列表和仪表盘数据
	await Promise.all([fetchAssets(), fetchDashboard()])
	// 启动自动刷新（同时刷新 assets 和 dashboard）
	startAutoRefresh(() => refreshAll(true))
})

onHide(() => {
	stopAutoRefresh()
})

onUnmounted(() => {
	stopAutoRefresh()
})

// 下拉刷新
onPullDownRefresh(async () => {
	await refreshAll()
	uni.stopPullDownRefresh()
})

const fetchDashboard = async () => {
	try {
		const res = await dashboardApi.getSummary()
		dashboard.value = {
			total_value: res.data.total_value || 0,
			total_cost: res.data.total_cost || 0,
			total_profit_loss: res.data.total_profit_loss || 0,
			total_profit_loss_percentage: res.data.total_profit_loss_percentage || 0,
		}
		dashboardLoaded.value = true
	} catch (e: any) {
		console.error('获取仪表盘数据失败', e, e?.message)
		dashboardLoaded.value = true
	}
}

const fetchAssets = async (isBackground = false) => {
	if (!isBackground) {
		loading.value = true
	}
	try {
		const res = await assetsApi.getList()
		assets.value = res.data || []
	} catch (e: any) {
		console.error('获取资产列表失败', e, e?.message)
	} finally {
		if (!isBackground) {
			loading.value = false
		}
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

const resetForm = () => {
	form.value = {
		crypto_symbol: '',
		buy_price: '',
		quantity: '',
		notes: '',
	}
}

const openEdit = (item: AssetItem) => {
	isManageMode.value = false
	editingId.value = item.id
	showForm.value = true
	form.value.crypto_symbol = item.crypto_symbol
	form.value.buy_price = String(item.buy_price)
	form.value.quantity = String(item.quantity)
	form.value.notes = item.notes || ''
	uni.pageScrollTo({ scrollTop: 0, duration: 200 })
}

const toggleManageMode = () => {
	isManageMode.value = !isManageMode.value
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
		const notesValue = form.value.notes.trim()
		const payload: any = {
			crypto_symbol: symbol,
			buy_price: buyPrice,
			quantity: quantity,
		}
		// notes 允许为空字符串，用于清空备注
		payload.notes = notesValue
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
	// 使用 formatPrice 格式化价格，$.00$ 确保只替换结尾的小数部分
	return formatPrice(n).replace(/\.00$/, '')
}

const formatInteger = (n: number): string => {
    if (n == null || isNaN(n)) return '0.00'
    // 调用 formatPrice 获取带符号的结果，再手动去掉小数部分
    return formatPrice(n).replace(/\.\d+$/, '')
}

const formatDate = (dateStr: string): string => {
	if (!dateStr) return ''
	const date = new Date(dateStr)
	const year = date.getFullYear()
	const month = String(date.getMonth() + 1).padStart(2, '0')
	const day = String(date.getDate()).padStart(2, '0')
	return `${year}/${month}/${day}`
}

const getItemPnl = (item: AssetItem): number => {
	// 使用 Math.round 消除浮点精度问题
	const pnl = (item.current_price - item.buy_price) * item.quantity
	return Math.round(pnl * 100) / 100
}

const getItemPnlPercent = (item: AssetItem): string => {
	if (item.cost_value === 0) return '0.00'
	const pct = ((item.current_price - item.buy_price) / item.buy_price) * 100
	return pct.toFixed(2)
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

.skeleton-dashboard {
	height: 200rpx;
	border-radius: 24rpx;
	margin-bottom: 30rpx;
	background: linear-gradient(90deg, var(--border-color) 25%, var(--text-placeholder) 50%, var(--border-color) 75%);
	background-size: 200% 100%;
	animation: skeleton-loading 1.5s ease-in-out infinite;
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
}

.value-row {
	display: flex;
	align-items: baseline;
	gap: 16rpx;
	margin-bottom: 30rpx;
}

.cost-label {
	font-size: 24rpx;
	color: rgba(255, 255, 255, 0.7);
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
	color: #ffb3b3;
}

.pnl-value.loss {
	color: #a8ffb2;
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
	animation: spin 1s linear infinite;
}

@keyframes spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}

.header-count {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

.manage-toggle {
	display: flex;
	align-items: center;
	justify-content: center;
	min-width: 100rpx;
	height: 56rpx;
	padding: 0 24rpx;
	border-radius: 28rpx;
	background-color: #ecf5ff;
}

.manage-toggle:active {
	background-color: #d9ecff;
}

.manage-text {
	font-size: 24rpx;
	color: #409eff;
	font-weight: 500;
}

.assets-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 10rpx 0 20rpx;
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
	flex-direction: column;
	background-color: var(--card-bg);
	border-radius: 16rpx;
	padding: 24rpx;
	box-shadow: var(--card-shadow);
}

.holding-main {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
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

.coin-name-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.coin-amount {
	font-size: 22rpx;
	color: var(--text-tertiary);
}

.coin-add-time {
	font-size: 20rpx;
	color: var(--text-tertiary);
}

.coin-meta-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	margin-top: 4rpx;
}

.coin-pnl-inline {
	display: inline-flex;
	align-items: center;
	padding: 2rpx 8rpx;
	border-radius: 4rpx;
	margin-top: 4rpx;
}

.coin-pnl-inline.profit {
	background-color: rgba(245, 108, 108, 0.1);
}

.coin-pnl-inline.loss {
	background-color: rgba(0, 200, 83, 0.1);
}

.coin-pnl-inline-text {
	font-size: 20rpx;
	font-weight: 600;
	font-family: 'Monaco', monospace;
}

.coin-pnl-inline-text.profit {
	color: #f56c6c;
}

.coin-pnl-inline-text.loss {
	color: #00c853;
}

.holding-right {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 8rpx;
	flex-shrink: 0;
}

.price-row {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.price-item {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2rpx;
}

.price-item-label {
	font-size: 18rpx;
	color: var(--text-tertiary);
}

.price-item-value {
	font-size: 20rpx;
	color: var(--text-primary);
	font-family: 'Monaco', monospace;
}

.price-sep {
	font-size: 18rpx;
	color: var(--text-tertiary);
}

.pnl-spacer {
	flex: 1;
}

.holding-pnl-row {
	display: flex;
	align-items: baseline;
	width: 100%;
	justify-content: flex-end;
}

.pnl-amount {
	font-size: 28rpx;
	font-weight: 600;
	font-family: 'Monaco', monospace;
}

.pnl-pct {
	font-size: 22rpx;
	font-family: 'Monaco', monospace;
	margin-left: 8rpx;
}

.price-row {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.price-item {
	display: flex;
	flex-direction: column;
	align-items: flex-end;
	gap: 2rpx;
}

.price-item-label {
	font-size: 18rpx;
	color: var(--text-tertiary);
}

.price-item-value {
	font-size: 20rpx;
	color: var(--text-primary);
	font-family: 'Monaco', monospace;
}

.item-actions {
	display: flex;
	gap: 12rpx;
	margin-top: 16rpx;
	padding-top: 16rpx;
	border-top: 2rpx solid var(--border-color);
}

.action-btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 56rpx;
	border-radius: 6rpx;
	font-size: 24rpx;
	font-weight: 500;
}

.action-btn:active {
	opacity: 0.7;
}

.action-btn.edit {
	background-color: #ecf5ff;
	color: #409eff;
}

.action-btn.delete {
	background-color: #fef0f0;
	color: #f56c6c;
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
