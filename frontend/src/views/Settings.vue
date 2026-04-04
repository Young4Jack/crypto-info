<template>
  <div class="page-container" :class="{ 'dark-mode': isDarkMode }">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>系统设置</h1>
          <p>管理您的账户、API密钥及系统偏好</p>
        </div>
        <div class="header-right">
          <el-button @click="toggleDarkMode" class="dark-mode-btn" :type="isDarkMode ? 'warning' : 'default'" plain>
            {{ isDarkMode ? '☀️' : '🌙' }}
          </el-button>
          <span class="welcome-text">欢迎，{{ authStore.user?.username || '用户' }}</span>
          <el-button-group class="action-buttons">
            <el-button @click="goToDashboard">返回面板</el-button>
            <el-button @click="goToHome">返回主页</el-button>
            <el-button type="danger" @click="handleLogout">退出登录</el-button>
          </el-button-group>
        </div>
      </div>
    </el-header>
      
    <el-main class="page-main">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="24" :md="16">
          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header"><span>🔔 通知推送设置</span></div>
            </template>
            <el-form ref="settingFormRef" :model="settingForm" :rules="settingRules" label-position="top">
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item label="推送 API 地址" prop="api_url">
                    <el-input v-model="settingForm.api_url" placeholder="请输入推送 API 地址" clearable />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item label="Authorization Token" prop="auth_token">
                    <el-input v-model="settingForm.auth_token" placeholder="请输入 Token" type="password" show-password clearable />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="推送渠道" prop="channel">
                <el-input v-model="settingForm.channel" placeholder="请输入推送渠道（可选）" clearable />
              </el-form-item>
              <el-form-item class="form-actions">
                <el-button type="primary" :loading="saveLoading" @click="handleSaveSetting">
                  {{ isEditing ? '更新设置' : '保存设置' }}
                </el-button>
                <el-button v-if="isEditing" type="warning" plain :loading="testLoading" @click="handleTestNotification">测试连接</el-button>
                <el-button v-if="isEditing" type="danger" plain :loading="deleteLoading" @click="handleDeleteSetting">删除设置</el-button>
              </el-form-item>
            </el-form>
          </el-card>
          
          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header"><span>🔌 价格获取 API 设置</span></div>
            </template>
            <el-form ref="apiSettingFormRef" :model="apiSettingForm" :rules="apiSettingRules" label-position="top">
              <el-form-item label="主 API 地址" prop="primary_api_url">
                <el-input v-model="apiSettingForm.primary_api_url" placeholder="如：https://api.binance.com/api/v3/ticker/price" clearable />
              </el-form-item>
              <el-form-item label="备用 API 地址" prop="backup_api_url">
                <el-input v-model="apiSettingForm.backup_api_url" placeholder="请输入备用 API 地址（可选）" clearable />
              </el-form-item>
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item label="API Key (可选)" prop="api_key">
                    <el-input v-model="apiSettingForm.api_key" placeholder="请输入 API Key" type="password" show-password clearable />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item label="API Secret (可选)" prop="api_secret">
                    <el-input v-model="apiSettingForm.api_secret" placeholder="请输入 API Secret" type="password" show-password clearable />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item class="form-actions">
                <el-button type="primary" :loading="apiSaveLoading" @click="handleSaveApiSetting">
                  {{ isApiEditing ? '更新 API' : '保存 API' }}
                </el-button>
                <el-button v-if="isApiEditing" type="warning" plain :loading="testPrimaryLoading" @click="handleTestPrimaryApi">测试主 API</el-button>
                <el-button v-if="isApiEditing && apiSettingForm.backup_api_url" type="warning" plain :loading="testBackupLoading" @click="handleTestBackupApi">测试备用</el-button>
                <el-button v-if="isApiEditing" type="danger" plain :loading="apiDeleteLoading" @click="handleDeleteApiSetting">删除 API</el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header"><span>⚙️ 系统级偏好</span></div>
            </template>
            <el-form ref="systemFormRef" :model="systemForm" :rules="systemRules" label-position="top">
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item label="网站标题" prop="site_title">
                    <el-input v-model="systemForm.site_title" placeholder="请输入网站标题" maxlength="50" />
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item label="价格刷新间隔 (秒)" prop="refresh_interval">
                    <el-input-number v-model="systemForm.refresh_interval" :min="1" :max="3600" style="width: 100%;" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="网站描述" prop="site_description">
                <el-input v-model="systemForm.site_description" type="textarea" :rows="2" placeholder="请输入网站描述" />
              </el-form-item>
              
              <el-row :gutter="20">
                <el-col :xs="24" :sm="12">
                  <el-form-item label="系统时区">
                    <el-select v-model="systemForm.timezone" style="width: 100%;">
                      <el-option label="亚洲/上海 (UTC+8)" value="Asia/Shanghai" />
                      <el-option label="亚洲/东京 (UTC+9)" value="Asia/Tokyo" />
                      <el-option label="UTC (UTC+0)" value="UTC" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :xs="24" :sm="12">
                  <el-form-item label="日志级别">
                    <el-select v-model="systemForm.log_level" style="width: 100%;">
                      <el-option label="DEBUG" value="DEBUG" />
                      <el-option label="INFO" value="INFO" />
                      <el-option label="WARNING" value="WARNING" />
                      <el-option label="ERROR" value="ERROR" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              
              <div class="switch-group">
                <el-form-item label="登录验证码" class="inline-switch">
                  <el-switch v-model="systemForm.enable_captcha" active-text="启用" inactive-text="禁用" />
                </el-form-item>
                <el-form-item label="记录系统日志" class="inline-switch">
                  <el-switch v-model="systemForm.enable_logging" active-text="启用" inactive-text="禁用" />
                </el-form-item>
                <el-form-item label="默认夜间模式" class="inline-switch">
                  <el-switch v-model="systemForm.default_dark_mode" active-text="启用" inactive-text="禁用" />
                </el-form-item>
              </div>

              <el-form-item label="API 共享密钥">
                <el-input v-model="systemForm.api_shared_secret" type="password" show-password clearable placeholder="设置密钥后，外部应用可通过 X-Shared-Secret 请求头修改系统设置" />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" :loading="systemSaveLoading" @click="handleSaveSystem" style="width: 100%; max-width: 200px;">
                  保存系统偏好
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>

        <el-col :xs="24" :sm="24" :md="8">
          <el-card class="content-card" shadow="never">
            <template #header>
              <div class="card-header"><span>👤 账户安全</span></div>
            </template>
            <el-form ref="accountFormRef" :model="accountForm" :rules="accountRules" label-position="top">
              <el-form-item label="新用户名 (留空不改)" prop="username">
                <el-input v-model="accountForm.username" placeholder="输入新用户名" clearable />
              </el-form-item>
              <el-form-item label="新邮箱 (留空不改)" prop="email">
                <el-input v-model="accountForm.email" placeholder="输入新邮箱" clearable />
              </el-form-item>
              <el-form-item label="当前密码 (验证身份)" prop="current_password">
                <el-input v-model="accountForm.current_password" type="password" show-password clearable />
              </el-form-item>
              <el-form-item label="新密码" prop="new_password">
                <el-input v-model="accountForm.new_password" type="password" show-password clearable />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirm_password">
                <el-input v-model="accountForm.confirm_password" type="password" show-password clearable />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="accountSaveLoading" @click="handleSaveAccount" style="width: 100%;">
                  更新安全信息
                </el-button>
              </el-form-item>
            </el-form>
          </el-card>
          
          <el-card class="content-card info-card" shadow="never">
            <template #header>
              <div class="card-header"><span>💡 系统说明</span></div>
            </template>
            <div class="info-content">
              <p><strong>通知推送：</strong>配置预警触发时的通知渠道，支持 Webhook、邮件等。</p>
              <p><strong>API 设置：</strong>系统会自动向配置的端点请求价格。若主节点超时，自动降级至备用节点。</p>
              <p><strong>账户变更：</strong>修改密码后需重新登录，请牢记您的新凭证。</p>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { settingsApi, apiSettingsApi, systemSettingsApi, authApi } from '../api'
