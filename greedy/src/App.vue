<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { onMounted } from 'vue'

const handleResize = () => {
	// #ifdef H5
	if (window.innerWidth >= 768) {
		uni.hideTabBar({ fail: () => {} })
	} else {
		uni.showTabBar({ fail: () => {} })
	}
	// #endif
}

onLaunch(() => {
	console.log('App Launch')
})

onMounted(() => {
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
	overflow: hidden;
	height: 100%;
}

/* 全局隐藏左侧导航栏滚动条（注意：不要选中类名本身，否则整个导航栏会被隐藏！） */
.uni-left-window::-webkit-scrollbar {
	display: none;
	width: 0;
	height: 0;
}

.uni-left-window {
	scrollbar-width: none;
	-ms-overflow-style: none;
}
</style>
