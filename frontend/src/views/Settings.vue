<template>
  <div class="settings-container">
    <el-container>
      <el-header class="settings-header">
        <div class="header-left">
          <h1>系统设置</h1>
        </div>
        <div class="header-right">
          <span>欢迎，{{ authStore.user?.username || '用户' }}</span>
          <el-button @click="goToDashboard">返回仪表盘</el-button>
          <el-button type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      
      <el-main class="settings-main">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>通知推送设置</span>
            </div>
          </template>
          
          <el-form
            ref="settingFormRef"
            :model="settingForm"
            :rules="settingRules"
            label-width="150px"
            @submit.prevent="handleSaveSetting"
          >
            <el-form-item label="推送 API 地址" prop="api_url">
              <el-input
                v-model="settingForm.api_url"
                placeholder="请输入推送 API 地址"
              />
            </el-form-item>
            
            <el-form-item label="Authorization Token" prop="auth_token">
              <el-input
                v-model="settingForm.auth_token"
                placeholder="请输入 Authorization Token"
                type="password"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="推送渠道" prop="channel">
              <el-input
                v-model="settingForm.channel"
                placeholder="请输入推送渠道（可选）"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                :loading="saveLoading"
                @click="handleSaveSetting"
              >
                {{ isEditing ? '更新设置' : '保存设置' }}
              </el-button>
              <el-button
                v-if="isEditing"
                type="warning"
                :loading="testLoading"
                @click="handleTestNotification"
              >
                测试连接
              </el-button>
              <el-button
                v-if="isEditing"
                type="danger"
                :loading="deleteLoading"
                @click="handleDeleteSetting"
              >
                删除设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>价格获取 API 设置</span>
            </div>
          </template>
          
          <el-form
            ref="apiSettingFormRef"
            :model="apiSettingForm"
            :rules="apiSettingRules"
            label-width="150px"
            @submit.prevent="handleSaveApiSetting"
          >
            <el-form-item label="主 API 地址" prop="primary_api_url">
              <el-input
                v-model="apiSettingForm.primary_api_url"
                placeholder="请输入主 API 地址，例如：https://api.binance.com/api/v3/ticker/price"
              />
            </el-form-item>
            
            <el-form-item label="备用 API 地址" prop="backup_api_url">
              <el-input
                v-model="apiSettingForm.backup_api_url"
                placeholder="请输入备用 API 地址（可选）"
              />
            </el-form-item>
            
            <el-form-item label="API Key" prop="api_key">
              <el-input
                v-model="apiSettingForm.api_key"
                placeholder="请输入 API Key（可选）"
                type="password"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="API Secret" prop="api_secret">
              <el-input
                v-model="apiSettingForm.api_secret"
                placeholder="请输入 API Secret（可选）"
                type="password"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                :loading="apiSaveLoading"
                @click="handleSaveApiSetting"
              >
                {{ isApiEditing ? '更新 API 设置' : '保存 API 设置' }}
              </el-button>
              <el-button
                v-if="isApiEditing"
                type="warning"
                :loading="testPrimaryLoading"
                @click="handleTestPrimaryApi"
              >
                测试主 API
              </el-button>
              <el-button
                v-if="isApiEditing && apiSettingForm.backup_api_url"
                type="warning"
                :loading="testBackupLoading"
                @click="handleTestBackupApi"
              >
                测试备用 API
              </el-button>
              <el-button
                v-if="isApiEditing"
                type="danger"
                :loading="apiDeleteLoading"
                @click="handleDeleteApiSetting"
              >
                删除 API 设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>系统设置</span>
            </div>
          </template>
          
          <el-form
            ref="systemFormRef"
            :model="systemForm"
            :rules="systemRules"
            label-width="150px"
            @submit.prevent="handleSaveSystem"
          >
            <div class="setting-group">
              <div class="setting-group-title">网站设置</div>
              <el-form-item label="网站标题" prop="site_title">
                <el-input
                  v-model="systemForm.site_title"
                  placeholder="请输入网站标题"
                  maxlength="100"
                  show-word-limit
                />
                <div class="form-tip">设置网站的标题，显示在浏览器标签页和登录页面</div>
              </el-form-item>
              
              <el-form-item label="网站描述" prop="site_description">
                <el-input
                  v-model="systemForm.site_description"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入网站描述"
                  maxlength="500"
                  show-word-limit
                />
                <div class="form-tip">设置网站的描述，用于SEO和登录页面展示</div>
              </el-form-item>
            </div>
            
            <el-divider />
            
            <div class="setting-group">
              <div class="setting-group-title">数据更新设置</div>
              <el-form-item label="价格刷新间隔" prop="refresh_interval">
                <div class="setting-input-group">
                  <el-input-number
                    v-model="systemForm.refresh_interval"
                    :min="5"
                    :max="3600"
                    placeholder="请输入刷新间隔"
                    style="width: 100%; max-width: 300px;"
                  />
                  <span class="setting-unit">秒</span>
                </div>
                <div class="form-tip">系统会按此间隔自动获取最新的交易对价格，推荐设置为10-30秒以获得较好的实时性</div>
              </el-form-item>
            </div>
            
            <el-divider />
            
            <div class="setting-group">
              <div class="setting-group-title">安全设置</div>
              <el-form-item label="登录验证码">
                <div class="setting-switch-group">
                  <el-switch
                    v-model="systemForm.enable_captcha"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                  <span class="setting-status">{{ systemForm.enable_captcha ? '已启用' : '已禁用' }}</span>
                </div>
                <div class="form-tip">开启后每次登录需要完成简单的数学验证，有效防止恶意登录尝试</div>
              </el-form-item>
            </div>
            
            <el-divider />
            
            <div class="setting-group">
              <div class="setting-group-title">日志设置</div>
              <el-form-item label="日志级别">
                <el-select
                  v-model="systemForm.log_level"
                  placeholder="请选择日志级别"
                  style="width: 100%; max-width: 300px;"
                >
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                  <el-option label="CRITICAL" value="CRITICAL" />
                </el-select>
                <div class="form-tip">设置系统日志的详细程度，DEBUG最详细，CRITICAL只记录严重错误</div>
              </el-form-item>
              
              <el-form-item label="启用日志">
                <div class="setting-switch-group">
                  <el-switch
                    v-model="systemForm.enable_logging"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                  <span class="setting-status">{{ systemForm.enable_logging ? '已启用' : '已禁用' }}</span>
                </div>
                <div class="form-tip">开启后系统会记录运行日志，便于排查问题和监控系统状态</div>
              </el-form-item>
            </div>
            
            <el-divider />
            
            <div class="setting-group">
              <div class="setting-group-title">时区设置</div>
              <el-form-item label="系统时区">
                <el-select
                  v-model="systemForm.timezone"
                  placeholder="请选择时区"
                  style="width: 100%; max-width: 300px;"
                >
                  <el-option label="亚洲/上海 (UTC+8)" value="Asia/Shanghai" />
                  <el-option label="亚洲/东京 (UTC+9)" value="Asia/Tokyo" />
                  <el-option label="亚洲/新加坡 (UTC+8)" value="Asia/Singapore" />
                  <el-option label="亚洲/香港 (UTC+8)" value="Asia/Hong_Kong" />
                  <el-option label="美国/纽约 (UTC-5)" value="America/New_York" />
                  <el-option label="美国/洛杉矶 (UTC-8)" value="America/Los_Angeles" />
                  <el-option label="欧洲/伦敦 (UTC+0)" value="Europe/London" />
                  <el-option label="欧洲/巴黎 (UTC+1)" value="Europe/Paris" />
                  <el-option label="UTC (UTC+0)" value="UTC" />
                </el-select>
                <div class="form-tip">设置系统使用的时区，影响日志时间戳和定时任务的执行时间</div>
              </el-form-item>
            </div>
            
            <el-divider />
            
            <el-form-item>
              <el-button
                type="primary"
                :loading="systemSaveLoading"
                @click="handleSaveSystem"
                class="save-button"
              >
                保存系统设置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>账户设置</span>
            </div>
          </template>
          
          <el-form
            ref="accountFormRef"
            :model="accountForm"
            :rules="accountRules"
            label-width="150px"
            @submit.prevent="handleSaveAccount"
          >
            <el-form-item label="新用户名" prop="username">
              <el-input
                v-model="accountForm.username"
                placeholder="请输入新用户名（留空保持不变）"
              />
            </el-form-item>
            
            <el-form-item label="新邮箱" prop="email">
              <el-input
                v-model="accountForm.email"
                placeholder="请输入新邮箱（留空保持不变）"
              />
            </el-form-item>
            
            <el-form-item label="当前密码" prop="current_password">
              <el-input
                v-model="accountForm.current_password"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="accountForm.new_password"
                type="password"
                placeholder="请输入新密码（留空保持不变）"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input
                v-model="accountForm.confirm_password"
                type="password"
                placeholder="请确认新密码"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                :loading="accountSaveLoading"
                @click="handleSaveAccount"
              >
                更新账户信息
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        
        <el-card class="info-card">
          <template #header>
            <div class="card-header">
              <span>说明信息</span>
            </div>
          </template>
          
          <div class="info-content">
            <h4>通知推送设置</h4>
            <p>配置预警触发时的通知推送方式，支持 Webhook、邮件等多种渠道。</p>
            
            <h4>价格获取 API 设置</h4>
            <p>配置获取数字货币价格的 API 地址，支持币安、OKX 等主流交易所 API，也可以使用自定义的价格数据源。</p>
            
            <h4>API 地址格式</h4>
            <p>主 API 地址：完整的 API 端点 URL，系统会自动添加币种符号参数。</p>
            <p>备用 API 地址：当主 API 不可用时，系统会自动切换到备用 API。</p>
            
            <h4>系统设置</h4>
            <p>价格刷新间隔：系统自动获取最新价格的时间间隔，建议设置为 5-60 秒。</p>
            
            <h4>账户设置</h4>
            <p>修改邮箱和密码后，需要重新登录。</p>
            
            <h4>测试 API</h4>
            <p>保存设置后，系统会在下次价格检查时使用新的 API 配置。您可以在仪表盘查看价格数据是否正常获取。</p>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import { settingsApi, apiSettingsApi, systemSettingsApi, authApi } from '../api'

