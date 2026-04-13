<template>
	<view class="history-page" @touchstart="onTouchStart" @touchend="onTouchEnd">
		<view class="history-container">
			<!-- 页面头部 -->
			<view class="page-header">
				<text class="header-title">预警历史</text>
				<view class="header-actions">
					<!-- 显示数量选择器 -->
					<picker
						mode="selector"
						:range="limitOptions"
						:value="selectedLimitIndex"
						@change="onLimitChange"
					>
						<view class="limit-picker">
							<text class="limit-text">{{ limitOptions[selectedLimitIndex] }}条</text>
							<text class="limit-arrow">▼</text>
						</view>
					</picker>
					<!-- 刷新按钮 -->
					<view class="header-action-btn" @tap="fetchHistoryList">
						<view class="action-icon-wrap">
							<text class="action-icon" :class="{ 'icon-spin': loading }">⟳</text>
						</view>
					</view>
					<!-- 清空按钮 -->
					<view v-if="isLoggedIn && historyList.length > 0" class="manage-toggle" @tap="confirmClear">
						<text class="manage-text">清空</text>
					</view>
				</view>
			</view>

			<!-- 未登录态：提示 + 登录按钮 -->
			<view v-if="!isLoggedIn" class="guest-state">
				<text class="guest-title">请登录后使用</text>
				<view class="guest-login-btn" @tap="goToLogin">
					<text class="btn-text">立即登录</text>
				</view>
			</view>

			<!-- 已登录态 -->
			<view v-else>
				<!-- 首次加载骨架屏 -->
				<view v-if="loading && historyList.length === 0" class="skeleton-state">
					<view class="skeleton-card"></view>
					<view class="skeleton-card"></view>
					<view class="skeleton-card"></view>
				</view>

				<!-- 历史列表 -->
				<view v-else class="history-list">
					<view v-for="item in historyList" :key="item.id" class="history-item">
						<view class="item-header">
							<view class="coin-info">
								<text class="coin">{{ item.crypto_symbol }}</text>
								<text class="type-badge" :class="'badge-' + item.alert_type">{{ formatAlertType(item.alert_type) }}</text>
							</view>
							<text class="status-text" :class="'status-' + item.status">{{ formatStatus(item.status) }}</text>
						</view>
						<view class="item-body">
							<view class="body-row">
								<view class="price-info">
									<text class="lbl">触发价</text>
									<text class="val">{{ formatPrice(item.trigger_price) }}</text>
								</view>
								<view class="price-info">
									<text class="lbl">目标价</text>
									<text class="val">{{ formatPrice(item.threshold_price) }}</text>
								</view>
							</view>
							<view class="body-row">
								<view class="price-info" v-if="item.notification_channel">
									<text class="lbl">通知</text>
									<text class="val notify">{{ item.notification_channel }}</text>
									<text class="val" v-if="item.notification_group"> / {{ item.notification_group }}</text>
								</view>
							</view>
						</view>
						<view class="item-meta">
							<view class="meta-item">
								<text class="meta-label">触发时间</text>
								<text class="meta-val">{{ formatDate(item.created_at) }}</text>
							</view>
							<view class="meta-item" v-if="item.notification_sent">
								<text class="meta-label">通知时间</text>
								<text class="meta-val">{{ formatDate(item.notification_sent) }}</text>
							</view>
						</view>
						<view class="item-actions">
							<view class="action-btn delete" @tap="confirmDelete(item)">
								<text>删除</text>
							</view>
						</view>
					</view>

					<view v-if="!loading && historyList.length === 0" class="empty-state">
						<text class="empty-text">暂无预警历史</text>
						<text class="empty-hint">预警触发后会显示在这里</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { alertHistoriesApi, type AlertHistoryItem } from '@/api'
import { formatPrice } from '@/utils/formatPrice'

const formatDate = (dateStr: string | null): string => {
	if (!dateStr) return '--'
	try {
		const date = new Date(dateStr)
		const month = String(date.getMonth() + 1).padStart(2, '0')
		const day = String(date.getDate()).padStart(2, '0')
		const hour = String(date.getHours()).padStart(2, '0')
		const min = String(date.getMinutes()).padStart(2, '0')
		return `${month}-${day} ${hour}:${min}`
	} catch {
		return '--'
	}
}

const formatAlertType = (type: string): string => {
	switch (type) {
		case 'above': return '涨破'
		case 'below': return '跌破'
		case 'percent_up': return '涨幅'
		case 'percent_down': return '跌幅'
		case 'amplitude': return '振幅'
		default: return type
	}
}

const formatStatus = (status: string): string => {
	switch (status) {
		case 'triggered': return '已触发'
		case 'notified': return '已通知'
		case 'failed': return '失败'
		default: return status
	}
}

const isLoggedIn = ref(false)
const loading = ref(false)
const historyList = ref<AlertHistoryItem[]>([])

const limitOptions = [10, 20, 30, 50, 100]
const selectedLimitIndex = ref(2)

const onLimitChange = (e: any) => {
	selectedLimitIndex.value = parseInt(e.detail.value, 10)
	fetchHistoryList()
}

onShow(async () => {
	const token = uni.getStorageSync('token')
	if (!token) {
		isLoggedIn.value = false
		historyList.value = []
		return
	}
	isLoggedIn.value = true
	await fetchHistoryList()
})

onPullDownRefresh(async () => {
	await fetchHistoryList()
	uni.stopPullDownRefresh()
})

const fetchHistoryList = async () => {
	loading.value = true
	try {
		const limit = limitOptions[selectedLimitIndex.value]
		const res = await alertHistoriesApi.getList(0, limit)
		historyList.value = res.data || []
	} catch (e: any) {
		console.error('获取预警历史失败', e)
	} finally {
		loading.value = false
	}
}

