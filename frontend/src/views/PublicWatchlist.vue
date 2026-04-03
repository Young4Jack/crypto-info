<template>
  <div class="page-container" :class="{ 'dark-mode': isDarkMode }">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>🔥 全球热门关注</h1>
          <p>实时查看全球热门加密货币价格走势</p>
        </div>
        <div class="header-right">
          <el-button @click="toggleDarkMode" class="dark-mode-btn" :type="isDarkMode ? 'warning' : 'default'" plain>
            {{ isDarkMode ? '☀️' : '🌙' }}
          </el-button>
          <el-button type="primary" @click="goToLogin" plain>系统登录</el-button>
        </div>
      </div> 
    </el-header>
      
    <el-main class="page-main">
      <div class="view-wrapper" v-loading="loading">
        <div class="desktop-view">
          <el-card class="table-card" shadow="never">
            <template #header>
              <div class="card-header"><span>🔥 全球热门关注</span></div>
            </template>
            
            <el-table :data="publicWatchlist" stripe hover style="width: 100%">
              <el-table-column label="交易对" min-width="120">
                <template #default="{ row }">
                  <el-tag effect="dark" round size="small" class="symbol-tag">{{ row.crypto_symbol }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="crypto_name" label="币种名称" min-width="150" />
              <el-table-column label="当前价格" min-width="150" align="right">
                <template #default="{ row }">
                  <span class="price-text">${{ row.current_price ? row.current_price.toFixed(4) : '0.0000' }}</span>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-if="!loading && publicWatchlist.length === 0" description="暂无公开关注数据" />
          </el-card>
        </div>

        <div class="mobile-view">
          <div class="mobile-header-title">🔥 热门关注</div>
          <el-empty v-if="!loading && publicWatchlist.length === 0" description="暂无关注数据" />
          <div v-else class="card-list">
            <el-card v-for="(item, index) in publicWatchlist" :key="index" shadow="hover" class="mobile-data-card">
              <div class="card-header-row">
                <div class="coin-info">
                  <el-tag effect="dark" round class="symbol-tag">{{ item.crypto_symbol }}</el-tag>
                  <span class="coin-name">{{ item.crypto_name }}</span>
                </div>
                <div class="price-highlight">
                  ${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}
                </div>
              </div>
            </el-card>
          </div>
        </div>
      </div>
      
      <div class="cta-section">
        <p>想要定制您的专属监控面板？</p>
        <el-button type="primary" size="large" @click="goToLogin">
          立即登录探索更多功能
        </el-button>
      </div>
    </el-main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { watchlistApi, systemSettingsApi } from '../api'
import { useDarkMode } from '../composables/useDarkMode'

const router = useRouter()
const { isDarkMode, toggleDarkMode } = useDarkMode()
const loading = ref(false)
const publicWatchlist = ref<any[]>([])
const siteTitle = ref('Crypto-info')
const siteDescription = ref('数字货币价格监控系统')
let refreshTimer: ReturnType<typeof setInterval> | null = null

const loadPublicWatchlist = async (isBackground = false) => {
  if (!isBackground) loading.value = true
  try {
    const response = await watchlistApi.getPublic()
    // 前端基础去重保护
    const uniqueData = []
    const seen = new Set()
    for (const item of response.data) {
      if (!seen.has(item.crypto_symbol)) {
        seen.add(item.crypto_symbol)
        uniqueData.push(item)
      }
    }
    publicWatchlist.value = uniqueData
  } catch (error) {
    // 静默失败，不打扰公开用户
  } finally {
    if (!isBackground) loading.value = false
  }
}

// 🚀 核心修改 1：让函数返回数字 (Promise<number>)，并加上 return 语句
const loadPublicSettings = async (): Promise<number> => {
  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      siteTitle.value = response.data.site_title || 'Crypto-info'
      siteDescription.value = response.data.site_description || '数字货币价格监控和预警系统'
      // console.log('真实接收到的后端刷新频率:', response.data.refresh_interval)
      // 返回后端配置的时间，保底 5 秒
      return response.data.refresh_interval || 5
    }
  } catch (error) {
    console.error('加载配置失败，使用默认 5 秒')
  }
  return 5
}

const goToLogin = () => {
  router.push('/login')
}

