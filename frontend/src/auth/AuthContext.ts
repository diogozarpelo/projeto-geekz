import { createContext } from 'react'

import type {
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from '../types/auth'

export type AuthContextValue = {
  token: string | null
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  signIn: (payload: LoginPayload) => Promise<void>
  signUp: (payload: RegisterPayload) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
