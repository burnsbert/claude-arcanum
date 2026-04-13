import { useEffect } from 'react'
import { useAppStore } from './store/appStore'
import { Toolbar } from './components/Toolbar'
import { Sidebar } from './components/Sidebar'
import { MainContent } from './components/MainContent'
import { ToastContainer } from './components/Toast'

export default function App() {
  const initialize = useAppStore((s) => s.initialize)

  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Toolbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <MainContent />
        </main>
      </div>
      <ToastContainer />
    </div>
  )
}