// 🚀 核心修改 2：加上 async，并使用 await 接收时间
onMounted(async () => {
  loadPublicWatchlist(false)
  
  // 等待获取设置和刷新时间
  const intervalSeconds = await loadPublicSettings()
  
  // 注入动态时间
  refreshTimer = setInterval(() => {
    loadPublicWatchlist(true)
  }, intervalSeconds * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
/* =========================================
   UI 架构层：继承全局设计规范
   ========================================= */
.page-container { min-height: 100vh; background-color: #f5f7fa; padding-bottom: 30px; overflow-x: hidden;}
.page-header { background: white; padding: 15px 25px; box-shadow: 0 1px 4px rgba(0,21,41,0.04); border-bottom: 1px solid #f0f0f0; }
.header-content { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; width: 100%; }
.header-left h1 { margin: 0; font-size: 22px; color: #409eff; font-weight: bold; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.page-main { padding: 20px 25px; max-width: 1200px; margin: 0 auto; width: 100%; }

.table-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); overflow: hidden; }
.card-header { font-weight: 600; color: #303133; font-size: 16px; }

/* 字体排版 */
.symbol-tag { font-weight: bold; font-family: 'Monaco', monospace; }
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; font-size: 15px;}

/* 引导注册区 */
.cta-section { text-align: center; padding: 50px 20px; margin-top: 20px; }
.cta-section p { color: #5e6d82; font-size: 15px; margin-bottom: 20px; }
.cta-section .el-button { font-size: 16px; padding: 12px 40px; border-radius: 8px; font-weight: bold; }

/* =========================================
   PC端视图 (> 768px)
   ========================================= */
@media (min-width: 769px) {
  .desktop-view { display: block; }
  .mobile-view { display: none !important; }
  :deep(.el-table th.el-table__cell) { background-color: #fafafa; color: #606266; font-weight: 600; height: 50px; }
}

/* =========================================
   移动端视图 (<= 768px)
   ========================================= */
@media (max-width: 768px) {
  .desktop-view { display: none !important; }
  .mobile-view { display: block; }
  
  .page-container { padding-bottom: 40px; }
  .page-main { padding: 12px; }
  .page-header { padding: 15px; }
  
  .mobile-header-title { font-size: 16px; font-weight: bold; color: #303133; margin: 10px 0 15px 5px; }

  /* 卡片流 - 每行2个 */
  .card-list { 
    display: grid; 
    grid-template-columns: repeat(2, 1fr);
    gap: 10px; 
  }
  .mobile-data-card { 
    border-radius: 10px; 
    border: none; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); 
  }
  :deep(.mobile-data-card .el-card__body) { padding: 12px; }
  
  .card-header-row { 
    display: flex; 
    flex-direction: column;
    align-items: flex-start;
    gap: 6px; 
  }
  .coin-info { display: flex; align-items: center; gap: 8px; }
  .coin-name { 
    font-weight: 500; 
    font-size: 12px; 
    color: #606266;
    display: none; /* 隐藏交易对名称 */
  }
  .price-highlight { 
    font-size: 16px; 
    font-weight: 600; 
    color: #409eff; 
    font-family: 'Monaco', monospace; 
  }
  
  .cta-section { padding: 30px 10px; }
}

/* 夜间模式 */
.page-container.dark-mode { background-color: #0f0f1a; }
.page-container.dark-mode .page-header { background: #1a1a2e; border-bottom-color: #2a2a3e; box-shadow: 0 1px 4px rgba(0,0,0,0.3); }
.page-container.dark-mode .header-left h1 { color: #60a5fa; }
.page-container.dark-mode .header-left p { color: #8080a0; }
.page-container.dark-mode .table-card { background: #1a1a2e; border: none; box-shadow: 0 2px 12px rgba(0,0,0,0.3); }
.page-container.dark-mode .card-header { color: #d0d0e0; }
.page-container.dark-mode :deep(.el-card__header) { background: #1a1a2e; border-bottom-color: #2a2a3e; }
.page-container.dark-mode :deep(.el-card__body) { background: #1a1a2e; }
.page-container.dark-mode :deep(.el-table) { background: #1a1a2e; color: #d0d0e0; }
.page-container.dark-mode :deep(.el-table td), .page-container.dark-mode :deep(.el-table th.is-leaf) { background: #1a1a2e; border-color: #2a2a3e; color: #d0d0e0; }
.page-container.dark-mode :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background: #16162a; }
.page-container.dark-mode .price-highlight { color: #60a5fa; }
</style>