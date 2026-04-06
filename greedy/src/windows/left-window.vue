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

// 动态设置高度，确保色块始终填满视口
const setFullHeight = () => {
	// #ifdef H5
	const el = document.querySelector('.left-window') as HTMLElement
	if (el) {
		el.style.height = window.innerHeight + 'px'
		el.style.minHeight = window.innerHeight + 'px'
	}
	// #endif
}

// #ifdef H5
setFullHeight()
window.addEventListener('resize', setFullHeight)
// #endif
</script>

<style scoped>
.left-window {
	display: flex;
	flex-direction: column;
	width: 240px !important;
	height: 100vh;
	min-height: 100vh;
	background-color: #1a1a2e;
	box-sizing: border-box;
}

.nav-header {
	padding: 30rpx 30rpx 20rpx;
	border-bottom: 2rpx solid #2a2a3e;
	flex-shrink: 0;
}

.nav-title {
	font-size: 36rpx;
	font-weight: bold;
	color: #ffffff;
}

.nav-list {
	display: flex;
	flex-direction: column;
	flex: 1;
	padding: 10rpx 0;
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
