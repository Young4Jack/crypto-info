<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>{{ siteTitle }}</h1>
        <p>{{ siteDescription }}</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="loginAccount">
          <el-input
            v-model="loginForm.loginAccount"
            placeholder="请输入邮箱或用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item v-if="captchaEnabled" prop="captchaAnswer">
          <div class="captcha-container">
            <el-input
              v-model="loginForm.captchaAnswer"
              placeholder="请输入验证码"
              size="large"
              class="captcha-input"
            />
            <div class="captcha-image-container" @click="refreshCaptcha">
              <img
                v-if="captchaImage"
                :src="captchaImage"
                alt="验证码"
                class="captcha-image"
              />
              <div v-else class="captcha-placeholder">
                <el-icon><Loading /></el-icon>
              </div>
            </div>
          </div>
          <div class="captcha-tip">点击图片刷新验证码</div>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-button"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { authApi, systemSettingsApi } from '../api'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref<FormInstance>()
const loading = ref(false)
const captchaEnabled = ref(false)
const captchaImage = ref('')
const captchaId = ref('')
const siteTitle = ref('Crypto-info')
const siteDescription = ref('数字货币价格监控和预警系统')

const loginForm = reactive({
  loginAccount: '',
  password: '',
  captchaAnswer: '',
  captchaId: ''
})

const loginRules = computed(() => {
  const rules: FormRules = {
    loginAccount: [
      { required: true, message: '请输入邮箱或用户名', trigger: 'blur' }
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
    ]
  }
  
  // 只有在验证码启用时才添加验证码验证规则
  if (captchaEnabled.value) {
    rules.captchaAnswer = [
      { required: true, message: '请输入验证码', trigger: 'blur' }
    ]
  }
  
  return rules
})

const getCaptcha = async () => {
  try {
    const response = await authApi.getCaptcha()
    captchaEnabled.value = response.data.enabled
    if (response.data.enabled) {
      captchaImage.value = response.data.captcha_image
      captchaId.value = response.data.captcha_id
      loginForm.captchaId = response.data.captcha_id
    }
  } catch (error) {
    console.error('获取验证码失败:', error)
  }
}

const refreshCaptcha = async () => {
  if (!captchaEnabled.value) return
  
  try {
    const response = await authApi.getCaptcha()
    if (response.data.enabled) {
      captchaImage.value = response.data.captcha_image
      captchaId.value = response.data.captcha_id
      loginForm.captchaId = response.data.captcha_id
      loginForm.captchaAnswer = ''
    }
  } catch (error) {
    console.error('刷新验证码失败:', error)
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const success = await authStore.login(
          loginForm.loginAccount, 
          loginForm.password,
          captchaEnabled.value ? loginForm.captchaAnswer : undefined,
          captchaEnabled.value ? loginForm.captchaId : undefined
        )
        if (success) {
          ElMessage.success('登录成功')
          router.push('/dashboard')
        } else {
          ElMessage.error('登录失败，请检查邮箱/用户名和密码')
          if (captchaEnabled.value) {
            refreshCaptcha()
          }
        }
      } catch (error: any) {
        ElMessage.error(error.message || '登录失败，请稍后重试')
        if (captchaEnabled.value) {
          refreshCaptcha()
        }
      } finally {
        loading.value = false
      }
    }
  })
}

onMounted(() => {
  getCaptcha()
  loadPublicSettings()
})

const loadPublicSettings = async () => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      siteTitle.value = response.data.site_title || 'Crypto-info'
      siteDescription.value = response.data.site_description || '数字货币价格监控和预警系统'
    }
  } catch (error) {
    console.error('加载公开设置失败:', error)
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  padding: var(--spacing-md);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: var(--spacing-xxl);
  background: var(--bg-color);
  border-radius: var(--border-radius-large);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.login-header h1 {
  font-size: var(--font-size-title);
  color: var(--text-primary);
  margin-bottom: var(--spacing-sm);
  font-weight: 700;
}

.login-header p {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
}

.login-form {
  width: 100%;
}

.captcha-container {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.captcha-input {
  flex: 1;
}

.captcha-image-container {
  width: 120px;
  height: 40px;
  cursor: pointer;
  border: 1px solid var(--border-color);
  border-radius: var(--border-radius-base);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
  transition: all var(--transition-duration) var(--transition-timing);
}

.captcha-image-container:hover {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.1);
}

.captcha-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.captcha-tip {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  margin-top: var(--spacing-xs);
  text-align: center;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: var(--font-size-lg);
  font-weight: 600;
  border-radius: var(--border-radius-base);
  margin-top: var(--spacing-lg);
  transition: all var(--transition-duration) var(--transition-timing);
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-light);
}

:deep(.el-input__wrapper) {
  border-radius: var(--border-radius-base);
  box-shadow: 0 0 0 1px var(--border-color);
  transition: all var(--transition-duration) var(--transition-timing);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-primary);
  font-size: var(--font-size-sm);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .login-container {
    padding: var(--spacing-sm);
  }
  
  .login-card {
    padding: var(--spacing-lg);
    margin: var(--spacing-sm);
    max-width: none;
  }
  
  .login-header h1 {
    font-size: var(--font-size-xl);
  }
  
  .login-header p {
    font-size: var(--font-size-sm);
  }
  
  .captcha-container {
    flex-direction: column;
    gap: var(--spacing-xs);
  }
  
  .captcha-image-container {
    width: 100%;
    height: 50px;
  }
  
  .login-button {
    height: 44px;
    font-size: var(--font-size-base);
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: var(--spacing-md);
    border-radius: var(--border-radius-base);
  }
  
  .login-header {
    margin-bottom: var(--spacing-lg);
  }
  
  .login-header h1 {
    font-size: var(--font-size-lg);
  }
  
  .login-button {
    margin-top: var(--spacing-md);
  }
}
</style>