import { useDarkMode } from '../composables/useDarkMode'

const router = useRouter()
const authStore = useAuthStore()
const { isDarkMode, toggleDarkMode } = useDarkMode()

const settingFormRef = ref<FormInstance>()
const apiSettingFormRef = ref<FormInstance>()
const systemFormRef = ref<FormInstance>()
const accountFormRef = ref<FormInstance>()

const saveLoading = ref(false)
const deleteLoading = ref(false)
const isEditing = ref(false)
const testLoading = ref(false)
const apiSaveLoading = ref(false)
const apiDeleteLoading = ref(false)
const isApiEditing = ref(false)
const testPrimaryLoading = ref(false)
const testBackupLoading = ref(false)
const systemSaveLoading = ref(false)
const accountSaveLoading = ref(false)

const settingForm = reactive({ api_url: '', auth_token: '', channel: 'email' })
const apiSettingForm = reactive({ primary_api_url: '', backup_api_url: '', api_key: '', api_secret: '' })
const systemForm = reactive({ refresh_interval: 5, enable_captcha: false, site_title: 'Crypto-info', site_description: '数字货币价格监控和预警系统', log_level: 'INFO', enable_logging: true, default_dark_mode: false, api_shared_secret: '', timezone: 'Asia/Shanghai' })
const accountForm = reactive({ username: '', email: '', current_password: '', new_password: '', confirm_password: '' })

