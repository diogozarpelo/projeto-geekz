export type AuthUser = {
  id: number
  email: string
  first_name: string
  last_name: string
}

export type AuthResponse = {
  token: string
  user: AuthUser
}

export type LoginPayload = {
  email: string
  password: string
}

export type RegisterPayload = {
  email: string
  first_name?: string
  last_name?: string
  password: string
  password_confirm: string
}