const confirmDelete = (item: AlertHistoryItem) => {
	uni.showModal({
		title: '确认删除',
		content: `确定删除 ${item.crypto_symbol} 的这条历史记录吗？`,
		success: async (res) => {
			if (res.confirm) {
				await deleteHistory(item.id)
			}
		},
	})
}

const deleteHistory = async (id: number) => {
	try {
		await alertHistoriesApi.delete(id)
		uni.showToast({ title: '已删除', icon: 'success' })
		await fetchHistoryList()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
	}
}

const confirmClear = () => {
	uni.showModal({
		title: '确认清空',
		content: '确定清空所有预警历史记录吗？',
		success: async (res) => {
			if (res.confirm) {
				await clearHistory()
			}
		},
	})
}

const clearHistory = async () => {
	try {
		await alertHistoriesApi.clear()
		uni.showToast({ title: '已清空', icon: 'success' })
		historyList.value = []
	} catch (e: any) {
		uni.showToast({ title: e?.message || '清空失败', icon: 'none' })
	}
}

const goToLogin = () => {
	uni.navigateTo({
		url: '/pages/login/login',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const onTouchStart = () => {}
const onTouchEnd = () => {}
</script>

<style scoped>
.history-page {
    min-height: 100vh;
    background-color: var(--page-bg);
    padding: 20rpx;
}

.history-container {
	width: 100%;
	max-width: 1200px;
	margin: 0 auto;
}

/* 页面头部 */
.page-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 10rpx 0 20rpx;
}

.header-title {
    font-size: 36rpx;
    font-weight: bold;
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

.action-icon {
	font-size: 36rpx;
	color: #666;
	font-weight: bold;
}

.icon-spin {
	animation: spin 1s linear infinite;
}

@keyframes spin {
	from { transform: rotate(0deg); }
	to { transform: rotate(360deg); }
}

.manage-toggle {
	display: flex;
	align-items: center;
	justify-content: center;
	min-width: 100rpx;
	height: 56rpx;
	padding: 0 24rpx;
	border-radius: 28rpx;
	background-color: #f56c6c;
}

.manage-toggle:active {
	background-color: #f78989;
}

.manage-text {
	font-size: 24rpx;
	color: #fff;
	font-weight: 500;
}

/* 显示数量选择器 */
.limit-picker {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 56rpx;
	padding: 0 20rpx;
	border-radius: 28rpx;
	background-color: #ecf5ff;
}

.limit-picker:active {
	background-color: #d9ecff;
}

.limit-text {
	font-size: 24rpx;
	color: #409eff;
	font-weight: 500;
}

.limit-arrow {
	font-size: 16rpx;
	color: #409eff;
	margin-left: 8rpx;
}

/* 未登录态 */
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

/* 骨架屏 */
.skeleton-state {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	padding: 20rpx 0;
}

.skeleton-card {
	height: 160rpx;
	background: linear-gradient(90deg, var(--border-color) 25%, var(--text-placeholder) 50%, var(--border-color) 75%);
	background-size: 200% 100%;
	animation: skeleton-loading 1.5s ease-in-out infinite;
	border-radius: 16rpx;
}

@keyframes skeleton-loading {
	0% { background-position: 200% 0; }
	100% { background-position: -200% 0; }
}

/* 列表 */
.history-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	padding-bottom: 20rpx;
}

.history-item {
	display: flex;
	flex-direction: column;
	background: var(--card-bg);
	border-radius: 16rpx;
	padding: 24rpx;
	margin-bottom: 16rpx;
	box-shadow: var(--card-shadow);
}

.item-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 16rpx;
}

.coin-info {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.coin {
	font-size: 32rpx;
	font-weight: 700;
	color: var(--text-primary);
}

.type-badge {
	font-size: 20rpx;
	padding: 4rpx 10rpx;
	border-radius: 8rpx;
}

.type-badge.badge-above {
	background-color: #fef0f0;
	color: #f56c6c;
}

.type-badge.badge-below {
	background-color: #ecf5ff;
	color: #409eff;
}

.type-badge.badge-percent_up,
.type-badge.badge-percent_down,
.type-badge.badge-amplitude {
	background-color: #fdf6ec;
	color: #e6a23c;
}

.status-text {
	font-size: 24rpx;
	font-weight: 500;
}

.status-triggered {
	color: #e6a23c;
}

.status-notified {
	color: #10b981;
}

.status-failed {
	color: #f56c6c;
}

.item-body {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	padding: 16rpx;
	background: var(--page-bg);
	border-radius: 10rpx;
}

.body-row {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx 32rpx;
}

.price-info {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.lbl {
	font-size: 22rpx;
	color: var(--text-tertiary);
	width: 60rpx;
	flex-shrink: 0;
}

.val {
	font-size: 26rpx;
	color: var(--text-primary);
}

.val.notify {
	color: #409eff;
}

.item-meta {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-top: 16rpx;
}

.meta-item {
	display: flex;
	align-items: center;
	gap: 6rpx;
}

.meta-label {
	font-size: 20rpx;
	color: var(--text-tertiary);
}

.meta-val {
	font-size: 20rpx;
	color: var(--text-secondary);
}

.item-actions {
	display: flex;
	gap: 12rpx;
	margin-top: 16rpx;
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

.action-btn.delete {
	background-color: #fef0f0;
	color: #f56c6c;
}

/* 空状态 */
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

/* PC 端 */
@media (min-width: 768px) {
	.history-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20rpx;
	}
}
</style>