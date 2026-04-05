import { ref } from 'vue'

export function useDarkMode() {
  // 默认亮色模式
  const isDarkMode = ref(false)

  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value
    
    // UniApp 特色：切换暗黑模式时，顺便把顶部状态栏颜色也改了
    if (isDarkMode.value) {
      uni.setNavigationBarColor({
        frontColor: '#ffffff',
        backgroundColor: '#1a1a2e',
        animation: { duration: 200, timingFunc: 'easeIn' }
      })
    } else {
      uni.setNavigationBarColor({
        frontColor: '#000000',
        backgroundColor: '#ffffff',
        animation: { duration: 200, timingFunc: 'easeIn' }
      })
    }
  }

  return {
    isDarkMode,
    toggleDarkMode
  }
}