const router = useRouter()
const authStore = useAuthStore()

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

const settingForm = reactive({
  api_url: '',
  auth_token: '',
  channel: 'email'
})

const apiSettingForm = reactive({
  primary_api_url: '',
  backup_api_url: '',
  api_key: '',
  api_secret: ''
})

const systemForm = reactive({
  refresh_interval: 5,
  enable_captcha: false,
  site_title: 'Crypto-info',
  site_description: '数字货币价格监控和预警系统',
  log_level: 'INFO',
  enable_logging: true,
  timezone: 'Asia/Shanghai'
})

const accountForm = reactive({
  username: '',
  email: '',
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const settingRules: FormRules = {
  api_url: [
    { required: true, message: '请输入推送 API 地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的 URL', trigger: 'blur' }
  ],
  auth_token: [
    { required: true, message: '请输入 Authorization Token', trigger: 'blur' }
  ],
  channel: []
}

const apiSettingRules: FormRules = {
  primary_api_url: [
    { required: true, message: '请输入主 API 地址', trigger: 'blur' }
  ]
}

const systemRules: FormRules = {
  refresh_interval: [
    { required: true, message: '请输入刷新间隔', trigger: 'blur' },
    { type: 'number', min: 5, max: 3600, message: '刷新间隔必须在5-3600秒之间', trigger: 'blur' }
  ]
}

const accountRules: FormRules = {
  current_password: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ]
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
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

const handleSaveSetting = async () => {
  if (!settingFormRef.value) return
  
  await settingFormRef.value.validate(async (valid) => {
    if (valid) {
      saveLoading.value = true
      try {
        if (isEditing.value) {
          await settingsApi.updateNotificationSetting({
            api_url: settingForm.api_url,
            auth_token: settingForm.auth_token,
            channel: settingForm.channel
          })
          ElMessage.success('设置更新成功')
        } else {
          await settingsApi.createNotificationSetting({
            api_url: settingForm.api_url,
            auth_token: settingForm.auth_token,
            channel: settingForm.channel
          })
          ElMessage.success('设置保存成功')
          isEditing.value = true
        }
      } catch (error) {
        console.error('保存设置失败:', error)
        ElMessage.error('保存设置失败')
      } finally {
        saveLoading.value = false
      }
    }
  })
}

const handleDeleteSetting = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除通知设置吗？删除后将无法接收预警通知。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    deleteLoading.value = true
    await settingsApi.deleteNotificationSetting()
    
    isEditing.value = false
    settingForm.api_url = ''
    settingForm.auth_token = ''
    settingForm.channel = 'email'
    
    ElMessage.success('设置已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除设置失败:', error)
      ElMessage.error('删除设置失败')
    }
  } finally {
    deleteLoading.value = false
  }
}

