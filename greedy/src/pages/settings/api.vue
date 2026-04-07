<template>
	<view class="api-page">
		<view class="api-container">
			<!-- 主用数据源 -->
			<view class="config-card">
				<view class="card-header">
					<text class="card-title">主用数据源</text>
					<view class="test-btn" @tap="testPrimary">
						<text class="test-text">{{ testingPrimary ? '测试中...' : '测试连接' }}</text>
					</view>
				</view>

				<view class="form-group">
					<text class="form-label">API Base URL</text>
					<input
						class="form-input"
						type="text"
						placeholder="如 https://www.okx.com"
						v-model="form.primary_api_url"
					/>
				</view>
			</view>

			<!-- 备用数据源 -->
			<view class="config-card">
				<view class="card-header">
					<text class="card-title">备用数据源</text>
					<view class="test-btn" @tap="testBackup">
						<text class="test-text">{{ testingBackup ? '测试中...' : '测试连接' }}</text>
					</view>
				</view>

				<view class="form-group">
					<text class="form-label">API Base URL</text>
					<input
						class="form-input"
						type="text"
						placeholder="如 https://api.binance.com"
						v-model="form.backup_api_url"
					/>
				</view>
			</view>

			<!-- 认证信息 -->
			<view class="config-card">
				<text class="card-title">认证信息</text>

				<view class="form-group">
					<text class="form-label">API Key</text>
					<input
						class="form-input"
						:type="showKey ? 'text' : 'password'"
						placeholder="留空则不修改"
						v-model="form.api_key"
					/>
					<view class="toggle-visibility" @tap="showKey = !showKey">
						<text class="toggle-text">{{ showKey ? '隐藏' : '显示' }}</text>
					</view>
				</view>

				<view class="form-group">
					<text class="form-label">API Secret</text>
					<input
						class="form-input"
						:type="showSecret ? 'text' : 'password'"
						placeholder="留空则不修改"
						v-model="form.api_secret"
					/>
					<view class="toggle-visibility" @tap="showSecret = !showSecret">
						<text class="toggle-text">{{ showSecret ? '隐藏' : '显示' }}</text>
					</view>
				</view>
			</view>

			<!-- 保存按钮 -->
			<view class="submit-btn" @tap="onSubmit">
				<text class="btn-text">{{ submitting ? '保存中...' : '保存配置' }}</text>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { apiSettingsApi } from '@/api'

const form = ref({
	primary_api_url: '',
	backup_api_url: '',
	api_key: '',
	api_secret: '',
})

const showKey = ref(false)
const showSecret = ref(false)
const submitting = ref(false)
const testingPrimary = ref(false)
const testingBackup = ref(false)

onShow(async () => {
	await fetchSettings()
})

const fetchSettings = async () => {
	try {
		const res = await apiSettingsApi.get()
		form.value.primary_api_url = res.data.primary_api_url || ''
		form.value.backup_api_url = res.data.backup_api_url || ''
		form.value.api_key = res.data.api_key || ''
		form.value.api_secret = res.data.api_secret || ''
	} catch (e: any) {
		uni.showToast({ title: '获取配置失败', icon: 'none' })
	}
}

const testPrimary = async () => {
	testingPrimary.value = true
	try {
		const res = await apiSettingsApi.testPrimary()
		const body = res.data as any
		uni.showToast({
			title: body?.message || '主 API 连接正常',
			icon: 'success',
		})
	} catch (e: any) {
		uni.showToast({ title: e?.message || '主 API 连接失败', icon: 'none' })
	} finally {
		testingPrimary.value = false
	}
}

const testBackup = async () => {
	testingBackup.value = true
	try {
		const res = await apiSettingsApi.testBackup()
		const body = res.data as any
		uni.showToast({
			title: body?.message || '备用 API 连接正常',
			icon: 'success',
		})
	} catch (e: any) {
		uni.showToast({ title: e?.message || '备用 API 连接失败', icon: 'none' })
	} finally {
		testingBackup.value = false
	}
}

const onSubmit = async () => {
	if (!form.value.primary_api_url.trim()) {
		uni.showToast({ title: '主用数据源地址不能为空', icon: 'none' })
		return
	}

	submitting.value = true
	try {
		const payload: Record<string, any> = {
			primary_api_url: form.value.primary_api_url.trim(),
		}
		if (form.value.backup_api_url.trim()) {
			payload.backup_api_url = form.value.backup_api_url.trim()
		}
		if (form.value.api_key) {
			payload.api_key = form.value.api_key
		}
		if (form.value.api_secret) {
			payload.api_secret = form.value.api_secret
		}

		await apiSettingsApi.save(payload)
		uni.showToast({ title: '配置已保存', icon: 'success' })
	} catch (e: any) {
		uni.showToast({ title: e?.message || '保存失败', icon: 'none' })
	} finally {
		submitting.value = false
	}
}
</script>

<style scoped>
.api-page {
	min-height: 100vh;
	background-color: var(--page-bg);
	padding: 20rpx;
}

.api-container {
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

.card-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
}

.card-title {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.test-btn {
	padding: 8rpx 20rpx;
	border-radius: 8rpx;
	background-color: var(--border-color);
}

.test-btn:active {
	opacity: 0.7;
}

.test-text {
	font-size: 22rpx;
	color: var(--text-primary);
	font-weight: 500;
}

.form-group {
	margin-bottom: 24rpx;
	position: relative;
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

.toggle-visibility {
	position: absolute;
	right: 16rpx;
	top: 60rpx;
	padding: 4rpx 12rpx;
}

.toggle-text {
	font-size: 22rpx;
	color: var(--text-tertiary);
}

.toggle-visibility:active {
	opacity: 0.6;
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
