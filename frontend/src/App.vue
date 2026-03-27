<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted } from 'vue'
import { systemSettingsApi } from './api'

onMounted(async () => {
  try {
    // 获取公开的系统设置
    const response = await systemSettingsApi.getPublicSystemSetting()
    if (response.data) {
      // 更新浏览器标签页的标题
      if (response.data.site_title) {
        document.title = response.data.site_title
      }
      
      // 更新Meta描述信息
      if (response.data.site_description) {
        const metaDescription = document.querySelector('meta[name="description"]')
        if (metaDescription) {
          metaDescription.setAttribute('content', response.data.site_description)
        } else {
          // 如果Meta描述不存在，创建一个新的
          const meta = document.createElement('meta')
          meta.name = 'description'
          meta.content = response.data.site_description
          document.head.appendChild(meta)
        }
      }
    }
  } catch (error) {
    console.error('加载公开设置失败:', error)
    // 如果API调用失败，使用默认标题
    document.title = 'Crypto-info'
  }
})
</script>

<template>
  <RouterView />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}
</style>