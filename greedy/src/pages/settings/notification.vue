<template>
	<view class="notification-page">
		<view class="notification-container">
			<!-- 加载/错误状态 -->
			<view v-if="loading && channels.length === 0" class="loading-state">
				<text class="loading-text">加载中...</text>
			</view>

			<view v-else-if="error" class="error-state">
				<text class="error-text">{{ error }}</text>
				<view class="retry-btn" @tap="fetchChannels">
					<text>重试</text>
				</view>
			</view>

			<!-- 渠道卡片列表 -->
			<scroll-view v-else scroll-y class="channels-scroll">
				<view class="channels-list">
					<view
						v-for="ch in channels"
						:key="ch.name"
						class="channel-card"
					>
						<view class="card-header">
							<text class="channel-name">{{ ch.name }}</text>
							<view v-if="ch.is_default" class="badge-default">
								<text class="badge-text">默认</text>
							</view>
						</view>
						<view class="card-body">
							<text class="channel-url">{{ ch.api_url }}</text>
							<text class="channel-groups">频道: {{ (ch.groups || []).join(', ') || '无' }}</text>
						</view>
						<view class="card-actions">
							<view class="action-btn action-test" @tap="testChannel(ch)">
								<text class="action-text">测试</text>
							</view>
							<view class="action-btn action-edit" @tap="openEdit(ch)">
								<text class="action-text">编辑</text>
							</view>
							<view class="action-btn action-delete" @tap="confirmDelete(ch)">
								<text class="action-text">删除</text>
							</view>
						</view>
					</view>

					<view v-if="channels.length === 0" class="empty-state">
						<text class="empty-text">暂无通知渠道</text>
						<text class="empty-hint">点击下方按钮添加</text>
					</view>
				</view>
			</scroll-view>

			<!-- 添加/编辑表单 -->
			<view v-if="showForm" class="form-overlay">
				<view class="form-card">
					<view class="form-header">
						<text class="form-title">{{ editingName ? '编辑渠道' : '添加渠道' }}</text>
						<text class="form-close" @tap="closeForm">×</text>
					</view>

					<view class="form-group">
						<text class="form-label">渠道名称</text>
						<input
							class="form-input"
							type="text"
							placeholder="如 自建Webhook"
							v-model="form.name"
							:disabled="!!editingName"
						/>
					</view>

					<view class="form-group">
						<text class="form-label">推送地址</text>
						<input
							class="form-input"
							type="text"
							placeholder="https://..."
							v-model="form.api_url"
						/>
					</view>

					<view class="form-group">
						<text class="form-label">认证令牌（可选）</text>
						<input
							class="form-input"
							type="text"
							placeholder="留空则不设置"
							v-model="form.auth_token"
						/>
					</view>

					<view class="form-group">
						<text class="form-label">默认频道</text>
						<input
							class="form-input"
							type="text"
							placeholder="如 default"
							v-model="form.default_group"
						/>
					</view>

					<view class="form-group">
						<text class="form-label">可用频道（逗号分隔）</text>
						<input
							class="form-input"
							type="text"
							placeholder="如 yes,urgent,test"
							v-model="form.groupsInput"
						/>
					</view>

					<view class="form-group form-row">
						<text class="form-label">设为默认渠道</text>
						<switch
							:checked="form.is_default"
							color="#409EFF"
							@change="onDefaultChange"
						/>
					</view>

					<view class="form-submit" @tap="submitForm">
						<text class="btn-text">{{ submitting ? '提交中...' : '确认保存' }}</text>
					</view>
				</view>
			</view>

			<!-- 底部添加按钮 -->
			<view class="add-fab" @tap="openAdd">
				<text class="fab-icon">＋</text>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { notificationChannelsApi, type NotificationChannel } from '@/api'

const channels = ref<NotificationChannel[]>([])
const loading = ref(false)
const error = ref('')
const showForm = ref(false)
const editingName = ref('')
const submitting = ref(false)

