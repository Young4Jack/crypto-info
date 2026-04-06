<template>
	<view class="security-page">
		<view class="security-container">
			<view class="form-card">
				<view class="form-group">
					<text class="form-label">用户名</text>
					<input
						class="form-input"
						type="text"
						v-model="form.username"
						placeholder="留空则不修改"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">邮箱</text>
					<input
						class="form-input"
						type="text"
						v-model="form.email"
						placeholder="留空则不修改"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">当前密码</text>
					<input
						class="form-input"
						type="password"
						v-model="form.currentPassword"
						placeholder="修改任意字段必填"
					/>
				</view>

				<view class="divider-label">修改密码（可选）</view>

				<view class="form-group">
					<text class="form-label">新密码</text>
					<input
						class="form-input"
						type="password"
						v-model="form.newPassword"
						placeholder="留空则不修改"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">确认密码</text>
					<input
						class="form-input"
						type="password"
						v-model="form.confirmPassword"
						placeholder="请再次输入新密码"
					/>
				</view>

				<view class="submit-btn" @tap="onSubmit">
					<text class="btn-text">{{ submitting ? '保存中...' : '保存更改' }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { authApi } from '@/api'

const form = ref({
	username: '',
	email: '',
	currentPassword: '',
	newPassword: '',
	confirmPassword: '',
})

const submitting = ref(false)

onShow(async () => {
	const token = uni.getStorageSync('token')
	if (!token) {
		uni.redirectTo({ url: '/pages/login/login' })
		return
	}
	await fetchUserInfo()
})

const fetchUserInfo = async () => {
	try {
		const res = await authApi.getMe()
		form.value.username = res.data.username || ''
		form.value.email = res.data.email || ''
	} catch (e: any) {
		uni.showToast({ title: '获取用户信息失败', icon: 'none' })
	}
}

const onSubmit = async () => {
	const wantsChangeUsername = form.value.username.trim() !== ''
	const wantsChangeEmail = form.value.email.trim() !== ''
	const wantsChangePassword = form.value.newPassword !== ''

	// 没有任何修改
	if (!wantsChangeUsername && !wantsChangeEmail && !wantsChangePassword) {
		uni.showToast({ title: '没有任何修改', icon: 'none' })
		return
	}

	// 有任何修改就必须填当前密码
	if (!form.value.currentPassword.trim()) {
		uni.showToast({ title: '修改任意字段需验证当前密码', icon: 'none' })
		return
	}

	// 密码一致性校验
	if (wantsChangePassword) {
		if (form.value.newPassword !== form.value.confirmPassword) {
			uni.showToast({ title: '两次密码输入不一致', icon: 'none' })
			return
		}
		if (form.value.newPassword.length < 6) {
			uni.showToast({ title: '密码长度不能少于6位', icon: 'none' })
			return
		}
	}

	submitting.value = true
	try {
		const payload: Record<string, any> = {
			current_password: form.value.currentPassword,
		}
		if (wantsChangeUsername) {
			payload.username = form.value.username.trim()
		}
		if (wantsChangeEmail) {
			payload.email = form.value.email.trim()
		}
		if (wantsChangePassword) {
			payload.new_password = form.value.newPassword
			payload.confirm_new_password = form.value.confirmPassword
		}

		await authApi.updateAccount(payload)
		uni.showToast({ title: '修改成功', icon: 'success' })
		setTimeout(() => {
			uni.navigateBack()
		}, 1500)
	} catch (e: any) {
		uni.showToast({ title: e?.message || '修改失败', icon: 'none' })
	} finally {
		submitting.value = false
	}
}
</script>

<style scoped>
.security-page {
	min-height: 100vh;
	background-color: #f5f7fa;
	padding: 20rpx;
}

.security-container {
	width: 100%;
	max-width: 800px;
	margin: 0 auto;
}

.form-card {
	background-color: #ffffff;
	border-radius: 16rpx;
	padding: 40rpx 30rpx;
	box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.form-group {
	margin-bottom: 32rpx;
}

.form-label {
	font-size: 26rpx;
	font-weight: 500;
	color: #303133;
	margin-bottom: 12rpx;
	display: block;
}

.form-input {
	width: 100%;
	height: 80rpx;
	padding: 0 20rpx;
	border: 2rpx solid #dcdfe6;
	border-radius: 8rpx;
	font-size: 28rpx;
	color: #303133;
	box-sizing: border-box;
	background-color: #ffffff;
}

.form-input:focus {
	border-color: #409eff;
}

.divider-label {
	font-size: 22rpx;
	color: #c0c4cc;
	text-align: center;
	margin: 20rpx 0 24rpx;
	position: relative;
}

.divider-label::before,
.divider-label::after {
	content: '';
	position: absolute;
	top: 50%;
	width: 30%;
	height: 2rpx;
	background-color: #ebeef5;
}

.divider-label::before {
	left: 0;
}

.divider-label::after {
	right: 0;
}

.submit-btn {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 88rpx;
	background-color: #409eff;
	border-radius: 8rpx;
	margin-top: 20rpx;
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
