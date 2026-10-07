import { createContext } from 'react'

import type {
  AuthUser,
  ChangePasswordPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
} from '../types/auth'

export type AuthContextValue = {
  token: string | null
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
  signIn: (payload: LoginPayload) => Promise<void>
  signUp: (payload: RegisterPayload) => Promise<void>
  updateProfile: (
    payload: UpdateProfilePayload,
  ) => Promise<AuthUser>
  changePassword: (
    payload: ChangePasswordPayload,
  ) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