const settingRules: FormRules = {
  api_url: [
    { required: true, message: '请输入推送 API 地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的 URL', trigger: 'blur' }
  ],
  auth_token: [{ required: true, message: '请输入 Token', trigger: 'blur' }]
}

const apiSettingRules: FormRules = {
  primary_api_url: [{ required: true, message: '请输入主 API 地址', trigger: 'blur' }]
}

const systemRules: FormRules = {
  refresh_interval: [
    { required: true, message: '请输入刷新间隔', trigger: 'blur' },
    { type: 'number', min: 1, max: 3600, message: '间隔 1-3600 秒', trigger: 'blur' }
  ]
}

const accountRules: FormRules = {
  current_password: [{ required: true, message: '验证身份需要当前密码', trigger: 'blur' }]
}

const loadSetting = async () => {
  try {
    const response = await settingsApi.getNotificationSetting()
    if (response.data) {
      isEditing.value = true
      settingForm.api_url = response.data.api_url || ''
      settingForm.auth_token = response.data.auth_token || ''
      settingForm.channel = response.data.channel || 'email'
    }
  } catch (error) {}
}

const handleSaveSetting = async () => {
  if (!settingFormRef.value) return
  await settingFormRef.value.validate(async (valid) => {
    if (valid) {
      saveLoading.value = true
      try {
        if (isEditing.value) {
          await settingsApi.updateNotificationSetting(settingForm)
          ElMessage.success('设置更新成功')
        } else {
          await settingsApi.createNotificationSetting(settingForm)
          ElMessage.success('设置保存成功')
          isEditing.value = true
        }
      } catch (error) {
        ElMessage.error('保存设置失败')
      } finally { saveLoading.value = false }
    }
  })
}

const handleDeleteSetting = async () => {
  try {
    await ElMessageBox.confirm('确定删除吗？将无法接收预警通知。', '确认', { type: 'warning' })
    deleteLoading.value = true
    await settingsApi.deleteNotificationSetting()
    isEditing.value = false
    settingForm.api_url = ''; settingForm.auth_token = ''; settingForm.channel = 'email'
    ElMessage.success('设置已删除')
  } catch (error) {} finally { deleteLoading.value = false }
}

const handleTestNotification = async () => {
  testLoading.value = true
  try {
    const response = await settingsApi.testNotificationSetting()
    if (response.data.success) ElMessage.success('通知API连接成功')
    else ElMessage.error(`失败: ${response.data.message}`)
  } catch (error) { ElMessage.error('测试失败') } finally { testLoading.value = false }
}

const loadApiSetting = async () => {
  try {
    const response = await apiSettingsApi.getApiSetting()
    if (response.data) {
      isApiEditing.value = true
      apiSettingForm.primary_api_url = response.data.primary_api_url || ''
      apiSettingForm.backup_api_url = response.data.backup_api_url || ''
      apiSettingForm.api_key = response.data.api_key || ''
      apiSettingForm.api_secret = response.data.api_secret || ''
    }
  } catch (error) {}
}