const form = ref({
	name: '',
	api_url: '',
	auth_token: '',
	default_group: '',
	groupsInput: '',
	is_default: false,
})

onShow(() => {
	fetchChannels()
})

const fetchChannels = async () => {
	loading.value = true
	error.value = ''
	try {
		const res = await notificationChannelsApi.getList()
		channels.value = res.data || []
	} catch (e: any) {
		error.value = e?.message || '加载失败'
	} finally {
		loading.value = false
	}
}

const resetForm = () => {
	form.value = {
		name: '',
		api_url: '',
		auth_token: '',
		default_group: '',
		groupsInput: '',
		is_default: false,
	}
	editingName.value = ''
}

const openAdd = () => {
	resetForm()
	showForm.value = true
}

const openEdit = (ch: NotificationChannel) => {
	editingName.value = ch.name
	form.value.name = ch.name
	form.value.api_url = ch.api_url
	form.value.auth_token = ch.auth_token || ''
	form.value.default_group = ch.default_group || ''
	form.value.groupsInput = (ch.groups || []).join(', ')
	form.value.is_default = ch.is_default
	showForm.value = true
}

const closeForm = () => {
	showForm.value = false
	resetForm()
}

const onDefaultChange = (event: any) => {
	form.value.is_default = event.detail?.value ?? event.value ?? false
}

const submitForm = async () => {
	if (!form.value.name.trim()) {
		uni.showToast({ title: '渠道名称不能为空', icon: 'none' })
		return
	}
	if (!form.value.api_url.trim()) {
		uni.showToast({ title: '推送地址不能为空', icon: 'none' })
		return
	}

	const groups = form.value.groupsInput
		.split(',')
		.map((g: string) => g.trim())
		.filter((g: string) => g)

	const payload: Record<string, any> = {
		name: form.value.name.trim(),
		api_url: form.value.api_url.trim(),
		auth_token: form.value.auth_token.trim() || undefined,
		is_default: form.value.is_default,
		default_group: form.value.default_group.trim() || undefined,
		groups: groups.length > 0 ? groups : undefined,
	}

	submitting.value = true
	try {
		if (editingName.value) {
			await notificationChannelsApi.update(editingName.value, payload)
			uni.showToast({ title: '更新成功', icon: 'success' })
		} else {
			await notificationChannelsApi.create(payload)
			uni.showToast({ title: '添加成功', icon: 'success' })
		}
		closeForm()
		await fetchChannels()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
	} finally {
		submitting.value = false
	}
}

const testChannel = async (ch: NotificationChannel) => {
	try {
		const res = await notificationChannelsApi.test(ch.name)
		const body = res.data as any
		uni.showToast({
			title: body?.message || '测试消息已发送',
			icon: 'success',
		})
	} catch (e: any) {
		uni.showToast({ title: e?.message || '测试发送失败', icon: 'none' })
	}
}

const confirmDelete = (ch: NotificationChannel) => {
	uni.showModal({
		title: '确认删除',
		content: `确定删除通知渠道「${ch.name}」吗？`,
		success: async (res) => {
			if (res.confirm) {
				await deleteChannel(ch)
			}
		},
	})
}

const deleteChannel = async (ch: NotificationChannel) => {
	try {
		await notificationChannelsApi.delete(ch.name)
		uni.showToast({ title: '已删除', icon: 'success' })
		await fetchChannels()
	} catch (e: any) {
		uni.showToast({ title: e?.message || '删除失败', icon: 'none' })
	}
}
</script>

<style scoped>
.notification-page {
	min-height: 100vh;
	background-color: var(--page-bg);
	padding: 20rpx;
}

.notification-container {
	width: 100%;
	max-width: 800px;
	margin: 0 auto;
	position: relative;
}

.loading-state,
.error-state,
.empty-state {
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 120rpx 0;
	gap: 20rpx;
}

.loading-text,
.error-text {
	font-size: 28rpx;
	color: var(--text-tertiary);
}

.error-text {
	color: #f56c6c;
}

