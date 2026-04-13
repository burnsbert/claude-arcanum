import { useEffect, useCallback } from 'react'
import { useAppStore } from '../store/appStore'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastItem {
  id: string
  message: string
  type: ToastType
}

function Toast({ item, onDismiss }: { item: ToastItem; onDismiss: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 4000)
    return () => clearTimeout(timer)
  }, [onDismiss])

  const icon = item.type === 'success' ? '✓' : item.type === 'error' ? '✕' : 'ℹ'
  const colors = item.type === 'success'
    ? 'bg-green-50 text-green-800 dark:bg-green-900 dark:text-green-200'
    : item.type === 'error'
    ? 'bg-red-50 text-red-800 dark:bg-red-900 dark:text-red-200'
    : 'bg-blue-50 text-blue-800 dark:bg-blue-900 dark:text-blue-200'

  return (
    <div
      role={item.type === 'error' ? 'alert' : 'status'}
      className={`flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm ${colors}`}
    >
      <span className="font-bold">{icon}</span>
      <span className="flex-1">{item.message}</span>
      <button
        type="button"
        onClick={onDismiss}
        className="text-current opacity-60 hover:opacity-100"
        aria-label="Dismiss"
      >
        ✕
      </button>
    </div>
  )
}

function ToastEntry({ item }: { item: ToastItem }) {
  const removeToast = useAppStore((s) => s.removeToast)
  const handleDismiss = useCallback(() => removeToast(item.id), [item.id, removeToast])
  return <Toast item={item} onDismiss={handleDismiss} />
}

export function ToastContainer() {
  const toasts = useAppStore((s) => s.toasts)

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-live="polite">
      {toasts.map((item) => (
        <ToastEntry key={item.id} item={item} />
      ))}
    </div>
  )
}
