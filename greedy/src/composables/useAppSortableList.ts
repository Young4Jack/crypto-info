import { ref, Ref } from 'vue'

export interface SortOrderItem {
  id: number
  sort_order: number
}

export interface SaveOrderFn {
  (items: SortOrderItem[]): Promise<void>
}

export function useAppSortableList<T extends { id: number }>(
  list: Ref<T[]>,
  saveOrderFn: SaveOrderFn
) {
  const isDragging = ref(false)
  const dragIndex = ref(-1)
  const startY = ref(0)
  const itemPositions = ref<number[]>([])
  const draggedItem = ref<T | null>(null)

  // 获取每个item的位置信息
  const getItemPositions = () => {
    return new Promise<number[]>((resolve) => {
      const query = uni.createSelectorQuery()
      query.selectAll('.coin-card').boundingClientRect((rects: any) => {
        if (rects && Array.isArray(rects) && rects.length > 0) {
          resolve(rects.map((r: any) => r.top))
        } else {
          resolve([])
        }
      }).exec()
    })
  }

  const onDragStart = (index: number, e: any) => {
    startY.value = e.touches[0].clientY
    dragIndex.value = index
    draggedItem.value = { ...list.value[index] }
    isDragging.value = true
    
    // 获取所有item的位置
    getItemPositions().then(positions => {
      itemPositions.value = positions
    })
  }

  const onDragMove = (e: any) => {
    if (!isDragging.value || dragIndex.value === -1) return

    const currentY = e.touches[0].clientY
    
    // 根据位置计算移动到了哪个item
    if (itemPositions.value.length === 0) return
    
    let newIndex = dragIndex.value
    for (let i = 0; i < itemPositions.value.length; i++) {
      if (i !== dragIndex.value && currentY < itemPositions.value[i] + 60) {
        newIndex = i
        break
      }
    }

    if (newIndex !== dragIndex.value && newIndex >= 0 && newIndex < list.value.length) {
      // 交换数组中的元素
      const items = [...list.value]
      const item = items.splice(dragIndex.value, 1)[0]
      items.splice(newIndex, 0, item)
      list.value = items as T[]
      
      // 更新当前位置
      dragIndex.value = newIndex
      startY.value = currentY
      
      getItemPositions().then(positions => {
        itemPositions.value = positions
      })
    }
  }

  const onDragEnd = async () => {
    if (!isDragging.value) return
    
    isDragging.value = false
    draggedItem.value = null
    
    // 保存排序
    try {
      const items = list.value.map((item, index) => ({
        id: item.id,
        sort_order: index
      }))
      await saveOrderFn(items)
    } catch (e) {
      uni.showToast({ title: '排序保存失败', icon: 'none' })
    }
    
    dragIndex.value = -1
  }

  return {
    isDragging,
    dragIndex,
    draggedItem,
    onDragStart,
    onDragMove,
    onDragEnd,
  }
}
