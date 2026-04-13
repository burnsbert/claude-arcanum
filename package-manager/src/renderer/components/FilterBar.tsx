import { useState, useEffect } from 'react'
import { useAppStore } from '../store/appStore'

export function FilterBar() {
  const { searchQuery, setSearchQuery, sortMode, setSortMode } = useAppStore()
  const [localQuery, setLocalQuery] = useState(searchQuery)

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => setSearchQuery(localQuery), 150)
    return () => clearTimeout(timer)
  }, [localQuery, setSearchQuery])

  // Sync if external reset
  useEffect(() => {
    setLocalQuery(searchQuery)
  }, [searchQuery])

  const hasFilters = searchQuery.length > 0

  return (
    <div className="flex items-center gap-3 px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      {/* Search */}
      <div className="relative flex-1 max-w-sm">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={localQuery}
          onChange={(e) => setLocalQuery(e.target.value)}
          placeholder="Search resources..."
          className="w-full pl-10 pr-3 py-2 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
      </div>

      {/* Sort toggle */}
      <button
        type="button"
        onClick={() => setSortMode(sortMode === 'recent' ? 'name' : 'recent')}
        className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-md border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
      >
        {sortMode === 'recent' ? 'Most recent' : 'By name'}
      </button>

      {/* Clear */}
      {hasFilters && (
        <button
          type="button"
          onClick={() => {
            setLocalQuery('')
            setSearchQuery('')
          }}
          className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          Clear
        </button>
      )}
    </div>
  )
}
