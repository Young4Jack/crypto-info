<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { initConfig } from '@/utils/config'

const handleResize = () => {
	// #ifdef H5
	if (window.innerWidth >= 768) {
		uni.hideTabBar({ fail: () => {} })
	} else {
		uni.showTabBar({ fail: () => {} })
	}
	// #endif
}

onLaunch(async () => {
	console.log('App Launch')
	// 初始化全局配置（API 域名、WS 域名）
	await initConfig()
	// #ifdef H5
	handleResize()
	window.addEventListener('resize', handleResize)
	// #endif
})
</script>

<style>
page {
	background-color: #f5f7fa;
}

/* 禁止 html/body 产生额外滚动容器 */
html, body {
	margin: 0;
	padding: 0;
	overflow-y: auto;
	height: 100%;
}

/* 全局隐藏左侧导航栏滚动条 + 强制色块延伸 */
.uni-left-window::-webkit-scrollbar {
	display: none;
	width: 0;
	height: 0;
}

.uni-left-window {
	scrollbar-width: none;
	-ms-overflow-style: none;
	position: fixed !important;
	top: 0 !important;
	left: 0 !important;
	bottom: 0 !important;
	background-color: #1a1a2e !important;
	margin: 0 !important;
	padding: 0 !important;
}
</style>
