<template>
	<view class="preference-page">
		<view class="preference-container">
			<!-- 基本设置 -->
			<view class="config-card">
				<text class="card-title">基本设置</text>

				<view class="form-group">
					<text class="form-label">站点标题</text>
					<input
						class="form-input"
						type="text"
						placeholder="如 Crypto-info"
						v-model="form.site_title"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">站点描述</text>
					<input
						class="form-input"
						type="text"
						placeholder="站点描述信息"
						v-model="form.site_description"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">系统时区</text>
					<picker mode="selector" :range="timezoneOptions" :value="timezoneIndex" @change="onTimezoneChange">
						<view class="picker-value">
							<text class="picker-text">{{ form.timezone || '请选择时区' }}</text>
							<text class="picker-arrow">▾</text>
						</view>
					</picker>
				</view>
			</view>

			<!-- 轮询与数据 -->
			<view class="config-card">
				<text class="card-title">轮询与数据</text>

				<view class="form-group">
					<text class="form-label">刷新频率（秒）</text>
					<input
						class="form-input"
						type="number"
						placeholder="默认 8 秒"
						v-model.number="form.refresh_interval"
					/>
				</view>
			</view>

			<!-- 功能开关 -->
			<view class="config-card">
				<text class="card-title">功能开关</text>

				<view class="switch-row">
					<text class="switch-label">启用验证码</text>
					<switch
						:checked="form.enable_captcha"
						color="#409EFF"
						@change="onSwitchChange('enable_captcha', $event)"
					/>
				</view>

				<view class="switch-row">
					<text class="switch-label">启用系统日志</text>
					<switch
						:checked="form.enable_logging"
						color="#409EFF"
						@change="onSwitchChange('enable_logging', $event)"
					/>
				</view>

				<view class="switch-row">
					<text class="switch-label">默认深色模式</text>
					<switch
						:checked="form.default_dark_mode"
						color="#409EFF"
						@change="onSwitchChange('default_dark_mode', $event)"
					/>
				</view>
			</view>

			<!-- 日志级别 -->
			<view class="config-card">
				<text class="card-title">日志级别</text>

				<view class="form-group">
					<picker mode="selector" :range="logLevelOptions" :value="logLevelIndex" @change="onLogLevelChange">
						<view class="picker-value">
							<text class="picker-text">{{ form.log_level || 'INFO' }}</text>
							<text class="picker-arrow">▾</text>
						</view>
					</picker>
				</view>
			</view>

			<!-- 保存按钮 -->
			<view class="submit-btn" @tap="onSubmit">
				<text class="btn-text">{{ submitting ? '保存中...' : '保存偏好' }}</text>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { systemSettingsApi } from '@/api'

const TIMEZONES = ['Asia/Shanghai', 'Asia/Tokyo', 'America/New_York', 'Europe/London', 'UTC']
const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

const timezoneOptions = TIMEZONES
const logLevelOptions = LOG_LEVELS

const form = ref({
	site_title: '',
	site_description: '',
	timezone: 'Asia/Shanghai',
	refresh_interval: 8,
	enable_captcha: false,
	enable_logging: false,
	default_dark_mode: false,
	log_level: 'INFO',
})

const submitting = ref(false)

const timezoneIndex = computed(() => {
	const idx = TIMEZONES.indexOf(form.value.timezone)
	return idx >= 0 ? idx : 0
})

const logLevelIndex = computed(() => {
	const idx = LOG_LEVELS.indexOf(form.value.log_level)
	return idx >= 0 ? idx : 1
})

onShow(async () => {
	await fetchSettings()
})

const fetchSettings = async () => {
	try {
		const res = await systemSettingsApi.getFull()
		const d = res.data
		form.value.site_title = d.site_title || ''
		form.value.site_description = d.site_description || ''
		form.value.timezone = d.timezone || 'Asia/Shanghai'
		form.value.refresh_interval = d.refresh_interval || 8
		form.value.enable_captcha = d.enable_captcha || false
		form.value.enable_logging = d.enable_logging || false
		form.value.default_dark_mode = d.default_dark_mode || false
		form.value.log_level = d.log_level || 'INFO'
	} catch (e: any) {
		uni.showToast({ title: '获取配置失败', icon: 'none' })
	}
}

const onTimezoneChange = (event: any) => {
	form.value.timezone = TIMEZONES[parseInt(event.detail.value)]
}

const onLogLevelChange = (event: any) => {
	form.value.log_level = LOG_LEVELS[parseInt(event.detail.value)]
}

const onSwitchChange = (key: string, event: any) => {
	form.value[key] = event.detail?.value ?? event.value ?? false
}

const onSubmit = async () => {
	if (form.value.refresh_interval && form.value.refresh_interval < 1) {
		uni.showToast({ title: '刷新频率不能小于1秒', icon: 'none' })
		return
	}

	submitting.value = true
	try {
		await systemSettingsApi.update({
			site_title: form.value.site_title.trim() || undefined,
			site_description: form.value.site_description.trim() || undefined,
			timezone: form.value.timezone || undefined,
			refresh_interval: form.value.refresh_interval || undefined,
			enable_captcha: form.value.enable_captcha,
			enable_logging: form.value.enable_logging,
			default_dark_mode: form.value.default_dark_mode,
			log_level: form.value.log_level || undefined,
		})
		uni.showToast({ title: '偏好已保存', icon: 'success' })
		setTimeout(() => {
			uni.navigateBack()
		}, 1500)
	} catch (e: any) {
		uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
	} finally {
		submitting.value = false
	}
}
</script>

<style scoped>
.preference-page {
	min-height: 100vh;
	background-color: var(--page-bg);
	padding: 20rpx;
}

.preference-container {
	width: 100%;
	max-width: 800px;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
	gap: 20rpx;
	padding-bottom: 40rpx;
}

.config-card {
	background-color: var(--card-bg);
	border-radius: 16rpx;
	padding: 30rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.card-title {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--text-primary);
	margin-bottom: 24rpx;
}

.form-group {
	margin-bottom: 24rpx;
}

.form-group:last-child {
	margin-bottom: 0;
}

.form-label {
 	font-size: 26rpx;
 	font-weight: 500;
 	color: var(--text-primary);
	margin-bottom: 12rpx;
	display: block;
}

.form-input {
	width: 100%;
	height: 80rpx;
	padding: 0 20rpx;
	border: 2rpx solid var(--border-color);
	border-radius: 8rpx;
	font-size: 28rpx;
	color: var(--text-primary);
	box-sizing: border-box;
	background-color: var(--input-bg);
}

.form-input:focus {
	border-color: #409eff;
}

.picker-value {
	width: 100%;
	height: 80rpx;
	padding: 0 20rpx;
	border: 2rpx solid var(--border-color);
	border-radius: 8rpx;
	font-size: 28rpx;
	color: var(--text-primary);
	display: flex;
	align-items: center;
	justify-content: space-between;
	box-sizing: border-box;
	background-color: var(--input-bg);
}

.picker-text {
	color: var(--text-primary);
}

.picker-text:empty::before {
	content: '请选择';
	color: var(--text-tertiary);
}

.picker-arrow {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

.switch-row {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 16rpx 0;
	border-bottom: 2rpx solid var(--border-color);
}

.switch-row:last-child {
	border-bottom: none;
}

.switch-label {
 	font-size: 28rpx;
 	color: var(--text-primary);
}

.submit-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 88rpx;
	background-color: #409eff;
	border-radius: 12rpx;
}

.submit-btn:active {
	opacity: 0.85;
}

.btn-text {
	font-size: 30rpx;
	color: #ffffff;
	font-weight: 500;
}
</style>
