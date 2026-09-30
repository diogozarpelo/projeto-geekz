import { apiRequest } from './api'
import type {
  AddCartItemPayload,
  Cart,
  UpdateCartItemPayload,
} from '../types/cart'

export function getActiveCart(
  token: string,
  signal?: AbortSignal,
) {
  return apiRequest<Cart>(
    '/cart/',
    {
      token,
      signal,
    },
  )
}

export function addCartItem(
  token: string,
  payload: AddCartItemPayload,
  signal?: AbortSignal,
) {
  return apiRequest<Cart>(
    '/cart/items/',
    {
      method: 'POST',
      token,
      body: payload,
      signal,
    },
  )
}

export function updateCartItem(
  token: string,
  itemId: number,
  payload: UpdateCartItemPayload,
  signal?: AbortSignal,
) {
  return apiRequest<Cart>(
    `/cart/items/${itemId}/`,
    {
      method: 'PATCH',
      token,
      body: payload,
      signal,
    },
  )
}

export function removeCartItem(
  token: string,
  itemId: number,
  signal?: AbortSignal,
) {
  return apiRequest<Cart>(
    `/cart/items/${itemId}/`,
    {
      method: 'DELETE',
      token,
      signal,
    },
  )
}
