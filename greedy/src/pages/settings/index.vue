<template>
	<view class="settings-page">
		<view class="settings-container">
			<view class="menu-group">
				<view class="menu-item" @tap="goToNotification">
					<view class="menu-left">
						<text class="menu-icon">📢</text>
						<text class="menu-label">通知渠道管理</text>
					</view>
					<view class="menu-right">
						<text class="menu-arrow">›</text>
					</view>
				</view>
				<view class="menu-item" @tap="goToApi">
					<view class="menu-left">
						<text class="menu-icon">🔌</text>
						<text class="menu-label">API 节点设置</text>
					</view>
					<view class="menu-right">
						<text class="menu-arrow">›</text>
					</view>
				</view>
				<view class="menu-item" @tap="goToPreference">
					<view class="menu-left">
						<text class="menu-icon">🛠️</text>
						<text class="menu-label">系统偏好设置</text>
					</view>
					<view class="menu-right">
						<text class="menu-arrow">›</text>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
const goToNotification = () => {
	uni.navigateTo({
		url: '/pages/settings/notification',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const goToApi = () => {
	uni.navigateTo({
		url: '/pages/settings/api',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}

const goToPreference = () => {
	uni.navigateTo({
		url: '/pages/settings/preference',
		fail: () => {
			uni.showToast({ title: '页面跳转失败', icon: 'none' })
		},
	})
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background-color: var(--page-bg);
  padding: 20rpx;
}

.settings-container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}

.menu-group {
  background-color: var(--card-bg);
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
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

.menu-item:active {
  background-color: var(--page-bg);
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

.menu-arrow {
  font-size: 36rpx;
  color: var(--text-tertiary);
}
</style>
