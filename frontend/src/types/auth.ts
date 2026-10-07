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

export type UpdateProfilePayload = {
  first_name: string
  last_name: string
}

export type ChangePasswordPayload = {
  current_password: string
  new_password: string
  new_password_confirm: string
}

export type UserAddress = {
  id: number
  postal_code: string
  street: string
  number: string
  complement: string
  neighborhood: string
  city: string
  state: string
  country: string
  created_at: string
  updated_at: string
}

export type UserAddressResponse = {
  address: UserAddress | null
}

export type UpdateUserAddressPayload = {
  postal_code: string
  street: string
  number: string
  complement: string
  neighborhood: string
  city: string
  state: string
  country: string
}
