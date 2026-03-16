import { useEffect, useState } from 'react'

import { ExperimentConsolePage } from '@/components/experiment-console-page'
import { ConsoleSiteToolbar, type ConsolePageId } from '@/components/console-site-toolbar'
import { TrainingConsolePage } from '@/components/training-console-page'
import { useConsoleData } from '@/hooks/use-console-data'
import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

function App() {
  return (
    <ConsolePreferencesProvider>
      <ConsoleSite />
    </ConsolePreferencesProvider>
  )
}

function ConsoleSite() {
  const [currentPage, setCurrentPage] = useState<ConsolePageId>(() => readPageFromLocation())
  const consoleData = useConsoleData()

  useEffect(() => {
    const onPopState = () => {
      setCurrentPage(readPageFromLocation())
    }

    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  function handlePageChange(page: ConsolePageId) {
    const nextPath = page === 'training' ? '/training' : '/'

    setCurrentPage(page)

    if (typeof window !== 'undefined') {
      window.history.pushState(null, '', nextPath)
    }
  }

  return (
    <div className="console-app-shell min-h-screen">
      <div className="console-app-grid mx-auto flex min-h-screen max-w-[1600px] flex-col gap-4 px-4 py-4 lg:px-6">
        <ConsoleSiteToolbar currentPage={currentPage} onPageChange={handlePageChange} />
        {currentPage === 'experiment' ? (
          <ExperimentConsolePage {...consoleData} />
        ) : (
          <TrainingConsolePage />
        )}
      </div>
    </div>
  )
}

function readPageFromLocation(): ConsolePageId {
  if (typeof window === 'undefined') {
    return 'experiment'
  }

  return window.location.pathname === '/training' ? 'training' : 'experiment'
}

export default App
