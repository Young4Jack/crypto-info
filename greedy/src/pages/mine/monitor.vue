<template>
	<view class="monitor-page">
		<!-- 非 App 端提示 -->
		<view v-if="!isAppPlus" class="platform-tip">
			<text class="tip-icon">⚠️</text>
			<text class="tip-text">该功能仅支持 Android 客户端</text>
		</view>

		<!-- App 端原生设置界面 -->
		<view v-else class="monitor-container">
			<!-- 悬浮窗总开关 -->
			<view class="setting-section">
				<view class="section-header">
					<text class="section-title">悬浮窗监控</text>
					<switch
						class="section-switch"
						:checked="monitorOn"
						@change="onMonitorSwitchChange"
					/>
				</view>
				<view class="section-desc">
					<text>开启后可在屏幕上层显示实时价格监控</text>
				</view>
			</view>

			<!-- 权限提示 -->
			<view v-if="!hasPermission" class="permission-tip">
				<text class="tip-text">需要悬浮窗权限才能正常使用</text>
				<button class="btn-grant" @tap="requestPermission">去授权</button>
			</view>

			<!-- 详细设置项 -->
			<view class="setting-section" v-if="monitorOn">
				<view class="section-header">
					<text class="section-title">常亮屏幕</text>
					<switch
						class="section-switch"
						:checked="keepScreenOn"
						@change="onKeepScreenChange"
					/>
				</view>
				<view class="section-desc">
					<text>防止屏幕在监控期间自动休眠</text>
				</view>
			</view>

			<view class="setting-section" v-if="monitorOn">
				<view class="section-header">
					<text class="section-title">显示常亮开关</text>
					<switch
						class="section-switch"
						:checked="showFloatToggle"
						@change="onShowFloatToggleChange"
					/>
				</view>
				<view class="section-desc">
					<text>在悬浮窗上显示常亮开关按钮</text>
				</view>
			</view>

			<view class="setting-section" v-if="monitorOn">
				<view class="section-header">
					<text class="section-title">显示关闭按钮</text>
					<switch
						class="section-switch"
						:checked="showCloseBtn"
						@change="onShowCloseBtnChange"
					/>
				</view>
				<view class="section-desc">
					<text>在悬浮窗上显示停止监控按钮</text>
				</view>
			</view>

			<!-- 刷新频率 -->
			<view class="setting-section" v-if="monitorOn">
				<view class="section-header">
					<text class="section-title">刷新频率</text>
					<text class="section-value">{{ refreshInterval }}秒</text>
				</view>
				<view class="slider-wrapper">
					<slider
						class="refresh-slider"
						min="1"
						max="30"
						:step="1"
						:value="refreshInterval"
						@change="onRefreshIntervalChange"
						activeColor="#409EFF"
						backgroundColor="#E0E0E0"
					/>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

// 平台判断 - 使用运行时判断
const isAppPlus = ref(uni.getSystemInfoSync().platform === 'android')

// 配置状态
const hasPermission = ref(false)
const monitorOn = ref(false)
const keepScreenOn = ref(false)
const showFloatToggle = ref(false)
const showCloseBtn = ref(true)
const refreshInterval = ref(3)

// 每次切回页面都重新拉取底层真实状态
onShow(async () => {
	if (!isAppPlus.value) return
	
	try {
		const module = plus.android.importClass('com.jack2u.cryptobox.PriceMonitorModule')
		module.checkPermission()
	} catch (e) {
		console.log('触发自动启动失败:', e)
	}
	
	await checkPermission()
	await loadConfig()
})



// 检查权限
async function checkPermission() {
	// #ifdef APP-PLUS
	try {
		const Context = plus.android.importClass('android.content.Context')
		const mainActivity = plus.android.runtimeMainActivity()
		const Settings = plus.android.importClass('android.provider.Settings')
		const result = Settings.canDrawOverlays(mainActivity)
		hasPermission.value = result
		console.log('权��检查结果:', result)
	} catch (e) {
		console.error('检查权限失败:', e)
		hasPermission.value = false
	}
	// #endif
}

// 请求权限
async function requestPermission() {
	// #ifdef APP-PLUS
	try {
		const mainActivity = plus.android.runtimeMainActivity()
		const Intent = plus.android.importClass('android.content.Intent')
		const Settings = plus.android.importClass('android.provider.Settings')
		const Uri = plus.android.importClass('android.net.Uri')
		const intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:" + mainActivity.getPackageName()))
		intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
		mainActivity.startActivity(intent)
	} catch (e) {
		console.error('请求权限失败:', e)
	}
	// #endif
}

