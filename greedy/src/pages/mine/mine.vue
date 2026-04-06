<template>
	<view class="mine-page">
		<view class="mine-container">
			<!-- 用户信息区 -->
			<view class="user-profile">
				<view class="avatar-wrapper">
					<view class="avatar">
						<text class="avatar-text">J</text>
					</view>
				</view>
				<view class="user-info">
					<text class="nickname">Jack</text>
					<text class="uid">UID: 88392017</text>
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
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
// @update: 实现个人中心页面，含用户信息区与设置菜单列表
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

/* PC 端响应式 */
@media (min-width: 768px) {
	.mine-container {
		max-width: 800px;
	}
}
</style>
