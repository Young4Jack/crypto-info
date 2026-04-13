import { ref, Ref, onUnmounted } from 'vue'

export interface SortOrderItem {
  id: number
  sort_order: number
}

export interface UseDraggableOptions<T> {
  saveOrder: (items: SortOrderItem[]) => Promise<void>
  enabled?: () => boolean
  realtimeReorder?: boolean
}

export interface DragState<T> {
  item: T
  index: number
  startY: number
  currentY: number
  itemHeight: number
}

export function useDraggableList<T extends { id: number }>(
  list: Ref<T[]>,
  options: UseDraggableOptions<T>
) {
  const isDragging = ref(false)
  const dragState = ref<DragState<T> | null>(null)
  const dragOverIndex = ref(-1)

  let longPressTimer: ReturnType<typeof setTimeout> | null = null
  let lastReorderIndex = -1

  const getClientY = (e: any) => {
    if (e.touches && e.touches.length > 0) {
      return e.touches[0].clientY
    } else if (e.clientY !== undefined) {
      return e.clientY
    }
    return 0
  }

  const onDragStart = (index: number, e: any) => {
    if (options.enabled && !options.enabled()) return

    const clientY = getClientY(e)
    const item = list.value[index]
    if (!item || !clientY) return

    const isMouse = e.type === 'mousedown'
    
    if (isMouse) {
      startDrag(index, clientY, item)
    } else {
      longPressTimer = setTimeout(() => {
        startDrag(index, clientY, item)
      }, 300)
    }
  }

  const startDrag = (index: number, clientY: number, item: T) => {
    lastReorderIndex = index
    isDragging.value = true
    dragState.value = {
      item,
      index,
      startY: clientY,
      currentY: clientY,
      itemHeight: 76
    }
    dragOverIndex.value = index
  }

  const performReorder = (newIndex: number) => {
    if (!dragState.value || !options.realtimeReorder) return
    if (newIndex === lastReorderIndex) return
    
    const currentItem = dragState.value.item as T
    const fromIdx = lastReorderIndex
    
    list.value.splice(fromIdx, 1)
    list.value.splice(newIndex, 0, currentItem)
    
    dragState.value.index = newIndex
    dragState.value.startY = dragState.value.currentY
    lastReorderIndex = newIndex
    dragOverIndex.value = newIndex
  }

  const onTouchMove = (e: any) => {
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }

    if (!isDragging.value || !dragState.value) return

    if (e.cancelable) {
      e.preventDefault()
    }
    e.stopPropagation()

    const clientY = getClientY(e)
    if (!clientY) return

    dragState.value.currentY = clientY

    const deltaY = clientY - dragState.value.startY
    const moveItems = Math.round(deltaY / dragState.value.itemHeight)

    let newIndex = dragState.value.index + moveItems
    newIndex = Math.max(0, Math.min(newIndex, list.value.length - 1))

    if (newIndex !== dragOverIndex.value) {
      dragOverIndex.value = newIndex
      
      if (options.realtimeReorder) {
        performReorder(newIndex)
      }
    }
  }

  const onMouseMove = (e: MouseEvent) => {
    if (!isDragging.value || !dragState.value) return

    dragState.value.currentY = e.clientY

    const deltaY = e.clientY - dragState.value.startY
    const moveItems = Math.round(deltaY / dragState.value.itemHeight)

    let newIndex = dragState.value.index + moveItems
    newIndex = Math.max(0, Math.min(newIndex, list.value.length - 1))

    if (newIndex !== dragOverIndex.value) {
      dragOverIndex.value = newIndex
      
      if (options.realtimeReorder) {
        performReorder(newIndex)
      }
    }
  }

  const onDragEnd = () => {
    longPressTimer && clearTimeout(longPressTimer)
    longPressTimer = null

    const wasDragging = isDragging.value
    const state = dragState.value

    isDragging.value = false
    dragState.value = null
    dragOverIndex.value = -1
    lastReorderIndex = -1

    if (!wasDragging || !state) return

    try {
      const items: SortOrderItem[] = list.value.map((coin, idx) => ({
        id: coin.id,
        sort_order: idx
      }))
      options.saveOrder(items)
    } catch (e) {
      console.error('保存排序失败:', e)
      uni.showToast({ title: '排序保存失败', icon: 'none' })
    }
  }

  const cancelDrag = () => {
    longPressTimer && clearTimeout(longPressTimer)
    longPressTimer = null
    isDragging.value = false
    dragState.value = null
    dragOverIndex.value = -1
    lastReorderIndex = -1
  }

  onUnmounted(() => {
    longPressTimer && clearTimeout(longPressTimer)
  })

  return {
    isDragging,
    dragState,
    dragOverIndex,
    onDragStart,
    onTouchMove,
    onMouseMove,
    onDragEnd,
    cancelDrag
  }
}