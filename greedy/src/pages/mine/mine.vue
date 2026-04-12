<template>
	<view class="mine-page" @touchstart="onTouchStart" @touchend="onTouchEnd">
		<view class="mine-container">
			<!-- 用户信息区：未登录态 -->
			<view v-if="!isLoggedIn" class="user-profile guest-profile" @tap="goToLogin">
				<view class="avatar-wrapper">
					<view class="avatar avatar-guest">
						<text class="avatar-text">?</text>
					</view>
				</view>
				<view class="user-info">
					<text class="nickname nickname-guest">点击登录/注册</text>
					<text class="uid">登录后享受更多服务</text>
				</view>
			</view>

			<!-- 用户信息区：已登录态 -->
			<view v-else class="user-profile">
				<view class="avatar-wrapper">
					<view class="avatar">
						<text class="avatar-text">{{ userInfo.nickname.charAt(0) }}</text>
					</view>
				</view>
				<view class="user-info">
					<text class="nickname">{{ userInfo.nickname }}</text>
					<text class="uid">{{ userInfo.uid }}</text>
				</view>
			</view>

			<!-- 设置菜单列表 -->
			<view class="menu-section">
				<view class="menu-group">
					<view class="menu-item" @tap="goToSecurity">
						<view class="menu-left">
							<text class="menu-icon">👤</text>
							<text class="menu-label">账户安全</text>
						</view>
						<view class="menu-right">
							<text class="menu-arrow">›</text>
						</view>
					</view>
					<view class="menu-item" @tap="goToSettings">
						<view class="menu-left">
							<text class="menu-icon">⚙️</text>
							<text class="menu-label">系统设置</text>
						</view>
						<view class="menu-right">
							<text class="menu-arrow">›</text>
						</view>
					</view>
					<!-- #ifdef APP-PLUS -->
					<view class="menu-item" @tap="goToMonitor">
						<view class="menu-left">
							<text class="menu-icon">🖥️</text>
							<text class="menu-label">悬浮窗监控</text>
						</view>
						<view class="menu-right">
							<text class="menu-arrow">›</text>
						</view>
					</view>
					<!-- #endif -->
				</view>

				<view class="menu-group">
					<view class="menu-item" @tap="showThemePicker = true">
						<view class="menu-left">
							<text class="menu-icon">🌙</text>
							<text class="menu-label">主题切换</text>
						</view>
						<view class="menu-right">
							<text class="menu-value">{{ currentThemeLabel }}</text>
							<text class="menu-arrow">›</text>
						</view>
					</view>
					<view class="menu-item" @tap="showCurrencyPicker = true">
						<view class="menu-left">
							<text class="menu-icon">💱</text>
							<text class="menu-label">计价货币</text>
						</view>
						<view class="menu-right">
							<text class="menu-value">{{ currentCurrencyDisplay }}</text>
							<text class="menu-arrow">›</text>
						</view>
					</view>
				</view>

				<view class="menu-group">
					<view class="menu-item" @tap="handleMenuTap('api')">
						<view class="menu-left">
							<text class="menu-icon">🔑</text>
							<text class="menu-label">API Keys 管理</text>
						</view>
						<view class="menu-right">
							<text class="menu-arrow">›</text>
						</view>
					</view>
					<view class="menu-item" @tap="handleMenuTap('about')">
						<view class="menu-left">
							<text class="menu-icon">ℹ️</text>
							<text class="menu-label">关于我们</text>
						</view>
						<view class="menu-right">
							<text class="menu-value">v0.0.1</text>
							<text class="menu-arrow">›</text>
						</view>
					</view>
				</view>

				<!-- 退出登录按钮：仅已登录态显示 -->
				<view v-if="isLoggedIn" class="menu-group logout-group">
					<view class="menu-item menu-item-logout" @tap="handleLogout">
						<view class="menu-left">
							<text class="menu-icon">🚪</text>
							<text class="menu-label menu-label-logout">退出登录</text>
						</view>
						<view class="menu-right">
							<text class="menu-arrow menu-arrow-logout">›</text>
						</view>
					</view>
				</view>
			</view>

			<!-- 主题选择弹窗 -->
			<view v-if="showThemePicker" class="modal-overlay" @tap="showThemePicker = false">
				<view class="modal-content" @tap.stop>
					<view class="modal-header">
						<text class="modal-title">选择主题</text>
						<text class="modal-close" @tap="showThemePicker = false">×</text>
					</view>
					<view class="theme-options">
						<view
							v-for="opt in themeOptions"
							:key="opt.value"
							class="theme-option"
							:class="{ active: themeMode === opt.value }"
							@tap="selectTheme(opt.value)"
						>
							<text class="theme-label">{{ opt.label }}</text>
							<text v-if="themeMode === opt.value" class="theme-check">✓</text>
						</view>
					</view>
				</view>
			</view>

			<!-- 计价货币选择弹窗 -->
			<view v-if="showCurrencyPicker" class="modal-overlay" @tap="showCurrencyPicker = false">
				<view class="modal-content" @tap.stop>
					<view class="modal-header">
						<text class="modal-title">选择计价货币</text>
						<text class="modal-close" @tap="showCurrencyPicker = false">×</text>
					</view>
					<view class="theme-options">
						<view
							v-for="opt in currencyOptions"
							:key="opt.value"
							class="theme-option"
							:class="{ active: currentCurrency === opt.value }"
							@tap="selectCurrency(opt.value)"
						>
							<text class="theme-label">{{ opt.label }}</text>
							<text v-if="currentCurrency === opt.value" class="theme-check">✓</text>
						</view>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { authApi, systemSettingsApi } from '@/api'
