<template>
  <div class="login-wrapper">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-box">
          <span class="logo-text">{{ siteTitle ? siteTitle.charAt(0).toUpperCase() : 'C' }}</span>
        </div>
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
            clearable
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
        
        <el-form-item class="submit-item">
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-button"
          >
            {{ loading ? '身份验证中...' : '安全登录' }}
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
    // 静默处理，避免未配置时报错打断渲染
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
    ElMessage.error('刷新验证码失败')
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
          ElMessage.error('登录失败，请检查凭证')
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

const loadPublicSettings = async () => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      siteTitle.value = response.data.site_title || 'Crypto-info'
      siteDescription.value = response.data.site_description || '数字货币价格监控和预警系统'
    }
  } catch (error) {
    // 采用默认设置
  }
}

onMounted(() => {
  getCaptcha()
  loadPublicSettings()
})
</script>

<style scoped>
/* =========================================
   全局架构层：强制与内部面板背景色对齐
   ========================================= */
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa; /* 统一的后台背景色 */
  padding: 20px;
  box-sizing: border-box;
}

/* =========================================
   核心组件：登录卡片
   ========================================= */
.login-card {
  width: 100%;
  max-width: 420px;
  padding: 40px 35px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
  border: 1px solid #f0f2f5;
  box-sizing: border-box;
}

.login-header {
  text-align: center;
  margin-bottom: 35px;
}

.logo-box {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #409eff 0%, #3a8ee6 100%);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.logo-text {
  color: white;
  font-size: 26px;
  font-weight: bold;
  font-family: 'Monaco', monospace;
}

.login-header h1 {
  font-size: 24px;
  color: #1f2f3d;
  margin: 0 0 8px 0;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.login-header p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.login-form {
  width: 100%;
}

/* 表单元素深度定制 */
:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6;
  padding: 0 15px;
  transition: all 0.2s cubic-bezier(0.645, 0.045, 0.355, 1);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff;
}

:deep(.el-input__inner) {
  height: 46px;
  line-height: 46px;
}

/* 验证码模块 */
.captcha-container {
  display: flex;
  gap: 12px;
  align-items: center;
  width: 100%;
}

.captcha-input {
  flex: 1;
}

.captcha-image-container {
  width: 130px;
  height: 48px;
  cursor: pointer;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  transition: border-color 0.2s;
}

.captcha-image-container:hover {
  border-color: #409eff;
}

.captcha-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha-placeholder {
  color: #909399;
}

.captcha-tip {
  font-size: 12px;
  color: #a8abb2;
  margin-top: 6px;
  line-height: 1.2;
}

/* 提交按钮 */
.submit-item {
  margin-top: 10px;
  margin-bottom: 0;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  letter-spacing: 1px;
}

/* =========================================
   移动端视图 (<= 768px)
   ========================================= */
@media (max-width: 768px) {
  .login-wrapper {
    padding: 15px;
    align-items: flex-start;
    padding-top: 10vh;
  }
  
  .login-card {
    padding: 30px 20px;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
  }
  
  .login-header {
    margin-bottom: 25px;
  }
  
  .logo-box {
    width: 46px;
    height: 46px;
  }
  
  .logo-text {
    font-size: 22px;
  }
  
  .login-header h1 {
    font-size: 22px;
  }
  
  .login-header p {
    font-size: 13px;
  }
  
  :deep(.el-input__inner) {
    height: 42px;
    line-height: 42px;
  }
  
  .login-button {
    height: 44px;
    font-size: 15px;
  }
  
  .captcha-image-container {
    width: 110px;
    height: 44px;
  }
}
</style>