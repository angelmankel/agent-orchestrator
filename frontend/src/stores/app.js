import { writable, derived } from 'svelte/store'

// Current project
export const currentProject = writable(null)

// Current page
export const currentPage = writable('dashboard')

// Loading states
export const loading = writable(false)

// Error state
export const error = writable(null)

// Toast notifications
export const toasts = writable([])

let toastId = 0

export function addToast(message, type = 'info', duration = 5000) {
  const id = ++toastId
  toasts.update(t => [...t, { id, message, type }])

  if (duration > 0) {
    setTimeout(() => {
      toasts.update(t => t.filter(toast => toast.id !== id))
    }, duration)
  }

  return id
}

export function removeToast(id) {
  toasts.update(t => t.filter(toast => toast.id !== id))
}

// Dark mode
export const darkMode = writable(
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-color-scheme: dark)').matches
)

darkMode.subscribe(value => {
  if (typeof document !== 'undefined') {
    document.documentElement.classList.toggle('dark', value)
  }
})
