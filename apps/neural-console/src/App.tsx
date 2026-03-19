import { useEffect, useState } from 'react'

import { ExperimentConsolePage } from '@/components/experiment-console-page'
import { ConsoleSiteToolbar, type ConsolePageId } from '@/components/console-site-toolbar'
import { TrainingConsolePage } from '@/components/training-console-page'
import { useConsoleData } from '@/hooks/use-console-data'
import { MujocoFlyBrowserViewerPage } from '@/pages/mujoco-fly-browser-viewer/mujoco-fly-browser-viewer-page'
import { MujocoFlyOfficialRenderPage } from '@/pages/mujoco-fly-official-render/mujoco-fly-official-render-page'
import { MujocoFlyPage } from '@/pages/mujoco-fly/mujoco-fly-page'
import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

type ConsoleRouteId =
  | ConsolePageId
  | 'mujoco-fly'
  | 'mujoco-fly-official-render'
  | 'mujoco-fly-browser-viewer'

function App() {
  return (
    <ConsolePreferencesProvider>
      <ConsoleSite />
    </ConsolePreferencesProvider>
  )
}

function ConsoleSite() {
  const [currentPage, setCurrentPage] = useState<ConsoleRouteId>(() => readPageFromLocation())

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

  if (currentPage === 'mujoco-fly') {
    return (
      <div className="console-app-shell min-h-screen">
        <MujocoFlyPage />
      </div>
    )
  }

  if (currentPage === 'mujoco-fly-official-render') {
    return (
      <div className="console-app-shell min-h-screen">
        <MujocoFlyOfficialRenderPage />
      </div>
    )
  }

  if (currentPage === 'mujoco-fly-browser-viewer') {
    return (
      <div className="console-app-shell min-h-screen">
        <MujocoFlyBrowserViewerPage />
      </div>
    )
  }

  return <ConsoleDataSite currentPage={currentPage} onPageChange={handlePageChange} />
}

function ConsoleDataSite({
  currentPage,
  onPageChange,
}: {
  currentPage: ConsolePageId
  onPageChange: (page: ConsolePageId) => void
}) {
  const consoleData = useConsoleData()

  return (
    <div className="console-app-shell min-h-screen">
      <div className="console-app-grid mx-auto flex min-h-screen max-w-[1600px] flex-col gap-4 px-4 py-4 lg:px-6">
        <ConsoleSiteToolbar currentPage={currentPage} onPageChange={onPageChange} />
        {currentPage === 'experiment' ? (
          <ExperimentConsolePage {...consoleData} />
        ) : (
          <TrainingConsolePage />
        )}
      </div>
    </div>
  )
}

function readPageFromLocation(): ConsoleRouteId {
  if (typeof window === 'undefined') {
    return 'experiment'
  }

  if (window.location.pathname === '/training') {
    return 'training'
  }
  if (window.location.pathname === '/mujoco-fly-official-render') {
    return 'mujoco-fly-official-render'
  }
  if (window.location.pathname === '/mujoco-fly-browser-viewer') {
    return 'mujoco-fly-browser-viewer'
  }
  if (window.location.pathname === '/mujoco-fly') {
    return 'mujoco-fly'
  }
  return 'experiment'
}

export default App
