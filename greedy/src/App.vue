<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { initConfig } from '@/utils/config'
import { useTheme, initTheme } from '@/composables/useDarkMode'
import { initCurrencyService } from '@/utils/exchangeRate'

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
	// 初始化主题（在 apiBase 设置完成之后）
	initTheme()
	// 应用用户选择的主题
	useTheme()
	// 初始化汇率服务
	initCurrencyService()
	// #ifdef H5
	handleResize()
	window.addEventListener('resize', handleResize)
	// #endif
})
</script>

<style>
/* ========== 全局 CSS 变量主题系统 ========== */
page {
	background-color: var(--page-bg, #f5f7fa);
}

/* 浅色主题（默认） */
:root {
	--page-bg: #f5f7fa;
	--card-bg: #ffffff;
	--text-primary: #1a1a2e;
	--text-secondary: #606266;
	--text-tertiary: #909399;
	--text-placeholder: #c0c4cc;
	--border-color: #dcdfe6;
	--card-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
	--header-bg: #ffffff;
	--input-bg: #ffffff;
}

/* 深色主题 */
.dark {
	--page-bg: #0f1419;
	--card-bg: #1a1f2e;
	--text-primary: #e8eaed;
	--text-secondary: #9aa0a6;
	--text-tertiary: #5f6368;
	--text-placeholder: #3c4043;
	--border-color: #2d333b;
	--card-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.3);
	--header-bg: #1a1f2e;
	--input-bg: #22272e;
}

/* 禁止 html/body 产生额外滚动容器 */
html, body {
	margin: 0;
	padding: 0;
	overflow-x: hidden;
	overflow-y: auto;
	height: 100%;
	width: 100%;
	max-width: 100vw;
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

/* ========== App 端底部导航栏样式适配 ========== */
/* #ifndef H5 */
.uni-tabbar {
	background-color: #ffffff !important;
	border-top: 1px solid #e4e7ed !important;
}

.uni-tabbar-item .uni-tabbar-item-icon {
	display: none !important;
}

.uni-tabbar-item .uni-tabbar-item-text {
	font-size: 14px !important;
	color: #606266 !important;
	font-weight: 500;
}

.uni-tabbar-item-selected .uni-tabbar-item-text {
	color: #409EFF !important;
	font-weight: 700 !important;
}
/* #endif */

/* ========== H5 端底部导航栏深色模式适配 ========== */
/* #ifdef H5 */
.dark .uni-tabbar {
	background-color: #1a1f2e !important;
	border-top-color: #2d333b !important;
}

.dark .uni-tabbar .uni-tabbar-item .uni-tabbar-item-icon image {
	filter: brightness(0.6) invert(1);
	opacity: 0.7;
	transition: all 0.3s;
}

.dark .uni-tabbar .uni-tabbar-item.uni-tabbar-item-selected .uni-tabbar-item-icon image {
	filter: brightness(1) invert(1);
	opacity: 1;
}

.dark .uni-tabbar .uni-tabbar-item .uni-tabbar-item-text {
	color: #5f6368 !important;
}

.dark .uni-tabbar .uni-tabbar-item.uni-tabbar-item-selected .uni-tabbar-item-text {
	color: #409EFF !important;
}

/* H5 端导航栏深色模式 */
.dark .uni-page-head {
	background-color: var(--card-bg) !important;
}

.dark .uni-page-head .uni-page-head__title,
.dark .uni-page-head .uni-page-head__inner .uni-page-head__title,
.dark .uni-page-head .uni-title {
	color: var(--text-primary) !important;
}

.dark .uni-page-head .uni-page-head__content {
	color: var(--text-primary) !important;
}

/* 修复全局横向滚动 */
html, body {
	overflow-x: hidden;
	width: 100%;
	max-width: 100vw;
}
/* #endif */
</style>