const handleSaveApiSetting = async () => {
  if (!apiSettingFormRef.value) return
  await apiSettingFormRef.value.validate(async (valid) => {
    if (valid) {
      apiSaveLoading.value = true
      try {
        if (isApiEditing.value) {
          await apiSettingsApi.updateApiSetting(apiSettingForm)
          ElMessage.success('API更新成功')
        } else {
          await apiSettingsApi.createApiSetting(apiSettingForm)
          ElMessage.success('API保存成功')
          isApiEditing.value = true
        }
      } catch (error) { ElMessage.error('保存失败') } finally { apiSaveLoading.value = false }
    }
  })
}

const handleDeleteApiSetting = async () => {
  try {
    await ElMessageBox.confirm('删除后将回退使用默认API，确定？', '确认', { type: 'warning' })
    apiDeleteLoading.value = true
    await apiSettingsApi.deleteApiSetting()
    isApiEditing.value = false
    apiSettingForm.primary_api_url = ''; apiSettingForm.backup_api_url = ''; apiSettingForm.api_key = ''; apiSettingForm.api_secret = ''
    ElMessage.success('API设置已删除')
  } catch (error) {} finally { apiDeleteLoading.value = false }
}

const handleTestPrimaryApi = async () => {
  testPrimaryLoading.value = true
  try {
    const response = await apiSettingsApi.testPrimaryApi()
    if (response.data.success) ElMessage.success(`主API通畅 (${response.data.response_time}s)`)
    else ElMessage.error(`失败: ${response.data.message}`)
  } catch (error) { ElMessage.error('测试失败') } finally { testPrimaryLoading.value = false }
}

const handleTestBackupApi = async () => {
  testBackupLoading.value = true
  try {
    const response = await apiSettingsApi.testBackupApi()
    if (response.data.success) ElMessage.success(`备用API通畅 (${response.data.response_time}s)`)
    else ElMessage.error(`失败: ${response.data.message}`)
  } catch (error) { ElMessage.error('测试失败') } finally { testBackupLoading.value = false }
}

const loadSystemSetting = async () => {
  try {
    const response = await systemSettingsApi.getSystemSetting()
    if (response.data) {
      Object.assign(systemForm, response.data)
    }
  } catch (error) {}
}

const handleSaveSystem = async () => {
  if (!systemFormRef.value) return
  await systemFormRef.value.validate(async (valid) => {
    if (valid) {
      systemSaveLoading.value = true
      try {
        await systemSettingsApi.createSystemSetting(systemForm)
        ElMessage.success('系统偏好已保存')
      } catch (error) { ElMessage.error('保存失败') } finally { systemSaveLoading.value = false }
    }
  })
}

const handleSaveAccount = async () => {
  if (!accountFormRef.value) return
  await accountFormRef.value.validate(async (valid) => {
    if (valid) {
      accountSaveLoading.value = true
      try {
        await authApi.updateAccount({
          username: accountForm.username,
          email: accountForm.email,
          current_password: accountForm.current_password,
          new_password: accountForm.new_password,
          confirm_new_password: accountForm.confirm_password
        })
        ElMessage.success('安全信息更新成功')
        accountForm.email = ''; accountForm.current_password = ''; accountForm.new_password = ''; accountForm.confirm_password = ''
        accountFormRef.value?.resetFields()
      } catch (error) { ElMessage.error('更新失败，请检查密码') } finally { accountSaveLoading.value = false }
    }
  })
}

const goToDashboard = () => router.push('/dashboard')

const goToHome = () => router.push('/')
const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出')
  router.push('/login')
}

onMounted(() => {
  loadSetting()
  loadApiSetting()
  loadSystemSetting()
})
</script>

