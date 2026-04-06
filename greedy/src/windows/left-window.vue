<template>
	<view class="left-window">
		<view class="nav-header">
			<text class="nav-title">Crypto-info</text>
		</view>
		<view class="nav-list">
			<view
				v-for="item in navItems"
				:key="item.path"
				class="nav-item"
				@click="switchTab(item.path)"
			>
				<text class="nav-text">{{ item.title }}</text>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
// @update: 修复 leftWindow 高度冲突导致消失的问题，改用 uni.switchTab 路由
interface NavItem {
	title: string
	path: string
}

const navItems: NavItem[] = [
	{ title: '关注列表', path: '/pages/market/market' },
	{ title: '预警中心', path: '/pages/alert/alert' },
	{ title: '资产列表', path: '/pages/assets/assets' },
	{ title: '个人中心', path: '/pages/mine/mine' },
]

const switchTab = (path: string) => {
	uni.switchTab({ url: path })
}
</script>

<style scoped>
.left-window {
	display: flex;
	flex-direction: column;
	min-height: 100vh;
	height: 100vh;
	position: sticky;
	top: 0;
	background-color: #1a1a2e;
	padding-top: 40rpx;
	box-sizing: border-box;
	overflow: hidden;
}

.nav-header {
	padding: 30rpx;
	border-bottom: 2rpx solid #2a2a3e;
}

.nav-title {
	font-size: 36rpx;
	font-weight: bold;
	color: #ffffff;
}

.nav-list {
	display: flex;
	flex-direction: column;
	padding: 20rpx 0;
}

.nav-item {
	padding: 30rpx;
	border-bottom: 2rpx solid #2a2a3e;
	cursor: pointer;
	transition: background-color 0.2s;
}

.nav-item:hover {
	background-color: #2a2a3e;
}

.nav-text {
	font-size: 30rpx;
	color: #cccccc;
}
</style>
