const TAB_INDEX_MAP: Record<string, number> = {
  '/pages/market/market': 0,
  '/pages/alert/alert': 1,
  '/pages/assets/assets': 2,
  '/pages/mine/mine': 3,
}

const TAB_LIST = [
  { path: '/pages/market/market', index: 0 },
  { path: '/pages/alert/alert', index: 1 },
  { path: '/pages/assets/assets', index: 2 },
  { path: '/pages/mine/mine', index: 3 },
]

export function useSwipeTab(
  onSwipeLeft?: () => void,
  onSwipeRight?: () => void
) {
  let startX = 0
  let startY = 0
  const threshold = 50

  const onTouchStart = (e: any) => {
    startX = e.touches[0].clientX
    startY = e.touches[0].clientY
  }

  const onTouchEnd = (e: any) => {
    const deltaX = e.changedTouches[0].clientX - startX
    const deltaY = e.changedTouches[0].clientY - startY

    if (Math.abs(deltaX) < threshold || Math.abs(deltaX) <= Math.abs(deltaY)) {
      return
    }

    if (deltaX < 0) {
      onSwipeLeft?.()
    } else {
      onSwipeRight?.()
    }
  }

  const switchToNextTab = () => {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1] as any
    const currentPath = '/' + currentPage.route
    const currentIndex = TAB_INDEX_MAP[currentPath]

    if (currentIndex === undefined || currentIndex >= TAB_LIST.length - 1) return
    const nextTab = TAB_LIST[currentIndex + 1]
    uni.switchTab({ url: nextTab.path })
  }

  const switchToPrevTab = () => {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1] as any
    const currentPath = '/' + currentPage.route
    const currentIndex = TAB_INDEX_MAP[currentPath]

    if (currentIndex === undefined || currentIndex <= 0) return
    const prevTab = TAB_LIST[currentIndex - 1]
    uni.switchTab({ url: prevTab.path })
  }

  return {
    onTouchStart,
    onTouchEnd,
    switchToNextTab,
    switchToPrevTab,
  }
}