<style scoped>
/* =========================================
   UI 架构层：与全局规范统一
   ========================================= */
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; }
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1400px; margin: 0 auto; width: 100%; }
.header-left h1 { margin: 0; font-size: 22px; color: #1f2f3d; font-weight: 600; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.header-right { display: flex; align-items: center; gap: 15px; }
.welcome-text { color: #606266; font-size: 14px; font-weight: 500; }
.page-main { padding: 20px 25px; max-width: 1400px; margin: 0 auto; width: 100%; }

.content-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); margin-bottom: 20px; }
.card-header { font-weight: 600; color: #303133; font-size: 15px; }

.form-actions { margin-top: 10px; margin-bottom: 0; }
.switch-group { display: flex; gap: 40px; margin-bottom: 20px; background: #f8f9fa; padding: 15px; border-radius: 8px; }
.inline-switch { margin-bottom: 0; }

.info-content p { color: #5e6d82; font-size: 13px; line-height: 1.6; margin-bottom: 12px; }
.info-content strong { color: #303133; }

/* 移动端适配 */
@media (max-width: 768px) {
  .page-container { padding-bottom: 80px; }
  .page-main { padding: 12px; }
  
  /* 1. 顶部容器改为相对定位，打断原有的 Flex 弹性流 */
  .page-header { padding: 15px; position: relative; }
  .header-content { display: block; }
  
  /* 2. 左侧标题区限制宽度，防止文字挤占右侧按钮空间 */
  .header-left { width: calc(100% - 50px); margin-bottom: 12px; }
  .header-left h1 { font-size: 18px; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  /* 恢复副标题显示，并强制单行超出显示省略号 */
  .header-left p { display: block; font-size: 12px; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  
  /* 3. 剥离暗黑模式按钮，使用绝对定位固定在右上角 */
  .header-right { display: block; width: 100%; }
  .dark-mode-btn { position: absolute; top: 15px; right: 15px; font-size: 16px; width: 36px; height: 36px; padding: 0; display: inline-flex; align-items: center; justify-content: center; z-index: 10; }

  /* 4. 按钮组重构为 CSS Grid 网格布局，强制一行三列 */
  :deep(.action-buttons) { display: grid !important; grid-template-columns: repeat(3, 1fr) !important; gap: 8px !important; width: 100%; }
  /* 抹除 Element Plus 按钮组默认的清除浮动伪元素，防止高度塌陷或间距异常 */
  :deep(.action-buttons::before), :deep(.action-buttons::after) { display: none !important; }
  /* 重置子按钮：清除浮动、独立赋予圆角、缩小字号以适应三列排版 */
  :deep(.action-buttons .el-button) { width: 100% !important; margin: 0 !important; border-radius: 6px !important; float: none !important; justify-content: center; padding: 8px 0 !important; font-size: 12px !important; height: auto !important; }
  .switch-group { flex-direction: column; gap: 15px; }
  .form-actions :deep(.el-button) { width: 100%; margin-left: 0; margin-bottom: 10px; }
}

/* 夜间模式 */
.page-container.dark-mode { background-color: #0f0f1a; }
.page-container.dark-mode .page-header { background: #1a1a2e; border-bottom-color: #2a2a3e; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.page-container.dark-mode .header-left h1 { color: #60a5fa; }
.page-container.dark-mode .header-left p { color: #8080a0; }
.page-container.dark-mode .welcome-text { color: #a0a0b0; }
.page-container.dark-mode .content-card { background: #1a1a2e; border: none; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
.page-container.dark-mode .card-header { color: #d0d0e0; }
.page-container.dark-mode :deep(.el-card__header) { background: #1a1a2e; border-bottom-color: #2a2a3e; }
.page-container.dark-mode :deep(.el-card__body) { background: #1a1a2e; }
.page-container.dark-mode :deep(.el-form-item__label) { color: #a0a0b0; }
.page-container.dark-mode :deep(.el-input__wrapper) { background: #16162a; }
.page-container.dark-mode :deep(.el-select .el-input__wrapper) { background: #16162a; }
.page-container.dark-mode :deep(.el-textarea__inner) { background: #16162a; color: #d0d0e0; }
.page-container.dark-mode .switch-group { background: #16162a; }
.page-container.dark-mode .info-content p { color: #8080a0; }
.page-container.dark-mode .info-content strong { color: #d0d0e0; }
</style>