const handleTestNotification = async () => {
  testLoading.value = true
  try {
    const response = await settingsApi.testNotificationSetting()
    if (response.data.success) {
      ElMessage.success('通知API连接测试成功')
    } else {
      ElMessage.error(`通知API连接测试失败: ${response.data.message}`)
    }
  } catch (error) {
    console.error('测试通知API失败:', error)
    ElMessage.error('测试通知API失败')
  } finally {
    testLoading.value = false
  }
}

const goToDashboard = () => {
  router.push('/dashboard')
}

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
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
  } catch (error) {
    console.error('加载API设置失败:', error)
  }
}

const loadSystemSetting = async () => {
  try {
    const response = await systemSettingsApi.getSystemSetting()
    if (response.data) {
      systemForm.refresh_interval = response.data.refresh_interval
      systemForm.enable_captcha = response.data.enable_captcha
      systemForm.site_title = response.data.site_title || 'Crypto-info'
      systemForm.site_description = response.data.site_description || '数字货币价格监控和预警系统'
    }
  } catch (error) {
    console.error('加载系统设置失败:', error)
  }
}

const handleSaveApiSetting = async () => {
  if (!apiSettingFormRef.value) return
  
  await apiSettingFormRef.value.validate(async (valid) => {
    if (valid) {
      apiSaveLoading.value = true
      try {
        if (isApiEditing.value) {
          await apiSettingsApi.updateApiSetting({
            primary_api_url: apiSettingForm.primary_api_url,
            backup_api_url: apiSettingForm.backup_api_url,
            api_key: apiSettingForm.api_key,
            api_secret: apiSettingForm.api_secret
          })
          ElMessage.success('API设置更新成功')
        } else {
          await apiSettingsApi.createApiSetting({
            primary_api_url: apiSettingForm.primary_api_url,
            backup_api_url: apiSettingForm.backup_api_url,
            api_key: apiSettingForm.api_key,
            api_secret: apiSettingForm.api_secret
          })
          ElMessage.success('API设置保存成功')
          isApiEditing.value = true
        }
      } catch (error) {
        console.error('保存API设置失败:', error)
        ElMessage.error('保存API设置失败')
      } finally {
        apiSaveLoading.value = false
      }
    }
  })
}

