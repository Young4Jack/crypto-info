import { ref, onUnmounted, Ref } from 'vue'

// #ifdef H5
import Sortable from 'sortablejs'
// #endif

export interface SortableOptions {
  handle?: string
  animation?: number
  ghostClass?: string
  chosenClass?: string
  dragClass?: string
}

export interface SortOrderItem {
  id: number
  sort_order: number
}

export interface SaveOrderFn {
  (items: SortOrderItem[]): Promise<void>
}

export function useSortableList<T extends { id: number }>(
  list: Ref<T[]>,
  saveOrderFn: SaveOrderFn,
  options: SortableOptions = {}
) {
  // #ifdef H5
  const sortableInstance = ref<any>(null)
  // #endif
  
  const isDragging = ref(false)

  const defaultOptions: SortableOptions = {
    handle: '.drag-handle',
    animation: 150,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    dragClass: 'sortable-drag',
    ...options,
  }

  const initSortable = (selector: string) => {
    // #ifdef H5
    if (sortableInstance.value) {
      destroySortable()
    }

    setTimeout(() => {
      const el = document.querySelector(selector) as HTMLElement
      if (!el) return

      sortableInstance.value = Sortable.create(el, {
        handle: defaultOptions.handle,
        animation: defaultOptions.animation,
        ghostClass: defaultOptions.ghostClass,
        chosenClass: defaultOptions.chosenClass,
        dragClass: defaultOptions.dragClass,
        onStart: () => {
          isDragging.value = true
        },
        onEnd: async (evt: any) => {
          isDragging.value = false
          const { oldIndex, newIndex } = evt
          if (oldIndex === undefined || newIndex === undefined || oldIndex === newIndex) return
          if (!list.value || !Array.isArray(list.value)) return

          const itemsCopy = [...list.value]
          const item = itemsCopy.splice(oldIndex, 1)[0]
          itemsCopy.splice(newIndex, 0, item)
          
          list.value = itemsCopy as T[]

          try {
            const sortItems = list.value.map((item, index) => ({
              id: item.id,
              sort_order: index,
            }))
            await saveOrderFn(sortItems)
          } catch (e) {
            uni.showToast({ title: '排序保存失败', icon: 'none' })
          }
        },
      })
    }, 100)
    // #endif
    
    // #ifdef APP-PLUS
    uni.showToast({ title: 'App端暂不支持拖拽排序', icon: 'none' })
    // #endif
  }

  const destroySortable = () => {
    // #ifdef H5
    if (sortableInstance.value) {
      sortableInstance.value.destroy()
      sortableInstance.value = null
    }
    // #endif
  }

  onUnmounted(() => {
    destroySortable()
  })

  return {
    isDragging,
    initSortable,
    destroySortable,
  }
}
