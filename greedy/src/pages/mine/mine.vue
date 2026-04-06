<template>
	<view class="mine-page">
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
					<view class="menu-item" @tap="handleMenuTap('theme')">
						<view class="menu-left">
							<text class="menu-icon">🌙</text>
							<text class="menu-label">主题切换</text>
						</view>
						<view class="menu-right">
							<text class="menu-value">浅色</text>
							<text class="menu-arrow">›</text>
						</view>
					</view>
					<view class="menu-item" @tap="handleMenuTap('currency')">
						<view class="menu-left">
							<text class="menu-icon">💱</text>
							<text class="menu-label">计价货币</text>
						</view>
						<view class="menu-right">
							<text class="menu-value">USD</text>
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
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { authApi } from '@/api'

// 登录状态
const isLoggedIn = ref(false)

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

// 菜单点击占位
const handleMenuTap = (type: string) => {
	uni.showToast({ title: `${type} 功能开发中`, icon: 'none' })
}
</script>

<style scoped>
.mine-page {
	display: flex;
	justify-content: center;
	min-height: 100vh;
	background-color: #f5f7fa;
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
	background-color: #ffffff;
	border-radius: 24rpx;
	padding: 40rpx;
	margin-bottom: 30rpx;
	box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
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
	background: linear-gradient(135deg, #409eff 0%, #2c7be5 100%);
	display: flex;
	align-items: center;
	justify-content: center;
}

/* 未登录灰色头像 */
.avatar-guest {
	background: linear-gradient(135deg, #c0c4cc 0%, #909399 100%);
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
	color: #1a1a2e;
}

/* 未登录态昵称 */
.nickname-guest {
	color: #909399;
}

.uid {
	font-size: 24rpx;
	color: #909399;
}

/* 设置菜单列表 */
.menu-section {
	display: flex;
	flex-direction: column;
	gap: 20rpx;
}

.menu-group {
	background-color: #ffffff;
	border-radius: 16rpx;
	overflow: hidden;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.menu-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 28rpx 30rpx;
	border-bottom: 2rpx solid #f0f2f5;
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
	color: #1a1a2e;
}

.menu-right {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.menu-value {
	font-size: 26rpx;
	color: #909399;
}

.menu-arrow {
	font-size: 36rpx;
	color: #c0c4cc;
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
</style>
