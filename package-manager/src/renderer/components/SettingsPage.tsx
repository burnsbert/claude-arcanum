import { useAppStore, startSystemThemeListener, stopSystemThemeListener } from '../store/appStore'

export function SettingsPage() {
  const { config, plugin, showNonArcanum, toggleNonArcanum } = useAppStore()

  if (!config) return null

  const handleInstallMethodChange = async (method: 'symlink' | 'copy') => {
    await window.api.setConfig({ defaultInstallMethod: method })
    useAppStore.setState((s) => ({
      config: s.config ? { ...s.config, defaultInstallMethod: method } : s.config,
    }))
  }

  const handleThemeChange = async (theme: 'light' | 'dark' | 'system') => {
    await window.api.setConfig({ theme })
    useAppStore.setState((s) => ({
      config: s.config ? { ...s.config, theme } : s.config,
    }))

    if (theme === 'dark') {
      stopSystemThemeListener()
      useAppStore.setState({ darkMode: true })
      document.documentElement.classList.add('dark')
    } else if (theme === 'light') {
      stopSystemThemeListener()
      useAppStore.setState({ darkMode: false })
      document.documentElement.classList.remove('dark')
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      useAppStore.setState({ darkMode: prefersDark })
      if (prefersDark) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
      startSystemThemeListener()
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Repo Info */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Repository</h3>
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500 dark:text-gray-400 w-16">Path:</span>
            <code className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
              {config.repoPath || '(not detected)'}
            </code>
          </div>
          {plugin && (
            <>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500 dark:text-gray-400 w-16">Plugin:</span>
                <span className="text-xs">{plugin.name} v{plugin.version}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500 dark:text-gray-400 w-16">Resources:</span>
                <span className="text-xs">
                  {plugin.agents.length} agents, {plugin.commands.length} commands, {plugin.skills.length} skills
                </span>
              </div>
            </>
          )}
        </div>
      </section>

      <hr className="border-gray-200 dark:border-gray-700" />

      {/* Install Method */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Default Install Method</h3>
        <div className="space-y-2">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="radio"
              name="installMethod"
              checked={config.defaultInstallMethod === 'symlink'}
              onChange={() => handleInstallMethodChange('symlink')}
              className="mt-0.5"
            />
            <div>
              <span className="text-sm font-medium">Symlink</span>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Resources auto-update when the repo changes. Recommended.
              </p>
            </div>
          </label>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="radio"
              name="installMethod"
              checked={config.defaultInstallMethod === 'copy'}
              onChange={() => handleInstallMethodChange('copy')}
              className="mt-0.5"
            />
            <div>
              <span className="text-sm font-medium">Copy</span>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Independent copies that don't change when the repo updates.
              </p>
            </div>
          </label>
        </div>
      </section>

      <hr className="border-gray-200 dark:border-gray-700" />

      {/* Display */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Display</h3>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={showNonArcanum}
            onChange={toggleNonArcanum}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
          />
          <span className="text-sm">Show non-Arcanum resources</span>
        </label>
      </section>

      <hr className="border-gray-200 dark:border-gray-700" />

      {/* Theme */}
      <section>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Theme</h3>
        <div className="flex gap-4">
          {(['system', 'light', 'dark'] as const).map((theme) => (
            <label key={theme} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="theme"
                checked={config.theme === theme}
                onChange={() => handleThemeChange(theme)}
              />
              <span className="text-sm capitalize">{theme}</span>
            </label>
          ))}
        </div>
      </section>
    </div>
  )
}