const handleDeleteApiSetting = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除API设置吗？删除后将使用默认的币安API。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    apiDeleteLoading.value = true
    await apiSettingsApi.deleteApiSetting()
    
    isApiEditing.value = false
    apiSettingForm.primary_api_url = ''
    apiSettingForm.backup_api_url = ''
    apiSettingForm.api_key = ''
    apiSettingForm.api_secret = ''
    
    ElMessage.success('API设置已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除API设置失败:', error)
      ElMessage.error('删除API设置失败')
    }
  } finally {
    apiDeleteLoading.value = false
  }
}

const handleTestPrimaryApi = async () => {
  testPrimaryLoading.value = true
  try {
    const response = await apiSettingsApi.testPrimaryApi()
    if (response.data.success) {
      ElMessage.success(`主API连接测试成功 (响应时间: ${response.data.response_time}秒)`)
    } else {
      ElMessage.error(`主API连接测试失败: ${response.data.message}`)
    }
  } catch (error) {
    console.error('测试主API失败:', error)
    ElMessage.error('测试主API失败')
  } finally {
    testPrimaryLoading.value = false
  }
}

const handleTestBackupApi = async () => {
  testBackupLoading.value = true
  try {
    const response = await apiSettingsApi.testBackupApi()
    if (response.data.success) {
      ElMessage.success(`备用API连接测试成功 (响应时间: ${response.data.response_time}秒)`)
    } else {
      ElMessage.error(`备用API连接测试失败: ${response.data.message}`)
    }
  } catch (error) {
    console.error('测试备用API失败:', error)
    ElMessage.error('测试备用API失败')
  } finally {
    testBackupLoading.value = false
  }
}

const handleSaveSystem = async () => {
  if (!systemFormRef.value) return
  
  await systemFormRef.value.validate(async (valid) => {
    if (valid) {
      systemSaveLoading.value = true
      try {
        // 调用系统设置API，包含新增的日志和时区设置
        await systemSettingsApi.createSystemSetting({
          refresh_interval: systemForm.refresh_interval,
          enable_captcha: systemForm.enable_captcha,
          site_title: systemForm.site_title,
          site_description: systemForm.site_description,
          log_level: systemForm.log_level,
          enable_logging: systemForm.enable_logging,
          timezone: systemForm.timezone
        })
        ElMessage.success('系统设置保存成功')
      } catch (error) {
        console.error('保存系统设置失败:', error)
        ElMessage.error('保存系统设置失败')
      } finally {
        systemSaveLoading.value = false
      }
    }
  })
}

