<template>
  <div class="page-container">
    <el-header class="page-header" height="auto">
      <div class="header-content">
        <div class="header-left">
          <h1>📈 数字货币价格监控和预警系统</h1>
          <p>实时掌控市场脉搏，快人一步捕捉交易良机</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="goToLogin" plain>系统登录</el-button>
        </div>
      </div> 
    </el-header>
      
    <el-main class="page-main">
      <!-- 关注列表 -->
      <el-card class="watchlist-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">🔥 全球热门关注</span>
            <el-button @click="loadPublicWatchlist" size="small" text bg>刷新</el-button>
          </div>
        </template>
        
        <div class="watchlist-grid" v-loading="loading">
          <div 
            v-for="item in publicWatchlist" 
            :key="item.crypto_symbol"
            class="watchlist-item"
            @click="goToKline(item.crypto_symbol)"
          >
            <div class="item-left">
              <el-tag effect="dark" round size="small" class="symbol-tag">{{ item.crypto_symbol }}</el-tag>
              <span class="item-name">{{ item.crypto_name }}</span>
            </div>
            <div class="item-right">
              <div class="price-text">${{ item.current_price ? item.current_price.toFixed(4) : '0.0000' }}</div>
            </div>
          </div>
          <el-empty v-if="!loading && publicWatchlist.length === 0" description="暂无公开关注数据" />
        </div>
      </el-card>
      
      <!-- 底部提示 -->
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

const router = useRouter()
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

// 跳转到K线页面
const goToKline = (symbol: string) => {
  router.push(`/kline?symbol=${symbol}`)
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
.header-left h1 { margin: 0; font-size: 22px; color: #1f2f3d; font-weight: 600; letter-spacing: 0.5px; }
.header-left p { margin: 6px 0 0; color: #909399; font-size: 13px; }
.page-main { padding: 20px 25px; max-width: 1200px; margin: 0 auto; width: 100%; }

.watchlist-card { border-radius: 10px; border: none; box-shadow: 0 2px 12px 0 rgba(0,0,0,0.02); margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-weight: 600; color: #303133; font-size: 15px; }

.watchlist-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }

.watchlist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #f0f2f5;
  cursor: pointer;
  transition: all 0.2s ease;
}

.watchlist-item:hover {
  background: #f0f2f5;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.item-left { display: flex; align-items: center; gap: 10px; }
.symbol-tag { font-weight: bold; font-family: 'Monaco', monospace; }
.item-name { font-size: 13px; color: #606266; }
.price-text { color: #409eff; font-weight: 600; font-family: 'Monaco', monospace; font-size: 15px; }

/* 引导注册区 */
.cta-section { text-align: center; padding: 50px 20px; margin-top: 20px; }
.cta-section p { color: #5e6d82; font-size: 15px; margin-bottom: 20px; }
.cta-section .el-button { font-size: 16px; padding: 12px 40px; border-radius: 8px; font-weight: bold; }

/* =========================================
   PC端视图 (> 768px)
   ========================================= */
@media (min-width: 769px) {
  .watchlist-grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
}

/* =========================================
   移动端视图 (<= 768px)
   ========================================= */
@media (max-width: 768px) {
  .page-container { padding-bottom: 40px; }
  .page-main { padding: 12px; }
  .page-header { padding: 15px; }
  
  .header-content { flex-direction: column; align-items: flex-start; gap: 12px; }
  .header-left h1 { font-size: 18px; }
  .header-left p { font-size: 12px; }
  
  .watchlist-grid { grid-template-columns: 1fr; }
  
  .cta-section { padding: 30px 10px; }
}
</style>