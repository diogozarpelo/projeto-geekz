import { apiRequest } from './api'
import type {
  AuthResponse,
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from '../types/auth'

export function login(
  payload: LoginPayload,
  signal?: AbortSignal,
) {
  return apiRequest<AuthResponse>(
    '/accounts/login/',
    {
      method: 'POST',
      body: payload,
      signal,
    },
  )
}

export function register(
  payload: RegisterPayload,
  signal?: AbortSignal,
) {
  return apiRequest<AuthResponse>(
    '/accounts/register/',
    {
      method: 'POST',
      body: payload,
      signal,
    },
  )
}

export function getCurrentUser(
  token: string,
  signal?: AbortSignal,
) {
  return apiRequest<AuthUser>(
    '/accounts/me/',
    {
      token,
      signal,
    },
  )
}

export function logout(
  token: string,
  signal?: AbortSignal,
) {
  return apiRequest<void>(
    '/accounts/logout/',
    {
      method: 'POST',
      token,
      signal,
    },
  )
}