.retry-btn {
	padding: 16rpx 40rpx;
	background-color: #409eff;
	border-radius: 8rpx;
}

.retry-btn text {
	color: #ffffff;
	font-size: 26rpx;
}

.empty-text {
    font-size: 30rpx;
    color: var(--text-tertiary);
}

.empty-hint {
	font-size: 24rpx;
	color: var(--text-tertiary);
}

.channels-scroll {
	height: calc(100vh - 120rpx);
}

.channels-list {
	display: flex;
	flex-direction: column;
	gap: 16rpx;
	padding-bottom: 120rpx;
}

.channel-card {
	background-color: var(--card-bg);
	border-radius: 16rpx;
	padding: 28rpx;
	box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04);
}

.card-header {
	display: flex;
	align-items: center;
	gap: 12rpx;
	margin-bottom: 12rpx;
}

.channel-name {
	font-size: 30rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.badge-default {
	background-color: #ecf5ff;
	border-radius: 6rpx;
	padding: 2rpx 10rpx;
}

.badge-text {
	font-size: 20rpx;
	color: #409eff;
}

.card-body {
	display: flex;
	flex-direction: column;
	gap: 8rpx;
	margin-bottom: 20rpx;
}

.channel-url {
    font-size: 22rpx;
    color: var(--text-secondary);
    word-break: break-all;
}

.channel-groups {
    font-size: 22rpx;
    color: var(--text-tertiary);
}

.card-actions {
	display: flex;
	gap: 12rpx;
}

.action-btn {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 12rpx 0;
	border-radius: 8rpx;
}

.action-btn:active {
	opacity: 0.7;
}

.action-test {
	background-color: #f0f9eb;
}

.action-test .action-text {
	color: #67c23a;
}

.action-edit {
	background-color: #ecf5ff;
}

.action-edit .action-text {
	color: #409eff;
}

.action-delete {
	background-color: #fef0f0;
}

.action-delete .action-text {
	color: #f56c6c;
}

.action-text {
	font-size: 24rpx;
	font-weight: 500;
}

/* 表单覆盖层 */
.form-overlay {
	position: fixed;
	top: 0;
	left: 0;
	right: 0;
	bottom: 0;
	background-color: rgba(0, 0, 0, 0.5);
	z-index: 999;
	display: flex;
	align-items: center;
	justify-content: center;
}

.form-card {
	width: 90%;
	max-width: 600rpx;
	background-color: var(--card-bg);
	border-radius: 20rpx;
	padding: 30rpx;
	max-height: 85vh;
	overflow-y: auto;
}

.form-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 24rpx;
}

.form-title {
	font-size: 32rpx;
	font-weight: 600;
	color: var(--text-primary);
}

.form-close {
	font-size: 48rpx;
	color: var(--text-tertiary);
	line-height: 1;
}

.form-group {
	margin-bottom: 24rpx;
}

.form-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
}

.form-label {
	font-size: 26rpx;
	font-weight: 500;
	color: var(--text-primary);
	margin-bottom: 12rpx;
	display: block;
}

.form-row .form-label {
	margin-bottom: 0;
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

.form-input:disabled {
	background-color: var(--page-bg);
	color: var(--text-tertiary);
}

.form-submit {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 88rpx;
	background-color: #409eff;
	border-radius: 8rpx;
	margin-top: 12rpx;
}

.form-submit:active {
	opacity: 0.85;
}

.btn-text {
	font-size: 30rpx;
	color: #ffffff;
	font-weight: 500;
}

/* 底部浮动添加按钮 */
.add-fab {
	position: fixed;
	bottom: 60rpx;
	right: 40rpx;
	width: 100rpx;
	height: 100rpx;
	border-radius: 50%;
	background-color: #409eff;
	box-shadow: 0 6rpx 20rpx rgba(64, 158, 255, 0.4);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 100;
}

.add-fab:active {
	transform: scale(0.92);
}

.fab-icon {
	font-size: 48rpx;
	color: #ffffff;
	font-weight: 300;
	line-height: 1;
}
</style>
