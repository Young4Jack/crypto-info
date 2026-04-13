declare module 'sortablejs' {
  interface SortableOptions {
    animation?: number
    handle?: string
    ghostClass?: string
    chosenClass?: string
    dragClass?: string
    scroll?: boolean | HTMLElement
    scrollSensitivity?: number
    scrollSpeed?: number
    onStart?: (evt: any) => void
    onEnd?: (evt: any) => void
    [key: string]: any
  }

  interface SortableInstance {
    el: HTMLElement
    options: SortableOptions
    destroy: () => void
  }

  const Sortable: {
    create: (el: HTMLElement, options?: SortableOptions) => SortableInstance
  }

  export default Sortable
  export {}
}