// 加载配置
async function loadConfig() {
	// #ifdef APP-PLUS
	// 优先尝试从原生模块读取配置
	try {
		const module = plus.android.importClass('com.jack2u.cryptobox.PriceMonitorModule')
		const configStr = module.getMonitorConfig()
		const config = JSON.parse(configStr)
		if (config) {
			// 如果 monitor_on 为 true，直接调用 updateMonitor 启动服务
			if (config.monitor_on) {
				module.updateMonitor(JSON.stringify({ monitor_on: true }))
				console.log('loadConfig: 触发服务启动')
			}
			
			monitorOn.value = config.monitor_on || false
			keepScreenOn.value = config.keep_screen_on || false
			showFloatToggle.value = config.show_float_toggle || false
			showCloseBtn.value = config.show_close_btn !== false
			refreshInterval.value = config.refresh_interval || 3
			// 同时保存到本地存储作为备份
			uni.setStorageSync('monitor_on', config.monitor_on)
			uni.setStorageSync('keep_screen_on', config.keep_screen_on)
			uni.setStorageSync('show_float_toggle', config.show_float_toggle)
			uni.setStorageSync('show_close_btn', config.show_close_btn)
			uni.setStorageSync('refresh_interval', config.refresh_interval)
			return
		}
	} catch (e) {
		console.log('读取原生配置失败，使用本地存储:', e)
	}
	
	// 备用：使用本地存储
	const monitorOnVal = uni.getStorageSync('monitor_on') || false
	const keepScreenOnVal = uni.getStorageSync('keep_screen_on') || false
	const showFloatToggleVal = uni.getStorageSync('show_float_toggle') || false
	const showCloseBtnVal = uni.getStorageSync('show_close_btn')
	const refreshIntervalVal = uni.getStorageSync('refresh_interval') || 3
	
	monitorOn.value = monitorOnVal
	keepScreenOn.value = keepScreenOnVal
	showFloatToggle.value = showFloatToggleVal
	showCloseBtn.value = showCloseBtnVal !== false
	refreshInterval.value = refreshIntervalVal
	// #endif
}

// 更新配置
async function updateMonitor(options: Record<string, any>) {
	// #ifdef APP-PLUS
	try {
		// 先保存到本地存储
		if ('monitor_on' in options) uni.setStorageSync('monitor_on', options.monitor_on)
		if ('keep_screen_on' in options) uni.setStorageSync('keep_screen_on', options.keep_screen_on)
		if ('show_float_toggle' in options) uni.setStorageSync('show_float_toggle', options.show_float_toggle)
		if ('show_close_btn' in options) uni.setStorageSync('show_close_btn', options.show_close_btn)
		if ('refresh_interval' in options) uni.setStorageSync('refresh_interval', options.refresh_interval)
		
		console.log('updateMonitor参数:', JSON.stringify(options))
		
		// 尝试调用原生
		try {
			const module = plus.android.importClass('com.jack2u.cryptobox.PriceMonitorModule')
			module.updateMonitor(JSON.stringify(options))
		} catch (e) {
			console.log('原生模块未初始化:', e)
		}
		
		if ('monitor_on' in options) monitorOn.value = options.monitor_on
		if ('keep_screen_on' in options) keepScreenOn.value = options.keep_screen_on
		if ('show_float_toggle' in options) showFloatToggle.value = options.show_float_toggle
		if ('show_close_btn' in options) showCloseBtn.value = options.show_close_btn
		if ('refresh_interval' in options) refreshInterval.value = options.refresh_interval
	} catch (e) {
		console.error('更新配置失败:', e)
	}
	// #endif
}

// 悬浮窗总开关
async function onMonitorSwitchChange(e: any) {
	const value = e.detail.value
	console.log('开关值:', value, '当前权限状态:', hasPermission.value)
    
    // ★ 修改 3：如果是要开启悬浮窗，强制进行一次实时检查
	if (value) {
		await checkPermission()
		console.log('检查后权限状态:', hasPermission.value)
		if (!hasPermission.value) {
            // UI 回弹为 false
            setTimeout(() => { monitorOn.value = false }, 50)
			uni.showToast({ title: '请先授予悬浮窗权限', icon: 'none' })
			await requestPermission()
			return
		}
	}
	await updateMonitor({ monitor_on: value })
}

// 常亮开关
async function onKeepScreenChange(e: any) {
	await updateMonitor({ keep_screen_on: e.detail.value })
}

// 显示常亮切换按钮
async function onShowFloatToggleChange(e: any) {
	await updateMonitor({ show_float_toggle: e.detail.value })
}

// 显示关闭按钮
async function onShowCloseBtnChange(e: any) {
	await updateMonitor({ show_close_btn: e.detail.value })
}

// 刷新频率
async function onRefreshIntervalChange(e: any) {
	await updateMonitor({ refresh_interval: e.detail.value })
}
</script>

<style scoped>
.monitor-page {
	min-height: 100vh;
	background-color: #F5F7FA;
}

.platform-tip {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 200rpx 0;
}

.tip-icon {
	font-size: 80rpx;
	margin-bottom: 30rpx;
}

.tip-text {
	font-size: 30rpx;
	color: #666;
}

.monitor-container {
	padding: 30rpx;
}

.setting-section {
	background-color: #FFFFFF;
	border-radius: 16rpx;
	padding: 30rpx;
	margin-bottom: 20rpx;
}

.section-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.section-title {
	font-size: 32rpx;
	color: #333;
	font-weight: 500;
}

.section-desc {
	font-size: 26rpx;
	color: #999;
	margin-top: 10rpx;
}

.section-value {
	font-size: 28rpx;
	color: #409EFF;
}

.permission-tip {
	background-color: #FFF7E6;
	border: 1rpx solid #FFB800;
	border-radius: 16rpx;
	padding: 30rpx;
	margin-bottom: 20rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.permission-tip .tip-text {
	color: #B8860B;
	font-size: 28rpx;
	margin-bottom: 20rpx;
}

.btn-grant {
	background-color: #409EFF;
	color: #FFFFFF;
	font-size: 28rpx;
	padding: 20rpx 60rpx;
	border-radius: 40rpx;
	border: none;
}

.slider-wrapper {
	margin-top: 20rpx;
}

.refresh-slider {
	width: 100%;
}
</style>
