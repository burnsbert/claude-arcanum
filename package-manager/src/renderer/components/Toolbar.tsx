import { useAppStore } from '../store/appStore'

export function Toolbar() {
  const {
    stagedChanges,
    isLoading,
    darkMode,
    clearStaged,
    rescan,
    toggleDarkMode,
    setActiveSection,
  } = useAppStore()

  const stagedCount = stagedChanges.length

  return (
    <header className="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shrink-0">
      <h1 className="text-lg font-bold tracking-tight">
        Arcanum Package Manager
      </h1>

      <div className="flex items-center gap-3">
        {stagedCount > 0 && (
          <>
            <button
              type="button"
              onClick={() => clearStaged()}
              className="px-3 py-1.5 text-xs font-medium rounded-md bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/50 transition-colors"
            >
              Unstage Changes
            </button>
            <button
              type="button"
              onClick={() => setActiveSection('review')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-indigo-600 text-white hover:bg-indigo-700 transition-colors"
            >
              Commit Changes
              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-white/20 text-[10px]">
                {stagedCount}
              </span>
            </button>
          </>
        )}

        <button
          type="button"
          onClick={() => rescan()}
          disabled={isLoading}
          className="p-2 rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 transition-colors"
          aria-label="Reload"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>

        <button
          type="button"
          onClick={toggleDarkMode}
          className="p-2 rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {darkMode ? (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>
      </div>
    </header>
  )
}
