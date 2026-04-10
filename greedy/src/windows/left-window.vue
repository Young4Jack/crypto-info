<template>
	<view class="left-window">
		<view class="nav-header">
			<view class="logo-wrap">
				<text class="logo-icon">📊</text>
				<text class="nav-title">{{ siteTitle }}</text>
			</view>
			<text class="nav-subtitle">{{ siteDescription }}</text>
		</view>
		<view class="nav-list">
			<view
				v-for="(item, index) in navItems"
				:key="item.path"
				class="nav-item"
				:class="{ active: activeIndex === index }"
				@click="switchTab(item.path, index)"
			>
				<text class="nav-icon">{{ item.icon }}</text>
				<text class="nav-text">{{ item.title }}</text>
				<view class="active-bar"></view>
			</view>
		</view>
		<view class="nav-footer">
			<text class="footer-text">v1.0.0</text>
		</view>
	</view>
</template>

<script setup lang="ts">
// @update: 修复 leftWindow 高度冲突导致消失的问题，改用 uni.switchTab 路由
import { ref, onMounted } from 'vue'
import { get } from '@/utils/request'

interface NavItem {
	title: string
	path: string
	icon: string
}

const navItems: NavItem[] = [
	{ title: '关注列表', path: '/pages/market/market', icon: '⭐' },
	{ title: '预警中心', path: '/pages/alert/alert', icon: '🔔' },
	{ title: '资产列表', path: '/pages/assets/assets', icon: '💰' },
	{ title: '个人中心', path: '/pages/mine/mine', icon: '👤' },
]

const siteTitle = ref('Crypto-info')
const siteDescription = ref('加密货币实时监控')
const activeIndex = ref(0)

const fetchSiteTitle = async () => {
	try {
		const res = await get<{ site_title: string; site_description: string }>('/api/system-settings/public')
		if (res.data?.site_title) {
			siteTitle.value = res.data.site_title
		}
		if (res.data?.site_description) {
			siteDescription.value = res.data.site_description
		}
	} catch (e) {
		console.error('获取站点设置失败', e)
	}
}

onMounted(() => {
	fetchSiteTitle()
})

const switchTab = (path: string, index: number) => {
	activeIndex.value = index
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
	background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
	box-sizing: border-box;
}

.nav-header {
	padding: 40rpx 30rpx 30rpx;
	border-bottom: 1rpx solid rgba(255,255,255,0.1);
	flex-shrink: 0;
}

.logo-wrap {
	display: flex;
	align-items: center;
	margin-bottom: 12rpx;
}

.logo-icon {
	font-size: 40rpx;
	margin-right: 16rpx;
}

.nav-title {
	font-size: 36rpx;
	font-weight: 700;
	color: #ffffff;
	letter-spacing: 2rpx;
}

.nav-subtitle {
	font-size: 22rpx;
	color: rgba(255,255,255,0.5);
}

.nav-list {
	display: flex;
	flex-direction: column;
	flex: 1;
	padding: 20rpx 0;
}

.nav-item {
	position: relative;
	display: flex;
	align-items: center;
	padding: 28rpx 30rpx;
	cursor: pointer;
	transition: all 0.3s ease;
}

.nav-item:hover {
	background: rgba(255,255,255,0.05);
}

.nav-item.active {
	background: linear-gradient(90deg, rgba(64,158,255,0.2) 0%, transparent 100%);
}

.nav-item.active .nav-text {
	color: #409EFF;
	font-weight: 600;
}

.nav-icon {
	font-size: 32rpx;
	margin-right: 20rpx;
	width: 40rpx;
	text-align: center;
}

.nav-text {
	font-size: 28rpx;
	color: rgba(255,255,255,0.8);
	transition: color 0.3s;
}

.active-bar {
	position: absolute;
	left: 0;
	top: 50%;
	transform: translateY(-50%);
	width: 6rpx;
	height: 40rpx;
	background: #409EFF;
	border-radius: 0 4rpx 4rpx 0;
	opacity: 0;
	transition: opacity 0.3s;
}

.nav-item.active .active-bar {
	opacity: 1;
}

.nav-footer {
	padding: 30rpx;
	border-top: 1rpx solid rgba(255,255,255,0.1);
	flex-shrink: 0;
	text-align: center;
}

.footer-text {
	font-size: 20rpx;
	color: rgba(255,255,255,0.3);
}
</style>
