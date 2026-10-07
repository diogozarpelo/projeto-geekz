import { apiRequest } from './api'
import type {
  AuthResponse,
  AuthUser,
  ChangePasswordPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  UpdateUserAddressPayload,
  UserAddressResponse,
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


export function updateCurrentUser(
  token: string,
  payload: UpdateProfilePayload,
  signal?: AbortSignal,
) {
  return apiRequest<AuthUser>(
    '/accounts/me/',
    {
      method: 'PATCH',
      token,
      body: payload,
      signal,
    },
  )
}



export function getCurrentUserAddress(
  token: string,
  signal?: AbortSignal,
) {
  return apiRequest<UserAddressResponse>(
    '/accounts/me/address/',
    {
      token,
      signal,
    },
  )
}

export function updateCurrentUserAddress(
  token: string,
  payload: UpdateUserAddressPayload,
  signal?: AbortSignal,
) {
  return apiRequest<UserAddressResponse>(
    '/accounts/me/address/',
    {
      method: 'PUT',
      token,
      body: payload,
      signal,
    },
  )
}

export function changePassword(
  token: string,
  payload: ChangePasswordPayload,
  signal?: AbortSignal,
) {
  return apiRequest<AuthResponse>(
    '/accounts/password/change/',
    {
      method: 'POST',
      token,
      body: payload,
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
