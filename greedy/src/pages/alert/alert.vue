<template>
	<view class="alert-page">
		<view class="alert-container">
			<!-- 页面头部 -->
			<view class="page-header">
				<text class="header-title">预警中心</text>
				<view v-if="isLoggedIn" class="add-btn pc-only" @tap="toggleAddForm">
					<text class="btn-text">+ 添加预警</text>
				</view>
			</view>

			<!-- 未登录态：提示 + 登录按钮 -->
			<view v-if="!isLoggedIn" class="guest-state">
				<text class="guest-title">登录后可设置专属价格预警</text>
				<view class="guest-login-btn" @tap="goToLogin">
					<text class="btn-text">立即登录</text>
				</view>
			</view>

			<!-- 已登录态：列表 + 添加表单 -->
			<template v-else>
				<!-- 添加预警表单 -->
				<view v-if="showAddForm" class="add-form-card">
					<view class="form-header">
						<text class="form-title">新建预警</text>
						<text class="form-close" @tap="toggleAddForm">×</text>
					</view>

					<view class="form-group">
						<text class="form-label">交易对</text>
						<input
							class="form-input"
							type="text"
							placeholder="如 BTCUSDT"
							v-model="form.crypto_symbol"
						/>
					</view>

					<view class="form-group">
						<text class="form-label">预警方向</text>
						<view class="radio-group">
							<view
								class="radio-btn"
								:class="{ active: form.alert_type === 'above' }"
								@tap="form.alert_type = 'above'"
							>
								<text>涨破（高于）</text>
							</view>
							<view
								class="radio-btn"
								:class="{ active: form.alert_type === 'below' }"
								@tap="form.alert_type = 'below'"
							>
								<text>跌破（低于）</text>
							</view>
						</view>
					</view>

					<view class="form-group">
						<text class="form-label">目标价格</text>
						<input
							class="form-input"
							type="digit"
							placeholder="输入触发价格"
							v-model="form.threshold_price"
						/>
					</view>

					<view class="form-submit-btn" @tap="submitAlert">
						<text class="btn-text">{{ submitting ? '提交中...' : '确认添加' }}</text>
					</view>
				</view>

				<!-- 预警规则列表 -->
				<scroll-view scroll-y class="alert-scroll">
					<view class="alert-list">
						<view
							v-for="item in alertRules"
							:key="item.id"
							class="alert-card"
						>
							<view class="rule-info">
								<view class="rule-header">
									<text class="rule-symbol">{{ item.crypto_symbol }}</text>
									<text :class="['rule-status', item.is_active ? 'active' : 'inactive']">
										{{ item.is_active ? '监控中' : '已暂停' }}
									</text>
								</view>
								<text class="rule-condition">{{ formatCondition(item) }}</text>
							</view>
							<view class="rule-actions">
								<text class="delete-btn" @tap="confirmDelete(item)">删除</text>
							</view>
						</view>

						<view v-if="!loading && alertRules.length === 0" class="empty-state">
							<text class="empty-text">暂无预警规则</text>
							<text class="empty-hint">点击添加按钮创建你的第一条预警</text>
						</view>
					</view>
				</scroll-view>

				<!-- 移动端底部添加按钮 -->
				<view class="add-btn mobile-only" @tap="toggleAddForm">
					<text class="btn-text">+ 添加预警</text>
				</view>
			</template>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { alertsApi, type AlertItem } from '@/api'

// 登录状态
const isLoggedIn = ref(false)

// 加载状态
const loading = ref(false)
const submitting = ref(false)

// 预警列表
const alertRules = ref<AlertItem[]>([])

// 添加表单显隐
const showAddForm = ref(false)

// 表单数据
const form = ref({
	crypto_symbol: '',
	alert_type: 'above' as 'above' | 'below',
	threshold_price: '',
})

// 每次页面显示时检查登录态并拉取列表
onShow(() => {
	const token = uni.getStorageSync('token')
	if (!token) {
		isLoggedIn.value = false
		alertRules.value = []
		return
	}
	isLoggedIn.value = true
	fetchAlertList()
})

// 获取预警列表
const fetchAlertList = async () => {
	loading.value = true
	try {
		const res = await alertsApi.getList()
		alertRules.value = res.data
	} catch (e: any) {
		console.error('获取预警列表失败', e)
	} finally {
		loading.value = false
	}
}

// 切换添加表单显隐
const toggleAddForm = () => {
	showAddForm.value = !showAddForm.value
	if (!showAddForm.value) {
		// 关闭表单时清空输入
		form.value = {
			crypto_symbol: '',
			alert_type: 'above',
			threshold_price: '',
		}
	}
}

