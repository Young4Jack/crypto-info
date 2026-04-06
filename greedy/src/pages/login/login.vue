<template>
	<view class="login-page">
		<view class="login-container">
			<view class="login-header">
				<text class="login-title">Crypto-info</text>
				<text class="login-subtitle">登录你的账户</text>
			</view>

			<view class="login-form">
				<view class="form-group">
					<text class="form-label">账号</text>
					<input
						class="form-input"
						type="text"
						placeholder="请输入邮箱或用户名"
						v-model="form.email"
						:disabled="loading"
					/>
				</view>

				<view class="form-group">
					<text class="form-label">密码</text>
					<input
						class="form-input"
						type="password"
						placeholder="请输入密码"
						v-model="form.password"
						:disabled="loading"
					/>
				</view>

				<view v-if="captchaEnabled" class="form-group captcha-group">
					<text class="form-label">验证码</text>
					<view class="captcha-row">
						<input
							class="form-input captcha-input"
							type="number"
							placeholder="请输入验证码"
							v-model="form.captchaAnswer"
							:disabled="loading"
						/>
						<image
							class="captcha-image"
							:src="captchaImage"
							mode="aspectFit"
							@click="refreshCaptcha"
						/>
					</view>
				</view>

				<button
					class="login-btn"
					:loading="loading"
					:disabled="loading"
					@tap="handleLogin"
				>
					{{ loading ? '登录中...' : '登 录' }}
				</button>
			</view>
		</view>
	</view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { authApi, type LoginPayload } from '@/api'

// 表单数据
const form = ref({
	email: '',
	password: '',
	captchaAnswer: '',
})

// 验证码状态
const captchaEnabled = ref(false)
const captchaId = ref('')
const captchaImage = ref('')

// 加载状态
const loading = ref(false)

// 页面加载时获取验证码配置
onLoad(async () => {
	await fetchCaptcha()
})

// 请求验证码图片
const fetchCaptcha = async () => {
	try {
		const res = await authApi.getCaptcha()
		const data = res.data
		captchaEnabled.value = data.enabled
		if (data.enabled) {
			captchaId.value = data.captcha_id
			// Base64 图片流可能不带 data URI 前缀，需补全
			captchaImage.value = data.captcha_image.startsWith('data:')
				? data.captcha_image
				: `data:image/png;base64,${data.captcha_image}`
		}
	} catch (e: any) {
		console.error('获取验证码失败', e)
	}
}

// 点击图片刷新验证码
const refreshCaptcha = async () => {
	await fetchCaptcha()
}

// 登录按钮点击事件
const handleLogin = async () => {
	// 基础校验
	if (!form.value.email.trim()) {
		uni.showToast({ title: '请输入账号', icon: 'none' })
		return
	}
	if (!form.value.password) {
		uni.showToast({ title: '请输入密码', icon: 'none' })
		return
	}
	if (captchaEnabled.value && !form.value.captchaAnswer.trim()) {
		uni.showToast({ title: '请输入验证码', icon: 'none' })
		return
	}

	loading.value = true
	try {
		const payload: LoginPayload = {
			email: form.value.email.trim(),
			password: form.value.password,
			login_type: 'email',
		}
		// 验证码启用时附加参数
		if (captchaEnabled.value) {
			payload.captchaId = captchaId.value
			payload.captchaAnswer = parseInt(form.value.captchaAnswer, 10)
		}

		const res = await authApi.login(payload)
		// 严格按后端 API 文档：响应体字段名为 access_token
		const token = res.data?.access_token

		// 防御性校验：确保 token 是有效非空字符串
		if (!token || typeof token !== 'string' || !token.trim()) {
			uni.showToast({ title: '登录异常：未获取到有效 Token', icon: 'none' })
			return
		}

		// 保存 Token 到本地缓存
		uni.setStorageSync('token', token.trim())
		console.log('[Login] Token 已保存:', token.substring(0, 10) + '...')

		uni.showToast({ title: '登录成功', icon: 'success' })

		// 跳转至个人中心（TabBar 页面需用 switchTab）
		setTimeout(() => {
			uni.switchTab({
				url: '/pages/mine/mine',
				fail: () => {
					uni.reLaunch({ url: '/pages/market/market' })
				},
			})
		}, 500)
	} catch (e: any) {
		// 登录失败，刷新验证码并重试
		if (captchaEnabled.value) {
			await refreshCaptcha()
			form.value.captchaAnswer = ''
		}
	} finally {
		loading.value = false
	}
}
</script>

<style scoped>
/* 页面容器：全屏居中 */
.login-page {
	display: flex;
	justify-content: center;
	align-items: center;
	min-height: 100vh;
	background-color: #f5f7fa;
	padding: 40rpx;
}

/* 登录卡片 */
.login-container {
	width: 100%;
	max-width: 800rpx;
	background-color: #ffffff;
	border-radius: 24rpx;
	padding: 60rpx 40rpx;
	box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);
}

/* 头部标题 */
.login-header {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 60rpx;
}

.login-title {
	font-size: 48rpx;
	font-weight: bold;
	color: #1a1a2e;
	margin-bottom: 12rpx;
}

.login-subtitle {
	font-size: 28rpx;
	color: #909399;
}

/* 表单区域 */
.login-form {
	display: flex;
	flex-direction: column;
	gap: 32rpx;
}

.form-group {
	display: flex;
	flex-direction: column;
	gap: 12rpx;
}

.form-label {
	font-size: 28rpx;
	font-weight: 500;
	color: #303133;
}

.form-input {
	width: 100%;
	height: 88rpx;
	padding: 0 24rpx;
	border: 2rpx solid #dcdfe6;
	border-radius: 12rpx;
	font-size: 28rpx;
	color: #303133;
	background-color: #ffffff;
	box-sizing: border-box;
}

.form-input:focus {
	border-color: #409eff;
}

/* 验证码行：输入框 + 图片 */
.captcha-row {
	display: flex;
	align-items: center;
	gap: 20rpx;
}

.captcha-input {
	flex: 1;
}

.captcha-image {
	width: 200rpx;
	height: 88rpx;
	border-radius: 8rpx;
	border: 2rpx solid #ebeef5;
	flex-shrink: 0;
}

/* 登录按钮 */
.login-btn {
	width: 100%;
	height: 88rpx;
	line-height: 88rpx;
	background-color: #409eff;
	color: #ffffff;
	font-size: 32rpx;
	font-weight: 600;
	border-radius: 12rpx;
	border: none;
	margin-top: 16rpx;
}

.login-btn:active {
	opacity: 0.85;
}

.login-btn[disabled] {
	opacity: 0.6;
}

/* PC 端限制最大宽度 400px */
@media (min-width: 768px) {
	.login-container {
		max-width: 400px;
	}
}
</style>
