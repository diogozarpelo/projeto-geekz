import {
  useEffect,
  useState,
  type PropsWithChildren,
} from 'react'

import { AuthContext } from './AuthContext'
import {
  clearStoredAuthToken,
  getStoredAuthToken,
  storeAuthToken,
} from './authStorage'
import {
  getCurrentUser,
  login,
  logout,
  register,
} from '../services/auth'
import type {
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from '../types/auth'

export function AuthProvider({
  children,
}: PropsWithChildren) {
  const [token, setToken] = useState<string | null>(
    () => getStoredAuthToken(),
  )

  const [user, setUser] = useState<AuthUser | null>(
    null,
  )

  const [isLoading, setIsLoading] = useState(
    () => Boolean(getStoredAuthToken()),
  )

  useEffect(() => {
    if (!token) {
      return
    }

    const currentToken = token
    const controller = new AbortController()

    async function restoreSession() {
      try {
        const currentUser = await getCurrentUser(
          currentToken,
          controller.signal,
        )

        setUser(currentUser)
      } catch {
        if (controller.signal.aborted) {
          return
        }

        clearStoredAuthToken()
        setToken(null)
        setUser(null)
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false)
        }
      }
    }

    void restoreSession()

    return () => {
      controller.abort()
    }
  }, [token])

  async function signIn(payload: LoginPayload) {
    const response = await login(payload)

    storeAuthToken(response.token)
    setToken(response.token)
    setUser(response.user)
    setIsLoading(false)
  }

  async function signUp(payload: RegisterPayload) {
    const response = await register(payload)

    storeAuthToken(response.token)
    setToken(response.token)
    setUser(response.user)
    setIsLoading(false)
  }

  async function signOut() {
    const currentToken = token

    clearStoredAuthToken()
    setToken(null)
    setUser(null)
    setIsLoading(false)

    if (!currentToken) {
      return
    }

    try {
      await logout(currentToken)
    } catch {
      // A sessao local ja foi encerrada.
    }
  }

  const value = {
    token,
    user,
    isLoading,
    isAuthenticated: Boolean(token && user),
    signIn,
    signUp,
    signOut,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