// 提交新预警
const submitAlert = async () => {
	const symbol = form.value.crypto_symbol.trim().toUpperCase()
	const price = parseFloat(form.value.threshold_price)

	if (!symbol) {
		uni.showToast({ title: '请输入交易对', icon: 'none' })
		return
	}
	if (!price || price <= 0) {
		uni.showToast({ title: '请输入有效价格', icon: 'none' })
		return
	}

	submitting.value = true
	try {
		await alertsApi.create({
			crypto_symbol: symbol,
			alert_type: form.value.alert_type,
			threshold_price: price,
		})
		uni.showToast({ title: '预警添加成功', icon: 'success' })
		// 关闭表单并刷新列表
		showAddForm.value = false
		form.value = {
			crypto_symbol: '',
			alert_type: 'above',
			threshold_price: '',
		}
		await fetchAlertList()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '添加失败', icon: 'none' })
	} finally {
		submitting.value = false
	}
}

// 确认删除
const confirmDelete = (item: AlertItem) => {
	uni.showModal({
		title: '确认删除',
		content: `确定删除 ${item.crypto_symbol} 的预警规则吗？`,
		success: async (res) => {
			if (res.confirm) {
				await deleteAlert(item.id)
			}
		},
	})
}

// 执行删除
const deleteAlert = async (id: number) => {
	try {
		await alertsApi.delete(id)
		uni.showToast({ title: '已删除', icon: 'success' })
		await fetchAlertList()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
	}
}

// 格式化预警条件显示
const formatCondition = (item: AlertItem): string => {
	const typeText = item.alert_type === 'above' ? '高于' : item.alert_type === 'below' ? '低于' : item.alert_type
	return `${typeText} $${item.threshold_price.toLocaleString()}`
}

// 跳转登录页
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
.alert-page {
	display: flex;
	justify-content: center;
	min-height: 100vh;
	background-color: #f5f7fa;
	padding: 20rpx;
}

.alert-container {
	width: 100%;
	max-width: 1200px;
	display: flex;
	flex-direction: column;
	height: 100%;
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
	color: #1a1a2e;
}

/* 添加按钮通用样式 */
.add-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 16rpx 32rpx;
	transition: opacity 0.2s;
}

.add-btn:active {
	opacity: 0.8;
}

.btn-text {
	font-size: 28rpx;
	color: #ffffff;
	font-weight: 500;
}

/* 响应式显隐控制 */
.pc-only {
	display: none;
}

.mobile-only {
	margin-top: 20rpx;
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
	color: #909399;
}

.guest-login-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	background-color: #409eff;
	border-radius: 12rpx;
	padding: 20rpx 60rpx;
}

/* 添加表单卡片 */
.add-form-card {
	background-color: #ffffff;
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
	color: #1a1a2e;
}

.form-close {
	font-size: 48rpx;
	color: #909399;
	line-height: 1;
	cursor: pointer;
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
	color: #303133;
}

.form-input {
	width: 100%;
	height: 80rpx;
	padding: 0 20rpx;
	border: 2rpx solid #dcdfe6;
	border-radius: 8rpx;
	font-size: 28rpx;
	color: #303133;
	background-color: #ffffff;
	box-sizing: border-box;
}

/* 单选按钮组 */
.radio-group {
	display: flex;
	gap: 20rpx;
}

.radio-btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	height: 72rpx;
	border: 2rpx solid #dcdfe6;
	border-radius: 8rpx;
	font-size: 26rpx;
	color: #606266;
	cursor: pointer;
}

.radio-btn.active {
	border-color: #409eff;
	background-color: #ecf5ff;
	color: #409eff;
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

/* 滚动列表 */
.alert-scroll {
	flex: 1;
	height: 0;
}

.alert-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	padding-bottom: 20rpx;
}

.alert-card {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background-color: #ffffff;
	border-radius: 16rpx;
	padding: 28rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.rule-info {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
	flex: 1;
}

.rule-header {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.rule-symbol {
	font-size: 30rpx;
	font-weight: 600;
	color: #1a1a2e;
}

.rule-status {
	font-size: 22rpx;
	padding: 4rpx 12rpx;
	border-radius: 6rpx;
}

.rule-status.active {
	background-color: #e6f7ec;
	color: #00c853;
}

.rule-status.inactive {
	background-color: #f0f2f5;
	color: #909399;
}

.rule-condition {
	font-size: 26rpx;
	color: #606266;
}

.rule-actions {
	display: flex;
	align-items: center;
	gap: 16rpx;
}

.delete-btn {
	font-size: 26rpx;
	color: #f56c6c;
	padding: 8rpx 16rpx;
	cursor: pointer;
}

.delete-btn:active {
	opacity: 0.6;
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
	color: #909399;
	margin-bottom: 12rpx;
}

.empty-hint {
	font-size: 24rpx;
	color: #c0c4cc;
}

/* PC 端响应式 */
@media (min-width: 768px) {
	.pc-only {
		display: flex;
	}

	.mobile-only {
		display: none;
	}

	.alert-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 20rpx;
	}
}
</style>