const handleSaveAccount = async () => {
  if (!accountFormRef.value) return
  
  await accountFormRef.value.validate(async (valid) => {
    if (valid) {
      accountSaveLoading.value = true
      try {
        // 调用账户设置API
        await authApi.updateAccount({
          username: accountForm.username,
          email: accountForm.email,
          current_password: accountForm.current_password,
          new_password: accountForm.new_password,
          confirm_new_password: accountForm.confirm_password
        })
        ElMessage.success('账户信息更新成功')
        
        // 清空表单
        accountForm.email = ''
        accountForm.current_password = ''
        accountForm.new_password = ''
        accountForm.confirm_password = ''
        accountFormRef.value?.resetFields()
      } catch (error) {
        console.error('更新账户信息失败:', error)
        ElMessage.error('更新账户信息失败')
      } finally {
        accountSaveLoading.value = false
      }
    }
  })
}

onMounted(() => {
  loadSetting()
  loadApiSetting()
  loadSystemSetting()
})
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.settings-header {
  background: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  margin: 0;
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.settings-main {
  padding: 20px;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-card {
  margin-top: 20px;
}

.info-content h4 {
  color: #333;
  margin-bottom: 10px;
}

.info-content p {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.6;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
  line-height: 1.4;
  display: block;
  width: 100%;
  clear: both;
}

.setting-group {
  margin-bottom: 10px;
}

.setting-group-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
  padding-left: 10px;
  border-left: 3px solid var(--primary-color);
}

.setting-input-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.setting-unit {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.setting-switch-group {
  display: flex;
  align-items: center;
  gap: 15px;
}

.setting-status {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.save-button {
  width: 200px;
  height: 40px;
  font-weight: 600;
}

:deep(.el-divider) {
  margin: 24px 0;
}

:deep(.el-form-item) {
  margin-bottom: 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--text-primary);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .settings-container {
    min-height: 100vh;
    background-color: #f5f5f5;
  }
  
  .settings-header {
    background: white;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    gap: 15px;
  }
  
  .header-left h1 {
    margin: 0;
    color: #409eff;
    font-size: 1.5rem;
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .settings-main {
    padding: 15px;
  }
  
  .settings-card {
    margin-bottom: 15px;
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
  }
  
  
  :deep(.el-form-item__label) {
    font-size: 14px;
    font-weight: 500;
  }
  
  :deep(.el-input__wrapper) {
    font-size: 16px;
  }
  
  :deep(.el-input-number) {
    width: 100% !important;
  }
  
  :deep(.el-button) {
    width: 100%;
    margin-left: 0 !important;
    margin-bottom: 10px;
  }
  
  :deep(.el-button:last-child) {
    margin-bottom: 0;
  }
}

@media (max-width: 480px) {
  .settings-header {
    padding: 10px 15px;
  }
  
  .header-left h1 {
    font-size: 1.2rem;
  }
  
  .header-right {
    gap: 8px;
  }
  
  .header-right .el-button {
    font-size: 12px;
    padding: 8px 12px;
  }
  
  .settings-main {
    padding: 10px;
  }
  
  .settings-card {
    margin-bottom: 10px;
  }
  
  :deep(.el-card__body) {
    padding: 15px;
  }
  
  :deep(.el-form-item) {
    margin-bottom: 18px;
  }
  
  .info-content h4 {
    font-size: 14px;
  }
  
  .info-content p {
    font-size: 13px;
  }
}
@media (max-width: 768px) {
  /* 强制表单元素转为纵向排列 */
  :deep(.el-form-item) {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 18px;
  }
  
  /* 取消 Label 的固定宽度并靠左对齐 */
  :deep(.el-form-item__label) {
    width: 100% !important;
    text-align: left;
    padding-bottom: 5px;
    line-height: 1.2;
  }
  
  /* 输入控件容器占满整行，并清除默认的左边距 */
  :deep(.el-form-item__content) {
    width: 100%;
    margin-left: 0 !important;
  }

  /* 修复页签选项卡（Tabs）在手机端过长被截断的问题 */
  :deep(.el-tabs__nav-scroll) {
    overflow-x: auto; /* 允许页签栏横向滑动 */
  }
}
</style>