import { useTheme, type ThemeMode } from '@/composables/useDarkMode'
import { useSwipeTab } from '@/composables/useSwipeTab'
import { getCurrentCurrency, setCurrentCurrency, currencySymbols, initCurrencyService, fetchCurrencyConfig } from '@/utils/exchangeRate'

const { themeMode, isDarkMode, setTheme, getThemeLabel } = useTheme()

const { onTouchStart, onTouchEnd, switchToNextTab, switchToPrevTab } = useSwipeTab(
  () => switchToNextTab(),
  () => switchToPrevTab()
)

// 登录状态
const isLoggedIn = ref(false)

// 初始化汇率服务
onMounted(async () => {
	await initCurrencyService()
	// 检查登录状态
	const token = uni.getStorageSync('token')
	isLoggedIn.value = !!token
})

// 页面显示时刷新登录状态
onShow(() => {
	const token = uni.getStorageSync('token')
	isLoggedIn.value = !!token
	if (isLoggedIn.value) {
		fetchCurrencyFromBackend()
	}
})

// 从后端获取计价货币
const fetchCurrencyFromBackend = async () => {
	try {
		const res = await systemSettingsApi.getFull()
		const backendCurrency = res.data.current_pricing_currency
		if (backendCurrency) {
			setCurrentCurrency(backendCurrency)
			currentCurrency.value = backendCurrency
		}
	} catch (e) {
		console.error('获取后端货币设置失败', e)
	}
}

const currentCurrency = ref(getCurrentCurrency())
const currentCurrencyDisplay = computed(() => {
	const curr = currentCurrency.value
	return `${curr} ${currencySymbols[curr] || ''}`
})

const showThemePicker = ref(false)
const showCurrencyPicker = ref(false)

const currentThemeLabel = computed(() => getThemeLabel(themeMode.value))

const themeOptions = [
  { value: 'light' as ThemeMode, label: '浅色' },
  { value: 'dark' as ThemeMode, label: '深色' },
  { value: 'system' as ThemeMode, label: '跟随系统' },
]

const currencyOptions = [
  { value: 'USD', label: '美元 ($)' },
  { value: 'CNY', label: '人民币 (¥)' },
  { value: 'EUR', label: '欧元 (€)' },
  { value: 'JPY', label: '日元 (¥)' },
]

const selectTheme = (mode: ThemeMode) => {
  setTheme(mode)
  showThemePicker.value = false
}

const selectCurrency = async (currency: string) => {
	// 先更新本地
	setCurrentCurrency(currency)
	currentCurrency.value = currency
	
	// 非 USD 时重新获取汇率
	if (currency !== 'USD') {
		await fetchCurrencyConfig()
	}
	
	// 如果已登录，保存到后端
	if (isLoggedIn.value) {
		try {
			await systemSettingsApi.update({
				current_pricing_currency: currency
			})
			uni.showToast({ title: '已保存', icon: 'success' })
		} catch (e: any) {
			uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
		}
	}
	
	showCurrencyPicker.value = false
}

// 加载状态
const loading = ref(false)

// 用户信息
interface UserInfo {
	nickname: string
	uid: string
	avatar: string
}

const userInfo = ref<UserInfo>({
	nickname: '',
	uid: '',
	avatar: '',
})

// 重置用户信息为空
const resetUserInfo = () => {
	userInfo.value = {
		nickname: '',
		uid: '',
		avatar: '',
	}
}

// 每次页面显示时读取本地 token 并拉取真实用户数据
onShow(async () => {
	const token = uni.getStorageSync('token')
	if (!token) {
		isLoggedIn.value = false
		resetUserInfo()
		return
	}

	loading.value = true
	try {
		const res = await authApi.getMe()
		const user = res.data
		isLoggedIn.value = true
		userInfo.value = {
			nickname: user.username,
			uid: user.email,
			avatar: '',
		}
	} catch {
		// Token 过期或请求失败，清除本地状态
		isLoggedIn.value = false
		uni.removeStorageSync('token')
		resetUserInfo()
	} finally {
		loading.value = false
	}
})

