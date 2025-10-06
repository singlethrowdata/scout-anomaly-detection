import React from 'react'
import ReactDOM from 'react-dom/client'
import {
  createRouter,
  RouterProvider,
  Outlet,
  RootRoute,
  Link,
  Route,
} from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Target } from 'lucide-react'

import ConfigTable from './routes/ConfigTable'
import Index from './routes/Index'
import Disasters from './routes/Disasters'
import Spam from './routes/Spam'
import Records from './routes/Records'
import Trends from './routes/Trends'
import './index.css'

const queryClient = new QueryClient()

// [AR1]: Scout brand identity visible in every view
const rootRoute = new RootRoute({
  component: () => (
    <div className="min-h-screen bg-scout-light">
      {/* STM-branded header with SCOUT identity */}
      <header className="bg-scout-blue text-white shadow-lg">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-scout-green" />
              <div>
                <h1 className="text-2xl font-bold tracking-tight">SCOUT</h1>
                <p className="text-xs text-scout-light/80">Statistical Client Observation & Unified Tracking</p>
              </div>
            </div>
            <nav className="flex gap-6">
              <Link
                to="/"
                className="px-4 py-2 rounded-md hover:bg-white/10 transition-colors [&.active]:bg-white/20 [&.active]:font-semibold"
              >
                Dashboard
              </Link>
              <Link
                to="/disasters"
                className="px-4 py-2 rounded-md hover:bg-white/10 transition-colors [&.active]:bg-white/20 [&.active]:font-semibold"
              >
                Disasters
              </Link>
              <Link
                to="/spam"
                className="px-4 py-2 rounded-md hover:bg-white/10 transition-colors [&.active]:bg-white/20 [&.active]:font-semibold"
              >
                Spam
              </Link>
              <Link
                to="/records"
                className="px-4 py-2 rounded-md hover:bg-white/10 transition-colors [&.active]:bg-white/20 [&.active]:font-semibold"
              >
                Records
              </Link>
              <Link
                to="/trends"
                className="px-4 py-2 rounded-md hover:bg-white/10 transition-colors [&.active]:bg-white/20 [&.active]:font-semibold"
              >
                Trends
              </Link>
              <Link
                to="/config"
                className="px-4 py-2 rounded-md hover:bg-white/10 transition-colors [&.active]:bg-white/20 [&.active]:font-semibold"
              >
                Configuration
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content area */}
      <main className="container mx-auto px-6 py-8">
        <Outlet />
      </main>

      {/* Footer with STM branding */}
      <footer className="mt-12 border-t bg-white">
        <div className="container mx-auto px-6 py-4 text-center text-sm text-scout-gray">
          <p>SCOUT Anomaly Detection System • Powered by STM Digital</p>
        </div>
      </footer>
    </div>
  ),
})

const indexRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Index,
})

const configRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/config',
  component: ConfigTable,
})

// [R17-R20]: 4-detector anomaly system routes
const disastersRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/disasters',
  component: Disasters,
})

const spamRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/spam',
  component: Spam,
})

const recordsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/records',
  component: Records,
})

const trendsRoute = new Route({
  getParentRoute: () => rootRoute,
  path: '/trends',
  component: Trends,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  configRoute,
  disastersRoute,
  spamRoute,
  recordsRoute,
  trendsRoute,
])

const router = createRouter({ routeTree })

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>,
)

