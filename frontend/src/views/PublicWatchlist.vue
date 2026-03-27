<template>
  <div class="public-watchlist-container">
    <el-container>
      <el-header class="public-watchlist-header">
        <div class="header-left">
          <h1>{{ siteTitle }}</h1>
          <p>{{ siteDescription }}</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="goToLogin">登录</el-button>
        </div>
      </el-header>
      
      <el-main class="public-watchlist-main">
        <div class="hero-section">
          <h2>实时关注加密货币价格</h2>
          <p>关注您感兴趣的交易对，实时监控价格变化</p>
        </div>
        
        <el-card class="watchlist-card">
          <template #header>
            <div class="card-header">
              <span>🔥 热门关注</span>
            </div>
          </template>
          
          <el-table
            :data="publicWatchlist"
            style="width: 100%"
            v-loading="loading"
          >
            <el-table-column prop="crypto_symbol" label="交易对" width="120">
              <template #default="{ row }">
                <el-tag>{{ row.crypto_symbol }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="crypto_name" label="币种名称" width="120" />
            
            <el-table-column prop="current_price" label="当前价格" width="120">
              <template #default="{ row }">
                <span class="price">${{ row.current_price ? row.current_price.toFixed(2) : '0.00' }}</span>
              </template>
            </el-table-column>
            
          </el-table>
          
          <div v-if="!loading && publicWatchlist.length === 0" class="empty-state">
            <p>暂无关注数据</p>
            <p>登录后即可添加关注</p>
          </div>
        </el-card>
        
        <div class="cta-section">
          <el-button type="primary" size="large" @click="goToLogin">
            登录查看更多
          </el-button>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { watchlistApi, systemSettingsApi } from '../api'

const router = useRouter()

const loading = ref(false)
const publicWatchlist = ref<any[]>([])
const siteTitle = ref('Crypto-info')
const siteDescription = ref('数字货币价格监控和预警系统')

const loadPublicWatchlist = async () => {
  loading.value = true
  try {
    const response = await watchlistApi.getPublic()
    publicWatchlist.value = response.data
  } catch (error) {
    console.error('加载公开关注列表失败:', error)
  } finally {
    loading.value = false
  }
}

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

const goToLogin = () => {
  router.push('/login')
}

onMounted(() => {
  loadPublicWatchlist()
  loadPublicSettings()
})
</script>

<style scoped>
.public-watchlist-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.public-watchlist-header {
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

.header-left p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.public-watchlist-main {
  padding: 20px;
}

.hero-section {
  text-align: center;
  padding: 40px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px;
  margin-bottom: 20px;
}

.hero-section h2 {
  margin: 0 0 10px 0;
  font-size: 28px;
}

.hero-section p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.watchlist-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.price {
  color: #e6a23c;
  font-weight: bold;
}

.notes {
  color: #666;
  font-size: 12px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.empty-state p {
  margin: 10px 0;
}

.cta-section {
  text-align: center;
  padding: 40px 20px;
}

.cta-section .el-button {
  font-size: 16px;
  padding: 12px 30px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .public-watchlist-header {
    padding: 10px 15px;
    flex-direction: column;
    gap: 10px;
  }
  
  .header-left h1 {
    font-size: 1.2rem;
  }
  
  .header-left p {
    font-size: 12px;
  }
  
  .header-right {
    gap: 8px;
  }
  
  .public-watchlist-main {
    padding: 10px;
  }
  
  .hero-section {
    padding: 20px 15px;
    margin-bottom: 15px;
  }
  
  .hero-section h2 {
    font-size: 20px;
  }
  
  .hero-section p {
    font-size: 14px;
  }
  
  .watchlist-card {
    margin-bottom: 15px;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-table-column {
    min-width: 60px;
  }
  
  .price {
    font-size: 11px;
  }
  
  .notes {
    font-size: 11px;
  }
  
  .empty-state {
    padding: 20px;
    font-size: 12px;
  }
  
  .cta-section {
    padding: 20px 15px;
  }
  
  .cta-section .el-button {
    font-size: 14px;
    padding: 10px 20px;
  }
}

/* 禁止左右滚动 */
@media (max-width: 768px) {
  .el-table {
    overflow-x: hidden;
  }
  
  .el-table__body-wrapper {
    overflow-x: hidden !important;
  }
}
</style>