import {
  Navigate,
  useLocation,
} from 'react-router-dom'

import { useAuth } from './useAuth'
import type { PropsWithChildren } from 'react'

export function RequireAuth({
  children,
}: PropsWithChildren) {
  const auth = useAuth()
  const location = useLocation()

  if (auth.isLoading) {
    return (
      <section className="page-section">
        <div className="container">
          <p className="eyebrow">Conta</p>
          <h1>Verificando sessão...</h1>
        </div>
      </section>
    )
  }

  if (!auth.isAuthenticated) {
    return (
      <Navigate
        replace
        to="/login"
        state={{
          from: location.pathname,
        }}
      />
    )
  }

  return children
}