// 跳转登录页
const goToLogin = () => {
	uni.navigateTo({
		url: '/pages/login/login',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

// 退出登录
const handleLogout = () => {
	uni.showModal({
		title: '提示',
		content: '确定要退出登录吗？',
		success: (res) => {
			if (res.confirm) {
				uni.removeStorageSync('token')
				isLoggedIn.value = false
				userInfo.value = {
					nickname: '',
					uid: '',
					avatar: '',
				}
				uni.showToast({ title: '已退出登录', icon: 'success' })
			}
		},
	})
}

// 菜单点击处理
const handleMenuTap = (type: string) => {
	switch (type) {
		case 'currency':
			uni.navigateTo({
				url: '/pages/settings/preference',
				fail: () => {
					uni.showToast({ title: '页面跳转失败', icon: 'none' })
				}
			})
			break
		case 'api':
			uni.showToast({ title: 'API 功能开发中', icon: 'none' })
			break
		case 'about':
			uni.showToast({ title: '关于功能开发中', icon: 'none' })
			break
		default:
			uni.showToast({ title: `${type} 功能开发中`, icon: 'none' })
	}
}

const goToSecurity = () => {
	uni.navigateTo({
		url: '/pages/mine/security',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const goToSettings = () => {
	uni.navigateTo({
		url: '/pages/settings/index',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const goToMonitor = () => {
	uni.navigateTo({
		url: '/pages/mine/monitor',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}
</script>

<style scoped>
.mine-page {
	display: flex;
	justify-content: center;
	min-height: 100vh;
	background-color: var(--page-bg);
	padding: 20rpx;
}

.mine-container {
	width: 100%;
	max-width: 800px;
}

/* 用户信息区 */
.user-profile {
	display: flex;
	align-items: center;
	gap: 30rpx;
	background-color: var(--card-bg);
	border-radius: 24rpx;
	padding: 40rpx;
	margin-bottom: 30rpx;
	box-shadow: var(--card-shadow);
}

/* 未登录态：可点击 */
.guest-profile {
	cursor: pointer;
	transition: opacity 0.2s;
}

.guest-profile:active {
	opacity: 0.7;
}

.avatar-wrapper {
	flex-shrink: 0;
}

.avatar {
	width: 100rpx;
	height: 100rpx;
	border-radius: 50%;
	background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
	display: flex;
	align-items: center;
	justify-content: center;
}

/* 未登录灰色头像 */
.avatar-guest {
	background: linear-gradient(135deg, #909399 0%, #606266 100%);
}

.avatar-text {
	font-size: 44rpx;
	font-weight: bold;
	color: #ffffff;
}

.user-info {
	display: flex;
	flex-direction: column;
	gap: 10rpx;
}

.nickname {
	font-size: 36rpx;
	font-weight: 600;
	color: var(--text-primary);
}

/* 未登录态昵称 */
.nickname-guest {
	color: var(--text-tertiary);
}

.uid {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

/* 设置菜单列表 */
.menu-section {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.menu-group {
	background-color: var(--card-bg);
	border-radius: 16rpx;
	overflow: hidden;
	box-shadow: var(--card-shadow);
}

.menu-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 28rpx 30rpx;
	border-bottom: 2rpx solid var(--border-color);
}

.menu-item:last-child {
	border-bottom: none;
}

.menu-left {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.menu-icon {
	font-size: 36rpx;
}

.menu-label {
    font-size: 30rpx;
    color: var(--text-primary);
}

.menu-right {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.menu-value {
    font-size: 26rpx;
    color: var(--text-tertiary);
}

.menu-arrow {
    font-size: 36rpx;
    color: var(--text-tertiary);
}

/* 退出登录按钮样式 */
.logout-group {
	margin-top: 20rpx;
}

.menu-item-logout {
	cursor: pointer;
}

.menu-item-logout:active {
	background-color: #fef0f0;
}

.menu-label-logout {
	color: #f56c6c;
	font-weight: 500;
}

.menu-arrow-logout {
	color: #f56c6c;
}

/* PC 端响应式 */
@media (min-width: 768px) {
	.mine-container {
		max-width: 800px;
	}
}

/* 主题选择弹窗 */
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

.theme-options {
	padding: 20rpx 0;
}

.theme-option {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 28rpx 30rpx;
}

.theme-option:active {
	background-color: var(--page-bg);
}

.theme-option.active {
	background-color: var(--border-color);
}

.theme-label {
    font-size: 30rpx;
    color: var(--text-primary);
}

.theme-check {
	font-size: 32rpx;
	color: var(--text-primary);
}
</style>
