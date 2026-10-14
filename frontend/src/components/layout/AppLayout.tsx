import { Outlet } from 'react-router-dom'

import { Footer } from './Footer'
import { Header } from './Header'

export function AppLayout() {
  return (
    <div className="app-shell">
      <Header />

      <main
        id="main-content"
        className="main-content"
        tabIndex={-1}
      >
        <Outlet />
      </main>

      <Footer />
    </div>
  )
}
